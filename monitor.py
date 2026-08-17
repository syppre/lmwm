import os
import requests
import hashlib
from bs4 import BeautifulSoup

URL_TO_MONITOR = "https://lizzymcalpine.com"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
HASH_FILE = "last_hash.txt"

def send_telegram(message):
    # This automatically fixes the token if the word 'bot' is missing or duplicated
    token = TELEGRAM_TOKEN
    if not token.startswith("bot"):
        token = f"bot{token}"
        
    telegram_url = f"https://telegram.org{token}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    
    try:
        response = requests.post(telegram_url, json=payload, timeout=10)
        print(f"Telegram API Response Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Telegram API Error Text: {response.text}")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def main():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Missing Telegram configuration in GitHub Secrets.")
        return

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) WebsiteMonitor/1.0'}
        response = requests.get(URL_TO_MONITOR, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        for element in soup(["script", "style", "meta", "noscript", "input"]):
            element.decompose()
            
        clean_content = soup.get_text(separator="\n", strip=True)
        current_hash = hashlib.sha256(clean_content.encode('utf-8')).hexdigest()
        
        previous_hash = ""
        if os.path.exists(HASH_FILE):
            with open(HASH_FILE, "r") as f:
                previous_hash = f.read().strip()
        
        if current_hash != previous_hash:
            print("Change detected!")
            if previous_hash:
                send_telegram(f"🎵 *LM Website Update!*\n\nA change was detected on the site. Check it out: {URL_TO_MONITOR}")
            else:
                print("First run initialized. Baseline hash stored.")
            
            with open(HASH_FILE, "w") as f:
                f.write(current_hash)
        else:
            print("No visible changes detected on the site.")
            
    except Exception as e:
        print(f"Error executing monitor: {e}")

if __name__ == "__main__":
    main()
