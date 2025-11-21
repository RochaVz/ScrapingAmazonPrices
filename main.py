import customtkinter as ctk
import threading
import time
import os
import requests
from bs4 import BeautifulSoup
import smtplib
from dotenv import load_dotenv
from tkinter import filedialog
import webbrowser  # <-- New Feature: Open URL in browser

# ====================================================================
# 1. SETUP & CONFIGURATION (Global Constants)
# ====================================================================

# Load Environment Variables for sender credentials
load_dotenv()
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
MY_EMAIL = os.getenv("MY_EMAIL")  # Sender Email (from .env)
MY_PASSWORD = os.getenv("MY_PASSWORD")  # Sender App Password (from .env)

AMAZON_BASE_URL = "https://www.amazon.com.mx"
AMAZON_SEARCH_URL = f"{AMAZON_BASE_URL}/s?k="

# Headers to make the request look like a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Host": "www.amazon.com.mx",
    "Connection": "keep-alive",
}

# CustomTkinter Setup
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


# ====================================================================
# 2. CORE TRACKING FUNCTIONS
# ====================================================================

def get_product_url(search_query):
    """Performs Amazon search and returns the URL of the first product result."""
    search_url = AMAZON_SEARCH_URL + search_query.replace(" ", "+")

    try:
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return None

    soup = BeautifulSoup(response.content, "lxml")
    first_result = soup.find("div", {"data-component-type": "s-search-result"})

    if first_result:
        link_element = first_result.find("a", class_="a-link-normal")
        if link_element and 'href' in link_element.attrs:
            relative_url = link_element['href']
            full_url = AMAZON_BASE_URL + relative_url
            return full_url

    return None


