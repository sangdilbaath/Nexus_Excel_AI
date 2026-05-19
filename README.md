# ◈ Nexus Excel AI — Setup Guide

A full-stack SaaS Streamlit application with user auth, feature-gated pricing tiers,
simulated billing, and an AI-powered data analyst backed by Gemini 2.5.

---

## Project Structure

```
nexus_excel_ai/
├── Home.py              # Entry point — landing page + email capture
├── database.py          # SQLite layer (users table, CRUD helpers)
├── styles.py            # Shared CSS for all pages
├── requirements.txt
├── nexus.db             # Auto-created on first run
└── pages/
    ├── 1_Pricing.py     # 4-tier pricing cards
    ├── 2_Billing.py     # Simulated checkout form
    └── 3_App.py         # AI Dashboard (feature-gated)
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
streamlit run Home.py
```

The SQLite database (`nexus.db`) is created automatically on first launch.

---

## User Flow

```
Home.py  (email capture)
  └─► pages/1_Pricing.py  (select plan)
        └─► pages/2_Billing.py  (simulated checkout)
              └─► pages/3_App.py  (AI Dashboard)
```

---

## Plan Feature Matrix

| Feature              | Free Trial | Basic | Premium | Pro |
|----------------------|:----------:|:-----:|:-------:|:---:|
| AI Chat Analysis     | ✅         | ✅    | ✅      | ✅  |
| Voice Commands       | ✅         | ❌    | ✅      | ✅  |
| Charts (matplotlib)  | ✅         | ❌    | ❌      | ✅  |
| CSV / Excel Export   | ✅         | ✅    | ✅      | ✅  |
| Trial expires after  | 7 days     | —     | —       | —   |

---

## Environment Notes

- **Gemini API Key**: entered in the sidebar of the dashboard.  
  Get yours at https://aistudio.google.com/
- **No real payments**: the billing form is simulated for demo purposes.
- **SQLite DB**: stored as `nexus.db` in the project root. Back it up before deploying.

---

## Deployment (Streamlit Cloud)

1. Push this folder to a GitHub repo.
2. Connect the repo to https://share.streamlit.io
3. Set the **Main file path** to `Home.py`.
4. Add any secrets (e.g. default API key) via the Secrets manager.
