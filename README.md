# Expenses Tracker

Track expenses manually and get AI-powered insights using Ollama (local) or Groq (cloud).

## Setup

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **AI insights** (choose one)
   - **Local:** Install [Ollama](https://ollama.com), run `ollama pull llama3.2:1b`
   - **Cloud:** Add `GROQ_API_KEY` to Streamlit secrets (see below)

3. **Run the app**
   ```bash
   streamlit run app.py
   ```

## Groq Setup (for AI insights on Streamlit Cloud)

Ollama runs only on your machine. For the deployed app, use **Groq** (free tier with Llama models).

1. Go to [console.groq.com](https://console.groq.com) and sign up
2. Create an API key under **API Keys**
3. Add to Streamlit Cloud secrets:
   ```toml
   GROQ_API_KEY = "gsk_your_api_key_here"
   ```
4. Save and redeploy

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

### 3. User authentication (optional)

To enable login/signup, add your Supabase API credentials:

1. Supabase Dashboard → **Project Settings** → **API**
2. Copy **Project URL** and **anon public** key
3. Add to Streamlit secrets:
   ```toml
   SUPABASE_URL = "https://[PROJECT_REF].supabase.co"
   SUPABASE_ANON_KEY = "your_anon_key"
   ```

**Tip:** To skip email confirmation for new signups, go to **Authentication** → **Providers** → **Email** and disable "Confirm email".

**Existing data:** If you had expenses before enabling auth, they have no `user_id` and won't show. In Supabase SQL Editor, run `UPDATE expenses SET user_id = 'YOUR_USER_ID' WHERE user_id IS NULL` (get your ID from the auth.users table or the app after signing in).

### 4. Add to Streamlit Community Cloud

1. Open your app on [share.streamlit.io](https://share.streamlit.io)
2. Click **Settings** (⚙️) → **Secrets**
3. Add your secrets (full deployment with auth + AI):
   ```toml
   DATABASE_URL = "postgresql://postgres.[PROJECT_REF]:[YOUR_PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres"
   SUPABASE_URL = "https://[PROJECT_REF].supabase.co"
   SUPABASE_ANON_KEY = "your_anon_key"
   GROQ_API_KEY = "gsk_your_groq_api_key"
   ```
4. Save and wait for the app to redeploy

### 5. Local development with Supabase

To use Supabase locally instead of SQLite:

1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
2. Add `DATABASE_URL`, `SUPABASE_URL`, and `SUPABASE_ANON_KEY` to `secrets.toml`
3. Run `streamlit run app.py`

## Features

- **Add expenses** – Amount, category, date, description
- **View & delete** – Table with date filters
- **Charts** – Bar, pie, and line charts for spending
- **AI Insights** – Pattern analysis and savings suggestions
- **User auth** – Sign up / sign in when using Supabase (each user sees only their expenses)

## Project Structure

```
expenses_tracker/
├── app.py          # Streamlit UI
├── auth.py         # Supabase Auth (login/signup)
├── db.py           # SQLite / Postgres CRUD
├── aggregator.py   # Pandas aggregation
├── ai_insights.py  # Ollama (local) / Groq (cloud) integration
├── expenses.db     # Local SQLite (when not using Supabase)
└── requirements.txt
```

## Notes

- **Auth:** Only when `SUPABASE_URL` + `SUPABASE_ANON_KEY` are set. Local SQLite = no auth.
- **AI:** Local = Ollama. Cloud = Groq (free). Neither = basic summary only.
- **Data:** Local = SQLite. Deployed = Supabase (`DATABASE_URL`).
