# GATE CSE Preparation Bot

A comprehensive Telegram bot to help Computer Science and Engineering students prepare for the GATE exam. Built with Python and `python-telegram-bot`.

## Features
- **Topic-wise Practice:** Covers Programming, Networks, OS, and more.
- **GATE Pattern Questions:** MCQ (with negative marking) and MSQ (exact-set evaluation).
- **Progress Tracking:** Tracks accuracy, strengths/weaknesses, and daily streaks.
- **Revise Mistakes:** Specifically target questions you got wrong.
- **AI Question Generation:** (Optional) Uses Google Gemini API to generate unique practice questions on the fly.
- **Mock Tests:** Take timed tests with a mix of questions.

## Setup Instructions (Windows / VS Code)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-repo/gate-cse-bot.git
   cd gate-cse-bot
   ```

2. **Set up a Virtual Environment (Recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   # Required: Get this from BotFather on Telegram
   TELEGRAM_BOT_TOKEN="your_telegram_bot_token_here"

   # Optional: Database connection string (defaults to local SQLite if omitted)
   DATABASE_URL="sqlite:///gate_bot.db"

   # Optional: For AI-generated questions
   GEMINI_API_KEY="your_google_gemini_api_key_here"
   ```

5. **Initialize the Database:**
   ```bash
   python -c "import src.database; src.database.init_db()"
   ```

6. **Run the Bot:**
   ```bash
   python -m src.bot
   ```

## Architecture

- `src/bot.py`: Entry point and main dispatcher.
- `src/handlers.py`: Core logic for showing topics, handling answers, and revision.
- `src/evaluation.py`: Grading logic for MCQs and MSQs.
- `src/database.py`: SQLAlchemy models and setup.
- `src/mock_tests.py`: Mock test generation and scoring.
- `src/ai_generation.py`: Gemini integration.
- `data/questions.json`: Sample Question Bank containing verified PYQs.

## Deployment Guide (Render / Railway)

### 1. Preparation
Ensure your `.env` variables (except local database URLs) are ready. SQLite is a file-based database, meaning if you deploy to an ephemeral file system (like Render's free tier without a persistent disk), **your users' progress will be wiped on every restart.**

### 2. Choosing a Cloud Host
- **Railway (Recommended):** Easier setup for Telegram bots. Add a persistent volume for the SQLite file or provision a free PostgreSQL database within Railway and update `DATABASE_URL`.
- **Render:** Can be used, but requires linking a persistent disk (paid) to store `gate_bot.db`, or you must use an external database (like Supabase PostgreSQL) and pass that `DATABASE_URL`.

### 3. Deployment Steps (Railway)
1. Push your code to a GitHub repository.
2. Go to Railway.app and create a new Project -> "Deploy from GitHub repo".
3. Select this repository.
4. Go to the "Variables" tab and add `TELEGRAM_BOT_TOKEN`, `DATABASE_URL` (if using Postgres), and `GEMINI_API_KEY`.
5. Under "Settings" -> "Deploy", ensure the start command is `python -m src.bot`.
6. Deploy! Your bot is now live.
