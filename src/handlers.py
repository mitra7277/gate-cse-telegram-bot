import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.logger import get_logger
from src.database import SessionLocal, Attempt, User, IncorrectAnswer, MockTestAttempt
from src.evaluation import evaluate_question
from src.progress import get_user_stats, get_weak_areas, format_progress_report
from src.mock_tests import generate_mock_test, calculate_mock_score, format_mock_report
from src.ai_generation import generate_ai_question
import datetime
import time

logger = get_logger(__name__)

# Load questions from JSON file (simple read for now)
def load_questions():
    try:
        with open("data/questions.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("questions.json not found!")
        return []

QUESTIONS = load_questions()

async def get_or_create_user(telegram_user, db_session) -> User:
    user = db_session.query(User).filter(User.telegram_id == telegram_user.id).first()
    if not user:
        user = User(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE, question: dict):
    """Formats and sends a question to the user."""
    context.user_data['current_question'] = question

    # Store state for MSQ multi-select
    if question['type'] == 'MSQ':
        context.user_data['msq_selections'] = []

    text = f"📝 *[{question['type']}] Topic: {question['topic']}*\n\n"
    text += f"{question['question']}\n\n"

    keyboard = []
    for opt, desc in question['options'].items():
        text += f"{opt}) {desc}\n"
        # For MSQ, we will use a different callback pattern to toggle selection
        cb_data = f"ans_{opt}" if question['type'] == 'MCQ' else f"msq_{opt}"
        keyboard.append([InlineKeyboardButton(f"Option {opt}", callback_data=cb_data)])

    if question['type'] == 'MSQ':
        keyboard.append([InlineKeyboardButton("Submit Answer", callback_data="msq_submit")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_topic_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the topic selection menu."""
    query = update.callback_query
    await query.answer()

    # Extract unique topics from the loaded questions
    topics = list(set([q['topic'] for q in QUESTIONS]))

    keyboard = []
    for topic in topics:
        # Standard practice button
        keyboard.append([InlineKeyboardButton(topic, callback_data=f"topic_{topic}")])
        # AI practice button
        keyboard.append([InlineKeyboardButton(f"🤖 AI {topic}", callback_data=f"ai_{topic}")])

    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text("📚 *Select a Topic to Practice:*", reply_markup=reply_markup, parse_mode="Markdown")

async def start_ai_practice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generates and sends an AI question for a topic."""
    query = update.callback_query
    await query.answer()

    topic = query.data.split("ai_")[1]
    await query.message.edit_text(f"⏳ Generating a unique AI question for {topic}...\nPlease wait.")

    question = generate_ai_question(topic)
    if question:
        # Save mode to context so handle_answer knows what to show next
        context.user_data['practice_mode'] = f"ai_{topic}"
        await send_question(update, context, question)
    else:
        await query.message.edit_text(
            "Failed to generate AI question. Please check API key or try again.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="menu_main")]])
        )

async def start_topic_practice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts practice for a specific topic."""
    query = update.callback_query
    await query.answer()

    topic = query.data.split("topic_")[1]

    # Filter questions
    topic_questions = [q for q in QUESTIONS if q['topic'] == topic]

    if not topic_questions:
        await query.message.reply_text("No questions found for this topic yet!")
        return

    # Track asked questions to prevent repetition
    if 'asked_questions' not in context.user_data:
        context.user_data['asked_questions'] = {}

    asked = context.user_data['asked_questions'].get(topic, [])

    # Filter out already asked questions
    eligible_questions = [q for q in topic_questions if q['id'] not in asked]

    # If all questions have been asked, reset the cycle
    if not eligible_questions:
        asked = []
        eligible_questions = list(topic_questions)
        # Avoid repeating the very last question if possible
        last_asked = context.user_data.get('last_asked_question')
        if last_asked and len(eligible_questions) > 1:
            eligible_questions = [q for q in eligible_questions if q['id'] != last_asked]

    # Select a random question for practice
    question = random.choice(eligible_questions)

    # Update tracking
    asked.append(question['id'])
    context.user_data['asked_questions'][topic] = asked
    context.user_data['last_asked_question'] = question['id']

    # Flag single-question topic
    context.user_data['single_question_topic'] = (len(topic_questions) == 1)

    context.user_data['practice_mode'] = f"topic_{topic}"
    await send_question(update, context, question)

async def show_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows user progress report."""
    query = update.callback_query
    await query.answer()

    user_telegram = update.effective_user
    with SessionLocal() as db:
        user = await get_or_create_user(user_telegram, db)
        stats = get_user_stats(db, user.id)
        weak = get_weak_areas(db, user.id)
        report = format_progress_report(stats, weak)

        await query.message.edit_text(
            report,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data="menu_main")]]),
            parse_mode="Markdown"
        )

