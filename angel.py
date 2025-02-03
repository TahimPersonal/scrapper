import time
import threading
import requests
import telebot
from bs4 import BeautifulSoup
from flask import Flask
import os

TOKEN = "7843096547:AAHzkh6gwbeYzUrwQmNlskzft6ZayCRKgNU"  # Replace with your bot token
CHANNEL_ID = -1002440398569  # Replace with your channel ID
LAST_POST_FILE = "last_post.txt"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

def load_last_post():
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE, "r") as file:
            return file.read().strip()
    return ""

def save_last_post(post_link):
    with open(LAST_POST_FILE, "w") as file:
        file.write(post_link)

last_post_link = load_last_post()

def fetch_latest_posts():
    url = "https://www.1tamilmv.pm/"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "lxml")
        posts = soup.find_all("div", {"class": "ipsType_break ipsContained"})
        
        new_posts = []
        for post in posts:
            title = post.find("a").text.strip()
            link = post.find("a")["href"]
            if link == last_post_link:
                break
            new_posts.append((title, link))

        return new_posts[::-1]  # Oldest first
    except requests.exceptions.RequestException as e:
        print(f"Error fetching posts: {e}")
        return []

def fetch_magnet_links(post_link):
    try:
        response = requests.get(post_link, timeout=10)
        soup = BeautifulSoup(response.text, "lxml")

        mag_links = [a["href"] for a in soup.find_all("a", href=True) if "magnet:" in a["href"]]
        for mag in mag_links:
            msg = f"/qbleech {mag}\n<b>Tag:</b> <code>@Mr_official_300</code> <code>2142536515</code>"
            bot.send_message(CHANNEL_ID, msg, parse_mode="HTML")
            time.sleep(300)  # Delay between posts
    except requests.exceptions.RequestException as e:
        print(f"Error fetching magnet links: {e}")

def background_scraper():
    global last_post_link
    while True:
        print("🔄 Checking for new movies...")
        new_posts = fetch_latest_posts()

        if new_posts:
            print(f"Found {len(new_posts)} new post(s). Posting now...")
            for title, link in new_posts:
                fetch_magnet_links(link)
                save_last_post(link)
                last_post_link = link
        else:
            print("No new posts found, sleeping...")

        time.sleep(600)  # Check every 10 minutes

@app.route("/")
def health_check():
    return "Bot is running!", 200

if __name__ == "__main__":
    threading.Thread(target=background_scraper, daemon=True).start()
    
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Bot polling error: {e}")

    app.run(host="0.0.0.0", port=3000)
