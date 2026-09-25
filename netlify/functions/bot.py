import os, base64, telebot

BOT_TOKEN = os.environ.get("8772570139:AAEEgKyLBa0NWP2jdNhXD-jc3EkmJqOp9tc")
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

@bot.message_handler(commands=['start'])
def handle_start(m):
    bot.send_message(m.chat.id, "✅ Bot LIVE! /start kaj kortese")

@bot.message_handler(func=lambda m: True)
def handle_all(m):
    bot.send_message(m.chat.id, f"You: {m.text}")

def handler(event, context):
    try:
        if event.get('httpMethod')!= 'POST':
            return {'statusCode': 200, 'body': 'Bot is running'}
        body = event.get('body','')
        if event.get('isBase64Encoded'):
            body = base64.b64decode(body).decode('utf-8')
        update = telebot.types.Update.de_json(body)
        bot.process_new_updates([update])
        return {'statusCode': 200, 'body': 'ok'}
    except Exception as e:
        print(e)
        return {'statusCode': 200, 'body': 'ok'}
