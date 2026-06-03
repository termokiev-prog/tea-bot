import os
import json
import requests
import telebot
from threading import Thread
from flask import Flask

# 1. Настройка веб-сервера для Render
app = Flask('')

@app.route('/')
def home():
    return "Бот с ИИ успешно работает!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


# 2. Настройка Телеграм-бота и ключей
TOKEN = os.environ.get('TELEGRAM_TOKEN')
OPENROUTER_KEY = os.environ.get('OPENROUTER_API_KEY')

bot = telebot.TeleBot(TOKEN)

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я твой ИИ-помощник. Задай мне любой вопрос или попроси что-то посчитать!")

# Отправка запроса в искусственный интеллект OpenRouter
@bot.message_handler(func=lambda message: True)
def ask_ai(message):
    # Отправляем пользователю статус, что бот думает
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        response = requests.post(
            url="https://openrouter.ai",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "google/gemma-2-9b-it:free", # Используем бесплатную и быструю модель ИИ
                "messages": [
                    {"role": "user", "content": message.text}
                ]
            })
        )
        
        # Разбираем ответ от нейросети
        result = response.json()
        ai_text = result['choices'][0]['message']['content']
        bot.reply_to(message, ai_text)
        
    except Exception as e:
        print(f"Ошибка ИИ: {e}")
        bot.reply_to(message, "Извини, возникла ошибка при подключении к ИИ-мозгу. Попробуй еще раз чуть позже.")


# 3. Запуск сервера и бота
if __name__ == "__main__":
    print("Запуск веб-сервера...")
    Thread(target=run).start()
    
    print("Бот запускается...")
    bot.infinity_polling()
