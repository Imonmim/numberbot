import telebot
import requests
import re
import os
import json
import base64
import time

# --- ENV theke nibe, hardcode na ---
BOT_TOKEN = os.environ.get("8772570139:AAEEgKyLBa0NWP2jdNhXD-jc3EkmJqOp9tc")
API_KEY = os.environ.get("MKR8MCYN7MZ")
GROUP_CHAT_ID = int(os.environ.get("GROUP_CHAT_ID", "-1004378025853"))
BASE_URL = os.environ.get("BASE_URL", "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False) if BOT_TOKEN else None
headers = {"mauthapi": API_KEY, "Content-Type": "application/json"}

USER_LAST_PURCHASE = {}
NUMBER_TO_USER = {}

def get_main_menu_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("📱 Get Number"))
    return markup

if bot:

    @bot.message_handler(commands=['start', 'menu'])
    def send_welcome(message):
        bot.send_message(message.chat.id, "👋 হ্যালো! Number নিতে 📱 Get Number চাপুন।", reply_markup=get_main_menu_keyboard())

    # --- 1. Get Number -> Live Range ana ---
    @bot.message_handler(func=lambda m: m.text == "📱 Get Number")
    def handle_get_number(message):
        chat_id = message.chat.id
        bot.send_message(chat_id, "🔍 সক্রিয় Range খোঁজা হচ্ছে...")
        try:
            res = requests.get(f"{BASE_URL}/console", headers=headers, timeout=20).json()
            if res.get("meta", {}).get("status") == "ok":
                hits = res.get("data", {}).get("hits", [])
                unique_ranges = sorted(set(h.get("range") for h in hits if h.get("range")))
                if not unique_ranges:
                    bot.send_message(chat_id, "ℹ️ কোনো live range নেই।")
                    return
                markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                for r_code in unique_ranges:
                    # FIX: : use korlam, _ na
                    markup.add(telebot.types.InlineKeyboardButton(f"📱 Range: {r_code}", callback_data=f"buy:{r_code}"))
                bot.send_message(chat_id, "🔥 **Live Range:**", reply_markup=markup, parse_mode="Markdown")
            else:
                bot.send_message(chat_id, f"❌ API Error: {res}")
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ Error: {e}")

    # --- 2. Range theke Number neya ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith("buy:"))
    def process_number_purchase(call):
        bot.answer_callback_query(call.id)
        chat_id = call.message.chat.id
        selected_range = call.data.split(":",1)[1]
        bot.send_message(chat_id, f"⏳ `{selected_range}` থেকে number নেওয়া হচ্ছে...", parse_mode="Markdown")
        try:
            res = requests.post(f"{BASE_URL}/getnum", json={"rid": selected_range}, headers=headers, timeout=20).json()
            if res.get("meta", {}).get("status") == "ok":
                data = res.get("data", {})
                full_number = str(data.get("full_number"))
                order_rid = res.get("rid") or data.get("rid")

                USER_LAST_PURCHASE[chat_id] = time.time()
                NUMBER_TO_USER[full_number[-8:]] = chat_id # auto OTP er jonno

                markup = telebot.types.InlineKeyboardMarkup()
                # FIX: : diye 4 ta part, jate full_number na vange
                markup.add(telebot.types.InlineKeyboardButton("🔄 OTP চেক", callback_data=f"check:{order_rid}:{selected_range}:{full_number}"))
                markup.add(telebot.types.InlineKeyboardButton("❌ বাতিল", callback_data=f"cancel:{order_rid}"))
                bot.send_message(chat_id, f"✅ **Number Ready!**\n📱 `{full_number}`\n🔢 Range: `{selected_range}`\n\nOTP আসলে auto bot e আসবে।", reply_markup=markup, parse_mode="Markdown")
            else:
                bot.send_message(chat_id, f"❌ {res.get('message','Range খালি')}")
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ {e}")

    # --- 3. Group theke auto OTP bot e ana ---
    @bot.message_handler(func=lambda m: m.chat.id == GROUP_CHAT_ID)
    def group_otp_listener(message):
        text = message.text or message.caption or ""
        nums = re.findall(r'\d{8,15}', text)
        otp_match = re.search(r'\b\d{4,8}\b', text)
        if nums and otp_match:
            for n in nums:
                key = n[-8:]
                if key in NUMBER_TO_USER:
                    try:
                        bot.send_message(NUMBER_TO_USER[key], f"🎉 **AUTO OTP!**\n📱 `{n}`\n🔑 `{otp_match.group(0)}`\n\n`{text}`", parse_mode="Markdown")
                    except: pass

    # --- 4. OTP Khoja (Manual Check) ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith("check:"))
    def check_otp_callback(call):
        chat_id = call.message.chat.id
        try:
            # FIX: : diye split, phone number vange na
            _, order_rid, selected_range, full_number = call.data.split(":", 3)
        except:
            bot.answer_callback_query(call.id, "Data error"); return

        bot.answer_callback_query(call.id, text="OTP খোঁজা হচ্ছে...")
        try:
            res = requests.get(f"{BASE_URL}/success-otp?rid={order_rid}", headers=headers, timeout=20).json()
            if res.get("meta", {}).get("status") == "ok":
                otps = res.get("data", {}).get("otps", [])
                if otps:
                    otp_message = otps[0].get("message")
                    next_markup = telebot.types.InlineKeyboardMarkup()
                    next_markup.add(telebot.types.InlineKeyboardButton("🔄 Same Range Buy", callback_data=f"buy:{selected_range}"))
                    next_markup.add(telebot.types.InlineKeyboardButton("📱 Change Range", callback_data="change_range"))
                    bot.send_message(chat_id, f"🎉 **OTP:**\n`{otp_message}`\n✅ Received!", reply_markup=next_markup, parse_mode="Markdown")
                else:
                    markup = telebot.types.InlineKeyboardMarkup()
                    markup.add(telebot.types.InlineKeyboardButton("🔄 Try Again", callback_data=f"check:{order_rid}:{selected_range}:{full_number}"))
                    bot.send_message(chat_id, "⏳ এখনো OTP আসেনি, group থেকে auto আসবে।", reply_markup=markup)
            else:
                bot.send_message(chat_id, "⏳ Log e data নেই।")
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ {e}")

    # --- 5. Number Change (Range Change) ---
    @bot.callback_query_handler(func=lambda c: c.data == "change_range")
    def change_range_callback(call):
        chat_id = call.message.chat.id
        last = USER_LAST_PURCHASE.get(chat_id, 0)
        if time.time() - last < 30:
            bot.answer_callback_query(call.id, f"⚠️ 30 sec por change korte parben, {int(30-(time.time()-last))}s baki", show_alert=True)
            return
        bot.answer_callback_query(call.id)
        # abar range list dekhao
        call.message.text = "📱 Get Number"
        handle_get_number(call.message)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("cancel:"))
    def cancel_order_callback(call):
        rid = call.data.split(":",1)[1]
        try:
            requests.post(f"{BASE_URL}/cancel", json={"rid": rid}, headers=headers, timeout=10)
            bot.answer_callback_query(call.id, "Cancel Done")
            bot.send_message(call.message.chat.id, "❌ Cancel করা হয়েছে।")
        except: pass

def handler(event, context):
    if event.get('httpMethod') == 'GET':
        return {"statusCode": 200, "body": f"Bot running - Token:{bool(BOT_TOKEN)}"}
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
