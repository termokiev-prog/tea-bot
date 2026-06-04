import os
import telebot
from flask import Flask
from threading import Thread
from google import genai

# 1. Настройка Flask-сервера
app = Flask('')

@app.route('/')
def home():
    return "Бот онлайн!"

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    # Принудительно берем порт, который требует Render
    port = int(os.environ.get("PORT", 10000))
    print(f"Запуск Flask на порту {port}...")
    app.run(host='0.0.0.0', port=port)

# 2. Инициализация Gemini и Telegram
TOKEN = os.environ.get('TELEGRAM_TOKEN')
gemini_client = genai.Client() # Автоматически подхватит GEMINI_API_KEY

bot = telebot.TeleBot(TOKEN)

# 3. Логика Telegram-бота
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Бот успешно запущен на стабильном API Google Gemini. Задай мне любой вопрос!")

@bot.message_handler(func=lambda message: True)
def ask_ai(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=message.text,
        )
        if response.text:
            ai_text = response.text
            if len(ai_text) > 4000:
                ai_text = ai_text[:4000] + "\n\n[Текст обрезан из-за лимитов]"
            bot.reply_to(message, ai_text)
        else:
            bot.reply_to(message, "⚠️ ИИ вернул пустой ответ.")
    except Exception as e:
        print(f"Ошибка Gemini: {e}")
        bot.reply_to(message, f"❌ Ошибка: {str(e)[:200]}")

def run_bot():
    print("Запуск Telegram-бота...")
    bot.infinity_polling(skip_pending=True)

# 4. Точка входа
if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    bot_thread = Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Главным процессом пускаем Flask, чтобы Render СРАЗУ видел открытый порт
    run_flask()
