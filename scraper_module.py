import sqlite3
import requests
from bs4 import BeautifulSoup
import re

DATABASE = 'dealerships.db'  # New database to manage dealerships

def get_dealership_urls(zip_code):
    """
    Query the dealerships database and return dealership website URLs for a given zip code.
    """
    urls = []
    try:
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute('SELECT website_url FROM dealerships WHERE zip_code = ?', (zip_code,))
        rows = cur.fetchall()
        urls = [row[0] for row in rows]
        conn.close()
    except Exception as e:
        print(f"[SCRAPER] Error fetching dealerships: {e}")

    return urls

def scrape_used_inventory(dealer_url):
    """
    Adaptive scraper for dealership websites.
    It detects possible car listings based on content, not static class names.
    """
    print(f"[SCRAPER] Scraping inventory from {dealer_url}...")
    cars = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36"
        }
        response = requests.get(dealer_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        potential_listings = soup.find_all(['div', 'li', 'section'], recursive=True)

        for item in potential_listings:
            text = item.get_text(separator=" ", strip=True)

            # Try to detect listings: must have year, make, model, price, mileage patterns
            year_match = re.search(r'\b(19|20)\d{2}\b', text)  # Match years like 2019, 2022
            price_match = re.search(r'\$\d{1,3}(,\d{3})*(\.\d{2})?', text)  # Match prices
            mileage_match = re.search(r'\d{1,3}(,\d{3})* miles', text, re.IGNORECASE)  # Match mileage

            if year_match and price_match and mileage_match:
                try:
                    year = int(year_match.group())
                    price = int(price_match.group().replace('$', '').replace(',', ''))
                    mileage = int(mileage_match.group().lower().replace(' miles', '').replace(',', ''))

                    split_text = text.split()
                    make = split_text[1] if len(split_text) > 1 else "Unknown"
                    model = split_text[2] if len(split_text) > 2 else "Unknown"

                    image_tag = item.find('img')
                    image_url = image_tag['src'] if image_tag and 'src' in image_tag.attrs else None

                    car = {
                        'make': make,
                        'model': model,
                        'year': year,
                        'mileage': mileage,
                        'price': price,
                        'location': dealer_url,  # fallback to dealership URL as location
                        'color': None,
                        'image_url': image_url
                    }
                    cars.append(car)
                except Exception as e:
                    print(f"[SCRAPER] Minor parsing error: {e}")
                    continue

    except Exception as e:
        print(f"[SCRAPER] Failed scraping {dealer_url}: {e}")

    print(f"[SCRAPER] Found {len(cars)} cars at {dealer_url}.")
    return cars

def save_cars_to_db(cars):
    """
    Save scraped cars into the cars database.
    """
    if not cars:
        print("[SCRAPER] No cars to save.")
        return

    try:
        conn = sqlite3.connect('users.db')  # Car data is saved into users.db
        cur = conn.cursor()

        for car in cars:
            cur.execute('''
                INSERT INTO cars (make, model, year, mileage, price, location, color, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                car['make'], car['model'], car['year'],
                car.get('mileage'), car.get('price'),
                car.get('location'), car.get('color'),
                car.get('image_url')
            ))

        conn.commit()
        conn.close()
        print(f"[SCRAPER] Saved {len(cars)} cars into database.")
    except Exception as e:
        print(f"[SCRAPER] Error saving cars to DB: {e}")
