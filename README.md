# Expenses Tracker

Track expenses manually and get AI-powered insights using Ollama.

## Setup

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install and run Ollama** (for AI insights)
   - Download from [ollama.com](https://ollama.com)
   - Pull Model
   - Keep Ollama running in the background

3. **Run the app**
   ```bash
   streamlit run app.py
   ```

## Supabase Setup (for persistent storage when deployed)

By default, the app uses **SQLite** locally. For deployed apps (e.g. Streamlit Cloud), use **Supabase (PostgreSQL)** so data persists.

### 1. Create a Supabase project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click **New Project** → choose org, name, password, region
3. Wait for the project to be ready

### 2. Get the connection string

1. In Supabase Dashboard → **Project Settings** (gear icon)
2. Go to **Database** → **Connection string**
3. Select **URI** tab
4. Copy the connection string (it looks like `postgresql://postgres.[ref]:[password]@...`)
5. Replace `[YOUR-PASSWORD]` with your actual database password (from project creation)
6. **Tip:** If you get connection errors, try a password with only letters and numbers (no `@`, `#`, `%`, etc.)

**Recommended for Streamlit Cloud:** Use the **Transaction** pooler (port **6543**) to handle many short-lived connections.

### 3. Add to Streamlit Community Cloud

1. Open your app on [share.streamlit.io](https://share.streamlit.io)
2. Click **Settings** (⚙️) → **Secrets**
3. Add:
   ```toml
   DATABASE_URL = "postgresql://postgres.[PROJECT_REF]:[YOUR_PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres"
   ```
4. Save and wait for the app to redeploy

### 4. Local development with Supabase

To use Supabase locally instead of SQLite:

1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
2. Add your `DATABASE_URL` to `secrets.toml`
3. Run `streamlit run app.py`

## Features

- **Add expenses** – Amount, category, date, description
- **View & delete** – Table with date filters
- **Charts** – Bar, pie, and line charts for spending
- **AI Insights** – Pattern analysis and savings suggestions

## Project Structure

```
expenses_tracker/
├── app.py          # Streamlit UI
├── db.py           # SQLite / Postgres CRUD
├── aggregator.py   # Pandas aggregation
├── ai_insights.py  # Ollama/DeepSeek-R1 integration
├── expenses.db     # Local SQLite (when not using Supabase)
└── requirements.txt
```

## Notes

- Works without Ollama: basic summary shown instead of AI insights
- **Local:** Data stored in `expenses.db` (SQLite)
- **Deployed:** Use Supabase and set `DATABASE_URL` for persistent storage
