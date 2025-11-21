# 🔥 Amazon Price Tracker GUI Application

A feature-rich, multi-threaded desktop application built with Python and CustomTkinter to monitor Amazon product prices and send email alerts when a target price is reached.

The application uses dynamic search functionality, allowing users to track any product by name.

## ✨ Features

*   **Dynamic Search:** Finds the product URL by searching Amazon based on user input (product name).
*   **Flexible Tracking:** User sets the target price and the recipient email address for each tracking session.
*   **Secure Emailing:** Uses environment variables (`.env` file) for secure sender credentials (email and App Password).
*   **Continuous Monitoring:** Runs a periodic check (default 12 hours) in the background.
*   **Manual Control:**
    *   **Check & Send Now:** Instantly forces a price check without waiting for the next scheduled interval.
    *   **Open in Browser:** Opens the currently tracked product page in the default web browser.
    *   **Download Log:** Saves the entire session log (all check attempts and status messages) to a `.txt` file.
    *   **Download HTML:** Fetches and saves the raw HTML of the product page for inspection/debugging.

## 🛠️ Prerequisites

Before running the application, you need to have Python installed and set up your environment:

1.  **Python 3.x:** Ensure Python is installed on your system.
2.  **Required Libraries:** Install the necessary Python packages.
    ```bash
    pip install customtkinter requests beautifulsoup4 lxml python-dotenv
    ```
3.  **Gmail App Password (Critical):**
    *   You **cannot** use your regular Gmail password.
    *   You must enable **2-Step Verification** on your Google Account.
    *   Generate a 16-character **App Password** for your Python application. This will be used as `MY_PASSWORD`.

## ⚙️ Setup and Configuration

### 1. Save the Code

Save the main application code (the final, complete block provided) into a file named, for example, `app_tracker.py`.

### 2. Create the `.env` File

Create a file named **`.env`** in the same directory as `app_tracker.py`. This file stores your **sender** credentials securely.

```dotenv
# .env file

# The email address that will send the alert (must have 2FA enabled)
MY_EMAIL=lobo012487@gmail.com

# The 16-character Google App Password (NOT your regular password)
MY_PASSWORD=cytbivqimirkifks 

# Optional: Ensure this is correct for your email provider
SMTP_SERVER=smtp.gmail.com
