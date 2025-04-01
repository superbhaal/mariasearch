import os
import requests
import sqlite3
import smtplib
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

# Configuration depuis les variables Railway
EMAIL_SENDER = "simon.collot@gmail.com"
EMAIL_PASSWORD = "gwmn roqv kequ hhkd"
EMAIL_RECIPIENT = "mariapgarzonn@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# URL de recherche Pararius
URL = "https://www.pararius.nl/huurwoningen/amsterdam/stadsdeel-centrum/0-2500/straal-1/2-slaapkamers/gemeubileerd"

# Connexion à la base SQLite
conn = sqlite3.connect("listings.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS listings (
        id TEXT PRIMARY KEY,
        title TEXT,
        price TEXT,
        link TEXT
    )
""")
conn.commit()

def fetch_listings():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    listings = []

    for item in soup.select(".search-list__item"):
        title_tag = item.select_one(".listing-search-item__title")
        price_tag = item.select_one(".listing-search-item__price")
        link_tag = item.select_one(".listing-search-item__title a")

        if title_tag and price_tag and link_tag:
            title = title_tag.text.strip()
            price = price_tag.text.strip()
            link = "https://www.pararius.nl" + link_tag["href"].strip()
            listing_id = link.split("/")[-1]
            listings.append((listing_id, title, price, link))

    return listings

def check_new_listings(listings):
    new_listings = []
    for listing in listings:
        cursor.execute("SELECT id FROM listings WHERE id = ?", (listing[0],))
        if not cursor.fetchone():
            new_listings.append(listing)
            cursor.execute("INSERT INTO listings VALUES (?, ?, ?, ?)", listing)
    conn.commit()
    return new_listings

def send_email(new_listings):
    if not new_listings:
        message = "No new availabilities for my love <3 (2 bedrooms - maximum 2500€)\n"
    else:
        message = "New availabilities for my love <3 (2 bedrooms - maximum 2500€):\n\n"
        for listing in new_listings:
            message += f"{listing[1]} - {listing[2]}\n{listing[3]}\n\n"

    msg = MIMEText(message)
    msg["Subject"] = "Nouvelles annonces immobilières"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECIPIENT

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())

def main():
    listings = fetch_listings()
    new_listings = check_new_listings(listings)
    send_email(new_listings)

if __name__ == "__main__":
    main()

