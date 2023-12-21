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
    filters,
    MessageHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Stages
START_ROUTES, TRAINING_MENU_ROUTES, TRAINING_ROUTES, DATA_ROUTES, VISUALS_ROUTES, END_ROUTES = range(6)
# Callback data
ZERO, ONE, TWO, THREE, FOUR = range(5)
GET_REMARK, REMARK, START_AGAIN, TRAINING_MENU, TRAINING, DATA, VISUALS, END, END_FINAL, SELECT_PLAN, START_TRAINING, SELECT_EXERCISES, SELECT_NEXT_EXERCISES, RUN_EXERCISE, GET_REPS = range(15)
# Initialize dbhelper
dbhelper = DBHelper(dbname="./DB/Calisthenics")

def bulid_exercise_keyboard():
    exercises = dbhelper.exercises()
    output_keyboard = [InlineKeyboardButton(exercise[1], callback_data=str(RUN_EXERCISE)+'_'+str(exercise[0])) for exercise in exercises]
    output_keyboard.insert(0, InlineKeyboardButton("End Training", callback_data=str(END)))
    return output_keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send message on `/start`."""
    keyboard = [
        [
            InlineKeyboardButton("Start Training", callback_data=str(TRAINING_MENU)),
            InlineKeyboardButton("Add or Change Data", callback_data=str(DATA)),
            InlineKeyboardButton("Visual", callback_data=str(VISUALS)),
            InlineKeyboardButton("End", callback_data=str(END)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    # Depending on when the this command is called, we need a new message or edit the message/keyboard.
    if update.message is not None:
        user = update.message.from_user
        logger.info("User %s started the conversation.", user.first_name)
        await update.message.reply_text("What do you want to do today :)?", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text="What do you want to do today :)?", reply_markup=reply_markup)
    return START_ROUTES

async def training_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Plan", callback_data=str(SELECT_PLAN)),
            InlineKeyboardButton("Exercises", callback_data=str(START_TRAINING)),
            InlineKeyboardButton("End", callback_data=str(END)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Choose a trainig.", reply_markup=reply_markup
    )
    return TRAINING_MENU_ROUTES

async def data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Run Again", callback_data=str(DATA)),
            InlineKeyboardButton("End", callback_data=str(END)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Let's add some more exercise", reply_markup=reply_markup
    )
    return DATA_ROUTES

async def visuals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Run Again", callback_data=str(VISUALS)),
            InlineKeyboardButton("End", callback_data=str(END)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="You want to see how strong you are?", reply_markup=reply_markup
    )
    return VISUALS_ROUTES

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Start again", callback_data=str(START_AGAIN)),
            InlineKeyboardButton("End", callback_data=str(END_FINAL)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Are you sure to quit?", reply_markup=reply_markup
    )
    return END_ROUTES

async def end_final(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="See you next time!")
    return ConversationHandler.END


async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Go Back", callback_data=str(TRAINING_MENU)),
            InlineKeyboardButton("Start training", callback_data=str(START_TRAINING)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Select today's plan", reply_markup=reply_markup
    )
    return TRAINING_MENU_ROUTES

async def start_training(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Go Back", callback_data=str(TRAINING_MENU)),
            InlineKeyboardButton("Start training", callback_data=str(SELECT_EXERCISES)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Okay, let's go!", reply_markup=reply_markup
    )
    return TRAINING_ROUTES

async def select_exercises(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """This function needs to have following functionalities:
            1. Show all exercieses with the possibility to choose them (maybe only 10? With more button? Later...)
            2. Have a fallback into start menu
    """
    query = update.callback_query
    await query.answer()
    keyboard = [bulid_exercise_keyboard()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if query.data == str(SELECT_EXERCISES):
        dbhelper.start_training()
        await query.edit_message_text(text="Select your exercise:", reply_markup=reply_markup)
    else:
        await query.edit_message_text(text="Nice, let's do the next exercise")
        await context.bot.send_message(chat_id=query.message.chat_id, text="Select your exercise:", reply_markup=reply_markup)
    return TRAINING_ROUTES

async def run_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """When this function is called for the first time, it should show the last set and repetions of the exercise (if there is any).
    Then it should ask for input of the new set and repetions. Set by set.
    """
    query = update.callback_query
    dbhelper.exercise_id = query.data.split('_')[1]
    await query.edit_message_text(text=dbhelper.get_last_exercise_info())
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Done", callback_data=str(SELECT_NEXT_EXERCISES))]])
    await context.bot.send_message(chat_id=query.message.chat_id, text="How many reps did you do?", reply_markup=reply_markup)
    return TRAINING_ROUTES

async def get_remark(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Write a remark for the current exercise and return to run exercise.
    """
    dbhelper.update_history_remark(update.message.text)

async def get_reps(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    """This function should be called after run_exercise and should get the number of reps for the last set."""
    dbhelper.update_history_reps(update.message.text)

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
                CallbackQueryHandler(training_menu, pattern="^" + str(TRAINING_MENU) + "$"),
                CallbackQueryHandler(data, pattern="^" + str(DATA) + "$"),
                CallbackQueryHandler(visuals, pattern="^" + str(VISUALS) + "$"),
                CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
            ],
            TRAINING_MENU_ROUTES: [
                CallbackQueryHandler(training_menu, pattern="^" + str(TRAINING_MENU) + "$"),
                CallbackQueryHandler(select_plan, pattern="^" + str(SELECT_PLAN) + "$"),
                CallbackQueryHandler(start_training, pattern="^" + str(START_TRAINING) + "$"),
                CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
            ],
            TRAINING_ROUTES: [
                CallbackQueryHandler(get_remark, pattern="^" + str(GET_REMARK) + "$"),
                CallbackQueryHandler(select_exercises, pattern="^" + str(SELECT_EXERCISES) + "$"),
                CallbackQueryHandler(select_exercises, pattern="^" + str(SELECT_NEXT_EXERCISES) + "$"),
                CallbackQueryHandler(run_exercise, pattern="^" + str(RUN_EXERCISE) + "_*."),
                CallbackQueryHandler(training_menu, pattern="^" + str(TRAINING_MENU) + "$"),
                CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
                # MessageHandler with regex filter for all numbers
                MessageHandler(filters.Regex(pattern="^[0-9]+$"), get_reps),
                # MessageHandler with regex filter message starting with a letter
                MessageHandler(filters.Regex(pattern="^[a-zA-Z]+"), get_remark),
            ],
            DATA_ROUTES: [
                CallbackQueryHandler(data, pattern="^" + str(DATA) + "$"),
                CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
            ],
            VISUALS_ROUTES: [
                CallbackQueryHandler(visuals, pattern="^" + str(VISUALS) + "$"),
                CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
            ],
            END_ROUTES: [
                CallbackQueryHandler(start, pattern="^" + str(START_AGAIN) + "$"),
                CallbackQueryHandler(end_final, pattern="^" + str(END_FINAL) + "$"),
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

