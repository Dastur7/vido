import logging
import json
import os
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# -------------------------------
# Sozlamalar
# -------------------------------
BOT_TOKEN = "8035262125:AAG1CW1co38uBsgP19kg85B1QuwNRbToHKg"  # 👈 Buni o'zgartiring!
ADMIN_ID = 8212861558
API_URL = "https://api.wwiw.uz/downloader?url="

DATA_DIR = "data"
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

os.makedirs(DATA_DIR, exist_ok=True)

# config.json yaratish
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "mandatory_channel": None,
            "channel_id": None
        }, f, indent=2, ensure_ascii=False)

# users.json yaratish
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=2, ensure_ascii=False)

# Xabarlar (3 til)
MESSAGES = {
    "uz": {
        "choose_lang": "Tilni tanlang 👇",
        "lang_set": "✅ Til sozlandi!",
        "not_subscribed": "⚠️ Botdan foydalanish uchun quyidagi kanalga obuna bo'ling:",
        "check_sub": "✅ Obunani tekshirish",
        "send_url": "Ijtimoiy tarmoq havolasini yuboring.",
        "invalid_url": "⚠️ Iltimos, to'g'ri URL yuboring.",
        "processing": "⏳ Qayta ishlanmoqda...",
        "downloaded": "✅ Yuklandi!",
        "error": "❌ Xatolik yuz berdi.",
        "banned": "🚫 Siz botdan foydalana olmaysiz.",
        "admin_only": "Sizga ruxsat yo'q!"
    },
    "en": {
        "choose_lang": "Choose your language 👇",
        "lang_set": "✅ Language set!",
        "not_subscribed": "⚠️ Please subscribe to the channel to use the bot:",
        "check_sub": "✅ Check subscription",
        "send_url": "Send a social media link.",
        "invalid_url": "⚠️ Please send a valid URL.",
        "processing": "⏳ Processing...",
        "downloaded": "✅ Downloaded!",
        "error": "❌ An error occurred.",
        "banned": "🚫 You are banned.",
        "admin_only": "Access denied!"
    },
    "ru": {
        "choose_lang": "Выберите язык 👇",
        "lang_set": "✅ Язык установлен!",
        "not_subscribed": "⚠️ Подпишитесь на канал, чтобы использовать бота:",
        "check_sub": "✅ Проверить подписку",
        "send_url": "Отправьте ссылку из соцсети.",
        "invalid_url": "⚠️ Пожалуйста, отправьте корректную ссылку.",
        "processing": "⏳ Обработка...",
        "downloaded": "✅ Загружено!",
        "error": "❌ Произошла ошибка.",
        "banned": "🚫 Вам запрещено использовать этого бота.",
        "admin_only": "Доступ запрещён!"
    }
}

# -------------------------------
# Yordamchi funksiyalar
# -------------------------------
def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def get_user_lang(user_id):
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
        return users.get(str(user_id), {}).get("lang", "uz")
    except:
        return "uz"

def set_user_lang(user_id, lang):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
    if str(user_id) not in users:
        users[str(user_id)] = {}
    users[str(user_id)]["lang"] = lang
    users[str(user_id)]["first_seen"] = datetime.now().isoformat()
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def is_banned(user_id):
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
        return users.get(str(user_id), {}).get("banned", False)
    except:
        return False

def ban_user(user_id):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
    if str(user_id) not in users:
        users[str(user_id)] = {}
    users[str(user_id)]["banned"] = True
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def unban_user(user_id):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
    if str(user_id) in users:
        users[str(user_id)]["banned"] = False
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

async def check_subscription(bot, user_id, channel_id):
    if not channel_id:
        return True
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# -------------------------------
# /start
# -------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 O'zbek", callback_data="set_lang_uz"),
            InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🌍 Tilni tanlang:", reply_markup=reply_markup)

# -------------------------------
# Tilni sozlash
# -------------------------------
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = query.data.split("_")[-1]

    if lang not in ["uz", "en", "ru"]:
        lang = "uz"

    set_user_lang(user_id, lang)
    await query.message.edit_text(MESSAGES[lang]["lang_set"])

    config = load_config()
    if config.get("channel_id"):
        channel_link = config["mandatory_channel"]
        check_btn = InlineKeyboardMarkup([[InlineKeyboardButton(MESSAGES[lang]["check_sub"], callback_data="check_sub")]])
        await query.message.reply_text(
            f'{MESSAGES[lang]["not_subscribed"]}\n\n{channel_link}',
            reply_markup=check_btn
        )
    else:
        await query.message.reply_text(MESSAGES[lang]["send_url"])

# -------------------------------
# Obunani tekshirish
# -------------------------------
async def check_subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = get_user_lang(user_id)

    config = load_config()
    if await check_subscription(context.bot, user_id, config.get("channel_id")):
        await query.message.edit_text(MESSAGES[lang]["send_url"])
    else:
        channel_link = config["mandatory_channel"]
        check_btn = InlineKeyboardMarkup([[InlineKeyboardButton(MESSAGES[lang]["check_sub"], callback_data="check_sub")]])
        await query.message.edit_text(
            f'{MESSAGES[lang]["not_subscribed"]}\n\n{channel_link}',
            reply_markup=check_btn
        )

