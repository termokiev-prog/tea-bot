import os
import telebot
from openai import OpenAI

TOKEN = os.environ.get('TELEGRAM_TOKEN')
OPENROUTER_KEY = os.environ.get('OPENROUTER_API_KEY')

bot = telebot.TeleBot(TOKEN)

# Инициализируем клиент со строгим v1 URL
ai_client = OpenAI(
    base_url="https://openrouter.ai",
    api_key=OPENROUTER_KEY,
)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Бот запущен в финальном стабильном режиме. Задай мне любой вопрос!")

@bot.message_handler(func=lambda message: True)
def ask_ai(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        completion = ai_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://render.com",
                "X-Title": "Telegram Bot Stable",
            },
            model="meta-llama/llama-3-8b-instruct:free",
            messages=[{"role": "user", "content": message.text}],
            timeout=25
        )
        
        # Защита от ответов-строк (когда OpenRouter возвращает ошибку в виде текста или HTML)
        if isinstance(completion, str):
            # Обрезаем до 200 символов, чтобы не поймать ошибку HTTP 431 от Telegram
            clean_error = completion[:200]
            bot.reply_to(message, f"⚠️ От API получен текстовый сбой:\n`{clean_error}`", parse_mode="Markdown")
            return

        # Если пришел нормальный объект ответа
        if hasattr(completion, 'choices') and completion.choices:
            ai_text = completion.choices[0].message.content
            bot.reply_to(message, ai_text if ai_text else "Нейросеть прислала пустой ответ.")
        else:
            bot.reply_to(message, "Не удалось распознать структуру ответа OpenRouter.")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка запроса: {str(e)[:200]}")

if __name__ == "__main__":
    print("Бот успешно запущен!")
    bot.infinity_polling(skip_pending=True)
