from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from dateutil import parser
import time

# 1. Set up headless Edge
options = Options()
options.use_chromium = True
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

service = EdgeService(EdgeChromiumDriverManager().install())
driver = webdriver.Edge(service=service, options=options)

# 2. Load the news page
url = "https://igamingontario.ca/en/news"
base_url = "https://igamingontario.ca"
driver.get(url)
time.sleep(5)  # Wait for JS-rendered content

# 3. Parse the page content
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# 4. Extract article blocks
items = soup.find_all("div", class_="views-row")

# 5. Generate RSS feed
fg = FeedGenerator()
fg.title("iGaming Ontario News")
fg.link(href=url)
fg.description("Latest updates from iGaming Ontario")

for item in items:
    text = item.get_text(separator=" ", strip=True)
    if not text or len(text) < 30:
        continue

    # Extract article URL
    link_tag = item.find("a", href=True)
    if link_tag:
        full_link = base_url + link_tag["href"]
    else:
        full_link = url

    # Try to parse date from beginning of text
    split = text.split(" ", 3)
    possible_date = " ".join(split[:3])
    try:
        pub_date = parser.parse(possible_date)
    except Exception:
        pub_date = datetime.now(timezone.utc)

    entry = fg.add_entry()
    entry.title(text)
    entry.link(href=full_link)
    entry.description(text)
    entry.pubDate(pub_date.astimezone(timezone.utc))

# 6. Save RSS to XML
fg.rss_file("igamingontario_feed_v2.xml")
print("✅ RSS feed created with article links and dates: igamingontario_feed_v2.xml")
