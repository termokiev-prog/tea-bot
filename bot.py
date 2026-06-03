import os
import telebot
from openai import OpenAI
import psycopg2
from psycopg2.extras import DictCursor

# Получение токенов и строки подключения из переменных окружения Railway
TOKEN = os.environ.get('TELEGRAM_TOKEN')
OPENROUTER_KEY = os.environ.get('OPENROUTER_API_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL')  # Railway автоматически предоставляет эту переменную при создании Postgres

# Инициализация бота и AI клиента
bot = telebot.TeleBot(TOKEN)
ai_client = OpenAI(
    base_url="https://openrouter.ai",
    api_key=OPENROUTER_KEY,
)

SYSTEM_PROMPT = {
    "role": "system",
    "content": "Ты — опытный, дружелюбный и лаконичный ИИ-ассистент. Помогаешь программировать, отвечавать на вопросы и собираешь данные для обучения."
}

def init_db():
    """Функция инициализации базы данных. Создает таблицу, если её нет."""
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
    """Сохраняет сообщение в базу данных для вечного хранения и обучения."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO chat_history (user_id, role, content) VALUES (%s, %s, %s)",
                (user_id, role, content)
            )
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка записи в БД: {e}")

def get_context(user_id, limit=15):
    """Получает последние N сообщений пользователя для передачи в LLM."""
    messages = [SYSTEM_PROMPT]
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # Берем последние сообщения, но сортируем их в хронологическом порядке
            cursor.execute("""
                SELECT role, content FROM (
                    SELECT role, content, id FROM chat_history 
                    WHERE user_id = %s 
                    ORDER BY id DESC LIMIT %s
                ) sub ORDER BY id ASC
            """, (user_id, limit))
            rows = cursor.fetchall()
            for row in rows:
                messages.append({"role": row['role'], "content": row['content']})
        conn.close()
    except Exception as e:
        print(f"Ошибка чтения из БД: {e}")
    return messages

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    welcome_text = (
        "Привет! Я запущен на Railway, подключен к базе данных PostgreSQL и готов к работе. 🚀\n\n"
        "🧠 Все наши диалоги записываются базы данных. Это поможет обучить моего будущего агента!\n"
        "🧹 Команда /clear — очистит текущий контекст нашей беседы (но старые логи останутся в базе для обучения)."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['clear'])
def clear_context(message):
    user_id = message.from_user.id
    # Для сохранения истории обучения мы не удаляем строки из БД, 
    # а просто вставляем маркер сброса контекста (опционально) или ничего не делаем.
    # Чтобы очистить контекст для модели, мы можем просто записать системный промпт как новое начало.
    save_message(user_id, "system", "--- Контекст очищен пользователем ---")
    bot.reply_to(message, "Контекст общения сброшен! Новые сообщения начнутся с чистого листа. 🧹")

@bot.message_handler(func=lambda message: True)
def ask_ai(message):
    user_id = message.from_user.id
    
    # 1. Сразу сохраняем сообщение пользователя в БД (оно уже залогировано для обучения)
    save_message(user_id, "user", message.text)
    
    # 2. Собираем контекст из базы данных для текущего запроса к ИИ
    history_context = get_context(user_id, limit=15)

    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # 3. Делаем запрос к нейросети
        completion = ai_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://railway.app",
                "X-Title": "Telegram AI Dataset Bot",
            },
            model="meta-llama/llama-3-8b-instruct:free",
            messages=history_context,
            timeout=25
        )
        
        ai_text = completion.choices.message.content
        
        if ai_text:
            # 4. Сохраняем ответ ИИ в базу данных
            save_message(user_id, "assistant", ai_text)
            
            if len(ai_text) > 4000:
                ai_text = ai_text[:4000] + "\n\n[Текст обрезан из-за лимитов Telegram]"
            bot.reply_to(message, ai_text)
        else:
            bot.reply_to(message, "Нейросеть вернула пустой ответ.")
            
    except Exception as e:
        print(f"Произошла ошибка при запросе к ИИ: {e}")
        bot.reply_to(message, f"Ошибка ИИ: {str(e)}")

if __name__ == "__main__":
    # Инициализируем таблицу в базе данных перед запуском бота
    print("Инициализация базы данных...")
    init_db()
    print("Бот со сбором датасета успешно запущен!")
    bot.infinity_polling(skip_pending=True)
