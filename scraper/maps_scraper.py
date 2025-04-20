import sqlite3
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent

# ====== CONFIGURATION ======
DATABASE = 'dealerships.db'
TARGET_SEARCH = "car dealerships"
BRAND_NAMES = [
    'BMW', 'Toyota', 'Honda', 'Ford', 'Chevrolet', 'Nissan', 'Mercedes', 'Hyundai',
    'Audi', 'Volkswagen', 'Kia', 'Lexus', 'Subaru', 'Mazda', 'Jeep', 'Chrysler', 'Dodge'
]

class GoogleMapsScraper:
    def __init__(self):
        self.driver = self.setup_driver()

    def setup_driver(self):
        """Set up headless Chrome driver."""
        ua = UserAgent()
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # New headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f'user-agent={ua.random}')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def search_dealerships(self, location_query):
        """Search Google Maps for dealerships near a location."""
        search_url = f"https://www.google.com/maps/search/{TARGET_SEARCH}+{location_query.replace(' ', '+')}"
        print(f"[INFO] Searching: {search_url}")
        self.driver.get(search_url)
        time.sleep(5)

        self.scroll_page()

        dealerships = self.scrape_dealerships()
        print(f"[INFO] Found {len(dealerships)} dealerships.")
        self.driver.quit()

        self.save_dealerships_to_db(dealerships)

    def scroll_page(self):
        """Scrolls the page down to load more results."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        for _ in range(15):
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        print("[INFO] Finished scrolling.")

    def get_shadow_root(self, element):
        """Expand shadow root."""
        return self.driver.execute_script('return arguments[0].shadowRoot', element)

    def scrape_dealerships(self):
        """Scrape dealership info through Shadow DOM."""
        dealerships = []

        try:
            listings = self.driver.find_elements(By.XPATH, '//a[contains(@href, "/place/")]')
            if not listings:
                print("[WARN] No listings found!")
                return dealerships

            print(f"[INFO] Found {len(listings)} raw place links.")

            for idx, listing in enumerate(listings):
                try:
                    print(f"[INFO] Visiting dealership {idx + 1}")

                    self.driver.execute_script("arguments[0].click();", listing)
                    time.sleep(4)

                    name = self.safe_get_text('//h1[contains(@class, "fontHeadlineLarge")]')
                    address = self.safe_get_text('//button[contains(@data-item-id, "address")]')
                    phone = self.safe_get_text('//button[contains(@data-item-id, "phone")]')
                    website = self.safe_get_website()

                    if name and any(brand.lower() in name.lower() for brand in BRAND_NAMES):
                        dealerships.append({
                            'name': name,
                            'address': address,
                            'phone': phone,
                            'website': website
                        })
                        print(f"[SAVE] {name} added.")
                    else:
                        print(f"[SKIP] {name} does not match brand filter.")

                    self.driver.back()
                    time.sleep(3)

                except Exception as e:
                    print(f"[WARN] Failed processing a dealership: {e}")
                    try:
                        self.driver.back()
                        time.sleep(3)
                    except:
                        pass
                    continue

        except Exception as e:
            print(f"[ERROR] Scraping failed: {e}")

        return dealerships

    def safe_get_text(self, xpath):
        """Safely get element text."""
        try:
            element = self.driver.find_element(By.XPATH, xpath)
            return element.text
        except:
            return None

    def safe_get_website(self):
        """Safely get website link."""
        try:
            website_btn = self.driver.find_element(By.XPATH, '//a[contains(@data-item-id, "authority")]')
            return website_btn.get_attribute('href')
        except:
            return None

    def save_dealerships_to_db(self, dealerships):
        """Save dealership data into the SQLite database."""
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS dealerships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                address TEXT,
                phone TEXT,
                website TEXT
            )
        ''')

        for dealer in dealerships:
            c.execute('''
                INSERT INTO dealerships (name, address, phone, website)
                VALUES (?, ?, ?, ?)
            ''', (dealer['name'], dealer['address'], dealer['phone'], dealer['website']))

        conn.commit()
        conn.close()
        print(f"[DB] Saved {len(dealerships)} dealerships into dealerships.db.")

# ====== IF RUN DIRECTLY ======
if __name__ == "__main__":
    location = input("Enter ZIP code or city: ")
    scraper = GoogleMapsScraper()
    scraper.search_dealerships(location)
