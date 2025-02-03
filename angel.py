import time
import threading
import requests
import telebot
from telebot import types
from bs4 import BeautifulSoup
from flask import Flask, request

TOKEN = "7843096547:AAHzkh6gwbeYzUrwQmNlskzft6ZayCRKgNU"  # Replace with your bot token
CHANNEL_ID = -1002440398569  # Replace with your private channel ID

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Global storage for tracking sent links
sent_links = set()

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
        movie_list.append(title)

        # Check if "time" exists before trying to access its attributes
        time_tag = movies[i].find("time")
        if time_tag:
            post_timestamp = time_tag.get("datetime")  # Safely get the datetime attribute
        else:
            post_timestamp = "No timestamp available"  # Handle case if there is no "time" tag

        movie_details = get_movie_details(link)
        real_dict[title] = movie_details

    return movie_list, real_dict

# Function to get magnet links and send to channel
def get_movie_details(url):
    try:
        html = requests.get(url)
        soup = BeautifulSoup(html.text, "lxml")

        mag_links = [a["href"] for a in soup.find_all("a", href=True) if "magnet:" in a["href"]]

        for mag in mag_links:
            if mag not in sent_links:
                sent_links.add(mag)
                msg = f"/qbleech1 {mag}\n\n<b>Tag:</b> <code>@Mr_official_300</code> <code>2142536515</code>"
                bot.send_message(CHANNEL_ID, msg, parse_mode="HTML")

                # Delay the next post by 300 seconds (5 minutes)
                time.sleep(300)  # Delay added here to wait 5 minutes before posting next magnet

        return mag_links
    except Exception as e:
        print(f"Error fetching movie details: {e}")
        return []

# Background scraper every 10 minutes
def background_scraper():
    while True:
        print("🔄 Checking for new movies...")
        tamilmv()
        time.sleep(600)

# Flask health check
@app.route("/")
def health_check():
    return "Bot is running!", 200

if __name__ == "__main__":
    threading.Thread(target=background_scraper, daemon=True).start()
    threading.Thread(target=bot.polling, kwargs={"none_stop": True}).start()
    app.run(host="0.0.0.0", port=3000)
