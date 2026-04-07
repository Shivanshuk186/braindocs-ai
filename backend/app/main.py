import logging
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.services.ingestion import ingest_data_room, ingest_file
from app.services.rag_pipeline import query_rag
from app.services.vector_store import get_corpus, load as load_vector_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_ROOM_DIR = BASE_DIR / "data_room"

app = FastAPI(title="BrainDocs AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    query: str = Field(min_length=1, description="User question")
    top_k: int | None = Field(default=None, ge=1, le=20)


@app.get("/")
def root() -> dict:
    return {"status": "ok", "service": "braindocs-ai"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask")
def ask(request: AskRequest) -> dict:
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        return query_rag(query=query, top_k=request.top_k)
    except Exception as exc:
        logger.exception("/ask failed")
        raise HTTPException(status_code=500, detail=f"RAG pipeline failed: {exc}") from exc


@app.get("/ask")
def ask_get(
    query: str = Query(..., min_length=1),
    top_k: int | None = Query(default=None, ge=1, le=20),
) -> dict:
    return query_rag(query=query.strip(), top_k=top_k)


@app.post("/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file name")

    suffix = Path(file.filename).suffix.lower()
    allowed_suffixes = {
        ".pdf",
        ".csv",
        ".txt",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".bmp",
        ".tif",
        ".tiff",
    }
    if suffix not in allowed_suffixes:
        raise HTTPException(
            status_code=400,
            detail="Supported formats: PDF, CSV, TXT, DOC, DOCX, XLS, XLSX, PNG, JPG, JPEG, WEBP, BMP, TIF, TIFF",
        )

    DATA_ROOM_DIR.mkdir(parents=True, exist_ok=True)
    file_path = DATA_ROOM_DIR / Path(file.filename).name

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    file_path.write_bytes(content)
    logger.info("Saved upload: %s", file_path)

    try:
        ingest_result = ingest_file(filename=file_path.name, content=content)
    except Exception as exc:
        logger.exception("Ingestion failed for uploaded file: %s", file_path.name)
        raise HTTPException(status_code=500, detail=f"Upload saved but ingestion failed: {exc}") from exc

    return {
        "status": "success",
        "message": "File uploaded and indexed",
        "file": file_path.name,
        "ingestion": ingest_result,
    }


@app.get("/documents")
def documents() -> dict:
    corpus = get_corpus()
    grouped: dict[str, dict] = {}

    for item in corpus:
        source = item.get("source", "unknown")
        page = item.get("page")
        if source not in grouped:
            grouped[source] = {
                "source": source,
                "chunks": 0,
                "pages": set(),
            }

        grouped[source]["chunks"] += 1
        if page is not None:
            grouped[source]["pages"].add(page)

    docs = []
    for data in grouped.values():
        docs.append(
            {
                "source": data["source"],
                "chunks": data["chunks"],
                "pages": len(data["pages"]),
            }
        )

    docs.sort(key=lambda x: x["source"].lower())
    return {"documents": docs}


@app.on_event("startup")
def startup() -> None:
    logger.info("Startup: loading persisted vector store")
    load_vector_store()
    logger.info("Startup: ingesting data_room")
    ingest_data_room()