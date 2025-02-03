import time
import threading
import requests
import telebot
from bs4 import BeautifulSoup
from pymongo import MongoClient
from flask import Flask
from datetime import datetime

# 🔹 Telegram Bot Credentials (Make Sure These Are Correct)
TOKEN = "7843096547:AAHzkh6gwbeYzUrwQmNlskzft6ZayCRKgNU"  # ⬅ Replace with your actual bot token
CHANNEL_ID = -1002440398569  # ⬅ Replace with your actual Telegram Channel ID

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# 🔹 MongoDB Connection
MONGO_URI = "mongodb+srv://FF:FF@cluster0.ryymb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # ⬅ Replace with your actual MongoDB connection string
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
posts_collection = db["posts"]

# 🔹 TamilMV URL
BASE_URL = "https://www.1tamilmv.pm/"

# 🔹 Function to Fetch Latest Posts
def fetch_latest_posts():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
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

        return new_posts[::-1]  # Reverse order to post older first
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching posts: {e}")
        return []

# 🔹 Function to Fetch Magnet Links from Post Page
def fetch_magnet_links(post_link):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(post_link, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        # Extract magnet links
        magnet_links = [a["href"] for a in soup.find_all("a", href=True) if "magnet:" in a["href"]]

        for magnet in magnet_links:
            msg = f"/qbleech {magnet}\n<b>Tag:</b> <code>@Mr_official_300</code> <code>2142536515</code>"
            bot.send_message(CHANNEL_ID, msg, parse_mode="HTML")
            print(f"✅ Posted magnet: {magnet}")  # Debugging Log
            time.sleep(150)  # Prevent spam

        return bool(magnet_links)  # Return True if magnets found
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching magnets: {e}")
        return False

# 🔹 Function to Check if Post is Already Sent
def is_post_already_sent(post_link):
    return posts_collection.find_one({"post_link": post_link}) is not None

# 🔹 Function to Save Posted Links in Database
def save_post_to_db(post_link):
    posts_collection.insert_one({"post_link": post_link, "timestamp": datetime.utcnow()})
    print(f"💾 Saved post: {post_link}")  # Debugging Log

# 🔹 Background Scraper (Runs Every 10 Minutes)
def background_scraper():
    while True:
        print("🔄 Checking for new movies...")
        new_posts = fetch_latest_posts()

        if new_posts:
            print(f"✅ Found {len(new_posts)} new post(s). Checking each post...")

            for link in new_posts:
                if not is_post_already_sent(link):
                    print(f"🆕 New post found: {link}")  # Debugging Log
                    if fetch_magnet_links(link):  # Only save if magnets are found
                        save_post_to_db(link)
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
    app.run(host="0.0.0.0", port=3000)

if __name__ == "__main__":
    # Start Flask and Scraper in Separate Threads
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=background_scraper, daemon=True).start()

    # Start Telegram Bot Polling
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"❌ Bot polling error: {e}")
