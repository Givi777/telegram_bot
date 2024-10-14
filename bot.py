import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from threading import Thread
from flask import Flask


app = Flask(__name__)

@app.route('/')
def index():
    return "<h1>Heroku</h1>"

load_dotenv()

bot_token = os.getenv('BOT_TOKEN')

user_states = {}




def fetch_houses():
    url = "https://home.ss.ge/en/real-estate/l/Flat/For-Sale?cityIdList=95&currencyId=1&advancedSearch=%7B%22individualEntityOnly%22%3Atrue%7D"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 403:
            return []

        soup = BeautifulSoup(response.content, 'html.parser')

        house_list = soup.find_all('div', class_='sc-8fa2c16a-0')

        fetched_houses = []
        for house in house_list:
            # Basic house info scraping
            title = house.find('h2', class_='listing-detailed-item-title')
            title = title.text.strip() if title else 'No title available'

            price = house.find('span', class_='listing-detailed-item-price').text.strip() if house.find('span', class_='listing-detailed-item-price') else 'No price available'
            location = house.find('h5', class_='listing-detailed-item-address').text.strip() if house.find('h5', class_='listing-detailed-item-address') else 'No location available'

            floor_divs = house.find_all('div', class_='sc-bc0f943e-14 hFQLKZ')
            floor = None
            for div in floor_divs:
                if "icon-stairs" in div.find('span')['class']:
                    floor = div.text.strip()
                    break
            floor = floor if floor else 'No floor information available'

            m2 = house.find_all('div', class_='sc-bc0f943e-14 hFQLKZ')[0].text.strip() if house.find_all('div', class_='sc-bc0f943e-14 hFQLKZ') else 'No m² information available'
           
            bedrooms = house.find('span', class_='icon-bed').find_parent('div')
            bedrooms = bedrooms.text.strip() if bedrooms else 'No available'

            link_tag = house.find('a', href=True)
            if link_tag:
                relative_link = link_tag['href']
                house_link = f"https://home.ss.ge{relative_link}"  # Construct full URL
            else:
                house_link = None

            photos = []


            fetched_houses.append({
                'title': title,
                'photos': photos,
                'price': price,
                'location': location,
                'floor': floor,
                'm2': m2,
                'bedrooms': bedrooms,
                'links': [house_link] if house_link else ['No link available']
            })

        return fetched_houses

    except Exception as e:
        print(f"Error fetching houses: {e}")
        return []





async def start(update: Update, context):
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
    if user_id not in user_states:
        user_states[user_id] = {
            'current_house_index': 0,
            'houses': [],
            'houses_fetched': False  # Track if houses have been fetched
        }

    query = update.callback_query
    await query.answer()

    if query.data == 'buy':
        if not user_states[user_id]['houses_fetched']:
            houses = fetch_houses()
            user_states[user_id]['houses'] = houses
            user_states[user_id]['houses_fetched'] = True  # Mark houses as fetched
            user_states[user_id]['current_house_index'] = 0

            if houses:
                await show_house(query, user_id)
            else:
                await query.edit_message_text("No houses found.")
        else:
            # Create the reply markup with the "Next" button
            keyboard = [
                [InlineKeyboardButton("Next", callback_data='next')]
            ]

            await query.edit_message_text(
                "Houses have already been fetched. Please use the Next button to view them.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    elif query.data == 'next':
        current_house_index = user_states[user_id]['current_house_index']
        
        if current_house_index + 1 < len(user_states[user_id]['houses']):
            user_states[user_id]['current_house_index'] += 1  # Increment the index
            await show_house(query, user_id)  # Show the next house
        else:
            await query.edit_message_text("No more houses available.")

    elif query.data.startswith('interested_'):
        house_index = int(query.data.split('_')[1])
        await query.edit_message_text(f"You've expressed interest in house {house_index + 1}. We'll follow up with more details.")
    else:
        await query.edit_message_text("Option not implemented yet.")


async def show_house(query, user_id):
    current_house_index = user_states[user_id]['current_house_index']
    house = user_states[user_id]['houses'][current_house_index]

    # Fallback for missing data
    title = house.get('title', 'No title available')
    price = house.get('price', 'No price available')
    location = house.get('location', 'No location available')
    bedrooms = house.get('bedrooms', 'No bedroom information available')
    floor = house.get('floor', 'No floor information available')
    m2 = house.get('m2', 'No m² information available')
    
    # Format the links as a single string, joined by newlines
    links_text = "\n".join(house.get('links', ['No link available']))

    # Compose the message text
    text = (
        f"🏠 Option: {current_house_index + 1}\n"
        f"📄 Title: {title}\n"
        f"💵 Price: {price}\n"
        f"📍 Location: {location}\n"
        f"🛏️ Bedrooms: {bedrooms}\n"
        f"🏢 Floor: {floor}\n"
        f"📏 Size: {m2}\n"
        f"🔗 Links: {links_text}\n"
    )

    # Create the reply markup with buttons for the user to navigate
    keyboard = [
        [InlineKeyboardButton("Next", callback_data='next')],
        [InlineKeyboardButton("I'm Interested", callback_data=f'interested_{current_house_index}')]
    ]
    
    # If photos are available, include the first one
    if house.get('photos'):
        photo = house['photos'][0]
        await query.message.reply_photo(photo=photo, caption=text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        # If no photos are available, just send the text message
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

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