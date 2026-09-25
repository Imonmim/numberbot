import telebot
import requests
import re
import os
import json
import base64

BOT_TOKEN = os.environ.get("8772570139:AAEEgKyLBa0NWP2jdNhXD-jc3EkmJqOp9tc")
API_KEY = os.environ.get("MKR8MCYN7MZ")
GROUP_CHAT_ID = int(os.environ.get("GROUP_CHAT_ID", "-1004378025853"))
BASE_URL = os.environ.get("BASE_URL", "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False) if BOT_TOKEN else None
headers = {"mauthapi": API_KEY, "Content-Type": "application/json"}
NUMBER_TO_USER = {}

if bot:

    @bot.message_handler(commands=['start'])
    def start(message):
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton("📱 Get Number"))
        bot.send_message(message.chat.id, "👋 স্বাগতম! Number নিতে 📱 Get Number চাপুন।", reply_markup=markup)

    @bot.message_handler(func=lambda m: m.text == "📱 Get Number")
    def get_number(message):
        chat_id = message.chat.id
        bot.send_message(chat_id, "🔍 Range খোঁজা হচ্ছে...")
        try:
            res = requests.get(f"{BASE_URL}/console", headers=headers, timeout=15).json()
            if res.get("meta", {}).get("status") == "ok":
                hits = res.get("data", {}).get("hits", [])
                ranges = sorted(set(h.get("range") for h in hits if h.get("range")))
                markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                for r in ranges:
                    markup.add(telebot.types.InlineKeyboardButton(f"📱 {r}", callback_data=f"buy:{r}"))
                bot.send_message(chat_id, "🔥 Live Range:", reply_markup=markup, parse_mode="Markdown")
            else:
                bot.send_message(chat_id, "❌ Range পাওয়া যায়নি।")
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ {e}")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("buy:"))
    def buy(call):
        bot.answer_callback_query(call.id)
        chat_id = call.message.chat.id
        rng = call.data.split(":",1)[1]
        bot.send_message(chat_id, f"⏳ {rng} থেকে number নেওয়া হচ্ছে...")
        try:
            res = requests.post(f"{BASE_URL}/getnum", json={"rid": rng}, headers=headers, timeout=15).json()
            if res.get("meta", {}).get("status") == "ok":
                full = str(res.get("data", {}).get("full_number"))
                rid = res.get("rid") or res.get("data", {}).get("rid")
                NUMBER_TO_USER[full[-8:]] = chat_id
                NUMBER_TO_USER[full] = chat_id
                markup = telebot.types.InlineKeyboardMarkup()
                markup.add(telebot.types.InlineKeyboardButton("🔄 OTP Check", callback_data=f"check:{rid}:{rng}:{full}"))
                markup.add(telebot.types.InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{rid}"))
                bot.send_message(chat_id, f"✅ **Number:** `{full}`\n\n⏳ OTP আসলে auto bot e চলে আসবে...", reply_markup=markup, parse_mode="Markdown")
            else:
                bot.send_message(chat_id, "❌ Number খালি নেই।")
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ {e}")

    # Group er OTP auto user ke forward
    @bot.message_handler(func=lambda m: m.chat.id == GROUP_CHAT_ID)
    def group_listener(message):
        text = message.text or message.caption or ""
        nums = re.findall(r'\d{8,15}', text)
        otp = re.search(r'\b\d{4,8}\b', text)
        if nums and otp:
            code = otp.group(0)
            for n in nums:
                key = n[-8:]
                if key in NUMBER_TO_USER:
                    uid = NUMBER_TO_USER[key]
                    try:
                        bot.send_message(uid, f"🎉 **AUTO OTP!**\n📱 `{n}`\n🔑 **OTP: `{code}`**\n\n`{text}`", parse_mode="Markdown")
                    except: pass

    @bot.callback_query_handler(func=lambda c: c.data.startswith("check:"))
    def check(call):
        _, rid, rng, full = call.data.split(":",3)
        bot.answer_callback_query(call.id, text="Checking...")
        try:
            res = requests.get(f"{BASE_URL}/success-otp?rid={rid}", headers=headers, timeout=15).json()
            otps = res.get("data", {}).get("otps", [])
            if otps:
                msg = otps[0].get("message")
                bot.send_message(call.message.chat.id, f"🎉 **OTP:** `{msg}`", parse_mode="Markdown")
            else:
                bot.send_message(call.message.chat.id, "⏳ এখনো আসেনি, group থেকে auto আসবে।")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"⚠️ {e}")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("cancel:"))
    def cancel(call):
        rid = call.data.split(":",1)[1]
        try:
            requests.post(f"{BASE_URL}/cancel", json={"rid": rid}, headers=headers, timeout=10)
            bot.answer_callback_query(call.id, "Cancel Done")
            bot.send_message(call.message.chat.id, "❌ Cancel করা হয়েছে।")
        except: pass

def handler(event, context):
    if event.get('httpMethod') == 'GET':
        return {"statusCode": 200, "body": "Bot running - Only Number"}
    try:
        if not bot: return {"statusCode": 200, "body": "BOT_TOKEN missing"}
        body = event.get('body','')
        if event.get('isBase64Encoded'): body = base64.b64decode(body).decode()
        if body:
            upd = telebot.types.Update.de_json(json.loads(body) if isinstance(body,str) else body)
            bot.process_new_updates([upd])
        return {"statusCode": 200, "body": "OK"}
    except Exception as e:
        print(e); return {"statusCode": 200, "body": "OK"}
