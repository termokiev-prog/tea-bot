import os
import telebot
from openai import OpenAI

TOKEN = os.environ.get('TELEGRAM_TOKEN')
OPENROUTER_KEY = os.environ.get('OPENROUTER_API_KEY')

bot = telebot.TeleBot(TOKEN)

ai_client = OpenAI(
    base_url="https://openrouter.ai",
    api_key=OPENROUTER_KEY,
)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я запущен на Railway и готов к работе. Задай мне любой вопрос!")

@bot.message_handler(func=lambda message: True)
def ask_ai(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        completion = ai_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://railway.app",
                "X-Title": "Telegram AI Bot",
            },
            model="meta-llama/llama-3-8b-instruct:free",
            messages=[{"role": "user", "content": message.text}],
            timeout=25
        )
        ai_text = completion.choices.message.content
        bot.reply_to(message, ai_text if ai_text else "Нейросеть вернула пустой ответ.")
    except Exception as e:
        bot.reply_to(message, f"Ошибка ИИ: {str(e)}")

if __name__ == "__main__":
    print("Бот успешно запущен!")
    bot.infinity_polling(skip_pending=True)