async def start_mock_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initializes and starts a mock test."""
    query = update.callback_query
    await query.answer()

    # Generate 5 questions for mock test
    mock_questions = generate_mock_test(QUESTIONS, 5)

    context.user_data['mock_test_active'] = True
    context.user_data['mock_questions'] = mock_questions
    context.user_data['mock_responses'] = []
    context.user_data['mock_start_time'] = time.time()

    # Send first question
    context.user_data['current_question'] = mock_questions[0]
    await send_question(update, context, mock_questions[0])

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles answer submission."""
    query = update.callback_query
    await query.answer()

    user_telegram = update.effective_user
    current_q = context.user_data.get('current_question')

    if not current_q:
        await query.message.edit_text("Session expired. Please start a new practice session.")
        return

    # Handle MSQ selection toggle
    if query.data.startswith("msq_") and query.data != "msq_submit":
        opt = query.data.split("_")[1]
        selections = context.user_data.get('msq_selections', [])
        if opt in selections:
            selections.remove(opt)
        else:
            selections.append(opt)
        context.user_data['msq_selections'] = selections

        # Update inline keyboard to show selected state with ✅
        keyboard = []
        for q_opt, desc in current_q['options'].items():
            btn_text = f"✅ Option {q_opt}" if q_opt in selections else f"Option {q_opt}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"msq_{q_opt}")])

        keyboard.append([InlineKeyboardButton("Submit Answer", callback_data="msq_submit")])

        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        return

    user_answers = []
    if query.data.startswith("ans_"):
        user_answers = [query.data.split("_")[1]] # MCQ
    elif query.data == "msq_submit":
        user_answers = context.user_data.get('msq_selections', []) # MSQ
        if not user_answers:
             await query.message.reply_text("Please select at least one option before submitting.")
             return

    # Evaluate
    correct_answers = current_q['correct_answers']
    marks = 1.0 # Default for this basic implementation
    is_correct, score = evaluate_question(current_q['type'], user_answers, correct_answers, marks)

    # Save to database
    with SessionLocal() as db:
        try:
            user = await get_or_create_user(user_telegram, db)

            attempt = Attempt(
                user_id=user.id,
                question_id=current_q['id'],
                topic=current_q['topic'],
                is_correct=is_correct
            )
            db.add(attempt)

            if not is_correct:
                # Add or update incorrect answer for revision
                inc = db.query(IncorrectAnswer).filter_by(user_id=user.id, question_id=current_q['id']).first()
                if inc:
                    inc.timestamp = datetime.datetime.utcnow()
                    inc.needs_revision = True
                else:
                    inc = IncorrectAnswer(user_id=user.id, question_id=current_q['id'], topic=current_q['topic'])
                    db.add(inc)

            # Simple streak update (could be more complex logic in progress.py)
            if is_correct:
                 user.current_streak += 1
                 if user.current_streak > user.highest_streak:
                     user.highest_streak = user.current_streak
            else:
                 user.current_streak = 0

            db.commit()
        except Exception as e:
            logger.error(f"Database error: {e}")
            db.rollback()

    # Handle Mock Test Flow
    if context.user_data.get('mock_test_active'):
        start_time = context.user_data.get('mock_start_time', time.time())
        # Example limit: 5 minutes (300 seconds)
        time_limit = 300
        elapsed = time.time() - start_time

        responses = context.user_data.get('mock_responses', [])

        if elapsed > time_limit:
            context.user_data['mock_test_active'] = False
            score_data = calculate_mock_score(responses)
            timeout_msg = f"⏳ *Time's Up!*\nYou took {int(elapsed)} seconds.\n\n"
            report = timeout_msg + format_mock_report(score_data)

            # Save partial mock test attempt to DB
            with SessionLocal() as db:
                try:
                    user = await get_or_create_user(user_telegram, db)
                    mta = MockTestAttempt(
                        user_id=user.id,
                        score=score_data['total_score'],
                        total_questions=score_data['total_questions'],
                        correct_answers=score_data['correct_count'],
                        incorrect_answers_count=score_data['incorrect_count'],
                        details=responses
                    )
                    db.add(mta)
                    db.commit()
                except Exception as e:
                    logger.error(f"Error saving mock test: {e}")

            await query.message.edit_text(
                report,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data="menu_main")]]),
                parse_mode="Markdown"
            )
            return

        # If not timed out, append this answer
        responses.append({
            'question_id': current_q.get('id', 'unknown'),
            'user_answers': user_answers,
            'is_correct': is_correct,
            'score': score
        })
        context.user_data['mock_responses'] = responses

        mock_qs = context.user_data.get('mock_questions', [])
        curr_idx = len(responses)

        if curr_idx < len(mock_qs):
            # Send next mock question
            next_q = mock_qs[curr_idx]
            context.user_data['current_question'] = next_q
            await send_question(update, context, next_q)
        else:
            # Finish mock test normally
            context.user_data['mock_test_active'] = False
            score_data = calculate_mock_score(responses)
            report = f"✅ *Mock Test Completed!* ({int(elapsed)} seconds)\n\n" + format_mock_report(score_data)

            # Save mock test attempt to DB
            with SessionLocal() as db:
                try:
                    user = await get_or_create_user(user_telegram, db)
                    mta = MockTestAttempt(
                        user_id=user.id,
                        score=score_data['total_score'],
                        total_questions=score_data['total_questions'],
                        correct_answers=score_data['correct_count'],
                        incorrect_answers_count=score_data['incorrect_count'],
                        details=responses
                    )
                    db.add(mta)
                    db.commit()
                except Exception as e:
                    logger.error(f"Error saving mock test: {e}")

            await query.message.edit_text(
                report,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data="menu_main")]]),
                parse_mode="Markdown"
            )
        return

    # Normal Practice Flow
    result_text = "✅ *Correct!*" if is_correct else "❌ *Incorrect!*"
    result_text += f" (Score: {score})\n\n"
    result_text += f"*Your Answer:* {', '.join(sorted(user_answers))}\n"
    result_text += f"*Correct Answer:* {', '.join(sorted(correct_answers))}\n\n"
    result_text += f"*Explanation:*\n{current_q['explanation']}\n\n"
    result_text += f"_Source: {current_q['source']}_"

    is_single_question = context.user_data.get('single_question_topic', False)
    if is_single_question:
        result_text += "\n\n_Note: This is the only question currently available for this topic._"

    next_cb = context.user_data.get('practice_mode', f"topic_{current_q['topic']}")

    keyboard = []
    if not is_single_question:
        keyboard.append([InlineKeyboardButton("Next Question", callback_data=next_cb)])
    keyboard.append([InlineKeyboardButton("Main Menu", callback_data="menu_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(result_text, reply_markup=reply_markup, parse_mode="Markdown")

async def revise_mistakes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches a question the user previously got wrong."""
    query = update.callback_query
    await query.answer()

    user_telegram = update.effective_user

    with SessionLocal() as db:
        try:
            user = await get_or_create_user(user_telegram, db)

            # Keep searching until we find a valid question or run out of mistakes
            while True:
                incorrect = db.query(IncorrectAnswer).filter_by(user_id=user.id, needs_revision=True).first()

                if not incorrect:
                    await query.message.edit_text("🎉 You have no pending mistakes to revise! Great job!",
                                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="menu_main")]]))
                    return

                # Find the question data
                question = next((q for q in QUESTIONS if q['id'] == incorrect.question_id), None)

                if question:
                    # Send it, then mark as no longer needing revision (simplistic)
                    incorrect.needs_revision = False
                    db.commit()
                    context.user_data['practice_mode'] = "menu_revise" # Allow chaining revision
                    await send_question(update, context, question)
                    return
                else:
                     # It might be an AI question or removed question, clear flag to avoid lock-out
                     incorrect.needs_revision = False
                     db.commit()

        except Exception as e:
            logger.error(f"DB Error: {e}")
