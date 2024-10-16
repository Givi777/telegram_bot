from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup

app = Flask(__name__)

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
        
        driver.get(house_link)
        wait = WebDriverWait(driver, 10)

        # Wait for image gallery to load
        try:
            image_gallery = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'sc-1acce1b7-10')))
            image_gallery.click()
            time.sleep(2)
        except Exception as e:
            return {"error": f"Could not click on image gallery: {e}"}

        images = set()
        blocked_urls = {
            "https://static.ss.ge/20220722/6ce888d7-3a78-4f81-9008-96c2dcf94e8c.png",
            "https://static.ss.ge/20221222/b31e02ba-052e-4d2c-b8de-df005086be12.png"
        }

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        images_divs = soup.find_all('div', class_='lg-item')

        for div in images_divs:
            img_tag = div.find('img', class_='lg-object lg-image')
            if img_tag:
                image_src = img_tag.get('src') or img_tag.get('data-src')
                if image_src and image_src not in blocked_urls:
                    images.add(image_src)

        return list(images)

    except Exception as e:
        return {"error": f"Error fetching images: {e}"}

@app.route('/fetch-images', methods=['POST'])
def fetch_images():
    data = request.json
    house_link = data.get('house_link')

    if not house_link:
        return jsonify({"error": "No house link provided"}), 400

    images = fetch_house_images_selenium_sync(house_link)

    return jsonify({"images": images})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
