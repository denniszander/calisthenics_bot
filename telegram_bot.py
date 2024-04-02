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
START_ROUTES, TRAINING_MENU_ROUTES, TRAINING_ROUTES, DATA_ROUTES, END_ROUTES = range(5)
# Callback data
ADD_EXERCISE, EDIT_EXERCISE, DELETE_EXERCISE_DATA, GET_REMARK, REMARK, START_AGAIN, TRAINING_MENU, TRAINING, DATA, END, END_FINAL, SELECT_PLAN, START_TRAINING, SELECT_EXERCISES, SELECT_EXERCISES_SPLIT, SELECT_NEXT_EXERCISES, RUN_EXERCISE, RUN_EXERCISE_SPLIT, GET_REPS, DATA_ADD = range(20)
# Initialize dbhelper
dbhelper = DBHelper(dbname="./DB/Calisthenics")

def bulid_exercise_keyboard():
    exercises = dbhelper.exercises()
    if dbhelper.split and dbhelper.exercise_id is None:
        callback_data = str(SELECT_EXERCISES_SPLIT)
    else:
        callback_data = str(RUN_EXERCISE)
    output_keyboard = [[InlineKeyboardButton(exercise[1], callback_data=callback_data + '_' + str(exercise[0]))] for exercise in exercises]
    if not dbhelper.split:
        output_keyboard.insert(0, [InlineKeyboardButton("Split Training", callback_data=str(SELECT_EXERCISES_SPLIT))])
        output_keyboard.insert(0, [InlineKeyboardButton("End Training", callback_data=str(END))])
    return output_keyboard

def bulid_plan_keyboard():
    plans = dbhelper.plans()
    output_keyboard = [[InlineKeyboardButton(plan[1], callback_data=str(START_TRAINING)+'_'+str(plan[0]))] for plan in plans]
    return output_keyboard

def build_run_exercise_keyboard():
    output_keyboard = [[InlineKeyboardButton("Done", callback_data=str(SELECT_NEXT_EXERCISES))],
                       [InlineKeyboardButton("Delete Data", callback_data=str(DELETE_EXERCISE_DATA))]
                      ]
    if dbhelper.split:
        split_exercise = dbhelper.split_exercise()
        output_keyboard.insert(2, [InlineKeyboardButton("Change to: " +  split_exercise[1], callback_data=str(RUN_EXERCISE_SPLIT) + '_' + str(split_exercise[0]))])
    return output_keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send message on `/start`."""
    keyboard = [
        [InlineKeyboardButton("Start Training", callback_data=str(TRAINING_MENU))],
        [InlineKeyboardButton("Add or Change Data", callback_data=str(DATA))],
        [InlineKeyboardButton("End", callback_data=str(END))],
     ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_markup
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
        [InlineKeyboardButton("Plan", callback_data=str(SELECT_PLAN))],
        [InlineKeyboardButton("Exercises", callback_data=str(START_TRAINING))],
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Choose a training.", reply_markup=reply_markup
    )
    return TRAINING_MENU_ROUTES

async def data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = [
            [InlineKeyboardButton("Add Exercise", callback_data=str(ADD_EXERCISE))],
        [InlineKeyboardButton("End", callback_data=str(END))],
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    basic_text = "Let's add some more exercise"
    if query.data == str(DATA):
        await query.edit_message_text(text=basic_text, reply_markup=reply_markup)
    elif query.data == str(DATA_ADD):
        add_text = F"Exercise: {context.user_data['exercise_name']} \nURL: {context.user_data['exercise_url']}\n"
        dbhelper.add_new_exercise(context.user_data['exercise_name'], context.user_data['exercise_url'])
        await query.edit_message_text(text='Exercise added!')
        await context.bot.send_message(chat_id=query.message.chat_id, text=add_text + basic_text, reply_markup=reply_markup)
    return DATA_ROUTES

async def add_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    status = context.user_data.get('add_exercise_status')
    if status is None:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text="Let me know the Name of the exercise:")
        context.user_data['last_query'] = query
    elif status == 1:
        query = context.user_data['last_query']
        await query.edit_message_text(text="Let me know the URL of the exercise:")
    elif status == 2:
        context.user_data.pop('add_exercise_status', None)
        query = context.user_data['last_query']
        context.user_data.pop('last_query', None)
        keyboard = [[InlineKeyboardButton("Save", callback_data=str(DATA_ADD))], [InlineKeyboardButton("Dismiss", callback_data=str(DATA))],]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="What do you want to do?", reply_markup=reply_markup)
    return DATA_ROUTES

async def get_message_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Write user input into context.user_data (name and url of exercise)
    Only accept two messages, after that no more messages are accepted.
    """
    status = context.user_data.get('add_exercise_status')
    message_text = update.message.text
    if status is None:
        context.user_data['exercise_name'] = message_text
        context.user_data['add_exercise_status'] = 1
    elif status == 1:
        context.user_data['exercise_url'] = message_text
        context.user_data['add_exercise_status'] = 2
    return await add_exercise(update, context)

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Start again", callback_data=str(START_AGAIN))],
        [InlineKeyboardButton("End", callback_data=str(END_FINAL))],
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
    dbhelper.training_id = None     # Reset training id! Only done here.
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="See you next time!")
    return ConversationHandler.END

