# BrainDocs AI

BrainDocs AI is a full-stack RAG document Q and A system built with FastAPI, Next.js, Ollama, sentence-transformers, FAISS, and BM25.

It supports upload, auto-ingestion, hybrid retrieval, and grounded responses with strict source attribution.

## Frontend Preview

![BrainDocs AI Frontend Layout](docs/images/frontend-layout.svg)

## Key Features

- Upload and auto-index without backend restart
- Supported documents: PDF, TXT, CSV, DOCX, DOC, XLSX, XLS, PNG, JPG, JPEG, WEBP, BMP, TIF, TIFF
- Hybrid retrieval: semantic search (FAISS) + keyword search (BM25)
- Strict single-source mode to reduce hallucination and mixed-context noise
- Optional structured multi-source comparison mode for compare-style questions
- Chat history panel with auto-named sessions
- Indexed documents panel in frontend

## Project Structure

```text
braindocs_ai/
	backend/
		app/
			main.py
			core/
			services/
			utils/
		data_room/
		vector_db/
	braindocs-frontend/
		app/
		components/
	docs/
		images/
```

## Architecture

1. User uploads a file from frontend
2. Backend saves file in backend/data_room
3. Backend parses file into records
4. Text is chunked and embedded
5. Vectors and metadata are saved in FAISS and meta store
6. BM25 index is rebuilt from active corpus
7. Query runs through hybrid retrieval and strict grounding
8. LLM generates answer from selected context only
9. Frontend renders answer and sources

## Backend Setup (FastAPI)

### 1. Create and activate virtual environment

PowerShell:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install fastapi uvicorn requests faiss-cpu sentence-transformers rank-bm25 pandas pypdf python-docx openpyxl pillow pytesseract
```

Optional for legacy DOC parsing:

```powershell
pip install textract
```

### 3. Run backend

```powershell
uvicorn app.main:app --reload
```

Backend URL:

- http://127.0.0.1:8000

## Frontend Setup (Next.js)

```powershell
cd braindocs-frontend
npm install
npm run dev
```

Frontend URL:

- http://localhost:3000

Optional frontend environment variable:

Create braindocs-frontend/.env.local

```text
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
```

## API Endpoints

### GET /

Health root status.

### GET /health

Backend connectivity check for frontend status indicator.

### POST /upload

Multipart upload and immediate ingestion.

Response example:

```json
{
	"status": "success",
	"message": "File uploaded and indexed",
	"file": "sample.pdf",
	"ingestion": {
		"status": "indexed",
		"source": "sample.pdf",
		"chunks": 12,
		"documents": 48
	}
}
```

### POST /ask

Request body:

```json
{
	"query": "What is unit 1 syllabus?",
	"top_k": 3
}
```

Response format:

```json
{
	"answer": "...",
	"sources": [
		{
			"source": "ml-syllabus.png",
			"page": 1,
			"score": 0.71
		}
	]
}
```

### GET /documents

Returns indexed document summary for frontend panel.

## Retrieval and Grounding Behavior

- Intent-aware token filtering for queries like syllabus, unit, curriculum
- Lexical overlap filtering to remove weakly relevant chunks
- Strict single-source mode is enabled by default
- Multi-source structured output is only used for compare-style queries
- Answer cleanup removes boilerplate and enforces concise output

## OCR Notes (Images)

Image OCR quality depends on local OCR setup.

- Required: pytesseract Python package
- Required: Tesseract OCR executable installed and available in PATH

If OCR is missing, image ingestion may return no usable text.

## Common Troubleshooting

### Backend says offline in UI

- Confirm backend is running on http://127.0.0.1:8000
- Check CORS and frontend backend URL value

### Upload works but answer is I do not know

- Verify file appears in backend/data_room
- Verify file appears in indexed documents panel
- Re-upload file to refresh chunks for that source

### OCR image answer is poor

- Ensure Tesseract OCR is installed and in PATH
- Upload a clearer, higher contrast image

### Empty or stale vector index

- Delete backend/vector_db and re-upload documents
- Restart backend and check logs for chunk and ingestion counts

## Production Readiness Notes

- Add authentication and file-level access control
- Add persistent database for chat sessions and audit logs
- Add background job queue for heavy ingestion workloads
- Add monitoring and tracing for latency and failures

## License

Use and modify freely for learning and internal project work.
