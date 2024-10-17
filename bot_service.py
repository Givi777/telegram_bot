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
    return "<h1>Hello</h1>"

load_dotenv()
bot_token = os.getenv('BOT_TOKEN')
user_states = {}

async def fetch_houses(page=1):
    url = f"https://home.ss.ge/en/real-estate/l/Flat/For-Sale?cityIdList=95&currencyId=1&page={page}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 403:
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Fetch house links from the first div
        house_link_divs = soup.find_all('div', class_='sc-8fa2c16a-0')
        house_links = [f"https://home.ss.ge{div.find('a')['href']}" for div in house_link_divs if div.find('a', href=True)]

        # Fetch other house details from the second div
        house_detail_divs = soup.find_all('div', class_='sc-bc0f943e-0')
        
        fetched_houses = []
        for i, detail_div in enumerate(house_detail_divs):
            title = detail_div.find('h2', class_='listing-detailed-item-title')
            title = title.text.strip() if title else 'No title available'

            price = detail_div.find('span', class_='listing-detailed-item-price')
            price = price.text.strip() if price else 'No price available'

            location = detail_div.find('h5', class_='listing-detailed-item-address')
            location = location.text.strip() if location else 'No location available'

            floor_divs = detail_div.find_all('div', class_='sc-bc0f943e-14 hFQLKZ')
            floor = next((div.text.strip() for div in floor_divs if "icon-stairs" in div.find('span')['class']), 'No floor information available')

            m2 = floor_divs[0].text.strip() if floor_divs else 'No m² information available'

            bedrooms = detail_div.find('span', class_='icon-bed').find_parent('div')
            bedrooms = bedrooms.text.strip() if bedrooms else 'No available'

            # Match the link from the previous div (assuming the number of links matches the number of details)
            house_link = house_links[i] if i < len(house_links) else None

            fetched_houses.append({
                'title': title,
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
    query = update.callback_query

    await query.answer()

    if user_id not in user_states:
        user_states[user_id] = {'current_house_index': 0, 'houses': [], 'houses_fetched': False, 'page': 1}

    if query.data == 'buy':
        # Show district options
        keyboard = [
            [InlineKeyboardButton("Vake-Saburtalo", callback_data='Vake-Saburtalo')],
            [InlineKeyboardButton("Isani-Samgori", callback_data='Isani-Samgori')],
            [InlineKeyboardButton("Gldani-Nadzaladevi", callback_data='Gldani-Nadzaladevi')],
            [InlineKeyboardButton("Didube-Chugureti", callback_data='Didube-Chugureti')],
            [InlineKeyboardButton("Old Tbilisi", callback_data='Old Tbilisi')],
            [InlineKeyboardButton("All regions", callback_data='all_regions')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Please choose a district:", reply_markup=reply_markup)

    # Handle district selection and ask for neighborhood if applicable
    elif query.data in ['Vake-Saburtalo', 'Isani-Samgori', 'Gldani-Nadzaladevi', 'Didube-Chugureti', 'Old Tbilisi']:
        user_states[user_id]['selected_district'] = query.data

        # Show relevant neighborhoods for the selected district
        if query.data == 'Vake-Saburtalo':
            neighborhoods = [
                "Nutsubidze plateau", "Saburtalo", "Digomi village", "Districts of Vazha-Pshavela", "Lisi lake",
                "Turtle lake", "Bagebi", "Didi digomi", "Digomi 1 - 9", "Vake", "Vashlijvari", "Vedzisi", "Tkhinvali"
            ]
        elif query.data == 'Isani-Samgori':
            neighborhoods = ["Airport village", "Dampalo village", "Vazisubani", "Varketili", "Isani", "Lilo", "Mesame masivi", "Ortachala", "Orkhevi", "Samgori", "Ponichala", "Airport", "Afrika", "Navtlugi"]
        elif query.data == 'Gldani-Nadzaladevi':
            neighborhoods = ["Avchala", "Gldani", "Gldanula", "Zahesi", "Tbilisi sea", "Temqa", "Koniaki village", "Lotkini", "Mukhiani", "Nadzaladevi", "Sanzona", "Gldani village", "Ivertubani"]
        elif query.data == 'Didube-Chugureti':
            neighborhoods = ["Didube", "Digomi", "Kukia", "Svanetis ubani", "Chugureti"]
        elif query.data == 'Old Tbilisi':
            neighborhoods = ["Abanotubani", "Avlabari", "Elia", "Vera", "Mtatsminda", "Sololaki"]

        keyboard = [[InlineKeyboardButton(nb, callback_data=f'neighborhood_{nb}')] for nb in neighborhoods]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"Please choose a neighborhood in {query.data}:", reply_markup=reply_markup)

    elif query.data == 'all_regions':
        user_states[user_id]['selected_district'] = 'all_regions'
        user_states[user_id]['houses_fetched'] = False
        await query.edit_message_text("Fetching houses for all regions, please wait...")
        houses = await fetch_houses(user_states[user_id]['page'])
        user_states[user_id]['houses'] = houses
        user_states[user_id]['houses_fetched'] = True

        if houses:
            await show_house(query, user_id)
        else:
            await query.edit_message_text("No houses found.")
    
    # Handle neighborhood selection
    elif query.data.startswith('neighborhood_'):
        neighborhood = query.data.split('_')[1]
        user_states[user_id]['selected_neighborhood'] = neighborhood
        await query.edit_message_text(f"You selected {neighborhood}. Fetching houses, please wait...")
        houses = await fetch_houses(user_states[user_id]['page'])
        user_states[user_id]['houses'] = houses
        user_states[user_id]['houses_fetched'] = True

        if houses:
            await show_house(query, user_id)
        else:
            await query.edit_message_text("No houses found.")

    elif query.data == 'next':
        current_index = user_states[user_id]['current_house_index']
        if current_index + 1 < len(user_states[user_id]['houses']):
            user_states[user_id]['current_house_index'] += 1
            await show_house(query, user_id)
        else:
            # If all houses from current page are shown, fetch the next page
            user_states[user_id]['page'] += 1
            await query.edit_message_text(f"Fetching page {user_states[user_id]['page']} houses, please wait...")
            new_houses = await fetch_houses(user_states[user_id]['page'])

            if new_houses:
                user_states[user_id]['houses'].extend(new_houses)
                user_states[user_id]['current_house_index'] += 1
                await show_house(query, user_id)
            else:
                await query.edit_message_text("All houses are fetched. Use 'Restart' to refetch.")
                keyboard = [
                    [InlineKeyboardButton("Restart", callback_data='restart')]
                ]
                await query.edit_message_text("All houses fetched.", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'restart':
        user_states[user_id] = {'current_house_index': 0, 'houses': [], 'houses_fetched': False, 'page': 1}
        await query.edit_message_text("Fetching new houses, please wait...")
        houses = await fetch_houses(user_states[user_id]['page'])
        user_states[user_id]['houses'] = houses
        user_states[user_id]['houses_fetched'] = True

        if houses:
            await show_house(query, user_id)
        else:
            await query.edit_message_text("No houses found.")

    elif query.data.startswith('interested_'):
        house_index = int(query.data.split('_')[1])
        await query.message.reply_text(f"You are interested in house {house_index + 1}. We'll follow up with more details.")

async def show_house(query, user_id):
    house = user_states[user_id]['houses'][user_states[user_id]['current_house_index']]
    
    title = house.get('title', 'No title available')
    price = house.get('price', 'Neogitable Price')
    location = house.get('location', 'No location available')
    bedrooms = house.get('bedrooms', 'No bedrooms available')
    floor = house.get('floor', 'No floor information available')
    size = house.get('m2', 'No size available')
    links = '\n'.join(house.get('links', ['No link available']))

    text = (
        f"🏠 Option: {user_states[user_id]['current_house_index'] + 1}\n"
        f"📄 Title: {title}\n"
        f"💵 Price: {price}\n"
        f"📍 Location: {location}\n"
        f"🛏️ Bedrooms: {bedrooms}\n"
        f"🏢 Floor: {floor}\n"
        f"📏 Size: {size}\n"
        f"📏 links: {links}\n"
    )

    keyboard = [
        [InlineKeyboardButton("Next", callback_data='next')],
        [InlineKeyboardButton("I'm Interested", callback_data=f'interested_{user_states[user_id]["current_house_index"]}')]
    ]

    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    application = Application.builder().token(bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    thread = Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))))
    thread.start()

    application.run_polling()

if __name__ == '__main__':
    main()
