import os
import requests
import hashlib
from bs4 import BeautifulSoup

# Fetches from hidden Repository Secrets
URL_TO_MONITOR = os.environ.get("URL_TO_MONITOR", "https://www.lizzymcalpine.com/")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
HASH_FILE = "last_hash.txt"

def send_telegram(message):
    telegram_url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(telegram_url, json=payload, timeout=10)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def main():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Missing Telegram configuration in GitHub Secrets.")
        return

    try:
        # Fetch the website
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) WebsiteMonitor/1.0'}
        response = requests.get(URL_TO_MONITOR, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse the page and strip noisy layout dynamic scripts/styles
        soup = BeautifulSoup(response.text, 'html.parser')
        for element in soup(["script", "style", "meta", "noscript", "input"]):
            element.decompose()
            
        # Extract purely the visible content structure
        clean_content = soup.get_text(separator="\n", strip=True)
        
        # Create a unique hash of the real text content
        current_hash = hashlib.sha256(clean_content.encode('utf-8')).hexdigest()
        
        # Read the previous hash cache
        previous_hash = ""
        if os.path.exists(HASH_FILE):
            with open(HASH_FILE, "r") as f:
                previous_hash = f.read().strip()
        
        # Check for modifications
        if current_hash != previous_hash:
            print("Change detected!")
            
            # Don't trigger an alert on the very first run when last_hash doesn't exist yet
            if previous_hash:
                send_telegram(f"🎵 *Website Update!*\n\nA change was detected on the site. Check it out: {URL_TO_MONITOR}")
            else:
                print("First run initialized. Baseline hash stored.")
            
            # Save the new state
            with open(HASH_FILE, "w") as f:
                f.write(current_hash)
        else:
            print("No visible changes detected on the site.")
            
    except Exception as e:
        print(f"Error executing monitor: {e}")

if __name__ == "__main__":
    main()
