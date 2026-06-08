import pandas as pd
import re


def search_products(
    catalog: pd.DataFrame,
    query: str = "",
    max_price: float = None,
    min_price: float = None,
    country: str = None,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Search products by keyword, price range, or country.
    Returns top_n matching products sorted by popularity.
    """
    results = catalog.copy()

    # Keyword search on description
    if query:
        keywords = [kw.strip() for kw in query.lower().split() if len(kw.strip()) > 2]
        if keywords:
            mask = results["description"].str.lower().apply(
                lambda d: any(kw in d for kw in keywords)
            )
            results = results[mask]

    # Price filters
    if max_price is not None:
        results = results[results["avg_price"] <= max_price]
    if min_price is not None:
        results = results[results["avg_price"] >= min_price]

    # Country filter
    if country:
        results = results[
            results["countries"].str.contains(country, case=False, na=False)
        ]

    return results.head(top_n).reset_index(drop=True)


def get_top_sellers(catalog: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return the top N best-selling products."""
    return catalog.sort_values("total_quantity", ascending=False).head(n).reset_index(drop=True)


def get_budget_picks(catalog: pd.DataFrame, max_price: float = 5.0, n: int = 10) -> pd.DataFrame:
    """Return affordable products under a given price threshold."""
    return (
        catalog[catalog["avg_price"] <= max_price]
        .sort_values("total_quantity", ascending=False)
        .head(n)
        .reset_index(drop=True)
    )


def format_products_for_prompt(products: pd.DataFrame, max_items: int = 8) -> str:
    """Format product dataframe into a readable string for LLM context."""
    if products.empty:
        return "No matching products found."

    lines = []
    for _, row in products.head(max_items).iterrows():
        lines.append(
            f"- {row['description']} | £{row['avg_price']:.2f} | "
            f"Sold: {int(row['total_quantity'])} units"
        )
    return "\n".join(lines)


def extract_price_from_message(message: str):
    """Try to extract a price limit mentioned in user message."""
    # Match patterns like "under £20", "less than 15", "below €10", "max 30"
    pattern = r"(?:under|less than|below|max|maximum|up to|budget of|within)\s*[£€$]?\s*(\d+(?:\.\d+)?)"
    match = re.search(pattern, message, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def extract_keywords_from_message(message: str) -> str:
    """Extract likely product-related keywords from a user message."""
    stopwords = {
        "i", "me", "my", "we", "want", "need", "looking", "for", "find",
        "show", "get", "give", "some", "the", "a", "an", "any", "buy",
        "purchase", "something", "good", "nice", "best", "please", "can",
        "you", "help", "recommend", "suggest", "what", "are", "is", "do",
        "have", "got", "like", "around", "about", "items", "products",
        "gift", "gifts", "cheap", "affordable", "expensive", "popular",
    }
    words = re.findall(r"\b[a-zA-Z]{3,}\b", message.lower())
    keywords = [w for w in words if w not in stopwords]
    return " ".join(keywords)
