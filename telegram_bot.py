# Internal packages:
from telegram_token import TOKEN
from dbhelpers import DBHelper
# External packages
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Stages
START_ROUTES, TRAINING_ROUTES, END_ROUTES = range(3)
# Callback data
ONE, TWO, THREE, FOUR = range(4)
# Initialize dbhelper
dbhelper = DBHelper(dbname="./DB/Calisthenics")

def bulid_exercise_keyboard():
    exercises = dbhelper.exercises()
    output_keyboard = [InlineKeyboardButton(exercise[0], callback_data=str(TWO)) for exercise in exercises]
    output_keyboard.insert(0, InlineKeyboardButton("Go Back to Start", callback_data=str(ONE)) )
    return output_keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    # Build InlineKeyboard where each button has a displayed text
    # and a string as callback_data
    # The keyboard is a list of button rows, where each row is in turn
    # a list (hence `[[...]]`).
    keyboard = [
        [
            InlineKeyboardButton("Start Training", callback_data=str(ONE)),
            InlineKeyboardButton("Do other stuff...(later)", callback_data=str(TWO)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    await update.message.reply_text("Start handler, Choose a route", reply_markup=reply_markup)
    # Tell ConversationHandler that we're in state `FIRST` now
    return START_ROUTES


async def training(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Plan", callback_data=str(ONE)),
            InlineKeyboardButton("Exercises", callback_data=str(TWO)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Choose a traing.", reply_markup=reply_markup
    )
    return TRAINING_ROUTES

async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Plan", callback_data=str(ONE)),
            InlineKeyboardButton("Exercises", callback_data=str(TWO)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Choose a traing.", reply_markup=reply_markup
    )
    return TRAINING_ROUTES

async def exercises(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """This function needs to have following functionalities:
            1. Show all exercieses with the possibility to choose them (maybe only 10? With more button? Later...)
            2. Have a fallback into start menu
    """
    query = update.callback_query
    await query.answer()
    keyboard = [bulid_exercise_keyboard()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Choose a traing.", reply_markup=reply_markup
    )
    return TRAINING_ROUTES

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="See you next time!")
    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Setup conversation handler with the states FIRST and SECOND
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_ROUTES: [
                CallbackQueryHandler(training, pattern="^" + str(ONE) + "$"),
                CallbackQueryHandler(end, pattern="^" + str(TWO) + "$"),
            ],
            TRAINING_ROUTES: [
                CallbackQueryHandler(plan, pattern="^" + str(ONE) + "$"),
                CallbackQueryHandler(exercises, pattern="^" + str(TWO) + "$"),
            ],
            END_ROUTES: [
                CallbackQueryHandler(end, pattern="^" + str(TWO) + "$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
