import os
import telebot
from openai import OpenAI
import psycopg2
from psycopg2.extras import DictCursor

# Получение токенов и строки подключения из переменных окружения
TOKEN = os.environ.get('TELEGRAM_TOKEN')
OPENROUTER_KEY = os.environ.get('OPENROUTER_API_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL')

# Инициализация бота и AI клиента
bot = telebot.TeleBot(TOKEN)
ai_client = OpenAI(
    base_url="https://openrouter.ai",
    api_key=OPENROUTER_KEY,
)

# Системный промпт для ИИ
SYSTEM_PROMPT = {
    "role": "system",
    "content": "Ты — опытный, дружелюбный и лаконичный ИИ-ассистент. Помогаешь программировать, отвечаешь на вопросы и собираешь данные для обучения."
}

def init_db():
    """Инициализация таблицы в PostgreSQL."""
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_user_id ON chat_history(user_id);
        """)
        conn.commit()
    conn.close()

def save_message(user_id, role, content):
    """Сохранение сообщений в БД для истории и обучения."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO chat_history (user_id, role, content) VALUES (%s, %s, %s)",
                (user_id, role, str(content))
            )
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка записи в БД: {e}")

def get_context(user_id, limit=15):
    """Получение контекста из БД для отправки в LLM."""
    messages = [SYSTEM_PROMPT]
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("""
                SELECT role, content FROM (
                    SELECT role, content, id FROM chat_history 
                    WHERE user_id = %s 
                    ORDER BY id DESC LIMIT %s
                ) sub ORDER BY id ASC
            """, (user_id, limit))
            rows = cursor.fetchall()
            for row in rows:
                if "--- Контекст очищен пользователем ---" not in row['content']:
                    messages.append({"role": row['role'], "content": row['content']})
        conn.close()
    except Exception as e:
        print(f"Ошибка чтения из БД: {e}")
    return messages

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    welcome_text = (
        "Привет! Я запущен и готов к работе. 🚀\n\n"
        "🧠 Все наши диалоги сохраняются в базу данных для обучения будущего агента.\n"
        "🧹 Команда /clear — сбросить текущий контекст беседы."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['clear'])
def clear_context(message):
    user_id = message.from_user.id
    save_message(user_id, "system", "--- Контекст очищен пользователем ---")
    bot.reply_to(message, "Контекст общения сброшен! Начинаем с чистого листа. 🧹")

@bot.message_handler(func=lambda message: True)
def ask_ai(message):
    user_id = message.from_user.id
    
    # 1. Сохраняем входящий запрос в БД
    save_message(user_id, "user", message.text)
    
    # 2. Собираем историю для ИИ
    history_context = get_context(user_id, limit=15)

    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # 3. Запрос к OpenRouter
        completion = ai_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://render.com",
                "X-Title": "Telegram AI Dataset Bot",
            },
            model="meta-llama/llama-3-8b-instruct:free",
            messages=history_context,
            timeout=25
        )
        
        # 4. Безопасный разбор ответа (Защита от 'str' object has no attribute 'choices')
        ai_text = ""
        if isinstance(completion, str):
            ai_text = completion
        elif hasattr(completion, 'choices') and completion.choices:
            ai_text = completion.choices.message.content
        elif isinstance(completion, dict) and 'choices' in completion:
            try:
                ai_text = completion['choices']['message']['content']
            except (KeyError, TypeError):
                ai_text = str(completion)
        else:
            ai_text = str(completion)
        
        # 5. Обработка и отправка результата
        if ai_text:
            save_message(user_id, "assistant", ai_text)
            
            if len(ai_text) > 4000:
                ai_text = ai_text[:4000] + "\n\n[Текст обрезан из-за лимитов Telegram]"
            bot.reply_to(message, ai_text)
        else:
            bot.reply_to(message, "Нейросеть вернула пустой или некорректный ответ.")
            
    except Exception as e:
        error_msg = f"Произошла ошибка при запросе к ИИ: {e}"
        print(error_msg)
        bot.reply_to(message, f"Ошибка ИИ: {str(e)}")

if __name__ == "__main__":
    print("Инициализация базы данных...")
    try:
        init_db()
        print("База данных готова.")
    except Exception as db_err:
        print(f"Критическая ошибка инициализации БД: {db_err}")
        
    print("Бот успешно запущен!")
    bot.infinity_polling(skip_pending=True)
