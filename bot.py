import os
import telebot
from openai import OpenAI

# Получение токенов
TOKEN = os.environ.get('TELEGRAM_TOKEN')
OPENROUTER_KEY = os.environ.get('OPENROUTER_API_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL')

bot = telebot.TeleBot(TOKEN)

# Инициализация ИИ
ai_client = OpenAI(
    base_url="https://openrouter.ai",
    api_key=OPENROUTER_KEY,
)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Проверяем, видит ли бот настройки
    status = (
        "ℹ️ **ДИАГНОСТИКА СЕРВЕРА:**\n"
        f"• Токен Telegram: {'✅ Доступен' if TOKEN else '❌ ОТСУТСТВУЕТ'}\n"
        f"• Ключ OpenRouter: {'✅ Доступен' if OPENROUTER_KEY else '❌ ОТСУТСТВУЕТ'}\n"
        f"• Ссылка на БД: {'✅ Доступна' if DATABASE_URL else '❌ ОТСУТСТВУЕТ (Работа без БД)'}\n\n"
        "Бот запущен в режиме отладки! Напишите мне любой текст."
    )
    bot.reply_to(message, status, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def ask_ai(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        # Делаем тестовый прямой запрос
        completion = ai_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://render.com",
                "X-Title": "Diagnostic Bot",
            },
            model="meta-llama/llama-3-8b-instruct:free",
            messages=[{"role": "user", "content": message.text}],
            timeout=25
        )
        
        # Выводим в чат сырой тип ответа, чтобы понять, что возвращает OpenRouter
        bot.reply_to(message, f"🔬 Тип ответа от API: {type(completion)}")
        
        if hasattr(completion, 'choices'):
            bot.reply_to(message, f"🤖 Ответ ИИ:\n{completion.choices[0].message.content}")
        else:
            bot.reply_to(message, f"⚠️ Нестандартный ответ. Сырые данные:\n{str(completion)}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при отправке запроса: {str(e)}")

if __name__ == "__main__":
    print("Диагностический бот успешно запущен!")
    bot.infinity_polling(skip_pending=True)
