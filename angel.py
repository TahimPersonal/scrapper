import time
import threading
import requests
import telebot
from telebot import types
from bs4 import BeautifulSoup
from flask import Flask
import logging

# 🔹 Setup Logging
logging.basicConfig(level=logging.INFO)  # Change to DEBUG for more detailed logs
logger = logging.getLogger(__name__)

# 🔹 Telegram Bot Credentials
TOKEN = "7843096547:AAHzkh6gwbeYzUrwQmNlskzft6ZayCRKgNU"  # Replace with your actual bot token
CHANNEL_ID = -1002440398569  # Replace with your actual Telegram Channel ID

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# 🔹 TamilMV URL
BASE_URL = "https://www.1tamilmv.pm/"

# 🔹 Fetch Latest Posts from the Website
def fetch_latest_posts():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        logger.info("⏳ Fetching latest posts from the website...")
        response = requests.get(BASE_URL, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        # Extract post links (these are the individual forum topic links)
        posts = soup.find_all("a", class_="ipsType_break")
        new_posts = []

        for post in posts:
            link = post.get("href")
            if link and "forums/topic/" in link:  # Filter for valid post links
                full_link = BASE_URL + link if not link.startswith("http") else link
                new_posts.append(full_link)

        logger.info(f"✅ Found {len(new_posts)} new posts.")
        return new_posts[::-1]  # Reverse order to post older posts first
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching posts: {e}")
        return []

# 🔹 Fetch Magnet Links from Post Page
def fetch_magnet_links(post_link):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        logger.info(f"⏳ Fetching magnet links from {post_link}...")
        response = requests.get(post_link, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        # Extract magnet links from the post page
        magnet_links = [a["href"] for a in soup.find_all("a", href=True) if "magnet:" in a["href"]]
        logger.info(f"✅ Found {len(magnet_links)} magnet links.")

        for magnet in magnet_links:
            msg = f"/qbleech {magnet}\n<b>Tag:</b> <code>@Mr_official_300</code> <code>2142536515</code>"
            bot.send_message(CHANNEL_ID, msg, parse_mode="HTML")
            logger.info(f"✅ Posted magnet: {magnet}")  # Debugging Log
            time.sleep(150)  # Prevent spam

        return bool(magnet_links)  # Return True if magnets found
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching magnets: {e}")
        return False

# 🔹 Send Old Posts from the Website
def send_old_posts():
    logger.info("🔄 Sending old posts from the website...")
    old_posts = fetch_latest_posts()  # Fetch old posts (same way as latest posts)
    for post in old_posts:
        if fetch_magnet_links(post):
            time.sleep(150)  # Prevent spam

# 🔹 Background Scraper (Runs Every 10 Minutes)
def background_scraper():
    while True:
        logger.info("🔄 Checking for new movies...")
        new_posts = fetch_latest_posts()

        if new_posts:
            logger.info(f"✅ Found {len(new_posts)} new post(s). Sending new posts...")
            for link in new_posts:
                if fetch_magnet_links(link):  # Send new posts if they contain magnets
                    logger.info(f"✅ New post sent: {link}")
                    time.sleep(150)

            logger.info("✅ Finished sending new posts. Now sending old posts...")
            send_old_posts()  # Send old posts after new ones
        else:
            logger.warning("❌ No new posts found. Sending old posts instead.")
            send_old_posts()  # Send old posts if no new ones are found

        logger.info("🕐 Waiting 10 minutes before next check...")
        time.sleep(600)  # Wait 10 minutes before checking again

# 🔹 Flask Health Check
@app.route("/")
def health_check():
    logger.info("Health check passed.")
    return "Bot is running!", 200

# 🔹 Run Flask for Koyeb Health Checks
def run_flask():
    try:
        app.run(host="0.0.0.0", port=3000)
    except Exception as e:
        logger.error(f"❌ Error starting Flask: {e}")

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
        logger.info("Bot is now polling Telegram...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        logger.error(f"❌ Error with Telegram Bot: {e}")
