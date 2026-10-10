import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from src.config import TELEGRAM_BOT_TOKEN
from src.logger import get_logger

logger = get_logger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user

    # Reset any active states to prevent bleed
    if context.user_data:
        context.user_data['mock_test_active'] = False
        context.user_data.pop('practice_mode', None)

    welcome_message = (
        f"Hi {user.first_name}! 👋\n\n"
        "Welcome to the GATE CSE Preparation Bot.\n"
        "I can help you practice PYQs, take mock tests, and track your progress.\n\n"
        "What would you like to do?"
    )

    keyboard = [
        [
            InlineKeyboardButton("📚 Topic-wise Practice", callback_data="menu_topics"),
            InlineKeyboardButton("⏱️ Mock Tests", callback_data="menu_mock_tests")
        ],
        [
            InlineKeyboardButton("📊 My Progress", callback_data="menu_progress"),
            InlineKeyboardButton("🔄 Revise Mistakes", callback_data="menu_revise")
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="menu_help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(welcome_message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = (
        "🤖 *GATE CSE Bot Help*\n\n"
        "Here are the commands you can use:\n"
        "/start - Start the bot and see the main menu\n"
        "/help - Show this help message\n\n"
        "*Features:*\n"
        "- *Topic-wise Practice:* Choose a specific subject to practice.\n"
        "- *Mock Tests:* Take a timed test with mixed questions.\n"
        "- *Progress Tracking:* See your stats, streaks, and weak areas.\n"
        "- *Revise Mistakes:* Revisit questions you got wrong.\n"
        "- *AI Questions:* (If enabled) Practice with unique AI-generated questions.\n\n"
        "Use the buttons to navigate!"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(help_text, parse_mode="Markdown")
    else:
        await update.message.reply_text(help_text, parse_mode="Markdown")

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu callbacks."""
    query = update.callback_query
    await query.answer()

    if query.data == "menu_help":
        await help_command(update, context)
    else:
        await query.message.reply_text(f"Feature '{query.data}' is under construction! 🚧")

def main() -> None:
    """Start the bot."""
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or not TELEGRAM_BOT_TOKEN:
        logger.error("Telegram bot token is missing! Please set TELEGRAM_BOT_TOKEN in .env")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    from src.handlers import handle_topic_selection, start_topic_practice, handle_answer, revise_mistakes, show_progress, start_mock_test, start_ai_practice

    # Main menu handling
    application.add_handler(CallbackQueryHandler(start_command, pattern="^menu_main$"))
    application.add_handler(CallbackQueryHandler(handle_topic_selection, pattern="^menu_topics$"))
    application.add_handler(CallbackQueryHandler(revise_mistakes, pattern="^menu_revise$"))
    application.add_handler(CallbackQueryHandler(show_progress, pattern="^menu_progress$"))
    application.add_handler(CallbackQueryHandler(start_mock_test, pattern="^menu_mock_tests$"))
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^menu_"))

    # Feature handling
    application.add_handler(CallbackQueryHandler(start_topic_practice, pattern="^topic_"))
    application.add_handler(CallbackQueryHandler(start_ai_practice, pattern="^ai_"))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern="^(ans_|msq_)"))

    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
