# ◆ FlashRFP.AI

> **AI-powered RFP Response Engine for B2B Sales Teams**  
> Cut proposal writing time by 90%. Win more tenders, faster.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.59-red?logo=streamlit)
![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5.4-green)
![Gemini](https://img.shields.io/badge/Google%20Gemini-AI-orange?logo=google)
![License](https://img.shields.io/badge/License-MIT-purple)

---

## 🚀 What is FlashRFP.AI?

FlashRFP.AI is a production-ready SaaS platform that uses **Retrieval-Augmented Generation (RAG)** to automatically answer RFP/tender questions using your company's own knowledge base. Upload your past proposals, product docs, and compliance documents — and let AI generate accurate, context-aware responses in seconds.

**Built for:** IT companies, government tender teams, and B2B sales teams in India who handle 5+ RFPs per month.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🧠 **RAG Knowledge Base** | Upload PDFs/DOCX, vector-indexed via ChromaDB |
| 🤖 **Multi-LLM Engine** | Supports Google Gemini, Groq, and OpenRouter with auto-fallback |
| 📄 **Batch RFP Processing** | Extract & answer all questions from an RFP PDF at once |
| 📊 **BOQ Excel Auto-Fill** | AI compliance analysis for tender Bill of Quantity Excel files |
| 📝 **Word Template Injection** | Inject AI answers directly into client-provided DOCX templates |
| 💬 **AI Copilot Chat** | Interactive chat interface for Q&A against your knowledge base |
| 📈 **ROI Dashboard** | Real-time tracking of hours saved and cost savings |
| 🎛️ **Admin Panel** | Full SaaS admin: user management, subscriptions, analytics |
| 🌐 **Landing Page** | B2B marketing site with pricing & demo booking |
| 🔐 **Auth System** | JWT cookie-based login with bcrypt passwords |
| 🛡️ **PII Scrubbing** | Automatically removes sensitive data before LLM calls |

---

## 🏗️ Architecture

```
FlashRFP.AI
├── app.py                  # Main Streamlit app (6 tabs)
├── rag_engine.py           # RAG pipeline + multi-provider LLM
├── exporter.py             # DOCX/Excel export engine
├── copilot.py              # AI Copilot chat interface
├── roi_tracker.py          # ROI metrics & dashboard
├── admin.py                # Admin panel (users, billing, analytics)
├── admin_db.py             # Local JSON data layer (swap to Supabase)
├── supabase_client.py      # Supabase cloud DB client (ready)
├── supabase_schema.sql     # Production DB schema (5 tables + RLS)
├── auth_db.py              # Authentication helpers
├── server.py               # Landing page HTTP server + API endpoints
├── index.html              # B2B Marketing Landing Page (2,637 lines)
└── requirements.txt        # All Python dependencies
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.12+
- A Google Gemini API key ([Get one here](https://aistudio.google.com/))

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/Taruntej081/FlashRFP_Ai.git
cd FlashRFP_Ai

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Run the App

```bash
# Start the Streamlit app
streamlit run app.py

# (Optional) Start the landing page server
python server.py
```

---

## 🤖 Supported LLM Providers

| Provider | Key Prefix | Default Model |
|----------|-----------|---------------|
| Google Gemini | `AIzaSy...` | `gemini-2.0-flash` |
| Groq | `gsk_...` | `llama-3.3-70b-versatile` |
| OpenRouter | others | `google/gemini-2.5-flash` |

The engine **auto-detects** the provider from your API key and **automatically falls back** to the next provider if rate-limited.

---

## 💰 Pricing Tiers

| Plan | Price | Responses/mo | Documents | Batches/mo |
|------|-------|-------------|-----------|------------|
| **Trial** | Free | 10 | 5 | 3 |
| **Starter** | ₹2,999/mo | 100 | 50 | 20 |
| **Professional** | ₹7,999/mo | 500 | 500 | 100 |
| **Enterprise** | ₹24,999/mo | Unlimited | Unlimited | Unlimited |

---

## 🧪 Running Tests

```bash
# Install test dependencies
pip install pytest openpyxl

# Run the full test suite
pytest test_boq_engine.py test_roi_tracker.py test_copilot_engine.py \
       test_pii_security.py test_adv_export.py test_word_injection_engine.py -v

# Run integration tests (requires valid API key in .env)
python test_rag.py
python test_batch_features.py
python test_docx_ingest.py
```

**Test Results:** 8/9 tests pass out-of-the-box (offline mode). Full integration tests pass with a valid API key.

---

## 🗄️ Database

### Local (Default)
Uses JSON files in `admin_data/` — no setup needed. Perfect for development.

### Supabase (Production)
1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Run `supabase_schema.sql` in the SQL Editor
3. Add to `.env`:
   ```
   SUPABASE_URL=your_project_url
   SUPABASE_KEY=your_service_role_key
   ```

---

## 🔒 Security

- ✅ `.env` file excluded from git (never committed)
- ✅ `auth_config.json` excluded from git
- ✅ `admin_data/` excluded from git
- ✅ All databases excluded from git
- ✅ PII scrubbing before LLM calls
- ✅ Supabase Row Level Security on all tables
- ✅ bcrypt password hashing

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**Taruntej081** — [github.com/Taruntej081](https://github.com/Taruntej081)

---

*Built with ❤️ to win more RFPs, faster.*
