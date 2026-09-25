import os
import json
import base64
import time
import requests
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8701736168:AAHhfQUelJm-Fl3BCGQmQ55biNdzYP6_EXw")
GROUP_CHAT_ID = int(os.environ.get("GROUP_CHAT_ID", "-1004429028470"))
API_KEY = os.environ.get("API_KEY", "MKR8MCYN7MZ")
BASE_URL = os.environ.get("BASE_URL", "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api")
SUPPORT_LINK = "https://t.me/flpsupport_bot"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False) if BOT_TOKEN else None
headers = {"mauthapi": API_KEY, "Content-Type": "application/json"}
USER_LAST_PURCHASE = {}

def mask_phone_number(phone):
    if not phone: return "Unknown"
    s = str(phone)
    return f"{s[:5]}★★★★★{s[-3:]}" if len(s) > 6 else s

def get_main_menu_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_get_num = telebot.types.KeyboardButton("📱 Get Number")
    btn_support = telebot.types.KeyboardButton("👨‍💻 Customer Support")
    markup.add(btn_get_num, btn_support)
    return markup

if bot:
    @bot.message_handler(commands=['start', 'menu'])
    def send_welcome(message):
        chat_id = message.chat.id
        bot.send_message(chat_id, "👋 হ্যালো! নাম্বার বোটে আপনাকে স্বাগতম।\n\nনাম্বার নিতে নিচের **📱 Get Number** বাটনে চাপুন।", reply_markup=get_main_menu_keyboard())

    @bot.message_handler(func=lambda message: message.text in ["📱 Get Number", "👨‍💻 Customer Support"])
    def handle_text_buttons(message):
        chat_id = message.chat.id
        if message.text == "👨‍💻 Customer Support":
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("💬 Contact Admin", url=SUPPORT_LINK))
            bot.send_message(chat_id, "🤝 সাহায্যের জন্য Admin এর সাথে যোগাযোগ করুন:", reply_markup=markup)
        elif message.text == "📱 Get Number":
            bot.send_message(chat_id, "🔍 সক্রিয় নাম্বার রেঞ্জ খোঁজা হচ্ছে...")
            try:
                response = requests.get(f"{BASE_URL}/console", headers=headers, timeout=20).json()
                if response.get("meta", {}).get("status") == "ok":
                    hits = response.get("data", {}).get("hits", [])
                    unique_ranges = sorted(set(h.get("range") for h in hits if h.get("range")))
                    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                    if unique_ranges:
                        for r_code in unique_ranges:
                            markup.add(telebot.types.InlineKeyboardButton(f"📱 Range: {r_code}", callback_data=f"buy:{r_code}"))
                        bot.send_message(chat_id, "🔥 **বর্তমানে লাইভ থাকা রেঞ্জসমূহ:**\nনিচের যেকোনো একটি রেঞ্জের ওপর ক্লিক করে নাম্বার নিন:", reply_markup=markup, parse_mode="Markdown")
                    else:
                        bot.send_message(chat_id, "ℹ️ এই মুহূর্তে কোনো সক্রিয় রেঞ্জ পাওয়া যায়নি।")
                else:
                    bot.send_message(chat_id, "❌ সার্ভার কনসোল থেকে ডেটা পাওয়া যায়নি।")
            except Exception as e:
                bot.send_message(chat_id, f"⚠️ ত্রুটি ঘটেছে: {str(e)}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("buy:"))
    def process_number_purchase(call):
        bot.answer_callback_query(call.id)
        chat_id = call.message.chat.id
        selected_range = call.data.split(":",1)[1]
        bot.send_message(chat_id, f"⏳ `{selected_range}` রেঞ্জ থেকে নাম্বার বরাদ্দ করা হচ্ছে...", parse_mode="Markdown")
        try:
            response = requests.post(f"{BASE_URL}/getnum", json={"rid": selected_range}, headers=headers, timeout=20).json()
            if response.get("meta", {}).get("status") == "ok":
                data = response.get("data", {})
                full_number = data.get("full_number")
                country = data.get("country")
                order_rid = response.get("rid")
                USER_LAST_PURCHASE[chat_id] = time.time()
                masked = mask_phone_number(full_number)
                try:
                    bot.send_message(GROUP_CHAT_ID, f"📱 **নতুন নাম্বার!**\nRID: `{order_rid}`\nNum: `{masked}`\n🌍 {country}", parse_mode="Markdown")
                except: pass
                markup = telebot.types.InlineKeyboardMarkup()
                markup.add(telebot.types.InlineKeyboardButton("🔄 ওটিপি চেক করুন", callback_data=f"check:{order_rid}:{selected_range}:{full_number}"),
                           telebot.types.InlineKeyboardButton("❌ বাতিল করুন", callback_data=f"cancel:{order_rid}"))
                bot.send_message(chat_id, f"✅ **নাম্বার রেডি!**\n\n📱 `{full_number}`\n🌍 {country}\n🔢 `{selected_range}`\n\nনাম্বারটি বসিয়ে কোড পাঠান, তারপর OTP চেক করুন।", reply_markup=markup, parse_mode="Markdown")
            else:
                bot.send_message(chat_id, f"❌ {response.get('message','এই রেঞ্জে কোনো নাম্বার খালি নেই।')}")
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ সমস্যা: {str(e)}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("check:"))
    def check_otp_callback(call):
        chat_id = call.message.chat.id
        try:
            _, order_rid, selected_range, full_number = call.data.split(":",3)
        except: return
        bot.answer_callback_query(call.id, text="ওটিপি খোঁজা হচ্ছে...")
        try:
            response = requests.get(f"{BASE_URL}/success-otp?rid={order_rid}", headers=headers, timeout=20).json()
            if response.get("meta", {}).get("status") == "ok":
                otps_list = response.get("data", {}).get("otps", [])
                if otps_list:
                    otp_message = otps_list[0].get("message", "No content")
                    data_phone = str(otps_list[0].get("number",""))
                    masked = mask_phone_number(data_phone)
                    try:
                        bot.send_message(GROUP_CHAT_ID, f"🎉 **NEW OTP!**\n📱 `{masked}`\n💬 `{otp_message}`", parse_mode="Markdown")
                    except: pass
                    next_markup = telebot.types.InlineKeyboardMarkup()
                    next_markup.add(telebot.types.InlineKeyboardButton("🔄 Same Range Auto Buy", callback_data=f"buy:{selected_range}"))
                    next_markup.add(telebot.types.InlineKeyboardButton("📱 Change Range", callback_data="change_range_action"))
                    bot.send_message(chat_id, f"🎉 **OTP Message:**\n`{otp_message}`\n\n✅ OTP Received!", reply_markup=next_markup, parse_mode="Markdown")
                else:
                    markup = telebot.types.InlineKeyboardMarkup()
                    markup.add(telebot.types.InlineKeyboardButton("🔄 Try Again", callback_data=f"check:{order_rid}:{selected_range}:{full_number}"),
                               telebot.types.InlineKeyboardButton("❌ বাতিল", callback_data=f"cancel:{order_rid}"))
                    bot.send_message(chat_id, "⏳ OTP এখনো আসেনি। আবার চেষ্টা করুন।", reply_markup=markup)
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ {e}")

    @bot.callback_query_handler(func=lambda call: call.data == "change_range_action")
    def change_range_callback(call):
        chat_id = call.message.chat.id
        if time.time() - USER_LAST_PURCHASE.get(chat_id,0) < 30:
            bot.answer_callback_query(call.id, f"⚠️ 30s পর Change করতে পারবেন", show_alert=True)
            return
        bot.answer_callback_query(call.id)
        call.message.text = "📱 Get Number"
        handle_text_buttons(call.message)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cancel:"))
    def cancel_order_callback(call):
        order_rid = call.data.split(":",1)[1]
        try:
            requests.post(f"{BASE_URL}/cancel", json={"rid": order_rid}, headers=headers, timeout=10)
            bot.answer_callback_query(call.id, text="বাতিল করা হয়েছে।")
            bot.send_message(call.message.chat.id, "❌ অর্ডার বাতিল করা হয়েছে।")
        except:
            bot.send_message(call.message.chat.id, "⚠️ বাতিল করা যায়নি।")

def handler(event, context):
    if event.get('httpMethod') == 'GET':
        return {"statusCode": 200, "body": "Bot running"}
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
