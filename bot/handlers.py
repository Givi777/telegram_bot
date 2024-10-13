from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from bot.utils import fetch_houses, show_house

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
            await show_house(query, houses, current_house_index)
        else:
            await query.edit_message_text("No houses found.")
    elif query.data == 'next':
        current_house_index += 1
        if current_house_index < len(houses):
            await show_house(query, houses, current_house_index)
        else:
            await query.edit_message_text("No more houses available.")
