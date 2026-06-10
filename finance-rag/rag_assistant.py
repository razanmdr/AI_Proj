import google.generativeai as genai
from vector_store import query_documents

SYSTEM_PROMPT = """You are FinanceBot, an expert financial analyst assistant.

You answer questions based strictly on the financial documents provided as context.
The documents may include annual reports, financial statements, earnings data, or tabular CSV/Excel data.

Rules:
- Base your answer only on the provided context. Do not make up numbers.
- If the context doesn't contain enough information, say so clearly.
- When citing figures, mention the source document and page if available.
- Be precise with numbers: use the exact values from the documents.
- Format financial figures clearly (e.g., £1.2M, $500K, 15.3%).
- Keep responses concise and professional.
"""


def build_context(retrieved_chunks: list[dict]) -> str:
    """Format retrieved chunks into a context block for the prompt."""
    if not retrieved_chunks:
        return "No relevant documents found."

    lines = ["=== RETRIEVED CONTEXT ==="]
    for i, chunk in enumerate(retrieved_chunks, 1):
        source_label = chunk["source"]
        if chunk["page"] != "N/A":
            source_label += f" (page {chunk['page']})"
        lines.append(f"\n[{i}] Source: {source_label} | Relevance: {chunk['score']}")
        lines.append(chunk["text"])
        lines.append("---")
    return "\n".join(lines)


def rag_chat(
    query: str,
    conversation_history: list,
    api_key: str,
    n_chunks: int = 5,
) -> tuple[str, list, list[dict]]:
    """
    RAG pipeline: retrieve relevant chunks → augment prompt → generate answer.

    Returns:
        (answer, updated_history, retrieved_chunks)
    """
    genai.configure(api_key=api_key)

    # Step 1: Retrieve relevant chunks
    retrieved = query_documents(query, api_key, n_results=n_chunks)
    context = build_context(retrieved)

    # Step 2: Build augmented prompt
    augmented_query = f"""{context}

=== QUESTION ===
{query}

Please answer based on the context above."""

    # Step 3: Convert history to Gemini format
    gemini_history = []
    for msg in conversation_history:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    # Step 4: Call Gemini
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=SYSTEM_PROMPT,
    )
    chat_session = model.start_chat(history=gemini_history)
    response = chat_session.send_message(augmented_query)
    answer = response.text

    # Step 5: Update history (store clean query, not augmented)
    updated_history = conversation_history + [
        {"role": "user", "content": query},
        {"role": "assistant", "content": answer},
    ]

    return answer, updated_history, retrieved


def generate_document_summary(chunks: list[dict], api_key: str) -> str:
    """Generate a brief overview of the uploaded document(s)."""
    genai.configure(api_key=api_key)

    # Use first 5 chunks as sample
    sample_text = "\n\n".join(c["text"] for c in chunks[:5])
    prompt = f"""Based on these excerpts from financial documents, provide a 3-sentence summary of what data is available:

{sample_text}

Summary:"""

    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text
