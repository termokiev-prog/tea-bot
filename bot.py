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
    return "Бот успешно работает и принимает порт!"

def run():
    # Получаем порт от Render или используем 10000 по умолчанию
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


# 2. Настройка самого Телеграм-бота
TOKEN = os.environ.get('TELEGRAM_TOKEN') 
bot = telebot.TeleBot(TOKEN)

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я успешно запущен на сервере Render!")

# Обработка любого текстового сообщения
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Вы написали: {message.text}")


# 3. Правильный запуск: сначала сервер, потом бот
if __name__ == "__main__":
    print("Запуск веб-сервера для Render...")
    Thread(target=run).start()
    
    print("Бот успешно запускается...")
    bot.infinity_polling()
