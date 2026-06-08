import google.generativeai as genai
import pandas as pd
from product_search import (
    search_products,
    get_top_sellers,
    get_budget_picks,
    format_products_for_prompt,
    extract_price_from_message,
    extract_keywords_from_message,
)

SYSTEM_PROMPT = """You are ShopBot, a friendly and helpful virtual shopping assistant for an online retail store.

You have access to a real product catalog from the UCI Online Retail II dataset — a UK-based gift and homeware store.
Products include home decorations, kitchenware, toys, candles, bags, and seasonal gifts.

Your job:
- Help customers find products they're looking for
- Answer questions about products, prices, and availability
- Suggest gift ideas, budget-friendly picks, or bestsellers when asked
- Be conversational, warm, and concise

When you receive product context, use it naturally in your response.
If no matching products are found, be honest and suggest alternatives.
Always mention prices in £ (GBP).
Keep responses short (3–5 sentences max) unless listing products.
"""


def build_user_message(user_input: str, product_context: str) -> str:
    """Combine user query with relevant product context."""
    if product_context and product_context != "No matching products found.":
        return f"""Customer message: {user_input}

Relevant products from our catalog:
{product_context}

Please respond naturally using this product information."""
    else:
        return f"""Customer message: {user_input}

No specific products matched this query. Please respond helpfully."""


def get_relevant_products(catalog: pd.DataFrame, user_message: str) -> str:
    """Route user message to the appropriate product search logic."""
    msg_lower = user_message.lower()

    # Detect intent: bestsellers
    if any(w in msg_lower for w in ["bestsell", "best sell", "popular", "top", "most sold", "trending"]):
        products = get_top_sellers(catalog, n=8)
        return format_products_for_prompt(products)

    # Detect intent: budget / cheap
    max_price = extract_price_from_message(user_message)
    if max_price or any(w in msg_lower for w in ["cheap", "budget", "affordable", "inexpensive", "low price"]):
        threshold = max_price if max_price else 5.0
        products = get_budget_picks(catalog, max_price=threshold, n=8)
        return format_products_for_prompt(products)

    # Detect intent: gift under a price
    if "gift" in msg_lower or "present" in msg_lower:
        max_price = extract_price_from_message(user_message) or 10.0
        products = search_products(catalog, query="gift", max_price=max_price, top_n=8)
        if products.empty:
            products = get_top_sellers(catalog, n=8)
        return format_products_for_prompt(products)

    # General keyword search
    keywords = extract_keywords_from_message(user_message)
    if keywords:
        products = search_products(catalog, query=keywords, top_n=8)
        return format_products_for_prompt(products)

    # Fallback: show top sellers
    products = get_top_sellers(catalog, n=5)
    return format_products_for_prompt(products)


def chat(
    catalog: pd.DataFrame,
    user_message: str,
    conversation_history: list,
    api_key: str,
) -> tuple[str, list]:
    """
    Send a message to the assistant and get a response.

    Args:
        catalog: Product catalog DataFrame
        user_message: Latest user input
        conversation_history: List of prior messages [{"role": ..., "content": ...}]
        api_key: Google Gemini API key

    Returns:
        (assistant_reply, updated_history)
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=SYSTEM_PROMPT,
    )

    # Get relevant product context
    product_context = get_relevant_products(catalog, user_message)

    # Build contextual user message
    enriched_message = build_user_message(user_message, product_context)

    # Convert history to Gemini format: [{"role": "user"/"model", "parts": [text]}]
    gemini_history = []
    for msg in conversation_history:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    # Start chat session with history
    chat_session = model.start_chat(history=gemini_history)

    # Send enriched message
    response = chat_session.send_message(enriched_message)
    assistant_reply = response.text

    # Store clean user message (not enriched) in history for display
    final_history = conversation_history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": assistant_reply},
    ]

    return assistant_reply, final_history
