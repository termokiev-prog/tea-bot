import os
import json
import requests
import telebot
import time
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
        # Строго проверяем HTTPS адрес, чтобы исключить ошибку 405
        api_url = "https://openrouter.ai"
        
        response = requests.post(
            url=api_url,
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY.strip()}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://render.com",
                "X-Title": "Telegram Bot"
            },
            data=json.dumps({
                "model": "gryphe/mythomax-l2-13b:free", 
                "messages": [
                    {"role": "user", "content": message.text}
                ]
            }),
            timeout=25
        )
        
        if response.status_code == 405:
            bot.reply_to(message, "Ошибка 405: Сервер OpenRouter отклонил формат запроса. Проверьте правильность вашего API-ключа.")
            return
        elif response.status_code != 200:
            bot.reply_to(message, f"Ошибка OpenRouter (Код {response.status_code}). Ответ: {response.text[:100]}")
            return

        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            ai_text = result['choices']['message']['content']
            bot.reply_to(message, ai_text)
        elif 'error' in result:
            bot.reply_to(message, f"Ошибка от OpenRouter: {result['error'].get('message', 'Неизвестная ошибка')}")
        else:
            bot.reply_to(message, "Сервер ИИ вернул пустой ответ. Проверьте баланс на OpenRouter.")
            
    except Exception as e:
        bot.reply_to(message, f"Ошибка обработки: {str(e)}")

if __name__ == "__main__":
    Thread(target=run).start()
    
    print("Очистка старых подключений Telegram...")
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception as e:
        pass
        
    print("Бот успешно запускается...")
    bot.infinity_polling(skip_pending=True)
