import telebot
import sqlite3
import yt_dlp
import os
import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8700931998:AAFsy6rKz8Kw4BTtKUWAokHog_3mRMhNPU8"
ADMIN_ID = 7588189557

bot = telebot.TeleBot(TOKEN)

db = sqlite3.connect("kino.db",check_same_thread=False)
cursor = db.cursor()

# TABLES
cursor.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS groups(chat_id INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS kinolar(kod TEXT,name TEXT,file_id TEXT,views INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS logs(user_id INTEGER, date TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS start_time(time TEXT)")
db.commit()

# uptime start
cursor.execute("SELECT time FROM start_time")
t = cursor.fetchone()
if not t:
    now = str(datetime.datetime.now())
    cursor.execute("INSERT INTO start_time VALUES(?)",(now,))
    db.commit()

# USER ADD
def add_user(user_id):
    cursor.execute("SELECT user_id FROM users WHERE user_id=?",(user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users VALUES(?)",(user_id,))
        db.commit()

# GROUP ADD
def add_group(chat_id):
    cursor.execute("SELECT chat_id FROM groups WHERE chat_id=?",(chat_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO groups VALUES(?)",(chat_id,))
        db.commit()

# START
@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.from_user.id)

    today = str(datetime.date.today())
    cursor.execute("INSERT INTO logs VALUES (?,?)",(message.from_user.id,today))
    db.commit()

    bot.send_message(message.chat.id,"🎬 Kino botga xush kelibsiz\n\nKod yuboring")

# GROUP
@bot.message_handler(content_types=['new_chat_members'])
def new_group(message):
    add_group(message.chat.id)

# ADD MOVIE
@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.send_message(message.chat.id,"🎬 Video yubor")
    bot.register_next_step_handler(msg,get_video)

def get_video(message):
    file_id = message.video.file_id
    msg = bot.send_message(message.chat.id,"🎬 Nom yoz")
    bot.register_next_step_handler(msg,get_name,file_id)

def get_name(message,file_id):
    name = message.text
    msg = bot.send_message(message.chat.id,"🔎 Kod yoz")
    bot.register_next_step_handler(msg,save_movie,file_id,name)

def save_movie(message,file_id,name):
    kod = message.text
    cursor.execute("INSERT INTO kinolar VALUES (?,?,?,?)",(kod,name,file_id,0))
    db.commit()
    bot.send_message(message.chat.id,"✅ Qo‘shildi")

# KINO QIDIRISH
@bot.message_handler(func=lambda m: True)
def kino(message):
    text = message.text

    cursor.execute("SELECT kod,name,file_id,views FROM kinolar WHERE kod=?",(text,))
    kino = cursor.fetchone()

    if kino:
        kod,name,file,views = kino
        views += 1
        cursor.execute("UPDATE kinolar SET views=? WHERE kod=?",(views,kod))
        db.commit()

        caption = f"🎬 {name}\n👁 {views}"

        bot.send_video(message.chat.id,file,caption=caption,protect_content=True)
    else:
        bot.send_message(message.chat.id,"❌ Topilmadi")

# VIDEO DOWNLOAD
@bot.message_handler(func=lambda m: m.text and ("youtube" in m.text or "tiktok" in m.text or "instagram" in m.text))
def download(message):
    url = message.text
    bot.send_message(message.chat.id,"📥 Yuklanmoqda...")

    try:
        ydl_opts = {'outtmpl':'video.mp4','format':'mp4'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        with open("video.mp4","rb") as v:
            bot.send_video(message.chat.id,v)

        os.remove("video.mp4")
    except:
        bot.send_message(message.chat.id,"❌ Xatolik")

# STATISTIKA
@bot.message_handler(commands=['stat'])
def stat(message):
    if message.from_user.id != ADMIN_ID:
        return

    today = str(datetime.date.today())

    cursor.execute("SELECT COUNT(*) FROM users")
    all_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM logs WHERE date=?",(today,))
    today_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM logs WHERE date >= date('now','-7 day')")
    week_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM logs WHERE date >= date('now','-30 day')")
    month_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM kinolar")
    movies = cursor.fetchone()[0]

    cursor.execute("SELECT time FROM start_time")
    start = cursor.fetchone()[0]

    start_time = datetime.datetime.fromisoformat(start)
    now = datetime.datetime.now()

    diff = now - start_time
    days = diff.days
    hours = diff.seconds // 3600

    text = f"""
📊 Bot statistikasi

👥 Barcha userlar: {all_users}
🟢 Bugungi faol: {today_users}

📅 7 kun: {week_users}
📆 30 kun: {month_users}

🎬 Kinolar: {movies}

⏱ Uptime: {days} kun {hours} soat
"""

    bot.send_message(message.chat.id,text)

print("BOT ISHLADI")
bot.infinity_polling()
