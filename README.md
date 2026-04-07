#  BrainDocs AI

> ⚡ *Chat with your documents — fully offline, private, and cost-efficient.*

BrainDocs AI is a **full-stack Retrieval-Augmented Generation (RAG) system** that enables users to interact with documents (PDFs, CSVs, images, etc.) using natural language.

It combines:

*  **Semantic search (FAISS)**
*  **Keyword search (BM25)**
*  **LLMs (Ollama / API)**

to deliver **accurate, source-grounded answers**.

---

#  Features

*  Upload & auto-index documents (no restart required)
*  Supports: PDF, TXT, CSV, DOCX, XLSX, Images (OCR)
*  Hybrid Retrieval (FAISS + BM25)
*  Local LLM (Ollama) + Cloud fallback (Groq)
*  Source-based answers with score & metadata
*  Chat UI with session history
*  Real-time ingestion & querying

---

#  Architecture

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

# 📁 Project Structure

```text
braindocs_ai/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── embeddings.py
│   │   │
│   │   ├── services/
│   │   │   ├── llm.py
│   │   │   ├── chunker.py
│   │   │   ├── ingestion.py
│   │   │   ├── retriever.py
│   │   │   ├── bm25_retriever.py
│   │   │   ├── reranker.py
│   │   │   ├── rag_pipeline.py
│   │   │   ├── memory.py
│   │   │   └── vector_store.py
│   │   │
│   │   └── utils/
│   │       └── file_loader.py
│   │
│   ├── data_room/
│   ├── vector_db/
│   ├── requirements.txt
│   └── .env
│
├── braindocs-frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   │
│   ├── components/
│   │   ├── ChatWindow.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── Sidebar.tsx
│   │   └── PDFViewer.tsx
│   │
│   ├── public/
│   ├── styles/
│   ├── package.json
│   └── .env.local
│
├── docs/
│   └── images/
│
├── .gitignore
└── README.md
```

---

# ⚙️ Tech Stack

## Backend

* FastAPI
* FAISS
* Sentence Transformers (MiniLM)
* BM25 (rank-bm25)
* Pandas
* PyPDF / Tesseract OCR

---

## Frontend

* Next.js (React)
* TypeScript
* Tailwind CSS
* Axios / Fetch

---

## AI / LLM

* Ollama (Phi-3) → Local offline LLM
* Groq API (Llama 3) → Cloud inference

---

#  System Capabilities

* Hybrid Retrieval (Semantic + Keyword)
* Offline AI (Local LLM)
* Cloud fallback support
* Real-time document ingestion
* Source-grounded answers

---

#  Design Principles

* Offline-first architecture
* Modular RAG pipeline
* Cost-efficient AI (no mandatory APIs)
* Scalable full-stack design

---

#  Local Setup (Offline Ready)

## Backend

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

## Install Ollama (Offline AI)

```bash
ollama run phi3
```

---

## Environment Config

```env
LLM_MODE=local
GROQ_API_KEY=your_key_here
```

---

## Run Backend

```powershell
uvicorn app.main:app --reload
```

http://127.0.0.1:8000

---

#  Frontend Setup

```powershell
cd braindocs-frontend
npm install
npm run dev
```

 http://localhost:3000

---

##  Frontend Env

```env
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
```

---

# How It Works

1. Upload document
2. File stored in `data_room`
3. Auto-ingestion starts
4. Text → chunks → embeddings
5. Stored in FAISS + BM25
6. Query → hybrid retrieval
7. LLM generates answer
8. UI shows answer + sources

---

#  API Endpoints

| Endpoint         | Description       |
| ---------------- | ----------------- |
| GET `/`          | Health check      |
| POST `/upload`   | Upload & ingest   |
| GET `/ask`       | Query documents   |
| GET `/documents` | List indexed docs |

---

# Troubleshooting

### ❌ Backend offline

* Check if running on port 8000
* Verify frontend API URL

### ❌ "I don't know"

* Re-upload file
* Check ingestion logs

### ❌ OCR issues

* Install Tesseract OCR
* Add to PATH

### ❌ Empty vector DB

```bash
rm -rf backend/vector_db
```

---

# Deployment (Free)

| Component | Platform |
| --------- | -------- |
| Frontend  | Vercel   |
| Backend   | Render   |
| LLM       | Groq     |

---

# Future Improvements

* Authentication system
* PDF page highlighting
* Streaming responses
* CSV analytics
* Usage tracking

---

# Use Cases

* Document Q&A
* Research assistant
* Resume analysis
* Knowledge base chatbot

---

# Final Note

This project demonstrates:

* Full-stack AI engineering
* RAG system design
* Hybrid retrieval architecture
* Offline-first AI systems

---

>  BrainDocs AI is a **production-ready, privacy-first document intelligence system**.

---

⭐ *Star the repo if you found it useful!*