async def start_training(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    # Get the plan_id from the callback data (if available)
    plan_id = query.data.split('_')
    if len(plan_id) == 2:
        dbhelper.plan_id = plan_id[1]
    else :
        dbhelper.plan_id = None # Reset plan_id if set before
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Start training", callback_data=str(SELECT_EXERCISES))],
        [InlineKeyboardButton("Go Back", callback_data=str(TRAINING_MENU))],
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
    # Prepare some variables
    exercise_text = "Select your exercise:"

    # Get and process the callback data
    query = update.callback_query
    await query.answer()
    query_split = query.data.split('_')
    if query.data == str(SELECT_EXERCISES): # SELECT_EXERCISES is only called once at the beginning of the training
        dbhelper.start_training()
        logger.info(f'Start new training with id: {dbhelper.training_id}')
    elif query.data == str(SELECT_NEXT_EXERCISES):
        # Reset exercise variables
        dbhelper.exercise_id = None
        dbhelper.exercise_split_id = None
        dbhelper.split = False
    elif query.data == str(SELECT_EXERCISES_SPLIT):
        dbhelper.split = True
    elif len(query_split) == 2 and query_split[0] == str(SELECT_EXERCISES_SPLIT):
        dbhelper.exercise_id = query_split[1]
        exercise_text = "Select your next exercise:"

    # Build the keyboard
    reply_markup = InlineKeyboardMarkup(bulid_exercise_keyboard())

    # Process answers to user
    if query.data == str(SELECT_NEXT_EXERCISES):
        text = "Nice job! \n" + dbhelper.get_last_exercise_info() 
        await query.edit_message_text(text=text)
        await context.bot.send_message(chat_id=query.message.chat_id, text=exercise_text, reply_markup=reply_markup)
    else:
        await query.edit_message_text(text=exercise_text, reply_markup=reply_markup)
    return TRAINING_ROUTES

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """This function needs to have following functionalities:
            1. Show all exercieses with the possibility to choose them (maybe only 10? With more button? Later...)
            2. Have a fallback into start menu
    """
    query = update.callback_query
    await query.answer()
    reply_markup = InlineKeyboardMarkup(bulid_plan_keyboard())
    await query.edit_message_text(text="Select your plan:", reply_markup=reply_markup)
    return TRAINING_MENU_ROUTES

async def run_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """When this function is called for the first time, it should show the last set and repetions of the exercise (if there is any).
    Then it should ask for input of the new set and repetions. Set by set.
    """
    query = update.callback_query
    query_split = query.data.split('_')
    if query_split[0] == str(RUN_EXERCISE): # RUN_EXERCISE is called from other functions
        if dbhelper.split:
            dbhelper.exercise_split_id = query_split[1]
        else:
            dbhelper.exercise_id = query_split[1]
    elif query_split[0] == str(RUN_EXERCISE_SPLIT):
        dbhelper.exercise_split_id = dbhelper.exercise_id
        dbhelper.exercise_id = query_split[1]

    text = "Last time you did: \n" + dbhelper.get_last_exercise_info()
    await query.edit_message_text(text=text)
    reply_markup = InlineKeyboardMarkup(build_run_exercise_keyboard())
    await context.bot.send_message(chat_id=query.message.chat_id, text="How many reps did you do?", reply_markup=reply_markup)
    return TRAINING_ROUTES

async def delete_exercise_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """This function should delete the last entry of the current exercise and return to run_exercise."""
    dbhelper.delete_exercise_data()

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
                CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
            ],
            TRAINING_MENU_ROUTES: [
                CallbackQueryHandler(training_menu, pattern="^" + str(TRAINING_MENU) + "$"),
                CallbackQueryHandler(select_plan, pattern="^" + str(SELECT_PLAN) + "$"),
                CallbackQueryHandler(start_training, pattern="^" + str(START_TRAINING) ),
                CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
            ],
            TRAINING_ROUTES: [
                CallbackQueryHandler(get_remark, pattern="^" + str(GET_REMARK) + "$"),
                CallbackQueryHandler(select_exercises, pattern="^" + str(SELECT_EXERCISES) + "$"),
                CallbackQueryHandler(select_exercises, pattern="^" + str(SELECT_EXERCISES_SPLIT)),
                CallbackQueryHandler(select_exercises, pattern="^" + str(SELECT_NEXT_EXERCISES) + "$"),
                CallbackQueryHandler(run_exercise, pattern="^" + str(RUN_EXERCISE) + "_*."),
                CallbackQueryHandler(run_exercise, pattern="^" + str(RUN_EXERCISE_SPLIT) + "_*."),
                CallbackQueryHandler(training_menu, pattern="^" + str(TRAINING_MENU) + "$"),
                CallbackQueryHandler(delete_exercise_data, pattern="^" + str(DELETE_EXERCISE_DATA) + "$"),
                CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
                # MessageHandler with regex filter for all numbers
                MessageHandler(filters.Regex(pattern="^[0-9]+$"), get_reps),
                # MessageHandler with regex filter message starting with a letter
                MessageHandler(filters.Regex(pattern="^[a-zA-Z]+"), get_remark),
            ],
            DATA_ROUTES: [
                CallbackQueryHandler(data, pattern="^" + str(DATA) + "$"),
                CallbackQueryHandler(data, pattern="^" + str(DATA_ADD) + "$"),
                CallbackQueryHandler(add_exercise, pattern="^" + str(ADD_EXERCISE) + "$"),
                CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
                MessageHandler(filters.TEXT, get_message_text),
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

