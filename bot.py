import os
import json
import requests
import telebot
from threading import Thread
from flask import Flask

# 1. Создаем веб-сервер, чтобы Render не отключал бота
app = Flask('')

@app.route('/')
def home():
    return "Бот успешно работает и принимает порт!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Запускаем веб-сервер параллельно с ботом
Thread(target=run).start()

# 2. Настройка самого Телеграм-бота
# Render автоматически подставит токен из настроек (Environment)
TOKEN = os.environ.get('TELEGRAM_TOKEN') 
bot = telebot.TeleBot(TOKEN)

# ТЕСТОВАЯ КОМАНДА: Проверка работоспособности
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я успешно запущен на сервере Render!")

# Пример обработки любого текстового сообщения
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Вы написали: {message.text}")

# 3. Запуск постоянного опроса Телеграм
if __name__ == "__main__":
    print("Бот запускается...")
    bot.infinity_polling()

