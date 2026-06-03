import os
import telebot
import requests
import json

# Получаем ключи из настроек сервера
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
OPENROUTER_KEY = os.environ.get('OPENROUTER_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def ask_ai(user_message):
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "google/gemini-2.5-flash", # Бесплатная и умная модель ИИ
            "messages": [
                {"role": "system", "content": "Ты полезный ИИ-агент и умный личный ассистент. Отвечай кратко и по делу."},
                {"role": "user", "content": user_message}
            ]
        }
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response.json()['choices']['message']['content']
    except Exception as e:
        return "Извини, возникла ошибка при подключении к ИИ-мозгу."

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я твой личный ИИ-агент. Задай мне любой вопрос!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Показываем статус "печатает...", пока ИИ думает
    bot.send_chat_action(message.chat.id, 'typing')
    ai_response = ask_ai(message.text)
    bot.reply_to(message, ai_response)

print("ИИ-агент успешно запущен!")
bot.infinity_polling()
