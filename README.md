# BrainDocs AI

BrainDocs AI is a **full-stack Retrieval-Augmented Generation (RAG) system** that allows users to chat with documents like PDFs, CSVs, and images using AI.

It combines **semantic search (FAISS)**, **keyword search (BM25)**, and **LLMs (Ollama / API)** to deliver **accurate, source-grounded answers**.

---

##  Features

*  Upload & auto-index documents (no restart required)
*  Supports: PDF, TXT, CSV, DOCX, XLSX, Images (OCR)
*  Hybrid Retrieval (FAISS + BM25)
*  Local LLM (Ollama) + Cloud LLM fallback
*  Source-based answers with score & metadata
*  Chat UI with session history
*  Real-time ingestion & querying

---

##  Architecture

```text
User → Frontend (Next.js)
      ↓
FastAPI Backend
      ↓
Ingestion Pipeline
  ├── File Loader (PDF, CSV, OCR)
  ├── Chunking
  ├── Embeddings (MiniLM)
  ├── FAISS (Vector DB)
  ├── BM25 (Keyword Index)
      ↓
Retrieval Pipeline
  ├── Semantic Search
  ├── Keyword Search
  ├── Hybrid Merge + Rerank
      ↓
LLM (Ollama / API)
      ↓
Response + Sources → Frontend
```

---

## 📁 Project Structure

```text
braindocs_ai/
├── backend/
│   ├── app/
│   ├── data_room/
│   └── vector_db/
├── braindocs-frontend/
├── docs/
│   └── images/
```

---

# LOCAL SETUP (FULL OFFLINE SUPPORT)

##  1. Backend Setup (FastAPI)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Install dependencies

```powershell
pip install fastapi uvicorn requests faiss-cpu sentence-transformers rank-bm25 pandas pypdf python-docx openpyxl pillow pytesseract python-dotenv
```

---

##  2. (OPTIONAL BUT IMPORTANT) Install Ollama

 Required for **offline AI mode**

Install Ollama and run:

```bash
ollama run phi3
```

---

##  3. Environment Configuration

Create:

```text
backend/.env
```

```env
LLM_MODE=local   # local OR api
GROQ_API_KEY=your_key_here
```

---

##  4. Run Backend

```powershell
uvicorn app.main:app --reload
```

Backend runs on:

```
http://127.0.0.1:8000
```

---

#  Frontend Setup (Next.js)

```powershell
cd braindocs-frontend
npm install
npm run dev
```

Frontend runs on:

```
http://localhost:3000
```

---

##  Frontend Environment (Optional)

Create:

```text
braindocs-frontend/.env.local
```

```env
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
```

---

#  HOW IT WORKS

1. Upload file via UI
2. File saved in `backend/data_room`
3. Auto-ingestion starts
4. Chunks + embeddings created
5. Stored in FAISS + BM25
6. Query → hybrid retrieval
7. LLM generates grounded answer
8. UI shows answer + sources

---

#  API ENDPOINTS

## Health

```
GET /
```

## Upload File

```
POST /upload
```

## Ask Question

```
GET /ask?query=your_question
```

## Documents List

```
GET /documents
```

---

# LLM MODES

| Mode    | Description                |
| ------- | -------------------------- |
| `local` | Uses Ollama (offline AI)   |
| `api`   | Uses cloud LLM (e.g. Groq) |

Automatic switching via `.env`

---

#  TROUBLESHOOTING

### ❌ Backend offline in UI

* Ensure backend is running on port 8000
* Check frontend API URL

---

### ❌ "I don't know" answers

* Re-upload file
* Check ingestion logs (chunk count)
* Verify document appears in index

---

### ❌ OCR not working

* Install Tesseract OCR
* Ensure it's in system PATH

---

### ❌ Empty vector DB

```powershell
rm -rf backend/vector_db
```

Restart and re-upload

---

#  DEPLOYMENT (FREE)

| Component | Platform |
| --------- | -------- |
| Frontend  | Vercel   |
| Backend   | Render   |
| LLM       | Groq     |

---

#  FUTURE IMPROVEMENTS

* Authentication system
*  PDF page highlighting
*  Streaming responses
*  Structured CSV querying
*  Usage analytics

---

#  USE CASES

* Research document Q&A
* Resume analysis
* Internal knowledge bots
* Academic syllabus queries

---

#  FINAL NOTE

This project demonstrates:

* Full-stack AI system design
* Hybrid retrieval (FAISS + BM25)
* Local + cloud LLM architecture

---

**If you like this project, give it a ⭐ on GitHub!**
