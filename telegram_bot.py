import os
import logging
import psycopg2
from psycopg2.extras import DictCursor
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database connection
def get_db_connection():
    return psycopg2.connect(os.getenv('DATABASE_URL'))

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    welcome_message = (
        "👋 Welcome to Twitter Tracker Bot!\n\n"
        "I can help you track Twitter accounts and get real-time updates "
        "right here in Telegram.\n\n"
        "Commands:\n"
        "/track <username> - Start tracking a Twitter account\n"
        "/untrack <username> - Stop tracking a Twitter account\n"
        "/list - Show all accounts you're tracking\n"
        "/help - Show this help message"
    )
    update.message.reply_text(welcome_message)

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "🤖 Twitter Tracker Bot Commands:\n\n"
        "/track <username> - Start tracking a Twitter account\n"
        "Example: /track elonmusk\n\n"
        "/untrack <username> - Stop tracking a Twitter account\n"
        "Example: /untrack elonmusk\n\n"
        "/list - Show all accounts you're currently tracking\n\n"
        "/help - Show this help message"
    )
    update.message.reply_text(help_text)

def track(update: Update, context: CallbackContext) -> None:
    """Track a Twitter account."""
    if not context.args:
        update.message.reply_text("❌ Please provide a Twitter username to track.\nExample: /track elonmusk")
        return

    username = context.args[0].strip('@').lower()
    chat_id = update.effective_chat.id

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tracked_accounts (chat_id, twitter_username)
                    VALUES (%s, %s)
                    ON CONFLICT (chat_id, twitter_username) DO NOTHING
                    RETURNING id
                    """,
                    (chat_id, username)
                )
                if cur.fetchone() is None:
                    update.message.reply_text(f"You're already tracking @{username}")
                else:
                    update.message.reply_text(f"✅ Now tracking @{username}")
                conn.commit()
    except Exception as e:
        logger.error(f"Database error while tracking: {e}")
        update.message.reply_text("❌ Sorry, something went wrong. Please try again later.")

def untrack(update: Update, context: CallbackContext) -> None:
    """Untrack a Twitter account."""
    if not context.args:
        update.message.reply_text("❌ Please provide a Twitter username to untrack.\nExample: /untrack elonmusk")
        return

    username = context.args[0].strip('@').lower()
    chat_id = update.effective_chat.id

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM tracked_accounts
                    WHERE chat_id = %s AND twitter_username = %s
                    RETURNING id
                    """,
                    (chat_id, username)
                )
                if cur.fetchone() is None:
                    update.message.reply_text(f"You're not tracking @{username}")
                else:
                    update.message.reply_text(f"✅ Stopped tracking @{username}")
                conn.commit()
    except Exception as e:
        logger.error(f"Database error while untracking: {e}")
        update.message.reply_text("❌ Sorry, something went wrong. Please try again later.")

def list_tracked(update: Update, context: CallbackContext) -> None:
    """List all tracked Twitter accounts."""
    chat_id = update.effective_chat.id

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT twitter_username
                    FROM tracked_accounts
                    WHERE chat_id = %s
                    ORDER BY twitter_username
                    """,
                    (chat_id,)
                )
                accounts = cur.fetchall()

                if not accounts:
                    update.message.reply_text("📋 You're not tracking any accounts yet.\nUse /track <username> to start tracking!")
                else:
                    account_list = "\n".join(f"• @{account[0]}" for account in accounts)
                    update.message.reply_text(f"📋 Tracked accounts:\n\n{account_list}")
    except Exception as e:
        logger.error(f"Database error while listing: {e}")
        update.message.reply_text("❌ Sorry, something went wrong. Please try again later.")

def main() -> None:
    """Start the bot."""
    try:
        # Create the Updater and pass it your bot's token
        updater = Updater(os.getenv('TELEGRAM_BOT_TOKEN', '7732246779:AAHCJQeiZFaH27SkQ2HaffiP7_l2tgAQwBM'))

        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher

        # Add command handlers
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CommandHandler("track", track))
        dispatcher.add_handler(CommandHandler("untrack", untrack))
        dispatcher.add_handler(CommandHandler("list", list_tracked))

        # Start the Bot
        logger.info("Starting bot...")
        updater.start_polling()

        # Run the bot until you press Ctrl-C
        updater.idle()

    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

if __name__ == "__main__":
    main()