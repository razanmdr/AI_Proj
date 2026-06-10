# 📊 FinanceBot — RAG Financial Document Analyst

A **Retrieval-Augmented Generation (RAG)** app that lets you upload financial documents (PDF annual reports, CSV/Excel data) and ask questions about them in natural language — powered by **Gemini 1.5 Flash** and **ChromaDB**.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red?logo=streamlit)
![Gemini](https://img.shields.io/badge/Gemini-API-blue?logo=google)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-orange)

---

## ✨ Features

- 📄 **PDF support** — parse annual reports, financial statements, earnings releases
- 📊 **CSV/Excel support** — index tabular financial data row by row
- 🔍 **Semantic search** — Google `text-embedding-004` for high-quality retrieval
- 💬 **Multi-turn chat** — conversation history preserved across questions
- 📎 **Source transparency** — see exactly which chunks were used per answer
- 🗄️ **Persistent vector store** — ChromaDB stores embeddings locally between sessions
- 🆓 **Fully free** — Gemini free tier + local ChromaDB

---

## 🏗️ Architecture

```
User uploads PDF / CSV / Excel
         │
         ▼
document_loader.py     ← Parse into text chunks (per page / per 10 rows)
         │
         ▼
vector_store.py        ← Embed with Google text-embedding-004 → store in ChromaDB
         │
   User asks question
         │
         ▼
vector_store.py        ← Embed query → cosine similarity search → top-5 chunks
         │
         ▼
rag_assistant.py       ← Build augmented prompt (context + question) → Gemini
         │
         ▼
app.py                 ← Display answer + source citations in Streamlit UI
```

---

## 🗂️ Project Structure

```
finance-rag/
├── app.py                  # Streamlit UI (3-column layout)
├── rag_assistant.py        # RAG pipeline + Gemini generation
├── vector_store.py         # ChromaDB + Google Embeddings
├── document_loader.py      # PDF (PyMuPDF) + CSV/Excel parser
├── requirements.txt
├── chroma_db/              # Auto-created: persistent vector store
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/YOUR_USERNAME/finance-rag.git
cd finance-rag
pip install -r requirements.txt
```

### 2. Get Gemini API key (free)

👉 [aistudio.google.com](https://aistudio.google.com) → **Get API key** → no billing required

Free tier: **1,500 requests/day**, **15 req/min** — plenty for personal use.

### 3. Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501), enter your API key in the sidebar, upload a document, and start asking!

---

## 💡 Example Questions

After uploading a financial document:

| Question | What it retrieves |
|---|---|
| *"What was the total revenue last year?"* | Revenue figures from income statement |
| *"Summarize the key financial highlights"* | Executive summary / highlights section |
| *"What are the main risk factors?"* | Risk factors section of annual report |
| *"Compare revenue across quarters"* | Quarterly breakdown table |
| *"What is the net profit margin?"* | Net income + revenue → calculated margin |

---

## 📄 Supported Documents

| Type | Format | Notes |
|---|---|---|
| Annual reports | PDF | Parsed page by page |
| Financial statements | PDF | P&L, balance sheet, cash flow |
| Earnings data | CSV | Each row becomes searchable context |
| Financial models | Excel (.xlsx) | Multi-sheet support |

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| LLM | Gemini 1.5 Flash (Google) — free |
| Embeddings | Google `text-embedding-004` — free |
| Vector store | ChromaDB (local, persistent) |
| PDF parsing | PyMuPDF (fitz) |
| Tabular data | Pandas |
| Frontend | Streamlit |

---

## 🔮 Future Ideas

- [ ] Multi-document comparison ("compare revenue between Company A and B")
- [ ] Chart generation from financial data (matplotlib / plotly)
- [ ] Export Q&A session as PDF report
- [ ] Deploy to Streamlit Cloud with `.streamlit/secrets.toml` for API key

---

## 📄 License

MIT License
