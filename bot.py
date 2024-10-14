import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#working
load_dotenv()
bot_token = os.getenv('BOT_TEST_TOKEN')
user_states = {}

async def fetch_house_images_selenium(house_link):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.fonts": 2,
        })

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(house_link)
        
        wait = WebDriverWait(driver, 10)
        try:
            image_gallery = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'sc-1acce1b7-10')))
            image_gallery.click()
            time.sleep(2)
        except Exception as e:
            print(f"Error clicking image gallery: {e}")

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        images_div = soup.find('div', class_='lg-inner')

        if not images_div:
            driver.quit()
            return []

        img_tags = images_div.find_all('img', class_='lg-object lg-image')
        images = [img.get('data-src', img.get('src')) for img in img_tags if img.get('src') or img.get('data-src')]
        driver.quit()
        return images
    except Exception as e:
        print(f"Error fetching images from {house_link}: {e}")
        return []

async def fetch_houses():
    url = "https://home.ss.ge/en/real-estate/l/Flat/For-Sale?cityIdList=95&currencyId=1"
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
            title = house.find('h2', class_='listing-detailed-item-title')
            title = title.text.strip() if title else 'No title available'

            price = house.find('span', class_='listing-detailed-item-price').text.strip() if house.find('span', class_='listing-detailed-item-price') else 'No price available'
            location = house.find('h5', class_='listing-detailed-item-address').text.strip() if house.find('h5', class_='listing-detailed-item-address') else 'No location available'

            floor_divs = house.find_all('div', class_='sc-bc0f943e-14 hFQLKZ')
            floor = next((div.text.strip() for div in floor_divs if "icon-stairs" in div.find('span')['class']), 'No floor information available')

            m2 = floor_divs[0].text.strip() if floor_divs else 'No m² information available'
            bedrooms = house.find('span', class_='icon-bed').find_parent('div')
            bedrooms = bedrooms.text.strip() if bedrooms else 'No available'

            link_tag = house.find('a', href=True)
            house_link = f"https://home.ss.ge{link_tag['href']}" if link_tag else None
            photos = await fetch_house_images_selenium(house_link) if house_link else []

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
    query = update.callback_query

    await query.answer()

    if user_id not in user_states:
        user_states[user_id] = {'current_house_index': 0, 'houses': [], 'houses_fetched': False}

    if query.data == 'buy':
        if not user_states[user_id]['houses_fetched']:
            await query.edit_message_text("Fetching houses, please wait...")
            houses = await fetch_houses()
            user_states[user_id]['houses'] = houses
            user_states[user_id]['houses_fetched'] = True

            if houses:
                await show_house(query, user_id)
            else:
                await query.edit_message_text("No houses found.")
        else:
            await query.edit_message_text("Houses already fetched. Use 'Next' to view them.")

    elif query.data == 'next':
        current_index = user_states[user_id]['current_house_index']
        if current_index + 1 < len(user_states[user_id]['houses']):
            user_states[user_id]['current_house_index'] += 1
            await show_house(query, user_id)
        else:
            await query.edit_message_text("No more houses available.")

    elif query.data.startswith('interested_'):
        house_index = int(query.data.split('_')[1])
        await query.edit_message_text(f"You are interested in house {house_index + 1}. We'll follow up with more details.")

async def show_house(query, user_id):
    house = user_states[user_id]['houses'][user_states[user_id]['current_house_index']]
    
    title = house.get('title', 'No title available')
    price = house.get('price', 'No price available')
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
        f"🔗 Links: {links}\n"
    )

    keyboard = [
        [InlineKeyboardButton("Next", callback_data='next')],
        [InlineKeyboardButton("I'm Interested", callback_data=f'interested_{user_states[user_id]["current_house_index"]}')]
    ]

    if house.get('photos'):
        await query.message.reply_photo(
            photo=house['photos'][0], caption=text, reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


def main():
    application = Application.builder().token(bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()


if __name__ == '__main__':
    main()
