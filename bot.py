import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from flask import Flask
from selenium import webdriver


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

    url = "https://home.ss.ge/en/real-estate/l/Flat/For-Sale?cityIdList=95&currencyId=1&advancedSearch=%7B%22individualEntityOnly%22%3Atrue%7D"
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
            title = house.find('h2', class_='listing-detailed-item-title').text.strip() if house.find('h2', class_='listing-detailed-item-title') else 'No title available'

            photo_divs = house.find_all('img', class_='sc-bc0f943e-3')
            photos = [img['src'] for img in photo_divs if img.get('src')]

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
            bedrooms = house.find('span', class_='icon-bed').find_parent('div').text.strip() if house.find('span', class_='icon-bed') else 'No bedroom information available'


            link_list = soup.find_all('div', class_='sc-1384a2b8-6 jlmink')  
            print(f"Number of links found: {len(link_list)}")

            link = None

            for link_div in link_list:
                a_tag = link_div.find('a') 
                if a_tag and 'href' in a_tag.attrs: 
                    link = a_tag['href']  
                    print(f"Found link: {link}")
                    break  
                else:
                    print('No valid link found in this div.')

            fetched_houses.append({
                'title': title,
                'photos': photos,  
                'price': price,
                'location': location,
                'floor': floor,
                'm2': m2,
                'bedrooms': bedrooms,
                'link': link if link else "No link available"  
            })

        return fetched_houses

    except Exception as e:
        print(f"Error fetching houses: {e}")
        return []



async def start(update: Update, context):
    print("Start command triggered.")
    keyboard = [
        [InlineKeyboardButton("Rent", callback_data='rent')],
        [InlineKeyboardButton("Buy", callback_data='buy')]
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
        f"🏠 Option: {current_house_index + 1}\n"
        f"📄 Title: {house['title']}\n"
        f"💵 Price: {house['price']}\n"
        f"📍 Location: {house['location']}\n"
        f"🛏️ Bedrooms: {house['bedrooms']}\n"
        f"🏢 Floor: {house['floor']}\n"
        f"📏 Size: {house['m2']}\n"
        f"🔗 Link: {house['link']}\n"  # Display the link
    )

    if house['photos']:
        photo = house['photos'][0] 
        keyboard = [
            [InlineKeyboardButton("Next", callback_data='next')],
            [InlineKeyboardButton("View more photos", callback_data=f'view_photos_{current_house_index}')]  # Button to view more photos
        ]
    else:
        photo = None
        keyboard = [[InlineKeyboardButton("Next", callback_data='next')]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if photo:
        await query.message.reply_photo(photo=photo, caption=text, reply_markup=reply_markup)
    else:
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
