Отлично 💪 — тогда идём с вариантом **Render.com**, это самый удобный и бесплатный способ держать Telegram-бота «в облаке» без постоянного сервера.

Ниже — **подробная, пошаговая инструкция** (тебе нужно просто следовать шагам последовательно).

---

## 🌤 ШАГ 1. Подготовь проект локально

Создай папку на своём компьютере (потом зальём в GitHub):

```
haircare-bot/
│
├── bot.py
├── analyzer.py
├── ocr_utils.py
├── data/
│   └── ingredients.xlsx
├── requirements.txt
├── .env
└── README.md
```

---

## 📦 ШАГ 2. Установи нужные инструменты

1. [Установи Python](https://www.python.org/downloads/) (версия 3.10+).
2. [Установи Git](https://git-scm.com/downloads).
3. [Создай GitHub-аккаунт](https://github.com/).
4. (по желанию) [Установи VS Code](https://code.visualstudio.com/).

---

## 🧰 ШАГ 3. Создай и активируй виртуальное окружение

В терминале в папке проекта:

```bash
python -m venv venv
```

Активируй:

* Windows:

  ```bash
  venv\Scripts\activate
  ```
* macOS/Linux:

  ```bash
  source venv/bin/activate
  ```

---

## 📄 ШАГ 4. Создай файл зависимостей `requirements.txt`

Скопируй в него:

```
python-telegram-bot==21.0
pandas
openpyxl
pytesseract
Pillow
opencv-python
flask
```

Установи пакеты:

```bash
pip install -r requirements.txt
```

---

## 🤖 ШАГ 5. Создай Telegram-бота

1. В Telegram открой **@BotFather**.
2. Напиши `/newbot`.
3. Задай имя и username (например, `HaircareBot`).
4. Скопируй **токен**, который он выдаст.
5. Создай файл `.env` в корне проекта:

```
BOT_TOKEN=1234567890:ABCDefGhijkLmNoPqRstUvWxYz
```

---

## 🧠 ШАГ 6. Создай файл `bot.py`

```python
import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

app = Flask(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет 👋 Отправь мне состав или фото этикетки — я проанализирую его!")

telegram_app = ApplicationBuilder().token(TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put(update)
    return "ok"

if __name__ == "__main__":
    telegram_app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"https://your-app-name.onrender.com/{TOKEN}"
    )
```

> ⚠️ Заменишь `your-app-name` на настоящее имя проекта после деплоя.

---

## 🧭 ШАГ 7. Залей проект в GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/твое_имя/haircare-bot.git
git push -u origin main
```

Добавь `.gitignore`:

```
venv/
__pycache__/
.env
*.xlsx
```

---

## ☁️ ШАГ 8. Деплой на Render

1. Зайди на [Render.com](https://render.com).
2. Авторизуйся через GitHub.
3. Нажми **New → Web Service**.
4. Выбери свой репозиторий `haircare-bot`.
5. Укажи:

   * **Environment:** `Python 3`
   * **Build Command:**

     ```
     pip install -r requirements.txt
     ```
   * **Start Command:**

     ```
     python bot.py
     ```
6. В разделе **Environment Variables** добавь:

   ```
   BOT_TOKEN = твой_токен
   ```
7. Нажми **Deploy**.

Render соберёт проект (1–2 минуты).

---

## 🔗 ШАГ 9. Настрой Webhook в Telegram

Когда Render задеплоит проект, ты получишь ссылку:

```
https://haircare-bot.onrender.com
```

Теперь в терминале (локально) выполни команду:

```bash
curl -F "url=https://haircare-bot.onrender.com/ТВОЙ_ТОКЕН" \
https://api.telegram.org/botТВОЙ_ТОКЕН/setWebhook
```

Если всё ок, Telegram ответит:

```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

Теперь бот **активен** и работает полностью из облака.

---

## 💤 ШАГ 10. Поведение при неактивности

* Render автоматически «засыпает» через ~15 минут без запросов.
* Когда пользователь снова напишет в Telegram → бот «просыпается» и отвечает.
* Никаких постоянных запусков или ПК не нужно.

---

## 🧾 ШАГ 11. Проверка

1. В Telegram открой своего бота.
2. Введи `/start`.
3. Должен ответить:
   *«Привет 👋 Отправь мне состав или фото этикетки…»*

---

## 🧩 Следующие шаги (после проверки запуска)

➡️ Добавим:

* `ocr_utils.py` — распознавание текста с фото (через `pytesseract`);
* `analyzer.py` — сверка состава с Excel-базой;
* красивый вывод анализа пользователю.

---

Хочешь, чтобы я сейчас написал **следующую часть** — `ocr_utils.py` и `analyzer.py`, уже совместимую с Render и твоей Excel-базой?
