import sys
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from feedgen.feed import FeedGenerator
from datetime import datetime

# --- Setup Chrome headless ---
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=options)

# --- Load page with retry logic ---
url = "https://igamingontario.ca/en/news"
max_attempts = 2
success = False
driver.set_page_load_timeout(30)

for attempt in range(1, max_attempts + 1):
    try:
        print(f"🌐 Attempt {attempt}: Loading {url}")
        driver.get(url)

        # Wait for articles to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.view-content .views-row"))
        )
        success = True
        break
    except (TimeoutException, WebDriverException) as e:
        print(f"⚠️ Attempt {attempt} failed: {e}")
        time.sleep(5)

if not success:
    print(f"❌ Failed to load {url} after {max_attempts} attempts.")
    driver.quit()
    sys.exit(0)

# --- Scrape and build RSS feed ---
html = driver.page_source
driver.quit()
soup = BeautifulSoup(html, "html.parser")

fg = FeedGenerator()
fg.id(url)
fg.title("iGaming Ontario News")
fg.link(href=url, rel="alternate")
fg.description("Latest news from iGaming Ontario")
fg.language("en")

articles = soup.select("div.view-content .views-row")
print(f"🧪 Found {len(articles)} articles")

added = 0
for article in articles:
    link_tag = article.select_one("a")
    date_tag = article.select_one("span.date-display-single")
    title_tag = article.select_one("div.field-content")

    if link_tag and date_tag and title_tag:
        link = "https://igamingontario.ca" + link_tag.get("href")
        title = title_tag.get_text(strip=True)
        pub_date = datetime.strptime(date_tag.get_text(strip=True), "%B %d, %Y")

        entry = fg.add_entry()
        entry.id(link)
        entry.guid(link, permalink=True)  # ensure unique ID for readers
        entry.title(title)
        entry.link(href=link)
        entry.pubDate(pub_date)

        print(f"✅ Added article: {title}")
        added += 1
    else:
        print("⚠️ Skipped article: missing tag(s)")

print(f"📦 Total entries added to feed: {added}")

filename = sys.argv[1] if len(sys.argv) > 1 else "igamingontario_feed_v2.xml"
fg.rss_file(filename)
print(f"✅ RSS feed written to {filename}")
