import fitz  # PyMuPDF
import pandas as pd
import re
from pathlib import Path


def load_document(file_path: str, filename: str) -> list[dict]:
    """
    Load a PDF or CSV/Excel file and return a list of text chunks with metadata.

    Each chunk: {"text": str, "source": str, "page": int or None, "chunk_id": str}
    """
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return _load_pdf(file_path, filename)
    elif ext in [".csv"]:
        return _load_csv(file_path, filename)
    elif ext in [".xlsx", ".xls"]:
        return _load_excel(file_path, filename)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _load_pdf(file_path: str, filename: str) -> list[dict]:
    """Extract text from PDF, split into chunks per page."""
    chunks = []
    doc = fitz.open(file_path)

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        if not text or len(text) < 50:
            continue

        # Split long pages into smaller chunks (~500 chars)
        sub_chunks = _split_text(text, chunk_size=500, overlap=50)
        for i, chunk_text in enumerate(sub_chunks):
            chunks.append({
                "text": chunk_text,
                "source": filename,
                "page": page_num,
                "chunk_id": f"{filename}_p{page_num}_c{i}",
            })

    doc.close()
    return chunks


def _load_csv(file_path: str, filename: str) -> list[dict]:
    """Convert CSV rows into descriptive text chunks."""
    df = pd.read_csv(file_path)
    return _dataframe_to_chunks(df, filename)


def _load_excel(file_path: str, filename: str) -> list[dict]:
    """Convert Excel sheets into descriptive text chunks."""
    xl = pd.ExcelFile(file_path)
    all_chunks = []
    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        chunks = _dataframe_to_chunks(df, filename, sheet_name=sheet)
        all_chunks.extend(chunks)
    return all_chunks


def _dataframe_to_chunks(df: pd.DataFrame, filename: str, sheet_name: str = None) -> list[dict]:
    """
    Convert a DataFrame into text chunks.
    Groups rows into batches of 10 to keep context per chunk.
    """
    chunks = []
    df = df.dropna(how="all").fillna("N/A")
    cols = df.columns.tolist()

    # Summary chunk: column overview
    summary = f"File: {filename}"
    if sheet_name:
        summary += f" | Sheet: {sheet_name}"
    summary += f"\nColumns: {', '.join(cols)}\nTotal rows: {len(df)}\n"
    summary += f"Sample data:\n{df.head(5).to_string(index=False)}"
    chunks.append({
        "text": summary,
        "source": filename,
        "page": None,
        "chunk_id": f"{filename}_summary",
    })

    # Row batches
    batch_size = 10
    for batch_start in range(0, len(df), batch_size):
        batch = df.iloc[batch_start: batch_start + batch_size]
        lines = []
        for _, row in batch.iterrows():
            row_text = " | ".join(f"{col}: {row[col]}" for col in cols)
            lines.append(row_text)
        chunk_text = "\n".join(lines)
        chunks.append({
            "text": chunk_text,
            "source": filename,
            "page": None,
            "chunk_id": f"{filename}_rows_{batch_start}",
        })

    return chunks


def _split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks by word boundaries."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i: i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
    return chunks


def get_file_summary(chunks: list[dict]) -> str:
    """Return a brief summary of what was loaded."""
    sources = {}
    for c in chunks:
        src = c["source"]
        sources[src] = sources.get(src, 0) + 1
    lines = [f"• {src}: {count} chunks" for src, count in sources.items()]
    return "\n".join(lines)
