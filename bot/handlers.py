from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from .utils import fetch_houses

current_house_index = 0
houses = []

async def start(update: Update, context: CallbackContext):
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

async def button(update: Update, context: CallbackContext):
    global current_house_index, houses
    query = update.callback_query
    await query.answer()

    print(f"Button pressed: {query.data}")

    if query.data == 'buy':
        print("User selected 'Buy'. Fetching house listings...")
        houses = fetch_houses() 
        current_house_index = 0

        if houses:
            print(f"Displaying the first house: {houses[0]}")
            await show_house(query)
        else:
            print("No houses found.")
            await query.edit_message_text("No houses found.")
    elif query.data == 'next':
        print(f"Next button pressed. Current house index: {current_house_index}")
        current_house_index += 1

        if current_house_index < len(houses):
            print(f"Displaying house at index {current_house_index}: {houses[current_house_index]}")
            await show_house(query)
        else:
            print("No more houses available.")
            await query.edit_message_text("No more houses available.")
    else:
        print(f"Option {query.data} not implemented yet.")
        await query.edit_message_text("Option not implemented yet.")

async def show_house(query):
    house = houses[current_house_index]
    print(f"Displaying house: {house}")

    text = (
        f"🏠 **House {current_house_index + 1}:**\n"
        f"💵 Price: {house['price']}\n"
        f"📍 Location: {house['location']}\n"
        f"📄 Title: {house['title']}\n"
    )
    keyboard = [[InlineKeyboardButton("Next", callback_data='next')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=text, reply_markup=reply_markup)

    print("House details sent to user.")
