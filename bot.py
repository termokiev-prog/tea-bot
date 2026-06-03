@bot.message_handler(func=lambda message: True)
def ask_ai(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
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
        response = requests.post(url, headers=headers, json=data, timeout=25)
        
        # ЕСЛИ ОШИБКА: Сначала проверяем статус-код от OpenRouter
        if response.status_code != 200:
            bot.reply_to(
                message, 
                f"⚠️ Сбой OpenRouter (Код {response.status_code}):\n`{response.text[:200]}`",
                parse_mode="Markdown"
            )
            return
            
        # Пытаемся безопасно прочитать JSON
        try:
            result = response.json()
        except Exception:
            bot.reply_to(message, f"❌ Ошибка: API вернул не JSON. Ответ:\n`{response.text[:200]}`", parse_mode="Markdown")
            return

        if 'choices' in result and len(result['choices']) > 0:
            ai_text = result['choices'][0]['message']['content']  # Добавлен индекс [0]
            bot.reply_to(message, ai_text)
        else:
            bot.reply_to(message, f"Необычный формат ответа: {str(result)[:200]}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка соединения: {str(e)[:200]}")
