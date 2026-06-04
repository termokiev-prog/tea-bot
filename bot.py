import os
import telebot
import requests
from threading import Thread
from flask import Flask

# Создаем веб-сервер заглушку для прохождения проверок портов Render
app = Flask('')

@app.route('/')
def home():
    return "Бот на Gemini онлайн и работает!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Получение токенов (ключ Gemini вставляем в поле OPENROUTER_API_KEY)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_KEY = os.environ.get('OPENROUTER_API_KEY')

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Бот успешно переключен на стабильное API Google Gemini. Задай мне любой вопрос!")

@bot.message_handler(func=lambda message: True)
def ask_ai(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Официальный адрес API Google Gemini 1.5 Flash
    url = f"https://googleapis.com{GEMINI_KEY}"
    headers = {"Content-Type": "application/json"}
    
    data = {
        "contents": [{
            "parts": [{"text": message.text}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=25)
        
        if response.status_code != 200:
            bot.reply_to(message, f"⚠️ Сбой Gemini API (Код {response.status_code}):\n`{response.text[:200]}`", parse_mode="Markdown")
            return
            
        result = response.json()
        
        # Безопасный многоуровневый разбор ответа от Google
        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content'] and len(candidate['content']['parts']) > 0:
                ai_text = candidate['content']['parts'][0]['text']
                
                # Ограничение длины для Telegram
                if len(ai_text) > 4000:
                    ai_text = ai_text[:4000] + "\n\n[Текст обрезан]"
                bot.reply_to(message, ai_text)
                return
                
        bot.reply_to(message, f"⚠️ Не удалось прочитать ответ ИИ. Сырые данные:\n`{str(result)[:200]}`", parse_mode="Markdown")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка соединения или парсинга: {str(e)[:200]}")

if __name__ == "__main__":
    # Запуск веб-сервера в потоке для Render
    print("Запуск веб-сервера Flask...")
    t = Thread(target=run_flask)
    t.start()
    
    print("Бот на Gemini успешно запущен!")
    bot.infinity_polling(skip_pending=True)
