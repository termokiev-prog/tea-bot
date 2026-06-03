import os
import time
import telebot
from threading import Thread
from flask import Flask
from openai import OpenAI

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

# Инициализируем официальный клиент для OpenRouter
ai_client = OpenAI(
    base_url="https://openrouter.ai",
    api_key=OPENROUTER_KEY,
)

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
        # Отправляем запрос через официальную библиотеку
        completion = ai_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://render.com",
                "X-Title": "Telegram Bot",
            },
            model="meta-llama/llama-3-8b-instruct:free",
            messages=[
                {"role": "user", "content": message.text}
            ],
            timeout=25
        )
        
        ai_text = completion.choices[0].message.content
        if ai_text:
            bot.reply_to(message, ai_text)
        else:
            bot.reply_to(message, "Нейросеть вернула пустой ответ. Проверьте настройки аккаунта.")
            
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Incorrect API key" in error_msg:
            bot.reply_to(message, "Ошибка: Неверный API-ключ OpenRouter. Перепроверьте его в Render.")
        elif "403" in error_msg:
            bot.reply_to(message, "Ошибка 403: Доступ ограничен. Возможно, нужен VPN или пополнение баланса OpenRouter.")
        else:
            bot.reply_to(message, f"Ошибка ИИ: {error_msg}")

if __name__ == "__main__":
    Thread(target=run).start()
    
    try:
        bot.remove_webhook()
        time.sleep(1)
    except:
        pass
        
    bot.infinity_polling(skip_pending=True)
