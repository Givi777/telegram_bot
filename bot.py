import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from flask import Flask

load_dotenv()

bot_token = os.getenv('BOT_TOKEN')

app = Flask(__name__)

@app.route('/')
def index():
    return "<h1>Heroku Python Flask Test Page</h1><p>Your Flask app is running successfully on Heroku!</p>"


current_house_index = 0
houses = []

def fetch_houses():
    print("Fetching houses from the website...")

    url = "https://home.ss.ge/ka/udzravi-qoneba/l/bina/iyideba?cityIdList=95&currencyId=1&advancedSearch=%7B%22individualEntityOnly%22%3Atrue%7D"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        print(f"HTTP status code: {response.status_code}")

        if response.status_code == 403:
            print("Forbidden: The request is being blocked.")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')

        house_list = soup.find_all('div', class_='sc-bc0f943e-0')  
        print(f"Number of houses found: {len(house_list)}")

        fetched_houses = []
        for house in house_list:
            title = house.find('div', class_='listing-detailed-item-title').text.strip() if house.find('div', class_='listing-detailed-item-title') else 'No title available'
            photo = house.find('div', class_='sc-bc0f943e-0').find('img')['src'] if house.find('div', class_='sc-bc0f943e-0') and house.find('div', class_='sc-bc0f943e-0').find('img') else 'No photo available'
            price = house.find('span', class_='listing-detailed-item-price').text.strip() if house.find('span', class_='listing-detailed-item-price') else 'No price available'
            location = house.find('div', class_='listing-detailed-item-address').text.strip() if house.find('div', class_='listing-detailed-item-address') else 'No location available'
            floor = house.find('div', class_='floor-class').text.strip() if house.find('div', class_='floor-class') else 'No floor information available'  # Update with the correct class
            m2 = house.find('div', class_='m2-class').text.strip() if house.find('div', class_='m2-class') else 'No m² information available'  # Update with the correct class
            bedrooms = house.find('div', class_='bedroom-class').text.strip() if house.find('div', class_='bedroom-class') else 'No bedroom information available'  # Update with the correct class

            fetched_houses.append({
                'title': title,
                'photo': photo,
                'price': price,
                'location': location,
                'floor': floor,
                'm2': m2,
                'bedrooms': bedrooms
            })

        print(f"Fetched {len(fetched_houses)} houses.")
        return fetched_houses

    except Exception as e:
        print(f"Error fetching houses: {e}")
        return []


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
            if query.message.text != "No houses found.":
                await query.edit_message_text("No houses found.")
            else:
                print("Message already says 'No houses found'.")
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

def main():
    print("Starting the bot...")
    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    from threading import Thread
    thread = Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))))
    thread.start()

    application.run_polling()

if __name__ == '__main__':
    main()