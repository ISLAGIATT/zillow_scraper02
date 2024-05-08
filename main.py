import json
import httpx
import sqlite3
from parsel import Selector
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import schedule
import time

BASE_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/96.0.4664.110 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "accept-language": "en-US;en;q=0.9",
    "accept-encoding": "gzip, deflate, br",
}

DB_PATH = "listings.db"

def create_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY,
            address TEXT UNIQUE,
            price TEXT,
            bedrooms INTEGER,
            bathrooms REAL,
            area INTEGER,
            img_src TEXT,
            detail_url TEXT
        )
    """)
    conn.commit()

def insert_or_ignore_listing(conn, listing):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO listings (address, price, bedrooms, bathrooms, area, img_src, detail_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (listing["address"], listing["price"], listing["bedrooms"], listing["bathrooms"],
          listing["area"], listing["imgSrc"], listing["detailUrl"]))
    conn.commit()
    return cursor.lastrowid  # Returns 0 if insertion was ignored

def scrape_big_island_zillow():
    url = "https://www.zillow.com/island-of-hawaii-hilo-hi/houses/"
    with httpx.Client(http2=True, headers=BASE_HEADERS, follow_redirects=True) as client:
        resp = client.get(url)
    sel = Selector(text=resp.text)
    data = json.loads(sel.css("script#__NEXT_DATA__::text").get())
    return data

def parse_and_insert_results(data, conn):
    list_results = data["props"]["pageProps"]["searchPageState"]["cat1"]["searchResults"]["listResults"]
    new_listings = []

    for result in list_results:
        listing = {
            "address": result["address"],
            "price": result["price"],
            "bedrooms": result["beds"],
            "bathrooms": result["baths"],
            "area": result.get("area", 0),
            "imgSrc": result["imgSrc"],
            "detailUrl": result["detailUrl"]
        }
        row_id = insert_or_ignore_listing(conn, listing)
        if row_id:  # New listing inserted
            new_listings.append(listing)
    print(new_listings)
    return new_listings

def send_email(new_listings, recipients):
    msg = MIMEMultipart()
    msg['From'] = "testcode65@outlook.com"
    msg['To'] = "mattrhansen@outlook.com, ".join(recipients)
    msg['Subject'] = "hawaii zillow bot news"

    body = "Here are the new listings found:\n\n"
    for listing in new_listings:
        body += (f"{listing['address']}: {listing['price']}, {listing['bedrooms']} beds, {listing['bathrooms']} baths, "
                 f"{listing['area']} sqft\n{listing['detailUrl']}\n\n")

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP('smtp-mail.outlook.com', 587) as server:
        server.starttls()
        server.login("testcode65@outlook.com", "buttsurprise100")
        server.sendmail(msg['From'], recipients, msg.as_string())

def scrape_and_notify():
    conn = sqlite3.connect(DB_PATH)
    create_table(conn)

    data = scrape_big_island_zillow()
    new_listings = parse_and_insert_results(data, conn)

    if new_listings:
        send_email(new_listings, ["mattrhansen@outlook.com"])

    conn.close()


# Schedule the scraping job to run twice daily
schedule.every().day.at("08:00").do(scrape_and_notify)
schedule.every().day.at("20:00").do(scrape_and_notify)

# Continuously run the scheduler
while True:
    schedule.run_pending()
    time.sleep(60)
