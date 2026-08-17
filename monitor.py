import os
import requests
import hashlib
from bs4 import BeautifulSoup

URL_TO_MONITOR = "https://lizzymcalpine.com"
HASH_FILE = "last_hash.txt"

# Fetching secrets from GitHub
TOKEN_SECRET = os.environ.get("TELEGRAM_TOKEN", "").strip()
CHAT_ID_SECRET = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

def send_telegram(message):
    # HARDCODED CLEAN URL STRUCTURE
    # This prevents any environment string corruption
    base_domain = "api.telegram.org"
    
    # Clean the token just in case
    clean_token = TOKEN_SECRET.replace("bot", "").strip()
    full_path = f"https://{base_domain}/bot{clean_token}/sendMessage"
    
    print(f"[DEBUG] Attempting request to structural domain: {base_domain}")
    
    payload = {
        "chat_id": CHAT_ID_SECRET,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        # We use explicit headers and a forced clean post request
        headers = {"Content-Type": "application/json"}
        response = requests.post(full_path, json=payload, headers=headers, timeout=15)
        
        print(f"[DEBUG] HTTP Status Code: {response.status_code}")
        if response.status_code == 200:
            print("🎉 Success! Message delivered to Telegram.")
        else:
            print(f"❌ Telegram Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def main():
    if not TOKEN_SECRET or not CHAT_ID_SECRET:
        print("❌ Configuration Error: GitHub Secrets are empty or missing.")
        return

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) WebsiteMonitor/1.3'}
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
        print(f"❌ System Error: {e}")

if __name__ == "__main__":
    main()
