import time
import threading
import requests
import telebot
from telebot import types
from bs4 import BeautifulSoup
from flask import Flask, request
import os

TOKEN = "7843096547:AAHzkh6gwbeYzUrwQmNlskzft6ZayCRKgNU"  # Replace with your bot token
CHANNEL_ID = -1002440398569  # Replace with your private channel ID
SENT_LINKS_FILE = "sent_links.txt"  # File to store sent links
LAST_TIMESTAMP_FILE = "last_timestamp.txt"  # File to store the last post timestamp

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Load and save sent links to avoid reposting
def load_sent_links():
    if os.path.exists(SENT_LINKS_FILE):
        with open(SENT_LINKS_FILE, "r") as file:
            return set(file.read().splitlines())
    return set()

def save_sent_links():
    with open(SENT_LINKS_FILE, "w") as file:
        for link in sent_links:
            file.write(f"{link}\n")

# Load the last post timestamp
def load_last_timestamp():
    if os.path.exists(LAST_TIMESTAMP_FILE):
        with open(LAST_TIMESTAMP_FILE, "r") as file:
            return file.read().strip()
    return "2000-01-01T00:00:00"  # A very old timestamp if no last timestamp is saved

def save_last_timestamp(timestamp):
    with open(LAST_TIMESTAMP_FILE, "w") as file:
        file.write(timestamp)

sent_links = load_sent_links()
last_timestamp = load_last_timestamp()

# Start command
@bot.message_handler(commands=["start"])
def start_command(message):
    text_message = (
        "Hello👋 \n\n"
        "🗳 Get latest Movies from 1Tamilmv\n\n"
        "⚙️ *How to use me??*🤔\n\n"
        "✯ Please Enter */view* command and you'll get magnet link as well as link to torrent file 😌\n\n"
        "🔗 Share and Support💝"
    )

    keyboard = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("📌Owner", url="https://t.me/mr_official_300"),
        types.InlineKeyboardButton(text="⚡ Powered By", url="https://t.me/cpflicks")
    )

    bot.send_photo(
        chat_id=message.chat.id,
        photo="https://graph.org/file/4e8a1172e8ba4b7a0bdfa.jpg",
        caption=text_message,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )

# View command
@bot.message_handler(commands=["view"])
def view_movies(message):
    bot.send_message(message.chat.id, "*🧲 Please wait for 10 ⏰ seconds*", parse_mode="Markdown")
    movie_list, _ = tamilmv()

    if not movie_list:
        bot.send_message(message.chat.id, "No movies found at the moment. Try again later.")
        return

    keyboard = types.InlineKeyboardMarkup()
    for key, value in enumerate(movie_list):
        keyboard.add(types.InlineKeyboardButton(text=value, callback_data=f"{key}"))

    bot.send_photo(
        chat_id=message.chat.id,
        photo="https://graph.org/file/4e8a1172e8ba4b7a0bdfa.jpg",
        caption="🔗 Select a Movie from the list 🎬:",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global real_dict
    for key, value in enumerate(movie_list):
        if call.data == f"{key}" and value in real_dict.keys():
            for i in real_dict[value]:
                bot.send_message(call.message.chat.id, text=i, parse_mode="HTML")

# Function to scrape 1TamilMV
def tamilmv():
    url = "https://www.1tamilmv.pm/"
    headers = {"User-Agent": "Mozilla/5.0"}

    movie_list = []
    real_dict = {}

    web = requests.get(url, headers=headers)
    soup = BeautifulSoup(web.text, "lxml")

    movies = soup.find_all("div", {"class": "ipsType_break ipsContained"})

    for i in range(min(20, len(movies))):
        title = movies[i].find("a").text.strip()
        link = movies[i].find("a")["href"]
        post_timestamp = movies[i].find("time").get("datetime") if movies[i].find("time") else "No timestamp available"

        # Only add movies that are newer than the last timestamp
        if post_timestamp > last_timestamp:
            movie_list.append(title)
            movie_details = get_movie_details(link)
            real_dict[title] = movie_details

            # Update the last timestamp if this is the newest post
            if post_timestamp > last_timestamp:
                save_last_timestamp(post_timestamp)

    return movie_list, real_dict

# Function to get magnet links and send to channel
def get_movie_details(url):
    try:
        html = requests.get(url)
        soup = BeautifulSoup(html.text, "lxml")

        mag_links = [a["href"] for a in soup.find_all("a", href=True) if "magnet:" in a["href"]]

        new_posts_found = False  # Track if any new post is found

        for mag in mag_links:
            if mag not in sent_links:
                sent_links.add(mag)
                save_sent_links()  # Save the new state of sent links

                msg = f"/qbleech1 {mag}\n<b>Tag:</b> <code>@Mr_official_300</code> <code>2142536515</code>"
                bot.send_message(CHANNEL_ID, msg, parse_mode="HTML")

                # Delay the next post by 300 seconds (5 minutes)
                time.sleep(300)  # Delay added here to wait 5 minutes before posting next magnet

                new_posts_found = True  # Mark that a new post has been found

        return mag_links, new_posts_found
    except Exception as e:
        print(f"Error fetching movie details: {e}")
        return [], False

# Background scraper every 10 minutes
def background_scraper():
    while True:
        print("🔄 Checking for new movies...")
        movie_list, new_posts_found = tamilmv()

        if new_posts_found:
            print("New posts found, posting them...")
        else:
            print("No new posts found, sleeping...")

        time.sleep(600)  # Sleep for 10 minutes before checking again

# Flask health check
@app.route("/")
def health_check():
    return "Bot is running!", 200

if __name__ == "__main__":
    threading.Thread(target=background_scraper, daemon=True).start()
    threading.Thread(target=bot.polling, kwargs={"none_stop": True}).start()
    app.run(host="0.0.0.0", port=3000)
