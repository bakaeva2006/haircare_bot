import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан")

app = Flask(__name__)

# Создаём Telegram-приложение
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я HairGeniusBot.\nОтправь мне состав или фото этикетки — я помогу проанализировать его.")

telegram_app.add_handler(CommandHandler("start", start))

# Роут для приема POST запросов от Telegram (Webhook)
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put(update)
    return "ok"

if __name__ == "__main__":
    # Запускаем Flask с webhook
    PORT = int(os.environ.get("PORT", "8080"))
    telegram_app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"https://haircare-bot.onrender.com/{BOT_TOKEN}"
    )