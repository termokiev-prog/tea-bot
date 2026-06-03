import os
import telebot
import requests

TOKEN = os.environ.get('TELEGRAM_TOKEN')
OPENROUTER_KEY = os.environ.get('OPENROUTER_API_KEY')

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Бот полностью перенастроен через прямые запросы. Задай мне любой вопрос!")

@bot.message_handler(func=lambda message: True)
def ask_ai(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Прямой URL и заголовки для OpenRouter
    url = "https://openrouter.ai"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://render.com",
        "X-Title": "Telegram AI Bot",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "meta-llama/llama-3-8b-instruct:free",
        "messages": [{"role": "user", "content": message.text}]
    }
    
    try:
        # Отправляем прямой POST запрос к API
        response = requests.post(url, headers=headers, json=data, timeout=25)
        
        # Если API вернул ошибку авторизации или лимитов (не 200 OK)
        if response.status_code != 200:
            bot.reply_to(
                message, 
                f"⚠️ Сбой OpenRouter (Код {response.status_code}):\n{response.text[:200]}"
            )
            return
            
        # Корректно разбираем JSON
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            ai_text = result['choices'][0]['message']['content']
            bot.reply_to(message, ai_text)
        else:
            bot.reply_to(message, f"Необычный формат ответа: {str(result)[:200]}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка соединения: {str(e)[:200]}")

if __name__ == "__main__":
    print("Бот на прямых запросах успешно запущен!")
    bot.infinity_polling(skip_pending=True)
