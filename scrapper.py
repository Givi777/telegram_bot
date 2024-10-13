import requests
from bs4 import BeautifulSoup

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

        print(f"Fetched {len(fetched_houses)} houses.")
        return fetched_houses

    except Exception as e:
        print(f"Error fetching houses: {e}")
        return []
