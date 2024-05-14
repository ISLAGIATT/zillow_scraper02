import json
import httpx
import os
import sqlite3
from parsel import Selector
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import schedule
import time

EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
RECIPIENT_1 = os.getenv('RECIPIENT_1')
RECIPIENT_2 = os.getenv('RECIPIENT_2')



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
            detail_url TEXT,
            variable_data TEXT  
        )
    """)
    conn.commit()

def insert_or_ignore_listing(conn, listing):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO listings (address, price, bedrooms, bathrooms, area, img_src, detail_url, variable_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (listing["address"], listing["price"], listing["bedrooms"], listing["bathrooms"],
          listing["area"], listing["imgSrc"], listing["detailUrl"], listing["variableData"]))
    conn.commit()
    return cursor.lastrowid  # Returns 0 if insertion was ignored


def scrape_big_island_zillow():
    url = "https://www.zillow.com/island-of-hawaii-hilo-hi/houses/"
    with httpx.Client(http2=True, headers=BASE_HEADERS, follow_redirects=True) as client:
        resp = client.get(url)
    sel = Selector(text=resp.text)
    big_island_data = json.loads(sel.css("script#__NEXT_DATA__::text").get())
    return big_island_data

def scrape_maui_zillow():
    url = ("https://www.zillow.com/maui-county-hi/?searchQueryState=%7B%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A"
           "%7B%22north%22%3A21.38728402791739%2C%22south%22%3A20.345325891144547%2C%22east%22%3A-155.84329175585935"
           "%2C%22west%22%3A-157.4500422441406%7D%2C%22usersSearchTerm%22%3A%22Maui%2C%20HI%22%2C%22filterState%22%3A"
           "%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C"
           "%22mf%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22ah%22%3A%7B%22value%22"
           "%3Atrue%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%2C%22price%22"
           "%3A%7B%22max%22%3A300000%7D%2C%22mp%22%3A%7B%22max%22%3A1558%7D%7D%2C%22isListVisible%22%3Atrue%2C"
           "%22regionSelection%22%3A%5B%7B%22regionId%22%3A250%2C%22regionType%22%3A4%7D%5D%2C%22pagination%22%3A%7B"
           "%7D%7D")
    with httpx.Client(http2=True, headers=BASE_HEADERS, follow_redirects=True) as client:
        resp = client.get(url)
    sel = Selector(text=resp.text)
    maui_data = json.loads(sel.css("script#__NEXT_DATA__::text").get())
    return maui_data

def scrape_kauai_zillow():
    url = ("https://www.zillow.com/kauai-county-hi/?searchQueryState=%7B%22isMapVisible%22%3Atrue%2C%22mapBounds%22"
           "%3A%7B%22north%22%3A22.46205510651506%2C%22south%22%3A21.427758392993628%2C%22east%22%3A-159"
           ".1179757558594%2C%22west%22%3A-160.72472624414064%7D%2C%22usersSearchTerm%22%3A%22Maui%2C%20HI%22%2C"
           "%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C%22tow%22%3A%7B%22value"
           "%22%3Afalse%7D%2C%22mf%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22ah%22"
           "%3A%7B%22value%22%3Atrue%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse"
           "%7D%2C%22price%22%3A%7B%22max%22%3A300000%7D%2C%22mp%22%3A%7B%22max%22%3A1558%7D%7D%2C%22isListVisible%22"
           "%3Atrue%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A578%2C%22regionType%22%3A4%7D%5D%2C%22pagination"
           "%22%3A%7B%7D%7D")
    with httpx.Client(http2=True, headers=BASE_HEADERS, follow_redirects=True) as client:
        resp = client.get(url)
    sel = Selector(text=resp.text)
    kauai_data = json.loads(sel.css("script#__NEXT_DATA__::text").get())
    return kauai_data

def parse_and_insert_results(data, conn):
    list_results = data["props"]["pageProps"]["searchPageState"]["cat1"]["searchResults"]["listResults"]
    new_listings = []

    for result in list_results:
        # Adding 'variableData' field extraction
        variable_data_text = result.get('variableData', {}).get('text', 'Not available')

        listing = {
            "address": result["address"],
            "price": result["price"],
            "bedrooms": result.get("beds", 0),  # Use get for optional fields
            "bathrooms": result.get("baths", 0.0),
            "area": result.get("area", 0),
            "imgSrc": result["imgSrc"],
            "detailUrl": result["detailUrl"],
            "variableData": variable_data_text  # Adding this new field
        }

        row_id = insert_or_ignore_listing(conn, listing)
        if row_id:  # New listing inserted
            new_listings.append(listing)
    print(new_listings)
    return new_listings


def send_email(new_listings, recipients):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = "hawaii zillow bot news"

    body = "<html><body>"
    body += "<h1>hey man i got some stuff</h1>"
    body += "<ul>"

    for listing in new_listings:
        body += "<li>"
        body += (f"<p><b>Address:</b> {listing['address']}<br>"
                 f"<b>Price:</b> {listing['price']}<br>"
                 f"<b>Bedrooms:</b> {listing['bedrooms']}<br>"
                 f"<b>Bathrooms:</b> {listing['bathrooms']}<br>"
                 f"<b>Area:</b> {listing['area']} sqft<br>"
                 f"<b>Days on Zillow:</b> {listing['variableData']}<br>"
                 f"<a href='{listing['detailUrl']}'>More details</a></p>")
        body += f"<img src='{listing['imgSrc']}' alt='Listing Image' width='300'><br><br>"
        body += "</li>"

    body += "</ul>"
    body += "</body></html>"

    msg.attach(MIMEText(body, 'html'))

    with smtplib.SMTP('smtp-mail.outlook.com', 587) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(msg['From'], recipients, msg.as_string())

def scrape_and_notify():
    conn = sqlite3.connect(DB_PATH)
    create_table(conn)

    # List of scraping functions
    scraping_functions = [scrape_maui_zillow, scrape_kauai_zillow]
    all_new_listings = []

    for scrape_function in scraping_functions:
        data = scrape_function()
        new_listings = parse_and_insert_results(data, conn)
        all_new_listings.extend(new_listings)

    if all_new_listings:
        send_email(all_new_listings, [RECIPIENT_1])

    conn.close()

scrape_and_notify()
# # Schedule the scraping job to run twice daily
# schedule.every().day.at("09:45").do(scrape_and_notify)
# schedule.every().day.at("20:00").do(scrape_and_notify)
#
# # Continuously run the scheduler
# while True:
#     schedule.run_pending()
#     time.sleep(60)
