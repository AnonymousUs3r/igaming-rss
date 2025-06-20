import sys
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone

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
    link_tag = article.select_one("h3.views-field-title a")
    date_tag = article.select_one("time.datetime")

    if link_tag and date_tag:
        link = "https://igamingontario.ca" + link_tag.get("href")
        title = link_tag.get_text(strip=True)
        pub_date = datetime.strptime(date_tag["datetime"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

        entry = fg.add_entry()
        entry.id(link)
        entry.guid(link, permalink=True)
        entry.title(title)
        entry.link(href=link)
        entry.pubDate(pub_date)

        print(f"✅ Added article: {title}")
        added += 1
    else:
        print("⚠️ Skipped article: missing link or date")
        print(article.prettify()[:300])

print(f"📦 Total entries added to feed: {added}")

filename = sys.argv[1] if len(sys.argv) > 1 else "igamingontario_feed_v3.xml"
fg.rss_file(filename)
print(f"✅ RSS feed written to {filename}")
