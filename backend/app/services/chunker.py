from app.core.config import CHUNK_SIZE, CHUNK_OVERLAP

def chunk_text(text):
    chunks = []
    for i in range(0, len(text), CHUNK_SIZE - CHUNK_OVERLAP):
        chunks.append(text[i:i+CHUNK_SIZE])
    return chunks