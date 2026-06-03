import os
import telebot
import requests
from threading import Thread
from flask import Flask

# Настройка Flask-заглушки для Render
app = Flask('')

@app.route('/')
def home():
    return "Бот работает!"

def run_flask():
    # Render автоматически передает нужный порт в переменную PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Инициализация Telegram-бота
TOKEN = os.environ.get('TELEGRAM_TOKEN')
OPENROUTER_KEY = os.environ.get('OPENROUTER_API_KEY')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Бот запущен с обходом проверки портов. Задай мне любой вопрос!")

@bot.message_handler(func=lambda message: True)
def ask_ai(message):
    bot.send_chat_action(message.chat.id, 'typing')
    url = "https://openrouter.ai"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://render.com",
        "X-Title": "Telegram AI Bot",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/llama-3-8b-instruct:free",
        "messages": [{"role": "user", "content": message.text}]
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=25)
        if response.status_code != 200:
            bot.reply_to(message, f"⚠️ Сбой OpenRouter (Код {response.status_code}):\n`{response.text[:200]}`", parse_mode="Markdown")
            return
        
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            ai_text = result['choices'][0]['message']['content']  # Исправлен индекс [0]
            bot.reply_to(message, ai_text)
        else:
            bot.reply_to(message, f"Необычный формат ответа: {str(result)[:200]}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка соединения или парсинга: {str(e)[:200]}")

if __name__ == "__main__":
    # Запускаем веб-сервер в отдельном потоке для прохождения проверок Render
    print("Запуск веб-сервера заглушки...")
    t = Thread(target=run_flask)
    t.start()
    
    print("Бот на прямых запросах успешно запущен!")
    bot.infinity_polling(skip_pending=True)
