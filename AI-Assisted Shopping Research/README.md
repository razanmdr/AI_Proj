# 🛍️ ShopBot — AI Virtual Shopping Assistant

A conversational AI shopping assistant powered by **Claude (Anthropic)** and built with **Streamlit**. The assistant uses a real e-commerce dataset (UCI Online Retail II) to answer product queries, suggest gifts, find budget picks, and recommend bestsellers — all through natural language.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red?logo=streamlit)
![Gemini](https://img.shields.io/badge/Gemini-API-blue?logo=google)

---

## ✨ Features

- 💬 **Natural language chat** — ask anything in plain English
- 🔍 **Smart product search** — keyword, price range, and country filters
- 🏆 **Bestseller detection** — surfaces most popular products automatically
- 💰 **Budget-aware recommendations** — understands "under £10", "cheap gifts", etc.
- 🎁 **Gift intent detection** — finds suitable gift products with price limits
- 🔄 **Multi-turn conversation** — remembers context across messages

---

## 🗂️ Project Structure

```
shopping-assistant/
├── app.py              # Streamlit frontend & chat UI
├── assistant.py        # Claude API integration + prompt engineering
├── data_loader.py      # Dataset loading & preprocessing
├── product_search.py   # Product search, filtering & ranking logic
├── requirements.txt    # Python dependencies
├── data/
│   └── online_retail_II.xlsx   # ← Place dataset here (see below)
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/shopping-assistant.git
cd shopping-assistant
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get a Gemini API key (free)

Sign up at [aistudio.google.com](https://aistudio.google.com) → **Get API key** 

### 4. (Optional) Download the full dataset

For the complete product catalog, download the **UCI Online Retail II** dataset:

👉 [Download from UCI ML Repository](https://archive.ics.uci.edu/dataset/502/online+retail+ii)

Place the file at: `data/online_retail_II.xlsx`

> **No dataset?** No problem — the app ships with a built-in demo catalog of 30 products so you can run it immediately.

### 5. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

Enter your API key in the sidebar and start chatting!

---

## 💡 Example Queries

| Query | What happens |
|---|---|
| *"What are your bestsellers?"* | Returns top products by sales volume |
| *"Show me gifts under £10"* | Filters products ≤ £10, gift-oriented |
| *"I need something for the kitchen"* | Keyword search on "kitchen" |
| *"Cheap items under £3?"* | Budget filter at £3 |
| *"Do you have any candles or lanterns?"* | Keyword search on "candle lantern" |

---

## 🧠 How It Works

```
User message
     │
     ▼
product_search.py          ← Extracts intent + keywords from message
     │                     ← Queries product catalog (search / filter / rank)
     ▼
assistant.py               ← Injects product context into Claude prompt
     │                     ← Calls Claude API (claude-sonnet-4-20250514)
     ▼
app.py                     ← Displays response in Streamlit chat UI
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| LLM | [Gemini 1.5 Flash (Google)](https://aistudio.google.com) — free tier |
| Frontend | [Streamlit](https://streamlit.io) |
| Dataset | [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) |
| Data processing | Pandas, NumPy |

---

## 📊 Dataset

**UCI Online Retail II** is a real transactional dataset from a UK-based online giftware retailer (2009–2011), containing ~1 million invoice rows across 40+ countries.

- Source: [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/502/online+retail+ii)
- License: CC BY 4.0

---

## 🔮 Future Ideas

- [ ] Add product image search via Google Shopping API
- [ ] Integrate geospatial signals (user location → country-specific recommendations)
- [ ] Collaborative filtering recommender (LightFM)
- [ ] Session analytics dashboard
- [ ] Deploy to Streamlit Cloud

---

## 📄 License

MIT License — feel free to fork and extend.
