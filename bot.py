import os
import re
import pandas as pd
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан")

# Разрешённые user_id (замени на свой)
ALLOWED_USERS = {
    977069285,
}

def user_allowed(update: Update) -> bool:
    return update.effective_user.id in ALLOWED_USERS

app = Flask(__name__)

EXCEL_URL = "https://github.com/bakaeva2006/haircare_bot/raw/refs/heads/main/data/ingredients.xlsx"
df_points = pd.read_excel(EXCEL_URL, sheet_name="Опорные_точки")
search_words = df_points['english_name'].dropna().tolist() + df_points['russian_name'].dropna().tolist()

def highlight_first_anchor(text: str) -> str:
    text_lower = text.lower()
    for word in search_words:
        word_lower = word.lower().strip()
        pattern = r'\b' + re.escape(word_lower) + r'\b'
        match = re.search(pattern, text_lower)
        if match:
            start, end = match.start(), match.end()
            highlighted = f"**{text[start:end]}**"
            result = text[:start] + highlighted + text[end:]
            return result
    return text

MENU, ANALYZE = range(2)

def get_main_keyboard():
    keyboard = [
        [KeyboardButton("/start"), KeyboardButton("/reset")],
        [KeyboardButton("Проанализировать состав")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_allowed(update):
        await update.message.reply_text("Извините, у вас нет доступа к этому боту.")
        return ConversationHandler.END

    await update.message.reply_text(
        "👋 Привет! Выбери действие:",
        reply_markup=get_main_keyboard()
    )
    return MENU

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_allowed(update):
        await update.message.reply_text("Извините, у вас нет доступа к этому боту.")
        return ConversationHandler.END

    text = update.message.text
    if text == "Проанализировать состав":
        await update.message.reply_text(
            "Отправь мне текст состава средства.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ANALYZE
    elif text == "/reset":
        await update.message.reply_text(
            "Состояние сброшено. Напишите /start для начала.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    elif text == "/start":
        return await start(update, context)
    else:
        await update.message.reply_text("Пожалуйста, выбери опцию из меню.")
        return MENU

async def analyze_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_allowed(update):
        await update.message.reply_text("Извините, у вас нет доступа к этому боту.")
        return ConversationHandler.END

    user_text = update.message.text
    highlighted = highlight_first_anchor(user_text)
    await update.message.reply_text(highlighted, parse_mode="Markdown")

    await update.message.reply_text(
        "Что хочешь сделать дальше?",
        reply_markup=get_main_keyboard()
    )
    return MENU

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_allowed(update):
        await update.message.reply_text("Извините, у вас нет доступа к этому боту.")
        return ConversationHandler.END

    await update.message.reply_text(
        "Состояние сброшено. Напишите /start для начала.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler)],
        ANALYZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, analyze_handler)],
    },
    fallbacks=[
        CommandHandler('start', start),
        CommandHandler('reset', reset)
    ]
)

telegram_app.add_handler(conv_handler)
telegram_app.add_handler(CommandHandler('reset', reset))

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put(update)
    return "ok"

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", "8080"))
    telegram_app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"https://haircare-bot.onrender.com/{BOT_TOKEN}"
    )