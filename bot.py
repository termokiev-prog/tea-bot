import os
import telebot
from openai import OpenAI

# Получение токенов из переменных окружения
TOKEN = os.environ.get('TELEGRAM_TOKEN')
OPENROUTER_KEY = os.environ.get('OPENROUTER_API_KEY')

# Инициализация бота и AI клиента
bot = telebot.TeleBot(TOKEN)
ai_client = OpenAI(
    base_url="https://openrouter.ai",
    api_key=OPENROUTER_KEY,
)

# Системный промпт для задания характера ИИ
SYSTEM_PROMPT = {
    "role": "system",
    "content": "Ты — опытный, дружелюбный и лаконичный ИИ-ассистент. Помогаешь программировать, отвечать на вопросы и даешь точные ответы."
}

# Память бота в оперативной памяти сервера {user_id: [история_сообщений]}
user_contexts = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_contexts[user_id] = [SYSTEM_PROMPT]
    
    welcome_text = (
        "Привет! Бот успешно настроен и работает без ошибок! 🚀\n\n"
        "🧠 Я помню контекст нашей текущей беседы.\n"
        "🧹 Команда /clear — очистить мою память."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['clear'])
def clear_context(message):
    user_id = message.from_user.id
    user_contexts[user_id] = [SYSTEM_PROMPT]
    bot.reply_to(message, "Память очищена! О чем поговорим? 🧹")

@bot.message_handler(func=lambda message: True)
def ask_ai(message):
    user_id = message.from_user.id
    
    # Инициализируем историю, если пользователя еще нет в памяти
    if user_id not in user_contexts:
        user_contexts[user_id] = [SYSTEM_PROMPT]
        
    # Добавляем реплику пользователя
    user_contexts[user_id].append({"role": "user", "content": message.text})
    
    # Ограничиваем историю последними 10 сообщениями
    if len(user_contexts[user_id]) > 11:
        user_contexts[user_id] = [SYSTEM_PROMPT] + user_contexts[user_id][-10:]

    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Запрос к OpenRouter
        completion = ai_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://render.com",
                "X-Title": "Telegram AI Bot Stable",
            },
            model="meta-llama/llama-3-8b-instruct:free",
            messages=user_contexts[user_id],
            timeout=25
        )
        
        # ЖЕСТКАЯ ЗАЩИТА: проверяем, что именно вернул OpenRouter
        ai_text = ""
        if isinstance(completion, str):
            ai_text = completion
        elif hasattr(completion, 'choices') and completion.choices:
            ai_text = completion.choices[0].message.content
        elif isinstance(completion, dict) and 'choices' in completion:
            try:
                ai_text = completion['choices'][0]['message']['content']
            except (KeyError, TypeError, IndexError):
                ai_text = str(completion)
        else:
            ai_text = str(completion)
        
        if ai_text:
            # Сохраняем ответ бота в память
            user_contexts[user_id].append({"role": "assistant", "content": ai_text})
            
            # Обрезаем под лимиты Telegram при необходимости
            if len(ai_text) > 4000:
                ai_text = ai_text[:4000] + "\n\n[Текст обрезан]"
            bot.reply_to(message, ai_text)
        else:
            bot.reply_to(message, "Нейросеть прислала пустой ответ.")
            
    except Exception as e:
        bot.reply_to(message, f"Ошибка ИИ: {str(e)}")
        # Если запрос упал, удаляем последний вопрос пользователя из памяти
        if user_contexts[user_id][-1]["role"] == "user":
            user_contexts[user_id].pop()

if __name__ == "__main__":
    print("Стабильный бот запущен!")
    bot.infinity_polling(skip_pending=True)
