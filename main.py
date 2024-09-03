import json
import httpx
import os
import sqlite3
from parsel import Selector
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time
import logging

from scrape_urls import Urls
from zip_code_data import ZipCodeData

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables for email configuration
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
RECIPIENT_1 = os.getenv('RECIPIENT_1')
RECIPIENT_2 = os.getenv('RECIPIENT_2')

# Ensure environment variables are set
if not EMAIL_SENDER or not EMAIL_PASSWORD or not RECIPIENT_1 or not RECIPIENT_2:
    raise ValueError("Please set the environment variables EMAIL_SENDER, EMAIL_PASSWORD, RECIPIENT_1, and RECIPIENT_2")

# Base headers for HTTP requests
BASE_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/96.0.4664.110 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "accept-language": "en-US;en;q=0.9",
    "accept-encoding": "gzip, deflate, br",
}

# Database path
DB_PATH = "listings.db"

# Function to create the listings table
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
            variable_data TEXT,
            county TEXT,
            price_last_checked TEXT
        )
    """)
    conn.commit()

# Function to insert a new listing or ignore if it already exists
def insert_or_ignore_listing(conn, listing):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO listings (address, price, bedrooms, bathrooms, area, img_src, detail_url, variable_data, county, price_last_checked)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (listing["address"], listing["price"], listing["bedrooms"], listing["bathrooms"],
          listing["area"], listing["imgSrc"], listing["detailUrl"], listing["variableData"], listing["county"], listing["price"]))
    conn.commit()
    return cursor.lastrowid  # Returns 0 if insertion was ignored

# Function to scrape listings from Big Island Zillow
def scrape_big_island_zillow():
    url = Urls.big_island_scrape
    with httpx.Client(http2=True, headers=BASE_HEADERS, follow_redirects=True) as client:
        resp = client.get(url)
    sel = Selector(text=resp.text)
    big_island_data = json.loads(sel.css("script#__NEXT_DATA__::text").get())
    return big_island_data

# Function to scrape listings from Maui Zillow
def scrape_maui_zillow():
    url = Urls.maui_scrape
    with httpx.Client(http2=True, headers=BASE_HEADERS, follow_redirects=True) as client:
        resp = client.get(url)
    sel = Selector(text=resp.text)
    maui_data = json.loads(sel.css("script#__NEXT_DATA__::text").get())
    return maui_data

# Function to scrape listings from Kauai Zillow
def scrape_kauai_zillow():
    url = Urls.kauai_scrape
    with httpx.Client(http2=True, headers=BASE_HEADERS, follow_redirects=True) as client:
        resp = client.get(url)
    sel = Selector(text=resp.text)
    kauai_data = json.loads(sel.css("script#__NEXT_DATA__::text").get())
    return kauai_data

# Function to parse and insert new listings into the database
def parse_and_insert_results(data, conn, zipcode_data):
    list_results = data["props"]["pageProps"]["searchPageState"]["cat1"]["searchResults"]["listResults"]
    price_changed_listings = []
    new_listings = []

    cursor = conn.cursor()

    for result in list_results:
        variable_data_text = result.get('variableData', {}).get('text', 'Not available')
        zip_code = result["address"].split()[-1]

        listing = {
            "address": result["address"],
            "price": result["price"],
            "bedrooms": result.get("beds", 0),
            "bathrooms": result.get("baths", 0.0),
            "area": result.get("area", 0),
            "imgSrc": result["imgSrc"],
            "detailUrl": result["detailUrl"],
            "county": zipcode_data.determine_county(zip_code),
            "variableData": variable_data_text
        }

        cursor.execute("SELECT price FROM listings WHERE address = ?", (listing["address"],))
        row = cursor.fetchone()
        if row:
            old_price = row[0]
            if old_price != listing["price"]:
                logging.info(f"Price change detected for {listing['address']}: {old_price} -> {listing['price']}")
                listing["old_price"] = old_price  # Store the old price
                price_changed_listings.append(listing)
                cursor.execute("""
                    UPDATE listings
                    SET price = ?, bedrooms = ?, bathrooms = ?, area = ?, img_src = ?, detail_url = ?, variable_data = ?, county = ?, price_last_checked = ?
                    WHERE address = ?
                """, (listing["price"], listing["bedrooms"], listing["bathrooms"], listing["area"], listing["imgSrc"],
                      listing["detailUrl"], listing["variableData"], listing["county"], listing["price"], listing["address"]))
        else:
            new_listings.append(listing)
            cursor.execute("""
                INSERT INTO listings (address, price, bedrooms, bathrooms, area, img_src, detail_url, variable_data, county, price_last_checked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (listing["address"], listing["price"], listing["bedrooms"], listing["bathrooms"], listing["area"],
                  listing["imgSrc"], listing["detailUrl"], listing["variableData"], listing["county"], listing["price"]))
            logging.info(f"New listing inserted: {listing['address']}")

    conn.commit()
    return new_listings, price_changed_listings

