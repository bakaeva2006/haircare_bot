import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Получаем токен из переменных окружения Render
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Проверим, что токен найден
if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN. Добавь его в Environment Variables на Render.")

# Создаём экземпляр приложения Telegram
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я HairGeniusBot.\nОтправь мне состав или фото этикетки — я помогу его проанализировать.")

# Добавляем обработчик в приложение
app.add_handler(CommandHandler("start", start))

# Запуск приложения
if __name__ == "__main__":
    app.run_polling()