import io
import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def _load_pdf(content: bytes) -> list[dict[str, Any]]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except Exception as exc:
            raise RuntimeError("PDF parser not available. Install pypdf or PyPDF2") from exc

    reader = PdfReader(io.BytesIO(content))
    records: list[dict[str, Any]] = []

    for idx, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        records.append({"text": text, "page": idx})

    return records


def _load_csv(content: bytes) -> list[dict[str, Any]]:
    df = pd.read_csv(io.BytesIO(content), dtype=str).fillna("")
    records: list[dict[str, Any]] = []

    for row_index, row in df.iterrows():
        parts = []
        for col in df.columns:
            value = str(row[col]).strip()
            if value:
                parts.append(f"{col} is {value}")

        if not parts:
            continue

        text = f"Row {row_index + 1}: " + "; ".join(parts)
        records.append({"text": text, "page": row_index + 1})

    return records


def _load_excel(content: bytes) -> list[dict[str, Any]]:
    workbook = pd.read_excel(io.BytesIO(content), sheet_name=None, dtype=str)
    records: list[dict[str, Any]] = []

    for sheet_name, df in workbook.items():
        safe_df = df.fillna("")
        for row_index, row in safe_df.iterrows():
            parts = []
            for col in safe_df.columns:
                value = str(row[col]).strip()
                if value:
                    parts.append(f"{col} is {value}")

            if not parts:
                continue

            text = f"Sheet {sheet_name}, row {row_index + 1}: " + "; ".join(parts)
            records.append({"text": text, "page": row_index + 1})

    return records


def _load_docx(content: bytes) -> list[dict[str, Any]]:
    try:
        from docx import Document  # type: ignore
    except Exception as exc:
        raise RuntimeError("DOCX parser not available. Install python-docx") from exc

    doc = Document(io.BytesIO(content))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    if not paragraphs:
        return []

    text = "\n".join(paragraphs)
    return [{"text": text, "page": 1}]


def _load_doc(content: bytes) -> list[dict[str, Any]]:
    try:
        import tempfile
        import textract  # type: ignore
    except Exception as exc:
        raise RuntimeError("DOC parser not available. Install textract for .doc support") from exc

    with tempfile.NamedTemporaryFile(suffix=".doc", delete=True) as temp:
        temp.write(content)
        temp.flush()
        extracted = textract.process(temp.name)

    text = extracted.decode("utf-8", errors="ignore").strip()
    if not text:
        return []
    return [{"text": text, "page": 1}]


def _load_image(content: bytes) -> list[dict[str, Any]]:
    try:
        from PIL import Image, ImageOps  # type: ignore
    except Exception as exc:
        raise RuntimeError("Image parser not available. Install pillow") from exc

    try:
        import pytesseract  # type: ignore
    except Exception as exc:
        raise RuntimeError("OCR not available. Install pytesseract and Tesseract OCR") from exc

    image = Image.open(io.BytesIO(content))
    image = ImageOps.exif_transpose(image)

    # OCR works better with grayscale + contrast and a couple of page-seg modes.
    candidates = [
        image,
        ImageOps.autocontrast(image.convert("L")),
    ]
    configs = [
        "--oem 3 --psm 6",
        "--oem 3 --psm 11",
    ]

    best_text = ""
    for candidate in candidates:
        for config in configs:
            text = (pytesseract.image_to_string(candidate, config=config) or "").strip()
            if len(text) > len(best_text):
                best_text = text

    if not best_text:
        return []
    return [{"text": best_text, "page": 1}]


def _load_text(content: bytes) -> list[dict[str, Any]]:
    text = content.decode("utf-8", errors="ignore").strip()
    if not text:
        return []
    return [{"text": text, "page": 1}]


def load_file(filename: str, content: bytes) -> list[dict[str, Any]]:
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        records = _load_pdf(content)
    elif suffix == ".csv":
        records = _load_csv(content)
    elif suffix in {".xlsx", ".xls"}:
        records = _load_excel(content)
    elif suffix == ".docx":
        records = _load_docx(content)
    elif suffix == ".doc":
        records = _load_doc(content)
    elif suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}:
        records = _load_image(content)
    elif suffix in {".txt", ".md"}:
        records = _load_text(content)
    else:
        records = _load_text(content)

    logger.info("Parsed %s into %s records", filename, len(records))
    return records