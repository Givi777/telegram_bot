import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient

load_dotenv()

# MongoDB setup
mongo_client = MongoClient(os.getenv('MONGO_URI'))
db = mongo_client['house_listings']
collection = db['house_images']

driver = None

def fetch_house_images_selenium_sync(house_link):
    global driver
    try:
        if driver is None:  # Initialize driver only once
            chrome_options = Options()
            chrome_options.add_argument("--window-size=1280x720")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Open a new tab for the house link
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get(house_link)

        wait = WebDriverWait(driver, 10)

        try:
            image_gallery = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'sc-1acce1b7-10')))
            image_gallery.click()
            time.sleep(2)
        except Exception as e:
            pass

        images = set()
        prev_image_count = 0
        max_retries = 7
        retries = 0

        blocked_urls = {
            "https://static.ss.ge/20220722/6ce888d7-3a78-4f81-9008-96c2dcf94e8c.png",
            "https://static.ss.ge/20221222/b31e02ba-052e-4d2c-b8de-df005086be12.png",
            "https://static.ss.ge/20240405/b2a5cf2d-b24b-4080-bb83-1955885e2e75.jpeg"
        }

        while retries < max_retries:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            images_divs = soup.find_all('div', class_='lg-item')

            new_images = set()
            for div in images_divs:
                img_tag = div.find('img', class_='lg-object lg-image')
                if img_tag:
                    image_src = img_tag.get('src') or img_tag.get('data-src')
                    if image_src and image_src not in blocked_urls:
                        new_images.add(image_src)
            
            images.update(new_images)
            
            current_image_count = len(images_divs)

            if current_image_count == prev_image_count:
                retries += 1
            else:
                retries = 0

            prev_image_count = current_image_count

            try:
                next_button = driver.find_element(By.CLASS_NAME, 'lg-next')
                if next_button:
                    next_button.click()
                    time.sleep(1)
                else:
                    break
            except Exception as e:
                break

        # Close the tab once done
        driver.close()
        driver.switch_to.window(driver.window_handles[0])  # Switch back to the main tab

        return list(images)

    except Exception as e:
        return []

def close_driver():
    global driver
    if driver:
        driver.quit()
        driver = None

def fetch_houses(offset=0, limit=1):
    url = f"https://home.ss.ge/en/real-estate/l/Flat/For-Sale?cityIdList=95&currencyId=1"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 403:
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        house_list = soup.find_all('div', class_='sc-8fa2c16a-0')[offset:offset + limit]

        fetched_houses = []
        for house in house_list:
            title = house.find('h2', class_='listing-detailed-item-title').text.strip() if house.find('h2', class_='listing-detailed-item-title') else 'No title available'
            price = house.find('span', class_='listing-detailed-item-price').text.strip() if house.find('span', class_='listing-detailed-item-price') else 'No price available'
            location = house.find('h5', class_='listing-detailed-item-address').text.strip() if house.find('h5', class_='listing-detailed-item-address') else 'No location available'
            floor_divs = house.find_all('div', class_='sc-bc0f943e-14 hFQLKZ')
            floor = next((div.text.strip() for div in floor_divs if "icon-stairs" in div.find('span')['class']), 'No floor information available')
            m2 = floor_divs[0].text.strip() if floor_divs else 'No m² information available'
            bedrooms = house.find('span', class_='icon-bed').find_parent('div')
            bedrooms = bedrooms.text.strip() if bedrooms else 'No bedrooms available'

            link_tag = house.find('a', href=True)
            house_link = f"https://home.ss.ge{link_tag['href']}" if link_tag else None

            photos = fetch_house_images_selenium_sync(house_link) if house_link else []

            house_data = {
                'title': title,
                'photos': photos,
                'price': price,
                'location': location,
                'floor': floor,
                'm2': m2,
                'bedrooms': bedrooms,
            }

            # Save house data to MongoDB
            collection.insert_one(house_data)

            fetched_houses.append(house_data)

        return fetched_houses
    except Exception as e:
        print(f"Error fetching houses: {e}")
        return []

if __name__ == '__main__':
    # Fetch and store house data
    fetch_houses(limit=5)

    # Close the Selenium driver when done
    close_driver()
