import telebot
import sqlite3
import yt_dlp
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8700931998:AAHIz8f0F0gmHUdKGQLSAv-jRuRM9vmv9m4"
ADMIN_ID = 7588189557

bot = telebot.TeleBot(TOKEN)

db = sqlite3.connect("kino.db",check_same_thread=False)
cursor = db.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS groups(chat_id INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS kinolar(kod TEXT,name TEXT,file_id TEXT,views INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS tg_channels(username TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS inst_links(link TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS yt_links(link TEXT)")

db.commit()


def add_user(user_id):
    cursor.execute("SELECT user_id FROM users WHERE user_id=?",(user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users VALUES(?)",(user_id,))
        db.commit()


def add_group(chat_id):
    cursor.execute("SELECT chat_id FROM groups WHERE chat_id=?",(chat_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO groups VALUES(?)",(chat_id,))
        db.commit()


def check_sub(user_id):

    cursor.execute("SELECT username FROM tg_channels")
    rows = cursor.fetchall()

    not_joined = []

    for r in rows:

        kanal = r[0]

        try:
            member = bot.get_chat_member(kanal,user_id)

            if member.status in ["left","kicked"]:
                not_joined.append(kanal)

        except:
            not_joined.append(kanal)

    return not_joined


def get_markup(not_joined):

    markup = InlineKeyboardMarkup()

    i = 1

    for kanal in not_joined:

        markup.add(
            InlineKeyboardButton(
                f"📢 {i}-kanal",
                url=f"https://t.me/{kanal.replace('@','')}"
            )
        )

        i += 1

    cursor.execute("SELECT link FROM inst_links")
    for r in cursor.fetchall():
        markup.add(
            InlineKeyboardButton("📸 Instagram",url=r[0])
        )

    cursor.execute("SELECT link FROM yt_links")
    for r in cursor.fetchall():
        markup.add(
            InlineKeyboardButton("▶️ YouTube",url=r[0])
        )

    markup.add(
        InlineKeyboardButton("✅ Tekshirish",callback_data="check_sub")
    )

    return markup


@bot.message_handler(commands=['start'])
def start(message):

    add_user(message.from_user.id)

    not_joined = check_sub(message.from_user.id)

    if not_joined:

        markup = get_markup(not_joined)

        bot.send_message(
            message.chat.id,
            "❗ Botdan foydalanish uchun kanallarga qo‘shiling",
            reply_markup=markup
        )

        return

    bot.send_message(message.chat.id,
"""
🎬 Kino botga xush kelibsiz

Kino kodini yuboring.

📥 Instagram / YouTube / TikTok link yuborsangiz video yuklab beradi.
""")


@bot.callback_query_handler(func=lambda call: call.data=="check_sub")
def check(call):

    not_joined = check_sub(call.from_user.id)

    if not not_joined:

        bot.edit_message_text(
            "✅ Hammasiga qo‘shildingiz\n\nEndi kino kodini yuboring",
            call.message.chat.id,
            call.message.message_id
        )

    else:

        markup = get_markup(not_joined)

        bot.edit_message_text(
            "❗ Hali ham kanallarga qo‘shilmagansiz",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )


@bot.message_handler(content_types=['new_chat_members'])
def new_group(message):
    add_group(message.chat.id)


@bot.message_handler(commands=['stats'])
def stats(message):

    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM groups")
    groups = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM kinolar")
    movies = cursor.fetchone()[0]

    bot.send_message(message.chat.id,f"""
📊 BOT HOLATI

👥 Users: {users}
👥 Groups: {groups}
🎬 Kinolar: {movies}
""")


# Telegram kanal qo‘shish
@bot.message_handler(commands=['addtg'])
def addtg(message):

    if message.from_user.id != ADMIN_ID:
        return

    kanal = message.text.split()[1]

    cursor.execute("INSERT INTO tg_channels VALUES(?)",(kanal,))
    db.commit()

    bot.send_message(message.chat.id,"✅ Kanal qo‘shildi")


# Telegram kanal o‘chirish
@bot.message_handler(commands=['deltg'])
def deltg(message):

    if message.from_user.id != ADMIN_ID:
        return

    kanal = message.text.split()[1]

    cursor.execute("DELETE FROM tg_channels WHERE username=?",(kanal,))
    db.commit()

    bot.send_message(message.chat.id,"❌ Kanal o‘chirildi")


# Instagram qo‘shish
@bot.message_handler(commands=['addinst'])
def addinst(message):

    if message.from_user.id != ADMIN_ID:
        return

    link = message.text.split()[1]

    cursor.execute("INSERT INTO inst_links VALUES(?)",(link,))
    db.commit()

    bot.send_message(message.chat.id,"📸 Instagram qo‘shildi")


# Instagram o‘chirish
@bot.message_handler(commands=['delinst'])
def delinst(message):

    if message.from_user.id != ADMIN_ID:
        return

    link = message.text.split()[1]

    cursor.execute("DELETE FROM inst_links WHERE link=?",(link,))
    db.commit()

    bot.send_message(message.chat.id,"❌ Instagram o‘chirildi")


# YouTube qo‘shish
@bot.message_handler(commands=['addyt'])
def addyt(message):

    if message.from_user.id != ADMIN_ID:
        return

    link = message.text.split()[1]

    cursor.execute("INSERT INTO yt_links VALUES(?)",(link,))
    db.commit()

    bot.send_message(message.chat.id,"▶️ YouTube qo‘shildi")


# YouTube o‘chirish
@bot.message_handler(commands=['delyt'])
def delyt(message):

    if message.from_user.id != ADMIN_ID:
        return

    link = message.text.split()[1]

    cursor.execute("DELETE FROM yt_links WHERE link=?",(link,))
    db.commit()

    bot.send_message(message.chat.id,"❌ YouTube o‘chirildi")


# ADMIN kino qo‘shish
@bot.message_handler(commands=['add'])
def add_movie(message):

    if message.from_user.id != ADMIN_ID:
        return

    msg = bot.send_message(message.chat.id,"🎬 Kino videosini yuboring")
    bot.register_next_step_handler(msg,get_video)


def get_video(message):

    file_id = message.video.file_id

    msg = bot.send_message(message.chat.id,"🎬 Kino nomini yozing")
    bot.register_next_step_handler(msg,get_name,file_id)


def get_name(message,file_id):

    name = message.text

    msg = bot.send_message(message.chat.id,"🔎 Kino kodini yozing")
    bot.register_next_step_handler(msg,save_movie,file_id,name)


def save_movie(message,file_id,name):

    kod = message.text

    cursor.execute(
        "INSERT INTO kinolar VALUES (?,?,?,?)",
        (kod,name,file_id,0)
    )

    db.commit()

    bot.send_message(message.chat.id,"✅ Kino qo‘shildi")


# reklama
@bot.message_handler(commands=['send'])
def send_ads(message):

    if message.from_user.id != ADMIN_ID:
        return

    msg = bot.send_message(message.chat.id,"📢 Reklama yuboring")
    bot.register_next_step_handler(msg,send_users)


def send_users(message):

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    for user in users:

        try:
            bot.send_message(user[0],message.text)
        except:
            pass


# video yuklash
@bot.message_handler(func=lambda m: m.text and ("youtube.com" in m.text or "youtu.be" in m.text or "instagram.com" in m.text or "tiktok.com" in m.text))
def download_video(message):

    url = message.text

    bot.send_message(message.chat.id,"📥 Video yuklanmoqda...")

    try:

        ydl_opts = {'outtmpl':'video.mp4','format':'mp4'}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        with open("video.mp4","rb") as video:
            bot.send_video(message.chat.id,video)

        os.remove("video.mp4")

    except:
        bot.send_message(message.chat.id,"❌ Video yuklab bo‘lmadi")


# kino kodi
@bot.message_handler(func=lambda m: True)
def kino(message):

    not_joined = check_sub(message.from_user.id)

    if not_joined:

        markup = get_markup(not_joined)

        bot.send_message(
            message.chat.id,
            "❗ Avval kanallarga qo‘shiling",
            reply_markup=markup
        )

        return

    text = message.text

    cursor.execute(
        "SELECT kod,name,file_id,views FROM kinolar WHERE kod=?",
        (text,)
    )

    kino = cursor.fetchone()

    if kino:

        kod = kino[0]
        name = kino[1]
        file = kino[2]
        views = kino[3] + 1

        cursor.execute(
            "UPDATE kinolar SET views=? WHERE kod=?",
            (views,kod)
        )

        db.commit()

        caption = f"""
🎬 {name}

🔎 Kino kodi: {kod}

👁 {views} ko‘rish
"""

        bot.send_video(
            message.chat.id,
            file,
            caption=caption,
            protect_content=True
        )

    else:

        bot.send_message(message.chat.id,"❌ Bunday kino topilmadi")


print("BOT ISHLAYAPTI")

bot.infinity_polling()
