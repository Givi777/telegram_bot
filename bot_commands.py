import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from scraper import fetch_houses

# Load the bot token from environment variables
bot_token = os.getenv('BOT_TOKEN')

# Global variables to store house data
current_house_index = 0
houses = []

async def start(update: Update, context):
    print("Start command triggered.")
    keyboard = [
        [InlineKeyboardButton("Rent", callback_data='rent')],
        [InlineKeyboardButton("Buy", callback_data='buy')],
        [InlineKeyboardButton("Mortgage", callback_data='mortgage')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Choose an option from the inline menu:",
        reply_markup=reply_markup
    )
    print("Main menu sent to user.")

async def button(update: Update, context):
    global current_house_index, houses
    query = update.callback_query
    await query.answer()

    if query.data == 'buy':
        print("User selected 'Buy'. Fetching house listings...")
        houses = fetch_houses() 
        current_house_index = 0

        if houses:
            await show_house(query)
        else:
            await query.edit_message_text("No houses found.")
    elif query.data == 'next':
        current_house_index += 1
        if current_house_index < len(houses):
            await show_house(query)
        else:
            await query.edit_message_text("No more houses available.")
    else:
        await query.edit_message_text("Option not implemented yet.")

async def show_house(query):
    house = houses[current_house_index]
    text = (
        f"🏠 **House {current_house_index + 1}:**\n"
        f"💵 Price: {house['price']}\n"
        f"📍 Location: {house['location']}\n"
        f"📄 Title: {house['title']}\n"
    )
    keyboard = [[InlineKeyboardButton("Next", callback_data='next')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=text, reply_markup=reply_markup)

def setup_bot():
    application = Application.builder().token(bot_token).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    # Start polling for updates
    application.run_polling()
