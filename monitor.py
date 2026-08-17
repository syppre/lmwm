import os
import requests
import difflib
from bs4 import BeautifulSoup

URL_TO_MONITOR = "https://www.lizzymcalpine.com/"
TEXT_FILE = "website_text.txt"

TOKEN_SECRET = os.environ.get("TELEGRAM_TOKEN", "").strip()
CHAT_ID_SECRET = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
REPO_SLUG = os.environ.get("GITHUB_REPOSITORY", "") # Automatically grabs your repo name (username/repo)

def send_telegram(message):
    base_domain = "api.telegram.org"
    clean_token = TOKEN_SECRET.replace("bot", "").strip()
    full_path = f"https://{base_domain}/bot{clean_token}/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID_SECRET,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        headers = {"Content-Type": "application/json"}
        requests.post(full_path, json=payload, headers=headers, timeout=15)
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

def main():
    if not TOKEN_SECRET or not CHAT_ID_SECRET:
        print("❌ Configuration Error: GitHub Secrets are empty.")
        return

    try:
        # 1. Fetch website text
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) WebsiteMonitor/1.5'}
        response = requests.get(URL_TO_MONITOR, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        for element in soup(["script", "style", "meta", "noscript", "input"]):
            element.decompose()
            
        new_text = soup.get_text(separator="\n", strip=True)
        new_lines = [line.strip() for line in new_text.splitlines() if line.strip()]

        # 2. Read old text from repository
        old_lines = []
        if os.path.exists(TEXT_FILE):
            with open(TEXT_FILE, "r", encoding="utf-8") as f:
                old_lines = [line.strip() for line in f.readlines() if line.strip()]

        # 3. Detect changes line-by-line
        if old_lines:
            # Compares the lines and extracts only additions (+) or removals (-)
            diff = list(difflib.ndiff(old_lines, new_lines))
            changes = []
            
            for line in diff:
                if line.startswith('+ '):
                    changes.append(f"🟢 *Added:* {line[2:]}")
                elif line.startswith('- '):
                    changes.append(f"🔴 *Removed:* {line[2:]}")

            if changes:
                print("Change detected!")
                
                # Limit size so Telegram handles the text size perfectly
                changes_summary = "\n".join(changes[:15])
                if len(changes) > 15:
                    changes_summary += f"\n...and {len(changes) - 15} more changes."

                # Create direct links to GitHub history and the real website
                github_history_link = f"https://github.com/{REPO_SLUG}/commits/main/{TEXT_FILE}"
                
                alert_msg = (
                    f"🎵 *LM Website Update!*\n\n"
                    f"*What changed:*\n{changes_summary}\n\n"
                    f"🔗 [Open Website]({URL_TO_MONITOR})\n"
                    f"📂 [View History Changes on GitHub]({github_history_link})"
                )
                
                send_telegram(alert_msg)
                
                # Save the new text update
                with open(TEXT_FILE, "w", encoding="utf-8") as f:
                    f.write("\n".join(new_lines))
            else:
                print("✅ No visible changes detected.")
        else:
            # First initialization run
            print("First run initialized. Full homepage content saved to GitHub.")
            with open(TEXT_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines))
            
    except Exception as e:
        print(f"❌ System Error: {e}")

if __name__ == "__main__":
    main()
