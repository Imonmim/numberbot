import telebot
import requests
import re
import os
import json
import base64

BOT_TOKEN = os.environ.get("8772570139:AAEEgKyLBa0NWP2jdNhXD-jc3EkmJqOp9tc")
API_KEY = os.environ.get("MKR8MCYN7MZ")
GROUP_CHAT_ID = int(os.environ.get("GROUP_CHAT_ID", "-1004429028470"))
BASE_URL = os.environ.get("BASE_URL", "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api")

print(f"BOT_TOKEN exists: {bool(BOT_TOKEN)}")

bot = None
if BOT_TOKEN:
    bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

headers = {"mauthapi": API_KEY, "Content-Type": "application/json"}
NUMBER_TO_USER = {}

def get_main_menu_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("📱 Get Number"))
    return markup

# --- Handlers only if bot exists ---
if bot:

    @bot.message_handler(commands=['start', 'menu'])
    def send_welcome(message):
        bot.send_message(message.chat.id, "👋 হ্যালো! নাম্বার নিতে 📱 Get Number চাপুন।", reply_markup=get_main_menu_keyboard())

    @bot.message_handler(func=lambda m: m.text == "📱 Get Number")
    def handle_get_number(message):
        chat_id = message.chat.id
        bot.send_message(chat_id, "🔍 রেঞ্জ খোঁজা হচ্ছে...")
        try:
            res = requests.get(f"{BASE_URL}/console", headers=headers, timeout=15).json()
            if res.get("meta", {}).get("status") == "ok":
                hits = res.get("data", {}).get("hits", [])
                unique_ranges = sorted(set(h.get("range") for h in hits if h.get("range")))
                markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                for r in unique_ranges:
                    markup.add(telebot.types.InlineKeyboardButton(f"📱 {r}", callback_data=f"buy:{r}"))
                bot.send_message(chat_id, "🔥 **Live Range:**", reply_markup=markup, parse_mode="Markdown")
            else:
                bot.send_message(chat_id, "❌ কোনো রেঞ্জ পাওয়া যায়নি।")
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ Error: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("buy:"))
    def process_number_purchase(call):
        bot.answer_callback_query(call.id)
        chat_id = call.message.chat.id
        selected_range = call.data.split(":", 1)[1]
        bot.send_message(chat_id, f"⏳ `{selected_range}` থেকে নাম্বার নেওয়া হচ্ছে...", parse_mode="Markdown")
        try:
            res = requests.post(f"{BASE_URL}/getnum", json={"rid": selected_range}, headers=headers, timeout=15).json()
            if res.get("meta", {}).get("status") == "ok":
                data = res.get("data", {})
                full_number = str(data.get("full_number"))
                country = data.get("country")
                order_rid = res.get("rid") or data.get("rid")
                last_digits = ''.join(filter(str.isdigit, full_number))[-8:]
                NUMBER_TO_USER[last_digits] = chat_id
                NUMBER_TO_USER[full_number] = chat_id
                markup = telebot.types.InlineKeyboardMarkup()
                markup.add(telebot.types.InlineKeyboardButton("🔄 ওটিপি চেক", callback_data=f"check:{order_rid}:{selected_range}:{full_number}"))
                markup.add(telebot.types.InlineKeyboardButton("❌ বাতিল", callback_data=f"cancel:{order_rid}"))
                bot.send_message(chat_id, f"✅ **Number Ready!**\n📱 `{full_number}`\n🌍 {country}\n\n⏳ OTP auto bot e chole asbe...", parse_mode="Markdown", reply_markup=markup)
            else:
                bot.send_message(chat_id, "❌ এই রেঞ্জ খালি।")
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ {e}")

    @bot.message_handler(func=lambda m: str(m.chat.id) == str(GROUP_CHAT_ID) or m.chat.id == GROUP_CHAT_ID)
    def group_otp_listener(message):
        text = message.text or message.caption or ""
        numbers = re.findall(r'\d{8,15}', text)
        otp_match = re.search(r'\b\d{4,8}\b', text)
        if numbers and otp_match:
            otp_code = otp_match.group(0)
            for num in numbers:
                key = num[-8:]
                if key in NUMBER_TO_USER:
                    user_id = NUMBER_TO_USER[key]
                    try:
                        bot.send_message(user_id, f"🎉 **AUTO OTP Received!**\n\n📱 Number: `{num}`\n🔑 **OTP: `{otp_code}`**\n\n📄 Full: `{text}`", parse_mode="Markdown")
                    except: pass

    @bot.callback_query_handler(func=lambda call: call.data.startswith("check:"))
    def check_otp_callback(call):
        chat_id = call.message.chat.id
        try:
            _, order_rid, selected_range, full_number = call.data.split(":", 3)
        except: return
        bot.answer_callback_query(call.id, text="চেক করা হচ্ছে...")
        try:
            res = requests.get(f"{BASE_URL}/success-otp?rid={order_rid}", headers=headers, timeout=15).json()
            if res.get("meta", {}).get("status") == "ok":
                otps = res.get("data", {}).get("otps", [])
                if otps:
                    msg = otps[0].get("message")
                    bot.send_message(chat_id, f"🎉 **OTP:** `{msg}`", parse_mode="Markdown")
                else:
                    bot.send_message(chat_id, "⏳ এখনো OTP আসেনি, group theke auto asbe।")
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cancel:"))
    def cancel_order_callback(call):
        order_rid = call.data.split(":", 1)[1]
        try:
            requests.post(f"{BASE_URL}/cancel", json={"rid": order_rid}, headers=headers, timeout=10)
            bot.answer_callback_query(call.id, text="বাতিল হয়েছে।")
            bot.send_message(call.message.chat.id, "❌ বাতিল করা হয়েছে।")
        except: pass

def handler(event, context):
    if event.get('httpMethod') == 'GET':
        return {"statusCode": 200, "body": f"Bot running - Token OK: {bool(BOT_TOKEN)}"}

    try:
        if not bot:
            print("BOT_TOKEN missing - check env vars")
            return {"statusCode": 200, "body": "BOT_TOKEN missing"}

        body = event.get('body', '')
        if event.get('isBase64Encoded'):
            body = base64.b64decode(body).decode('utf-8')

        if body:
            update_dict = json.loads(body) if isinstance(body, str) else body
            update = telebot.types.Update.de_json(update_dict)
            bot.process_new_updates([update])
        return {"statusCode": 200, "body": "OK"}
    except Exception as e:
        print(f"Handler Error: {e}")
        return {"statusCode": 200, "body": "OK"}
