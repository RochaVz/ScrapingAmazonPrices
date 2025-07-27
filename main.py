import requests
from bs4 import BeautifulSoup
import smtplib
import time
# You don't need 'os' or 'dotenv' for this version
# import os
# from dotenv import load_dotenv

# --- Your Credentials (as Python variables) ---
# NOTE: It's a security risk to keep these in the code. We'll fix that next.
# And let's fix the typos for consistency
SMTP_SERVER = "smtp.gmail.com"
MY_EMAIL = "lobo012487@gmail.com"
MY_PASSWORD = "cytbivqimirkifks" # This is your App Password
#practice
PRODUCT_URL= "https://www.amazon.com/Beats-Studio-AppleCare-Headphones-Years/dp/B0CMZQNDR4?ref=dlx_prime_dg_dcl_B0CMZQNDR4_dt_sl7_12_pi"
BUY_PRICE = 250.00
# ================ add Headers to the Request ======================
# full headers would look something like this
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Dnt": "1", # Do Not Track Request Header
    "Host": "www.amazon.com", # IMPORTANT: This should match the URL's domain
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

def check_price():
    """Fetches the product page, parses the price and title, and sends an email if the price is low."""
    if not MY_EMAIL or not MY_PASSWORD:
        print("ERROR: Enviroment variable MY_EMAIL or MY_PASSWORD not set.")
        print("Please set them before running this script.")
        return

    print("Fetching product page...")
    response = requests.get(PRODUCT_URL, headers=HEADERS)

    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to get page. Status code: {response.status_code}")
        print("Amazon might be blocking the request. Check the response content:")
        return

    soup = BeautifulSoup(response.content, "lxml") # lxml is generally faster than
    # 'html.parser'

    # find product title, usually in an element with id="productTitle"
    title_element = soup.find(id="productTitle")
    if title_element:
        title = title_element.get_text().strip()
    else:
        print("Could not find product title. Amazon may have blocked the request.")
        return

    # Find Product Price ---
    price_element = soup.find(class_="a-offscreen")
    if not price_element:
        print("Could not find the price. The page layout may have changed.")
        return

    price_str= price_element.get_text()

    #Clean up the price string and convert to float
    try:
        price_clean = price_str.replace("$", "").replace(",", "")
        price_as_float = float(price_clean)
        print(f"Product: {title}")
        print(f"Current Price: {price_as_float:./2f}")

    except ValueError:
        print(f"Could not convert price to float: {price_str}")
        return

    # -- Check if the price is low enough to trigger an alert ---
    if price_as_float < BUY_PRICE:
        print(f"Price is below ${BUY_PRICE}! Sending email alert...")
        send_email_alert(title, price_as_float)
    else:
        print(f"Price is not below the target of ${BUY_PRICE}! No alert sent.")

def send_email_alert(product_title, product_price):
    """Sends an email notification about the price drop."""
    try:
        with smtplib.SMTP(SMTP_SERVER, port=587) as connection:
            connection.starttls()
            connection.login(MY_EMAIL, MY_PASSWORD)

            subject = "Amazon price alert!!"
            body = f"{product_title}  is now on sale for ${product_price:.2f}!\n\nBuy it now: {PRODUCT_URL}"
            email_message = f"Subject: {subject}\n\n{body}".encode("utf-8")

            connection.sendmail(MY_EMAIL, MY_EMAIL, email_message)

        print("Email alert sent successfully.")
    except Exception as e:
        print(f"Failed to send email alert: {e}")

# --- Main execution block ---
if __name__ == "__main__":
    check_price()


