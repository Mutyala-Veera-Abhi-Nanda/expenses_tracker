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

## Features

- **Add expenses** – Amount, category, date, description
- **View & delete** – Table with date filters
- **Charts** – Bar, pie, and line charts for spending
- **AI Insights** – Pattern analysis and savings suggestions via DeepSeek-R1

## Project Structure

```
expenses_tracker/
├── app.py          # Streamlit UI
├── db.py           # SQLite CRUD
├── aggregator.py   # Pandas aggregation
├── ai_insights.py  # Ollama/DeepSeek-R1 integration
├── expenses.db     # Database (created on first run)
└── requirements.txt
```

## Notes

- Works without Ollama: basic summary shown instead of AI insights
- Data is stored locally in `expenses.db`