# Function to send email notifications
def send_email(new_listings, price_changed_listings, recipients, max_retries=3):
    if not new_listings and not price_changed_listings:
        logging.info("No new listings or price changes detected, no email sent.")
        return

    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = "zillow bot news v2"

    body = "<html><body>"

    if new_listings:
        body += "<h1>new listings:</h1>"
        body += "<ul>"
        for listing in new_listings:
            body += "<li>"
            body += (f"<p><b>Address:</b> {listing['address']}<br>"
                     f"<b>Price:</b> {listing['price']}<br>"
                     f"<b>Bedrooms:</b> {listing['bedrooms']}<br>"
                     f"<b>Bathrooms:</b> {listing['bathrooms']}<br>"
                     f"<b>Area:</b> {listing['area']} sqft<br>"
                     f"<b>Days on Zillow:</b> {listing['variableData']}<br>"
                     f"<b>County:</b> {listing['county']}<br>"
                     f"<a href='{listing['detailUrl']}'>More details</a></p>")
            body += f"<img src='{listing['imgSrc']}' alt='Listing Image' width='300'><br><br>"
            body += "</li>"
        body += "</ul>"

    if price_changed_listings:
        body += "<h1>price changes:</h1>"
        body += "<ul>"
        for listing in price_changed_listings:
            body += "<li>"
            body += (f"<p><b>Address:</b> {listing['address']}<br>"
                     f"<b>Old Price:</b> {listing['old_price']}<br>"
                     f"<b>New Price:</b> {listing['price']}<br>"
                     f"<b>Bedrooms:</b> {listing['bedrooms']}<br>"
                     f"<b>Bathrooms:</b> {listing['bathrooms']}<br>"
                     f"<b>Area:</b> {listing['area']} sqft<br>"
                     f"<b>Days on Zillow:</b> {listing['variableData']}<br>"
                     f"<b>County:</b> {listing['county']}<br>"
                     f"<a href='{listing['detailUrl']}'>More details</a></p>")
            body += f"<img src='{listing['imgSrc']}' alt='Listing Image' width='300'><br><br>"
            body += "</li>"
        body += "</ul>"

    body += "</body></html>"

    msg.attach(MIMEText(body, 'html'))

    attempt = 0
    while attempt < max_retries:
        try:
            with smtplib.SMTP('smtp.office365.com', 587, timeout=60) as server:
                server.set_debuglevel(1)  # Enable debug output
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.sendmail(msg['From'], recipients, msg.as_string())
                logging.info(f"Email sent to {recipients}")
                break  # Break the loop if email is sent successfully
        except smtplib.SMTPException as e:
            logging.error(f"Failed to send email: {e}")
            attempt += 1
            if attempt < max_retries:
                logging.info(f"Retrying... ({attempt}/{max_retries})")
                time.sleep(5)  # Wait before retrying
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            break

# Function to scrape and notify recipients
def scrape_and_notify():
    conn = sqlite3.connect(DB_PATH)
    create_table(conn)

    zipcode_data = ZipCodeData()  # Instantiate ZipCodeData

    # List of scraping functions
    scraping_functions = [scrape_kauai_zillow, scrape_big_island_zillow]
    all_new_listings = []
    all_price_changed_listings = []

    for scrape_function in scraping_functions:
        data = scrape_function()
        new_listings, price_changed_listings = parse_and_insert_results(data, conn, zipcode_data)
        all_new_listings.extend(new_listings)
        all_price_changed_listings.extend(price_changed_listings)

    if all_new_listings or all_price_changed_listings:  # Only send email if there are new listings or price changes
        send_email(all_new_listings, all_price_changed_listings, [RECIPIENT_1, RECIPIENT_2])
        #send_email(all_new_listings, all_price_changed_listings, [RECIPIENT_1]) just me for debug

    conn.close()

# Initial scrape and notify for debug
#scrape_and_notify()

# Schedule the scraping job to run twice daily
schedule.every().day.at("08:00").do(scrape_and_notify)
schedule.every().day.at("20:00").do(scrape_and_notify)

# Continuously run the scheduler
while True:
    schedule.run_pending()
    time.sleep(60)
