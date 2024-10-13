from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from bot.utils import fetch_houses

houses = []
current_house_index = 0

async def start(update: Update, context: CallbackContext):
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

async def button(update: Update, context: CallbackContext):
    global houses, current_house_index
    query = update.callback_query
    await query.answer()

    if query.data == 'buy':
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
   