def check_price(product_url, target_price, recipient_email):
    """Fetches the price, compares it, and sends an alert if the price is low."""

    try:
        response = requests.get(product_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return "Failed to get product page."

    soup = BeautifulSoup(response.content, "lxml")

    # 1. Find Product Title
    title_element = soup.find(id="productTitle")
    title = title_element.get_text().strip() if title_element else "Unknown Product Title"

    # 2. Find Product Price
    price_element = soup.find(class_="a-offscreen")

    if not price_element:
        return f"Could not find price for '{title}'. Item unavailable or page changed."

    price_str = price_element.get_text()

    # 3. Clean up the price string and convert to float
    try:
        price_clean = price_str.replace("$", "").replace(",", "")
        price_as_float = float(price_clean)
    except ValueError:
        return f"Could not convert price to float: '{price_str}'."

    # 4. Check if the price is low enough to trigger an alert
    if price_as_float <= target_price:
        send_email_alert(title, price_as_float, target_price, product_url, recipient_email)
        return f"ALERT! {title} is ${price_as_float:.2f} (Target: ${target_price:.2f}). Email sent."
    else:
        return f"Price for {title} is ${price_as_float:.2f}. No alert sent."


def send_email_alert(product_title, current_price, target_price, product_url, recipient_email):
    """Sends an email notification about the price drop."""
    # Ensure sender credentials are set
    if not MY_EMAIL or not MY_PASSWORD:
        return "Error: Sender MY_EMAIL or MY_PASSWORD not set in .env."

    try:
        with smtplib.SMTP(SMTP_SERVER, port=587, timeout=60) as connection:
            connection.starttls()
            connection.login(MY_EMAIL, MY_PASSWORD)

            subject = f"🔥 PRICE ALERT! {product_title[:50]}..."

            body = (
                f"The product is now on sale for ${current_price:.2f} MXN!\n\n"
                f"Your target price was ${target_price:.2f} MXN.\n\n"
                f"Product: {product_title}\n"
                f"Buy it now: {product_url}"
            )

            email_message = f"Subject: {subject}\nTo: {recipient_email}\n\n{body}".encode("utf-8")

            connection.sendmail(MY_EMAIL, recipient_email, email_message)

        return "Email alert sent successfully."
    except Exception as e:
        return f"Failed to send email alert: {e}"


# ====================================================================
# 3. GUI APPLICATION CLASS
# ====================================================================

class PriceTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Amazon Price Tracker")
        self.geometry("850x550")  # Wider window for new buttons

        # --- Variables to store user input ---
        self.product_name = ctk.StringVar()
        self.target_price = ctk.StringVar()
        self.recipient_email = ctk.StringVar(value=MY_EMAIL if MY_EMAIL else "")

        self.tracking_url = None
        self.is_tracking = False

        # --- UI Elements Setup ---

        input_frame = ctk.CTkFrame(self)
        input_frame.pack(pady=10, padx=20, fill="x")

        # Product Name
        ctk.CTkLabel(input_frame, text="Product Name:").pack(pady=(10, 0), padx=10, anchor="w")
        ctk.CTkEntry(input_frame, textvariable=self.product_name).pack(pady=(0, 5), padx=10, fill="x")

        # Target Price
        ctk.CTkLabel(input_frame, text="Target Price (MXN):").pack(pady=(5, 0), padx=10, anchor="w")
        ctk.CTkEntry(input_frame, textvariable=self.target_price).pack(pady=(0, 5), padx=10, fill="x")

        # Recipient Email
        ctk.CTkLabel(input_frame, text="Recipient Email:").pack(pady=(5, 0), padx=10, anchor="w")
        ctk.CTkEntry(input_frame, textvariable=self.recipient_email).pack(pady=(0, 10), padx=10, fill="x")

        # 2. Control Buttons
        control_frame = ctk.CTkFrame(self, fg_color="transparent")
        control_frame.pack(pady=5, padx=20)

        self.start_button = ctk.CTkButton(control_frame, text="Start Tracking", command=self.start_tracking_thread)
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ctk.CTkButton(control_frame, text="Stop Tracking", command=self.stop_tracking,
                                         state="disabled")
        self.stop_button.pack(side="left", padx=5)

        self.send_now_button = ctk.CTkButton(control_frame, text="Check & Send Now", command=self.send_now_thread,
                                             state="disabled")
        self.send_now_button.pack(side="left", padx=5)

        self.open_url_button = ctk.CTkButton(control_frame, text="Open in Browser", command=self.open_product_url,
                                             state="disabled")
        self.open_url_button.pack(side="left", padx=5)

        self.download_html_button = ctk.CTkButton(control_frame, text="Download HTML",
                                                  command=self.download_product_html, state="disabled")
        self.download_html_button.pack(side="left", padx=5)

        self.download_button = ctk.CTkButton(control_frame, text="Download Log", command=self.download_log)
        self.download_button.pack(side="left", padx=5)

        # 3. Status Log
        ctk.CTkLabel(self, text="Status/Log:").pack(pady=(10, 0))
        self.log_text = ctk.CTkTextbox(self, width=800, height=180)
        self.log_text.pack(pady=10, padx=20)

    def log_message(self, message):
        """Updates the log Textbox with a new message, handling thread safety."""
        self.after(0, lambda: self._update_log_gui(message))

    def _update_log_gui(self, message):
        """Internal GUI update for the log."""
        self.log_text.insert(ctk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(ctk.END)

    def download_log(self):
        """Opens a file dialog to save the content of the log_text widget."""
        log_content = self.log_text.get("1.0", ctk.END)

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"Amazon_Tracker_Log_{time.strftime('%Y%m%d_%H%M%S')}.txt",
            title="Save Tracker Log"
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(log_content)
                self.log_message(f"Log saved successfully to: {file_path}")
            except Exception as e:
                self.log_message(f"Error saving log: {e}")

    def open_product_url(self):
        """Opens the tracked product URL in the default web browser."""
        if self.tracking_url:
            try:
                webbrowser.open_new_tab(self.tracking_url)
                self.log_message("Opened product URL in browser.")
            except Exception as e:
                self.log_message(f"Error opening browser: {e}")
        else:
            self.log_message("Error: No product URL is currently being tracked.")

    def download_product_html(self):
        """Fetches the HTML of the current product page and saves it to a file."""
        if not self.tracking_url:
            self.log_message("Error: No product URL is currently being tracked to download.")
            return

        self.log_message("Starting HTML download thread...")
        threading.Thread(target=self._run_html_download_thread, daemon=True).start()

    def _run_html_download_thread(self):
        """Threaded function to handle fetching and saving the HTML content."""

        # 1. Fetch HTML Content
        try:
            response = requests.get(self.tracking_url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            html_content = response.text
        except requests.exceptions.RequestException as e:
            self.log_message(f"Error fetching product HTML: {e}")
            return

        # 2. Prepare Filename
        file_name = self.product_name.get().replace(' ', '_').replace('/', '').replace('\\', '')[:30]
        initial_file = f"{file_name}_html_dump.html"

        # 3. Open Save Dialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            initialfile=initial_file,
            title="Save Product HTML Dump"
        )

        # 4. Save to File
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                self.log_message(f"HTML saved successfully to: {file_path}")
            except Exception as e:
                self.log_message(f"Error saving HTML file: {e}")
        else:
            self.log_message("HTML download canceled by user.")

    def send_now_thread(self):
        """Starts an immediate price check in a separate thread."""
        if not self.is_tracking:
            self.log_message("Error: Start tracking first to check the price.")
            return

        self.send_now_button.configure(state="disabled")
        self.log_message("Initiating immediate price check...")

        threading.Thread(target=self._run_single_check, daemon=True).start()

    def _run_single_check(self):
        """Helper to run a single check (used by Send Now button)"""
        try:
            target_price = float(self.target_price.get().replace(",", ""))
        except ValueError:
            self.log_message("Error: Invalid target price format.")
            self.send_now_button.configure(state="normal")
            return

        status_message = check_price(
            product_url=self.tracking_url,
            target_price=target_price,
            recipient_email=self.recipient_email.get()
        )
        self.log_message(status_message)

        self.send_now_button.configure(state="normal")

    def start_tracking_thread(self):
        """Starts the main logic in a separate thread."""
        if self.is_tracking:
            self.log_message("Already tracking!")
            return

        try:
            target_price = float(self.target_price.get().replace(",", ""))
            if target_price <= 0: raise ValueError
        except ValueError:
            self.log_message("Error: Invalid or missing target price.")
            return

        product_name = self.product_name.get()
        recipient = self.recipient_email.get()
        if not product_name or not recipient:
            self.log_message("Error: Please fill in all fields.")
            return

        self.start_button.configure(text="Tracking...", state="disabled")
        self.stop_button.configure(state="normal")
        self.is_tracking = True
        self.log_message("Setup complete. Starting search...")

        self.thread = threading.Thread(target=self._initial_setup_and_start_loop, daemon=True)
        self.thread.start()

    def _initial_setup_and_start_loop(self):
        """Performs URL search and starts the periodic check (runs in a separate thread)."""

        product_name = self.product_name.get()
        self.tracking_url = get_product_url(product_name)

        if not self.tracking_url:
            self.log_message(f"Failed to find product URL for '{product_name}'. Tracking stopped.")
            self.stop_tracking()
            return

        # Enable all control buttons once URL is successfully found
        self.send_now_button.configure(state="normal")
        self.open_url_button.configure(state="normal")
        self.download_html_button.configure(state="normal")

        self.log_message(f"Found product page. URL: {self.tracking_url[:50]}...")
        self.log_message(f"Starting periodic checks (12-hour interval)...")

        self.recurrent_check()

    def stop_tracking(self):
        """Resets the application state and stops the recurring check."""
        self.is_tracking = False
        self.start_button.configure(text="Start Tracking", state="normal")
        self.stop_button.configure(state="disabled")
        self.send_now_button.configure(state="disabled")
        self.open_url_button.configure(state="disabled")
        self.download_html_button.configure(state="disabled")
        self.tracking_url = None
        self.log_message("Tracking stopped by user.")

    def recurrent_check(self):
        """The main loop function, called by Tkinter's after()"""
        if not self.is_tracking:
            return

        self.log_message(f"Checking price for: {self.product_name.get()}")

        try:
            target_price = float(self.target_price.get().replace(",", ""))
        except ValueError:
            self.log_message("Error: Target price changed to invalid format. Tracking stopped.")
            self.stop_tracking()
            return

        status_message = check_price(
            product_url=self.tracking_url,
            target_price=target_price,
            recipient_email=self.recipient_email.get()
        )
        self.log_message(status_message)

        NEXT_CHECK_MS = 43200000
        self.log_message(f"Next check scheduled in {NEXT_CHECK_MS // 3600000} hours.")
        self.after(NEXT_CHECK_MS, self.recurrent_check)


# ====================================================================
# 4. EXECUTION BLOCK
# ====================================================================

if __name__ == "__main__":
    app = PriceTrackerApp()

    # FIX: Schedule the initial log message to run AFTER the mainloop starts
    app.after(100, lambda: app.log_message("Ready. Enter details and click 'Start Tracking'."))

    app.mainloop()

