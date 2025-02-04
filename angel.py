import time
import threading
import requests
import telebot
from telebot import types
from bs4 import BeautifulSoup
from flask import Flask

# 🔹 Telegram Bot Credentials
TOKEN = "7843096547:AAHzkh6gwbeYzUrwQmNlskzft6ZayCRKgNU"  # Replace with your actual bot token
CHANNEL_ID = -1002440398569  # Replace with your actual Telegram Channel ID

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# 🔹 TamilMV URL
BASE_URL = "https://www.1tamilmv.pm/"
SEEN_POSTS_FILE = "seen_posts.txt"  # File to store already posted links

# 🔹 Load seen posts from file
def load_seen_posts():
    try:
        with open(SEEN_POSTS_FILE, "r") as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()

# 🔹 Save seen post to file
def save_seen_post(post_link):
    try:
        with open(SEEN_POSTS_FILE, "a") as file:
            file.write(post_link + "\n")
    except Exception as e:
        print(f"❌ Error saving post: {e}")

# 🔹 Fetch Latest Posts
def fetch_latest_posts():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        print("⏳ Fetching latest posts from the website...")
        response = requests.get(BASE_URL, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        # Extract post links
        posts = soup.find_all("a", class_="ipsType_break")
        new_posts = []

        for post in posts:
            link = post.get("href")
            if link and "forums/topic/" in link:
                full_link = BASE_URL + link if not link.startswith("http") else link
                new_posts.append(full_link)

        print(f"✅ Found {len(new_posts)} new posts.")
        return new_posts[::-1]  # Reverse order to post older first
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching posts: {e}")
        return []

# 🔹 Fetch Magnet Links from Post Page
def fetch_magnet_links(post_link):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        print(f"⏳ Fetching magnet links from {post_link}...")
        response = requests.get(post_link, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        # Extract magnet links
        magnet_links = [a["href"] for a in soup.find_all("a", href=True) if "magnet:" in a["href"]]
        print(f"✅ Found {len(magnet_links)} magnet links.")

        for magnet in magnet_links:
            msg = f"/qbleech {magnet}\n<b>Tag:</b> <code>@Mr_official_300</code> <code>2142536515</code>"
            bot.send_message(CHANNEL_ID, msg, parse_mode="HTML")
            print(f"✅ Posted magnet: {magnet}")  # Debugging Log
            time.sleep(150)  # Prevent spam

        return bool(magnet_links)  # Return True if magnets found
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching magnets: {e}")
        return False

# 🔹 Background Scraper (Runs Every 10 Minutes)
def background_scraper():
    seen_posts = load_seen_posts()

    while True:
        print("🔄 Checking for new movies...")
        new_posts = fetch_latest_posts()

        if new_posts:
            print(f"✅ Found {len(new_posts)} new post(s). Checking each post...")

            for link in new_posts:
                if link not in seen_posts:
                    print(f"🆕 New post found: {link}")
                    if fetch_magnet_links(link):  # Only save if magnets are found
                        save_seen_post(link)  # Save new post to avoid duplicates
                        seen_posts.add(link)  # Update seen posts list
                else:
                    print(f"⚠️ Already posted: {link}")
        else:
            print("❌ No new posts found.")

        print("🕐 Waiting 10 minutes before next check...")
        time.sleep(600)  # Wait 10 minutes before checking again

# 🔹 Flask Health Check
@app.route("/")
def health_check():
    return "Bot is running!", 200

# 🔹 Run Flask for Koyeb Health Checks
def run_flask():
    try:
        app.run(host="0.0.0.0", port=3000)
    except Exception as e:
        print(f"❌ Error starting Flask: {e}")

# 🔹 Start Flask and Scraper in Separate Threads
def start_threads():
    # Start Flask in a separate thread for health check
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Start background scraper in another thread
    scraper_thread = threading.Thread(target=background_scraper, daemon=True)
    scraper_thread.start()

if __name__ == "__main__":
    try:
        # Start the threads for Flask and Scraper
        start_threads()

        # Start Telegram Bot Polling
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"❌ Error with Telegram Bot: {e}")
