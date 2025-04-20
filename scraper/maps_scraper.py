import sqlite3
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent

# ====== CONFIGURATION ======
DATABASE = 'dealerships.db'  # Save into dealerships.db
TARGET_SEARCH = "car dealerships"  # Default search query

BRAND_NAMES = [
    'BMW', 'Toyota', 'Honda', 'Ford', 'Chevrolet', 'Nissan', 'Mercedes', 'Hyundai',
    'Audi', 'Volkswagen', 'Kia', 'Lexus', 'Subaru', 'Mazda', 'Jeep', 'Chrysler', 'Dodge'
]

# ====== MAIN SCRAPER CLASS ======

class GoogleMapsScraper:
    def __init__(self):
        self.driver = self.setup_driver()

    def setup_driver(self):
        """Set up the Selenium Chrome driver."""
        ua = UserAgent()
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run headless
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f'user-agent={ua.random}')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        return driver

    def search_dealerships(self, location_query):
        """Search Google Maps for dealerships near a location."""
        search_url = f"https://www.google.com/maps/search/{TARGET_SEARCH}+{location_query.replace(' ', '+')}"
        print(f"[INFO] Searching Google Maps: {search_url}")

        self.driver.get(search_url)
        time.sleep(5)

        self.scroll_down()

        dealerships = self.extract_dealerships()
        print(f"[INFO] Found {len(dealerships)} dealerships.")

        self.driver.quit()

        self.save_dealerships_to_db(dealerships, location_query)

    def scroll_down(self):
        """Scrolls the Google Maps sidebar to load more results."""
        scrollable_xpath = '//div[contains(@aria-label, "Results for")]'

        try:
            scrollable_div = self.driver.find_element(By.XPATH, scrollable_xpath)
        except Exception:
            print("[WARN] Scrollable div not found. Limited results.")
            return

        last_height = self.driver.execute_script("return arguments[0].scrollHeight", scrollable_div)

        while True:
            self.driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
            time.sleep(2)
            new_height = self.driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
            if new_height == last_height:
                break
            last_height = new_height

        print("[INFO] Finished scrolling.")

    def extract_dealerships(self):
        """Extract dealership info from Google Maps."""
        dealerships = []

        listings = self.driver.find_elements(By.XPATH, '//a[contains(@href, "/place/")]')

        for listing in listings:
            try:
                self.driver.execute_script("arguments[0].click();", listing)
                time.sleep(3)  # Wait for details to load

                name = self.safe_get_text('//h1[contains(@class, "fontHeadlineLarge")]')
                address = self.safe_get_text('//button[contains(@data-item-id, "address")]')
                phone = self.safe_get_text('//button[contains(@data-item-id, "phone")]')
                website = self.get_website_link()

                if name and any(brand.lower() in name.lower() for brand in BRAND_NAMES):
                    dealerships.append({
                        'name': name,
                        'address': address,
                        'phone': phone,
                        'website_url': website
                    })
            except Exception as e:
                print(f"[WARN] Skipping a listing due to error: {e}")
                continue

        return dealerships

    def safe_get_text(self, xpath):
        """Safely get text by XPath."""
        try:
            element = self.driver.find_element(By.XPATH, xpath)
            return element.text
        except:
            return None

    def get_website_link(self):
        """Get the website link if available."""
        try:
            website_button = self.driver.find_element(By.XPATH, '//a[contains(@data-item-id, "authority")]')
            return website_button.get_attribute('href')
        except:
            return None

    def save_dealerships_to_db(self, dealerships, zip_code):
        """Save dealership info into dealerships.db."""
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS dealerships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                address TEXT,
                phone TEXT,
                website_url TEXT UNIQUE,
                zip_code TEXT
            )
        ''')

        for dealer in dealerships:
            try:
                c.execute('''
                    INSERT OR IGNORE INTO dealerships (name, address, phone, website_url, zip_code)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    dealer['name'], dealer['address'], dealer['phone'], dealer['website_url'], zip_code
                ))
            except Exception as e:
                print(f"[DB] Error inserting dealer {dealer['name']}: {e}")

        conn.commit()
        conn.close()
        print(f"[INFO] Saved {len(dealerships)} dealerships into dealerships.db.")

# ====== IF RUN DIRECTLY ======

if __name__ == "__main__":
    location_input = input("Enter a ZIP code or city to scrape dealerships: ")
    scraper = GoogleMapsScraper()
    scraper.search_dealerships(location_input)
