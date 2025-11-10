import os
import re
import pandas as pd
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан")

app = Flask(__name__)

EXCEL_URL = "https://raw.githubusercontent.com/bakaeva2006/haircare_bot/main/data/ingredients.xlsx"
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Проанализировать состав"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Привет! Выбери действие:",
        reply_markup=reply_markup
    )
    return MENU

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Проанализировать состав":
        await update.message.reply_text(
            "Отправь мне текст состава средства.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ANALYZE
    else:
        await update.message.reply_text("Пожалуйста, выбери опцию из меню.")
        return MENU

async def analyze_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    highlighted = highlight_first_anchor(user_text)
    await update.message.reply_text(highlighted, parse_mode="Markdown")
    # После анализа предлагаем вернуться в меню
    keyboard = [["Проанализировать состав"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Что хочешь сделать дальше?",
        reply_markup=reply_markup
    )
    return MENU

telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler)],
        ANALYZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, analyze_handler)]
    },
    fallbacks=[CommandHandler('start', start)]
)

telegram_app.add_handler(conv_handler)

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