# -------------------------------
# Video yuklash
# -------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)

    if is_banned(user_id):
        await update.message.reply_text(MESSAGES[lang]["banned"])
        return

    config = load_config()
    if config.get("channel_id"):
        if not await check_subscription(context.bot, user_id, config["channel_id"]):
            channel_link = config["mandatory_channel"]
            check_btn = InlineKeyboardMarkup([[InlineKeyboardButton(MESSAGES[lang]["check_sub"], callback_data="check_sub")]])
            await update.message.reply_text(
                f'{MESSAGES[lang]["not_subscribed"]}\n\n{channel_link}',
                reply_markup=check_btn
            )
            return

    text = update.message.text.strip() if update.message.text else ""
    if not text.startswith("http"):
        await update.message.reply_text(MESSAGES[lang]["invalid_url"])
        return

    await update.message.reply_text(MESSAGES[lang]["processing"])

    try:
        response = requests.get(f"{API_URL}{text}", timeout=30)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and data.get("status") is True and "data" in 
            video_url = data["data"].get("url")
            if video_url:
                await update.message.reply_text(MESSAGES[lang]["downloaded"])
                await update.message.reply_video(video=video_url)
            else:
                await update.message.reply_text(MESSAGES[lang]["error"])
        else:
            error_msg = data.get("message", MESSAGES[lang]["error"]) if isinstance(data, dict) else MESSAGES[lang]["error"]
            await update.message.reply_text(f"❌ {error_msg}")
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await update.message.reply_text(MESSAGES[lang]["error"])

# -------------------------------
# Admin panel
# -------------------------------
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        lang = get_user_lang(update.effective_user.id)
        await update.message.reply_text(MESSAGES[lang]["admin_only"])
        return

    keyboard = [
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton("📣 Majburiy kanal", callback_data="admin_channel")],
        [InlineKeyboardButton("📤 Xabar yuborish", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔒 Ban / 🔓 Unban", callback_data="admin_ban")],
        [InlineKeyboardButton("❌ Yopish", callback_data="admin_close")]
    ]
    await update.message.reply_text("🔐 Admin panel:", reply_markup=InlineKeyboardMarkup(keyboard))

# -------------------------------
# Admin tugmalar
# -------------------------------
async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return

    data = query.data

    if data == "admin_close":
        await query.message.delete()
    elif data == "admin_stats":
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
        total = len(users)
        banned = sum(1 for u in users.values() if u.get("banned"))
        langs = {"uz": 0, "en": 0, "ru": 0}
        for u in users.values():
            l = u.get("lang", "uz")
            if l in langs:
                langs[l] += 1
        text = (
            f"👥 Jami: {total}\n"
            f"🚫 Banlangan: {banned}\n\n"
            f"🇺🇿 O'zbek: {langs['uz']}\n"
            f"🇬🇧 English: {langs['en']}\n"
            f"🇷🇺 Русский: {langs['ru']}"
        )
        await query.edit_message_text(text)
    elif data == "admin_channel":
        config = load_config()
        current = config.get("mandatory_channel") or "❌ Yo'q"
        await query.edit_message_text(f"Joriy kanal: {current}\n\nKanal linkini yuboring (yoki 'yoq' deb yozing):")
        context.user_data["admin_set_channel"] = True
    elif data == "admin_ban":
        await query.edit_message_text("Foydalanuvchi ID sini yuboring:\n`ban 123` yoki `unban 123`")
        context.user_data["admin_ban_mode"] = True
    elif data == "admin_broadcast":
        await query.edit_message_text("Xabarni yuboring (matn/rasm/video):")
        context.user_data["admin_broadcast"] = True

# -------------------------------
# Admin xabarlarini qayta ishlash
# -------------------------------
async def admin_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = update.message.text or ""

    if context.user_data.get("admin_set_channel"):
        context.user_data["admin_set_channel"] = False
        config = load_config()
        if text.strip().lower() == "yoq":
            config["mandatory_channel"] = None
            config["channel_id"] = None
        else:
            config["mandatory_channel"] = text.strip()
            try:
                chat = await context.bot.get_chat(text.strip())
                config["channel_id"] = chat.id
            except Exception as e:
                logging.error(f"Kanal ID olishda xatolik: {e}")
                config["channel_id"] = None
        save_config(config)
        await update.message.reply_text("✅ Kanal sozlandi!")

    elif context.user_data.get("admin_ban_mode"):
        context.user_data["admin_ban_mode"] = False
        try:
            if text.startswith("ban "):
                uid = int(text.split()[1])
                ban_user(uid)
                await update.message.reply_text(f"✅ {uid} banlandi.")
            elif text.startswith("unban "):
                uid = int(text.split()[1])
                unban_user(uid)
                await update.message.reply_text(f"🔓 {uid} unban qilindi.")
            else:
                await update.message.reply_text("⚠️ `ban 123` yoki `unban 123`")
        except Exception as e:
            logging.error(f"Ban xatosi: {e}")
            await update.message.reply_text("⚠️ ID noto'g'ri.")

    elif context.user_data.get("admin_broadcast"):
        context.user_data["admin_broadcast"] = False
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
        success = 0
        for uid_str in users.keys():
            try:
                if update.message.text:
                    await context.bot.send_message(chat_id=int(uid_str), text=update.message.text)
                elif update.message.photo:
                    await context.bot.send_photo(chat_id=int(uid_str), photo=update.message.photo[-1].file_id, caption=update.message.caption)
                elif update.message.video:
                    await context.bot.send_video(chat_id=int(uid_str), video=update.message.video.file_id, caption=update.message.caption)
                success += 1
            except Exception as e:
                logging.warning(f"Xabar yuborishda xatolik {uid_str}: {e}")
        await update.message.reply_text(f"✅ {success} ta foydalanuvchiga yuborildi.")

# -------------------------------
# Asosiy
# -------------------------------
def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_message))
    app.add_handler(MessageHandler(filters.ALL & filters.ChatType.PRIVATE, admin_message_handler))
    app.add_handler(CallbackQueryHandler(set_language, pattern="^set_lang_"))
    app.add_handler(CallbackQueryHandler(check_subscription_handler, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(admin_button_handler, pattern="^admin_"))

    app.run_polling()

if __name__ == "__main__":
    main()