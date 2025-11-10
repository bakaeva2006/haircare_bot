import os
import logging
import sys
import asyncio
import httpx
import pandas as pd
import re
import nest_asyncio
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан")

# Прямая ссылка на raw Excel файл на GitHub (без редиректов)
EXCEL_URL = "https://raw.githubusercontent.com/bakaeva2006/haircare_bot/main/data/ingredients.xlsx"

# Разрешённые пользователи
ALLOWED_USERS = {977069285}

# Загрузка Excel с опорными точками
def load_reference_points():
    logger.info("Скачиваем Excel с GitHub...")
    try:
        with httpx.Client() as client:
            response = client.get(EXCEL_URL)
            response.raise_for_status()
            excel_bytes = BytesIO(response.content)
            df = pd.read_excel(excel_bytes, sheet_name="Опорные_точки")
        logger.info("Excel загружен успешно")
        return df
    except Exception as e:
        logger.error(f"Ошибка загрузки Excel: {e}")
        return None

df_points = load_reference_points()

# Формируем словарь для поиска опорных точек
points_dict = {}
if df_points is not None:
    for _, row in df_points.iterrows():
        eng = str(row['english_name']).strip()
        rus = str(row['russian_name']).strip()
        desc = str(row['description']).strip()
        points_dict[eng.lower()] = {"russian_name": rus, "description": desc}
        points_dict[rus.lower()] = {"russian_name": rus, "description": desc}

# FSM состояния
STATE_WAITING_FOR_COMPOSITION = "waiting_for_composition"
STATE_IDLE = "idle"

# Хранилище состояний пользователей
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("Извините, доступ к боту закрыт.")
        return

    user_states[user_id] = STATE_IDLE
    keyboard = [
        [InlineKeyboardButton("Проанализировать состав", callback_data="analyze")],
        [InlineKeyboardButton("Сбросить", callback_data="reset")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Привет! Я HairGeniusBot.\nВыбери действие:",
        reply_markup=reply_markup,
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id not in ALLOWED_USERS:
        await query.edit_message_text("Извините, доступ к боту закрыт.")
        return

    if query.data == "analyze":
        user_states[user_id] = STATE_WAITING_FOR_COMPOSITION
        await query.edit_message_text("Пожалуйста, пришлите текст состава средства.")
    elif query.data == "reset":
        user_states[user_id] = STATE_IDLE
        await query.edit_message_text("Состояние сброшено. Выберите действие командой /start")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("Извините, доступ к боту закрыт.")
        return

    state = user_states.get(user_id, STATE_IDLE)
    if state != STATE_WAITING_FOR_COMPOSITION:
        await update.message.reply_text("Пожалуйста, выберите действие командой /start")
        return

    composition_text = update.message.text.lower()

    first_found = None
    first_pos = len(composition_text) + 1
    for key in points_dict.keys():
        pos = composition_text.find(key)
        if pos != -1 and pos < first_pos:
            first_pos = pos
            first_found = key

    if first_found:
        point_info = points_dict[first_found]
        highlighted = f"*{point_info['russian_name']}*"
        pattern = re.compile(re.escape(first_found), re.IGNORECASE)
        result_text = pattern.sub(highlighted, update.message.text, count=1)

        await update.message.reply_text(
            f"Опорная точка:\n{result_text}\n\nОписание: {point_info['description']}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("Опорные точки в составе не найдены.")

    user_states[user_id] = STATE_IDLE

async def unknown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Неизвестная команда. Пожалуйста, используйте /start.")

async def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_handler))

    logger.info("Запуск бота...")
    await application.run_polling()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    nest_asyncio.apply()
    asyncio.run(main())