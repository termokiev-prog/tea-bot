import os
import json
import requests
import telebot
from threading import Thread
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "Бот с ИИ успешно работает!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

TOKEN = os.environ.get('TELEGRAM_TOKEN')
# Проверяем оба варианта имени ключа на всякий случай
OPENROUTER_KEY = os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENROUTER_KEY')

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Задай мне любой вопрос!")

@bot.message_handler(func=lambda message: True)
def ask_ai(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
    if not OPENROUTER_KEY:
        bot.reply_to(message, "Ошибка: В Render не добавлен ключ OPENROUTER_API_KEY")
        return

    try:
        response = requests.post(
            url="https://openrouter.ai",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "google/gemma-2-9b-it:free",
                "messages": [
                    {"role": "user", "content": message.text}
                ]
            }),
            timeout=20
        )
        
        result = response.json()
        
        # Защита от ошибок в ответе ИИ
        if 'choices' in result and len(result['choices']) > 0:
            ai_text = result['choices'][0]['message']['content']
            bot.reply_to(message, ai_text)
        elif 'error' in result:
            bot.reply_to(message, f"Ошибка от OpenRouter: {result['error'].get('message', 'Неизвестная ошибка')}")
        else:
            bot.reply_to(message, f"Неверный ответ сервера ИИ. Проверьте баланс аккаунта OpenRouter.")
            
    except Exception as e:
        bot.reply_to(message, f"Ошибка соединения: {str(e)}")

if __name__ == "__main__":
    Thread(target=run).start()
    bot.infinity_polling()
