import os
from threading import Thread
import telebot
from flask import Flask
from google import genai
from google.genai import types

# 1. Создаем веб-сервер заглушку для Render
app = Flask('')

@app.route('/')
def home():
    return "Бот на Gemini онлайн и работает!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. Инициализация токенов и клиентов
TOKEN = os.environ.get('TELEGRAM_TOKEN')
# Официальный SDK автоматически ищет переменную GEMINI_API_KEY
gemini_client = genai.Client() 

bot = telebot.TeleBot(TOKEN)

# 3. Обработчики команд Telegram
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message, 
        "Привет! Бот успешно запущен на стабильном API Google Gemini. Задай мне любой вопрос!"
    )

@bot.message_handler(func=lambda message: True)
def ask_ai(message):
    # Показываем пользователю, что бот "печатает"
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Запрос к актуальной модели Gemini 2.5 Flash через официальный SDK
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=message.text,
        )
        
        # Проверяем, что ответ вообще пришел
        if response.text:
            ai_text = response.text
            
            # Защита от лимитов Telegram (макс. 4096 символов)
            if len(ai_text) > 4000:
                ai_text = ai_text[:4000] + "\n\n[Текст обрезан из-за лимитов Telegram]"
                
            bot.reply_to(message, ai_text)
        else:
            bot.reply_to(message, "⚠️ Ошибка: ИИ вернул пустой ответ (возможно, сработали фильтры безопасности).")
            
    except Exception as e:
        # Логируем ошибку, чтобы ты видел её в консоли Render
        print(f"Ошибка при запросе к Gemini: {e}")
        bot.reply_to(message, f"❌ Произошла ошибка при обращении к Gemini: {str(e)[:200]}")

# 4. Точка входа для запуска
if __name__ == "__main__":
    print("Запуск веб-сервера Flask для Render...")
    t = Thread(target=run_flask)
    t.start()
    
    print("Бот на Gemini успешно запущен!")
    bot.infinity_polling(skip_pending=True)
