import requests
from bs4 import BeautifulSoup

def fetch_houses():
    url = "https://home.ss.ge/ka/udzravi-qoneba/l/bina/iyideba?cityIdList=95&currencyId=1&advancedSearch=%7B%22individualEntityOnly%22%3Atrue%7D"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 403:
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    house_list = soup.find_all('div', class_='sc-bc0f943e-0')
    
    fetched_houses = []
    for house in house_list:
        price = house.find('span', class_='listing-detailed-item-price').text.strip() if house.find('span', class_='listing-detailed-item-price') else 'No price available'
        title = house.find('div', class_='listing-detailed-item-title').text.strip() if house.find('div', class_='listing-detailed-item-title') else 'No title available'
        location = house.find('div', class_='listing-detailed-item-address').text.strip() if house.find('div', class_='listing-detailed-item-address') else 'No location available'

        fetched_houses.append({
            'price': price,
            'title': title,
            'location': location
        })

    return fetched_houses

async def show_house(query, houses, index):
    house = houses[index]
    text = (
        f"🏠 **House {index + 1}:**\n"
        f"💵 Price: {house['price']}\n"
        f"📍 Location: {house['location']}\n"
        f"📄 Title: {house['title']}\n"
    )
    keyboard = [[InlineKeyboardButton("Next", callback_data='next')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=text, reply_markup=reply_markup)
