import sqlite3

class ZipCodeData:
    # Zip code to county mapping
    zip_to_county = {
        "96701": "Honolulu County",
        "96703": "Kauai County",
        "96704": "Hawaii County",
        "96705": "Kauai County",
        "96706": "Honolulu County",
        "96707": "Honolulu County",
        "96708": "Maui County",
        "96709": "Honolulu County",
        "96710": "Hawaii County",
        "96712": "Honolulu County",
        "96713": "Maui County",
        "96714": "Kauai County",
        "96715": "Kauai County",
        "96716": "Kauai County",
        "96717": "Honolulu County",
        "96718": "Hawaii County",
        "96719": "Hawaii County",
        "96720": "Hawaii County",
        "96721": "Hawaii County",
        "96722": "Kauai County",
        "96725": "Hawaii County",
        "96726": "Hawaii County",
        "96727": "Hawaii County",
        "96728": "Hawaii County",
        "96729": "Maui County",
        "96730": "Honolulu County",
        "96731": "Honolulu County",
        "96732": "Maui County",
        "96733": "Maui County",
        "96734": "Honolulu County",
        "96737": "Hawaii County",
        "96738": "Hawaii County",
        "96739": "Hawaii County",
        "96740": "Hawaii County",
        "96741": "Kauai County",
        "96742": "Kalawao County",
        "96743": "Hawaii County",
        "96744": "Honolulu County",
        "96745": "Hawaii County",
        "96746": "Kauai County",
        "96747": "Kauai County",
        "96748": "Maui County",
        "96749": "Hawaii County",
        "96750": "Hawaii County",
        "96751": "Kauai County",
        "96752": "Kauai County",
        "96753": "Maui County",
        "96754": "Kauai County",
        "96755": "Hawaii County",
        "96756": "Kauai County",
        "96757": "Maui County",
        "96759": "Honolulu County",
        "96760": "Hawaii County",
        "96761": "Maui County",
        "96762": "Honolulu County",
        "96763": "Maui County",
        "96764": "Hawaii County",
        "96765": "Kauai County",
        "96766": "Kauai County",
        "96767": "Maui County",
        "96768": "Maui County",
        "96769": "Kauai County",
        "96770": "Maui County",
        "96771": "Hawaii County",
        "96772": "Hawaii County",
        "96773": "Hawaii County",
        "96774": "Hawaii County",
        "96776": "Hawaii County",
        "96777": "Hawaii County",
        "96778": "Hawaii County",
        "96779": "Maui County",
        "96780": "Hawaii County",
        "96781": "Hawaii County",
        "96782": "Honolulu County",
        "96783": "Hawaii County",
        "96784": "Maui County",
        "96785": "Hawaii County",
        "96786": "Honolulu County",
        "96788": "Maui County",
        "96789": "Honolulu County",
        "96790": "Maui County",
        "96791": "Honolulu County",
        "96792": "Honolulu County",
        "96793": "Maui County",
        "96795": "Honolulu County",
        "96796": "Kauai County"
    }

    def add_county_column(self, conn):
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE listings ADD COLUMN county TEXT")
        conn.commit()

    def determine_county(self, zip_code):
        return self.zip_to_county.get(zip_code, "Unknown")

    def update_county_info(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT id, address FROM listings")
        rows = cursor.fetchall()

        for row in rows:
            listing_id, address = row
            zip_code = address.split()[-1]  # Assuming the zip code is the last part of the address
            county = self.determine_county(zip_code)
            cursor.execute("UPDATE listings SET county = ? WHERE id = ?", (county, listing_id))

        conn.commit()
