import pandas as pd
import numpy as np
import os

SAMPLE_DATA_PATH = "data/online_retail_sample.csv"
EXCEL_DATA_PATH = "data/online_retail_II.xlsx"


def load_dataset() -> pd.DataFrame:
    """
    Load UCI Online Retail II dataset.
    Priority:
    1. Pre-processed CSV sample (fastest)
    2. Raw Excel file (if downloaded manually)
    3. Built-in demo data (fallback)
    """
    if os.path.exists(SAMPLE_DATA_PATH):
        df = pd.read_csv(SAMPLE_DATA_PATH)
        return _clean(df)

    if os.path.exists(EXCEL_DATA_PATH):
        print("Loading Excel file... this may take a moment.")
        df = pd.read_excel(EXCEL_DATA_PATH, sheet_name="Year 2010-2011", engine="openpyxl")
        os.makedirs("data", exist_ok=True)
        df.to_csv(SAMPLE_DATA_PATH, index=False)
        return _clean(df)

    # Fallback: built-in demo dataset
    return _demo_data()


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip() for c in df.columns]

    # Rename to standard column names
    rename_map = {
        "StockCode": "stock_code",
        "Description": "description",
        "Quantity": "quantity",
        "InvoiceDate": "invoice_date",
        "Price": "price",
        "UnitPrice": "price",
        "Customer ID": "customer_id",
        "CustomerID": "customer_id",
        "Country": "country",
        "Invoice": "invoice",
        "InvoiceNo": "invoice",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Drop rows with missing description or price
    df = df.dropna(subset=["description"])
    df["description"] = df["description"].str.strip().str.title()
    df["price"] = pd.to_numeric(df.get("price", 0), errors="coerce").fillna(0)
    df["quantity"] = pd.to_numeric(df.get("quantity", 0), errors="coerce").fillna(0)

    # Remove cancelled orders and invalid prices
    if "invoice" in df.columns:
        df = df[~df["invoice"].astype(str).str.startswith("C")]
    df = df[df["price"] > 0]
    df = df[df["quantity"] > 0]

    return df.reset_index(drop=True)


def _demo_data() -> pd.DataFrame:
    """Minimal built-in demo dataset for offline/no-download use."""
    records = [
        ("85123A", "White Hanging Heart T-Light Holder", 6, 2.55, "United Kingdom"),
        ("71053",  "White Metal Lantern", 6, 3.39, "United Kingdom"),
        ("84406B", "Cream Cupid Hearts Coat Hanger", 8, 2.75, "United Kingdom"),
        ("84029G", "Knitted Union Flag Hot Water Bottle", 6, 3.39, "United Kingdom"),
        ("84029E", "Red Woolly Hottie White Heart", 6, 3.39, "United Kingdom"),
        ("22752",  "Set 7 Babushka Nesting Boxes", 2, 7.65, "United Kingdom"),
        ("21730",  "Glass Star Frosted T-Light Holder", 6, 4.25, "France"),
        ("22633",  "Hand Warmer Union Jack", 6, 1.85, "Germany"),
        ("22632",  "Hand Warmer Red Polka Dot", 6, 1.85, "Germany"),
        ("84879",  "Assorted Colour Bird Ornament", 32, 1.69, "United Kingdom"),
        ("47566",  "Party Bunting", 6, 4.95, "Australia"),
        ("85099B", "Jumbo Bag Red Retrospot", 10, 1.95, "United Kingdom"),
        ("22745",  "Poppy'S Playhouse Bedroom", 6, 2.10, "United Kingdom"),
        ("22748",  "Poppy'S Playhouse Kitchen", 6, 2.10, "United Kingdom"),
        ("22749",  "Feltcraft Princess Charlotte Doll", 8, 3.75, "United Kingdom"),
        ("22310",  "Ivory Knitted Mug Cosy", 6, 1.65, "United Kingdom"),
        ("84969",  "Box Of 6 Assorted Colour Teaspoons", 12, 4.25, "United Kingdom"),
        ("22623",  "Victorian Sewing Box Large", 3, 10.95, "France"),
        ("22622",  "Baking Set 9 Piece Retrospot", 12, 4.95, "Germany"),
        ("21754",  "Home Building Block Word", 3, 5.95, "United Kingdom"),
        ("21755",  "Love Building Block Word", 3, 5.95, "United Kingdom"),
        ("21777",  "Recipe Box With Metal Lid", 4, 7.95, "United Kingdom"),
        ("48187",  "Doormat New Home", 4, 7.08, "United Kingdom"),
        ("22960",  "Jam Making Set Printed", 6, 4.25, "United Kingdom"),
        ("22086",  "Paper Chain Kit 50'S Christmas", 12, 2.55, "United Kingdom"),
        ("85099C", "Jumbo Bag Baroque Black White", 10, 1.95, "Australia"),
        ("20685",  "Red Retrospot Purse", 6, 3.75, "France"),
        ("23166",  "Medium Ceramic Top Storage Jar", 12, 1.25, "United Kingdom"),
        ("82582",  "Camera Lens Mug", 8, 4.25, "United Kingdom"),
        ("23355",  "HOT WATER BOTTLE KEEP CALM", 4, 4.95, "Germany"),
    ]
    df = pd.DataFrame(records, columns=["stock_code", "description", "quantity", "price", "country"])
    return df


def get_product_catalog(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate to unique products with avg price and total quantity sold."""
    catalog = (
        df.groupby(["stock_code", "description"])
        .agg(
            avg_price=("price", "mean"),
            total_quantity=("quantity", "sum"),
            countries=("country", lambda x: ", ".join(sorted(set(x.dropna()))) if "country" in df.columns else "N/A"),
        )
        .reset_index()
    )
    catalog["avg_price"] = catalog["avg_price"].round(2)
    catalog = catalog.sort_values("total_quantity", ascending=False).reset_index(drop=True)
    return catalog
