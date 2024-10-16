import requests
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import logging
import asyncio
from flask import Flask, render_template
from threading import Thread

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
bot_token = os.getenv('BOT_TOKEN')  # Set this in your .env file
selenium_service_url = os.getenv('SELENIUM_SERVICE_URL')  # Set the URL for Selenium Service in .env

app = Flask(__name__)  # Initialize Flask app

user_states = {}
user_states_lock = asyncio.Lock()

# Full house information fetched, but skipping photo fetching
async def fetch_houses(offset=0, limit=1):
    url = f"https://home.ss.ge/en/real-estate/l/Flat/For-Sale?cityIdList=95&currencyId=1"
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 403:
            logger.error(f"Failed to fetch houses: Received status code {response.status_code}.")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        house_list = soup.find_all('div', class_='sc-8fa2c16a-0')[offset:offset + limit]

        fetched_houses = []
        for house in house_list:
            title = house.find('h2', class_='listing-detailed-item-title').text.strip() if house.find('h2', class_='listing-detailed-item-title') else 'No title available'
            price = house.find('span', class_='listing-detailed-item-price').text.strip() if house.find('span', class_='listing-detailed-item-price') else 'No price available'
            location = house.find('h5', class_='listing-detailed-item-address').text.strip() if house.find('h5', class_='listing-detailed-item-address') else 'No location available'
            link_tag = house.find('a', href=True)
            house_link = f"https://home.ss.ge{link_tag['href']}" if link_tag else None
            
            # Extracting other details like bedrooms and size (if available)
            bedrooms = house.find('span', class_='listing-detailed-item-bedroom').text.strip() if house.find('span', class_='listing-detailed-item-bedroom') else 'No bedroom info'
            size = house.find('span', class_='listing-detailed-item-size').text.strip() if house.find('span', class_='listing-detailed-item-size') else 'No size info'

            # We skip the photo-fetching part in this version
            fetched_houses.append({
                'title': title,
                'photos': [],  # No photos for now
                'price': price,
                'location': location,
                'bedrooms': bedrooms,  # Add bedroom info
                'size': size,  # Add size info
                'links': [house_link] if house_link else ['No link available']
            })

        logger.info(f"Fetched {len(fetched_houses)} houses.")
        return fetched_houses
    except Exception as e:
        logger.error(f"Error fetching houses: {e}")
        return []

async def start(update: Update, context):
    user_id = update.effective_user.id

    async with user_states_lock:
        if user_id not in user_states:
            user_states[user_id] = {
                'current_house_index': 0,
                'current_photo_index': 0,
                'houses': [],
                'houses_fetched': 0,
                'fetch_task': None
            }

    keyboard = [
        [InlineKeyboardButton("Rent", callback_data='rent')],
        [InlineKeyboardButton("Buy", callback_data='buy')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Choose an option from the inline menu:",
        reply_markup=reply_markup
    )

async def button(update: Update, context):
    user_id = update.effective_user.id
    query = update.callback_query

    await query.answer()

    async with user_states_lock:
        if query.data == 'buy':
            if user_states[user_id]['houses_fetched'] == 0:
                await query.edit_message_text("Fetching the first house, please wait...")

                houses = await fetch_houses(limit=1)
                if houses:
                    user_states[user_id]['houses'] = houses
                    user_states[user_id]['houses_fetched'] = 1

                    await show_house(query, user_id)
                else:
                    await query.edit_message_text("No houses found.")
            else:
                await query.edit_message_text("Houses already fetched. Use 'Next' to view them.")

        elif query.data == 'next':
            current_index = user_states[user_id]['current_house_index']

            if current_index + 1 < user_states[user_id]['houses_fetched']:
                user_states[user_id]['current_house_index'] += 1
                await show_house(query, user_id)
            else:
                # Fetch more houses if the user reaches the end
                await query.edit_message_text("Fetching more houses, please wait...")
                houses = await fetch_houses(offset=user_states[user_id]['houses_fetched'], limit=1)
                if houses:
                    user_states[user_id]['houses'].extend(houses)
                    user_states[user_id]['houses_fetched'] += len(houses)
                    user_states[user_id]['current_house_index'] += 1

                    await show_house(query, user_id)
                else:
                    await query.edit_message_text("No more houses available.")

async def show_house(query, user_id):
    house = user_states[user_id]['houses'][user_states[user_id]['current_house_index']]

    title = house.get('title', 'No title available')
    price = house.get('price', 'No price available')
    location = house.get('location', 'No location available')
    bedrooms = house.get('bedrooms', 'No bedrooms available')
    size = house.get('size', 'No size info available')
    links = '\n'.join(house.get('links', ['No link available']))

    text = (
        f"🏠 Option: {user_states[user_id]['current_house_index'] + 1}\n\n"
        f"Title: {title}\n"
        f"Price: {price}\n"
        f"Location: {location}\n"
        f"Bedrooms: {bedrooms}\n"
        f"Size: {size}\n"
        f"Link: {links}"
    )

    # Add a "Next" button to go to the next house
    keyboard = [[InlineKeyboardButton("Next", callback_data='next')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, reply_markup=reply_markup)

def run_flask():
    @app.route('/')
    def hello():
        return "<h1>Hello</h1>"  # Return "Hello" message as HTML

    app.run(host='0.0.0.0', port=5000)  # Run Flask on port 5000

def run_telegram_bot():
    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == '__main__':
    # Use threading to run both Flask and Telegram bot
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    run_telegram_bot()
