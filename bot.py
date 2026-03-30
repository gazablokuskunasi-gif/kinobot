import telebot
import sqlite3
import yt_dlp
import os
import datetime
import threading
import time
import csv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8700931998:AAFsy6rKz8Kw4BTtKUWAokHog_3mRMhNPU8"
ADMIN_ID = 7588189557

bot = telebot.TeleBot(TOKEN)

db = sqlite3.connect("kino.db", check_same_thread=False)
cursor = db.cursor()

# ===== TABLES =====
cursor.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS groups(chat_id INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS kinolar(kod TEXT,name TEXT,file_id TEXT,views INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS logs(user_id INTEGER,date TEXT)")
db.commit()

# ===== GLOBAL =====
AUTO_STATUS = False
AUTO_TIMES = []
AUTO_TEXT = "Reklama"

# ===== USER =====
def add_user(user_id):
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users VALUES(?)", (user_id,))
        db.commit()

# ===== GROUP CLEANER =====
@bot.message_handler(content_types=['new_chat_members'])
def join_clean(message):
    try:
        cursor.execute("INSERT OR IGNORE INTO groups VALUES(?)", (message.chat.id,))
        db.commit()
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

@bot.message_handler(content_types=['left_chat_member'])
def left_clean(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

# ===== START =====
@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.from_user.id)

    today = str(datetime.date.today())
    cursor.execute("INSERT INTO logs VALUES (?,?)",(message.from_user.id,today))
    db.commit()

    bot.send_message(message.chat.id,"🎬 Kino kod yubor yoki link tashla")

# ===== ADMIN PANEL (FIXED) =====
@bot.message_handler(func=lambda m: m.text == "/admin")
def admin(message):

    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id,"⛔ Siz admin emassiz")
        return

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ Kino", callback_data="add"),
        InlineKeyboardButton("❌ Delete", callback_data="delete")
    )
    markup.add(
        InlineKeyboardButton("📢 Reklama", callback_data="ads"),
        InlineKeyboardButton("🚀 Auto Ads", callback_data="auto")
    )
    markup.add(
        InlineKeyboardButton("📊 Stat", callback_data="stat"),
        InlineKeyboardButton("📤 Export", callback_data="export")
    )

    bot.send_message(message.chat.id,"⚙️ ADMIN PANEL",reply_markup=markup)

# ===== CALLBACK =====
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    global AUTO_STATUS

    if call.data == "add":
        msg = bot.send_message(call.message.chat.id,"🎬 Video yubor")
        bot.register_next_step_handler(msg,get_video)

    elif call.data == "delete":
        msg = bot.send_message(call.message.chat.id,"Kod yoz")
        bot.register_next_step_handler(msg,delete_kino)

    elif call.data == "ads":
        msg = bot.send_message(call.message.chat.id,"Reklama yoz")
        bot.register_next_step_handler(msg,send_ads)

    elif call.data == "auto":
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("ON", callback_data="on"),
            InlineKeyboardButton("OFF", callback_data="off")
        )
        markup.add(
            InlineKeyboardButton("Add Time", callback_data="time")
        )
        bot.send_message(call.message.chat.id,"⚙️ AUTO REKLAMA",reply_markup=markup)

    elif call.data == "on":
        AUTO_STATUS = True
        bot.send_message(call.message.chat.id,"🟢 ON")

    elif call.data == "off":
        AUTO_STATUS = False
        bot.send_message(call.message.chat.id,"🔴 OFF")

    elif call.data == "time":
        msg = bot.send_message(call.message.chat.id,"Masalan 09:00")
        bot.register_next_step_handler(msg,set_time)

    elif call.data == "stat":
        show_stats(call.message)

    elif call.data == "export":
        export_users(call.message)

# ===== ADD TIME =====
def set_time(message):
    AUTO_TIMES.append(message.text)
    bot.send_message(message.chat.id,"✅ Time qo‘shildi")

# ===== AUTO ADS =====
def auto_ads():
    while True:
        now = datetime.datetime.now().strftime("%H:%M")

        if AUTO_STATUS and now in AUTO_TIMES:
            cursor.execute("SELECT user_id FROM users")
            users = cursor.fetchall()

            for u in users:
                try:
                    bot.send_message(u[0], AUTO_TEXT)
                except:
                    pass

        time.sleep(30)

threading.Thread(target=auto_ads).start()

# ===== ADS =====
def send_ads(message):
    cursor.execute("SELECT user_id FROM users")
    for u in cursor.fetchall():
        try:
            bot.send_message(u[0], message.text)
        except:
            pass

    cursor.execute("SELECT chat_id FROM groups")
    for g in cursor.fetchall():
        try:
            bot.send_message(g[0], message.text)
        except:
            pass

    bot.send_message(message.chat.id,"✅ Yuborildi")

# ===== EXPORT =====
def export_users(message):
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    with open("users.csv","w",newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id"])
        for u in users:
            writer.writerow([u[0]])

    with open("users.csv","rb") as f:
        bot.send_document(message.chat.id,f)

    os.remove("users.csv")

# ===== STAT =====
def show_stats(message):
    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(views) FROM kinolar")
    views = cursor.fetchone()[0] or 0

    bot.send_message(message.chat.id,f"👥 Users: {users}\n👁 Views: {views}")

# ===== ADD MOVIE =====
def get_video(message):
    file_id = message.video.file_id
    msg = bot.send_message(message.chat.id,"Nom yoz")
    bot.register_next_step_handler(msg,get_name,file_id)

def get_name(message,file_id):
    name = message.text
    msg = bot.send_message(message.chat.id,"Kod yoz")
    bot.register_next_step_handler(msg,save_movie,file_id,name)

def save_movie(message,file_id,name):
    kod = message.text
    cursor.execute("INSERT INTO kinolar VALUES (?,?,?,?)",(kod,name,file_id,0))
    db.commit()
    bot.send_message(message.chat.id,"✅ Qo‘shildi")

def delete_kino(message):
    cursor.execute("DELETE FROM kinolar WHERE kod=?", (message.text,))
    db.commit()
    bot.send_message(message.chat.id,"❌ O‘chirildi")

# ===== VIDEO DOWNLOAD =====
@bot.message_handler(func=lambda m: m.text and ("http" in m.text))
def download_video(message):

    url = message.text
    bot.send_message(message.chat.id,"📥 Yuklanmoqda...")

    try:
        ydl_opts = {
            'format': 'mp4',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as f:
            bot.send_video(message.chat.id, f)

        os.remove(filename)

    except:
        bot.send_message(message.chat.id,"❌ Xatolik")

# ===== KINO =====
@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/") and "http" not in m.text)
def kino(message):
    cursor.execute("SELECT name,file_id,views FROM kinolar WHERE kod=?", (message.text,))
    k = cursor.fetchone()

    if k:
        name, file, views = k
        views += 1
        cursor.execute("UPDATE kinolar SET views=? WHERE kod=?", (views,message.text))
        db.commit()

        bot.send_video(message.chat.id,file,caption=f"🎬 {name}\n👁 {views}")
    else:
        bot.send_message(message.chat.id,"❌ Topilmadi")

print("🚀 BOT ISHLADI")
bot.infinity_polling()
