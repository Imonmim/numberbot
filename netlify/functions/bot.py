def handler(event, context):
    # code
import telebot
import requests
import time
import os
import json

# --- Environment Variables ---
BOT_TOKEN = os.environ.get("8772570139:AAEEgKyLBa0NWP2jdNhXD-jc3EkmJqOp9tc")
GROUP_CHAT_ID = int(os.environ.get("GROUP_CHAT_ID", "-1004429028470"))
API_KEY = os.environ.get("MKR8MCYN7MZ")
BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"
SUPPORT_LINK = "https://t.me/flpsupport_bot"

if not BOT_TOKEN or not API_KEY:
    print("ERROR: BOT_TOKEN or API_KEY missing in ENV")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

headers = {
    "mauthapi": API_KEY,
    "Content-Type": "application/json"
}

OTP_PRICE = 0.003
MIN_WITHDRAW = 100.0

# --- Memory Only (Netlify er jonno file save off) ---
USER_BALANCES = {}
PROCESSED_OTPS = set()
USER_LAST_PURCHASE = {}

def mask_phone_number(phone):
    if not phone:
        return "Unknown"
    phone_str = str(phone).strip()
    if len(phone_str) > 7:
        return f"{phone_str[:5]}★★★★★{phone_str[-3:]}"
    return f"{phone_str[:2]}★★★"

def get_main_menu_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("📱 Get Number"), telebot.types.KeyboardButton("💰 Get Balance"))
    markup.add(telebot.types.KeyboardButton("💸 Withdraw"), telebot.types.KeyboardButton("👨‍💻 Customer Support"))
    return markup

def is_user_joined(user_id):
    try:
        member = bot.get_chat_member(GROUP_CHAT_ID, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception as e:
        print(f"Group check error: {e}")
        # Error hole True return korle join bypass hoye jabe, tai False dilam
        return False

def send_join_alert(chat_id):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/flpsmshub"))
    markup.add(telebot.types.InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/gmailbuysellpublicchannel"))
    markup.add(telebot.types.InlineKeyboardButton("🔄 𝖢𝗁𝖾c𝗄 𝖩𝗈𝗂𝗇 (চেক করুন)", callback_data="check_membership"))
    bot.send_message(chat_id, "⚠️ **আপনাকে প্রথমে আমাদের সবগুলো অফিশিয়াল চ্যানেল ও গ্রুপে জয়েন করতে হবে!**\n\nনিচের বাটনগুলো থেকে প্রত্যেকটিতে জয়েন করুন, তারপর **Check Join** বাটনে চাপুন।", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    chat_id = message.chat.id
    if not is_user_joined(chat_id):
        send_join_alert(chat_id)
        return
    USER_BALANCES.setdefault(chat_id, 0.0)
    welcome_text = "👋 হ্যালো! নাম্বার বোটে আপনাকে স্বাগতম।\n\nনাম্বার নিতে নিচের **📱 Get Number** বাটনে চাপুন।"
    bot.send_message(chat_id, welcome_text, reply_markup=get_main_menu_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "check_membership")
def check_membership_callback(call):
    chat_id = call.message.chat.id
    if is_user_joined(chat_id):
        bot.answer_callback_query(call.id, "✅ ধন্যবাদ! আপনি সফলভাবে গ্রুপে জয়েন করেছেন।")
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        USER_BALANCES.setdefault(chat_id, 0.0)
        bot.send_message(chat_id, "👋 হ্যালো! ওটিপি বোটে আপনাকে স্বাগতম।", reply_markup=get_main_menu_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো গ্রুপে জয়েন করেননি!", show_alert=True)

@bot.message_handler(func=lambda message: message.text in ["📱 Get Number", "💰 Get Balance", "💸 Withdraw", "👨‍💻 Customer Support"])
def handle_text_buttons(message):
    chat_id = message.chat.id
    if not is_user_joined(chat_id):
        send_join_alert(chat_id)
        return
    USER_BALANCES.setdefault(chat_id, 0.0)

    if message.text == "💰 Get Balance":
        current_bal = USER_BALANCES[chat_id]
        bot.send_message(chat_id, f"💳 **আপনার বর্তমান ব্যালেন্স:** `{current_bal:.3f}` Tk\n(প্রতি ওটিপি রেট: `{OTP_PRICE}` Tk)", parse_mode="Markdown")

    elif message.text == "👨‍💻 Customer Support":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("💬 Contact Admin", url=SUPPORT_LINK))
        bot.send_message(chat_id, "🤝 যেকোনো সমস্যার জন্য সাপোর্টে যোগাযোগ করুন:", reply_markup=markup)

    elif message.text == "📱 Get Number":
        bot.send_message(chat_id, "🔍 সক্রিয় নাম্বার রেঞ্জ খোঁজা হচ্ছে...")
        url = f"{BASE_URL}/console"
        try:
            response = requests.get(url, headers=headers, timeout=10).json()
            if response.get("meta", {}).get("status") == "ok":
                hits = response.get("data", {}).get("hits", [])
                unique_ranges = sorted(set(hit.get("range") for hit in hits if hit.get("range")))
                markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                if unique_ranges:
                    for r_code in unique_ranges:
                        # FIX: callback data safe korlam
                        markup.add(telebot.types.InlineKeyboardButton(f"📱 Range: {r_code}", callback_data=f"buy:{r_code}"))
                    bot.send_message(chat_id, "🔥 **লাইভ রেঞ্জসমূহ:**", reply_markup=markup, parse_mode="Markdown")
                else:
                    bot.send_message(chat_id, "ℹ️ এই মুহূর্তে কোনো সক্রিয় রেঞ্জ পাওয়া যায়নি।")
            else:
                bot.send_message(chat_id, "❌ সার্ভার থেকে ডেটা পাওয়া যায়নি।")
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ ত্রুটি: {str(e)}")

    elif message.text == "💸 Withdraw":
        current_bal = USER_BALANCES[chat_id]
        if current_bal >= MIN_WITHDRAW:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("বিকাশ", callback_data="w_bkash"), telebot.types.InlineKeyboardButton("নগদ", callback_data="w_nagad"))
            bot.send_message(chat_id, f"🎉 পর্যাপ্ত ব্যালেন্স আছে!\n💰 **ব্যালেন্স:** `{current_bal:.3f}` Tk\nমাধ্যম সিলেক্ট করুন:", reply_markup=markup)
        else:
            bot.send_message(chat_id, f"❌ **ব্যালেন্স পর্যাপ্ত নয়।**\n📌 সর্বনিম্ন: `{MIN_WITHDRAW}` Tk\n💳 আপনার: `{current_bal:.3f}` Tk")

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy:"))
def process_number_purchase(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    selected_range = call.data.split(":", 1)[1]
    bot.send_message(chat_id, f"⏳ `{selected_range}` রেঞ্জ থেকে নাম্বার নেওয়া হচ্ছে...", parse_mode="Markdown")
    url = f"{BASE_URL}/getnum"
    payload = {"rid": selected_range}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10).json()
        if response.get("meta", {}).get("status") == "ok":
            data = response.get("data", {})
            full_number = data.get("full_number")
            country = data.get("country")
            order_rid = response.get("rid") or data.get("rid")
            USER_LAST_PURCHASE[chat_id] = time.time()

            masked_number = mask_phone_number(full_number)
            try:
                bot.send_message(GROUP_CHAT_ID, f"📱 **নতুন নাম্বার:** `{masked_number}`\n🆔 **RID:** `{order_rid}`\n🌍 **দেশ:** {country}", parse_mode="Markdown")
            except: pass

            success_msg = f"✅ **নাম্বার রেডি!**\n\n📱 **নাম্বার:** `{full_number}`\n🌍 **দেশ:** {country}\n🔢 **রেঞ্জ:** `{selected_range}`"
            markup = telebot.types.InlineKeyboardMarkup()
            # FIX: callback e : use korlam, _ na. jate number katbe na
            markup.add(telebot.types.InlineKeyboardButton("🔄 ওটিপি চেক", callback_data=f"check:{order_rid}:{selected_range}:{full_number}"))
            markup.add(telebot.types.InlineKeyboardButton("❌ বাতিল", callback_data=f"cancel:{order_rid}"))
            bot.send_message(chat_id, success_msg, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(chat_id, f"❌ {response.get('message', 'এই রেঞ্জে নাম্বার খালি নেই।')}")
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ সমস্যা: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("check:"))
def check_otp_callback(call):
    chat_id = call.message.chat.id
    try:
        _, order_rid, selected_range, full_number = call.data.split(":", 3)
    except ValueError:
        bot.answer_callback_query(call.id, "Callback data error!")
        return

    bot.answer_callback_query(call.id, text="ওটিপি খোঁজা হচ্ছে...")
    url = f"{BASE_URL}/success-otp?rid={order_rid}"
    try:
        response = requests.get(url, headers=headers, timeout=10).json()
        if response.get("meta", {}).get("status") == "ok":
            otps_list = response.get("data", {}).get("otps", [])
            if otps_list:
                latest_otp = otps_list[0]
                otp_message = latest_otp.get("message", "No content")
                data_phone = str(latest_otp.get("number", "")).strip()
                otp_id = latest_otp.get("otp_id", order_rid)

                clean_data_phone = ''.join(filter(str.isdigit, data_phone))
                clean_full_number = ''.join(filter(str.isdigit, full_number))

                if clean_full_number and clean_data_phone and clean_data_phone[-8:]!= clean_full_number[-8:]:
                    markup = telebot.types.InlineKeyboardMarkup()
                    markup.add(telebot.types.InlineKeyboardButton("🔄 Try Again", callback_data=f"check:{order_rid}:{selected_range}:{full_number}"))
                    bot.send_message(chat_id, "⏳ এই নম্বরের জন্য এখনো কোড আসেনি।", reply_markup=markup)
                    return

                balance_added_text = ""
                if otp_id not in PROCESSED_OTPS:
                    USER_BALANCES[chat_id] = USER_BALANCES.get(chat_id, 0.0) + OTP_PRICE
                    PROCESSED_OTPS.add(otp_id)
                    balance_added_text = f"💰 `+{OTP_PRICE}` Tk যোগ হয়েছে।"
                else:
                    balance_added_text = "ℹ️ এই ওটিপির ব্যালেন্স আগেই যোগ হয়েছে।"

                try:
                    bot.send_message(GROUP_CHAT_ID, f"🎉 **NEW OTP!**\n🆔 `{order_rid}`\n📱 `{mask_phone_number(data_phone)}`\n💬 `{otp_message}`", parse_mode="Markdown")
                except: pass

                otp_success_text = f"🎉 **ওটিপি মেসেজ:**\n`{otp_message}`\n\n✅ **Received!**\n{balance_added_text}\n💳 **মোট:** `{USER_BALANCES.get(chat_id, 0.0):.3f}` Tk"
                next_markup = telebot.types.InlineKeyboardMarkup()
                next_markup.add(telebot.types.InlineKeyboardButton("🔄 Same Range Buy", callback_data=f"buy:{selected_range}"))
                next_markup.add(telebot.types.InlineKeyboardButton("📱 Change Range", callback_data="change_range_action"))
                bot.send_message(chat_id, otp_success_text, parse_mode="Markdown", reply_markup=next_markup)
            else:
                markup = telebot.types.InlineKeyboardMarkup()
                markup.add(telebot.types.InlineKeyboardButton("🔄 Try Again", callback_data=f"check:{order_rid}:{selected_range}:{full_number}"), telebot.types.InlineKeyboardButton("❌ বাতিল", callback_data=f"cancel:{order_rid}"))
                bot.send_message(chat_id, "⏳ ওটিপি এখনো আসেনি।", reply_markup=markup)
        else:
            bot.send_message(chat_id, "⏳ লগে এখনো ডেটা নেই।")
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel:"))
def cancel_order_callback(call):
    order_rid = call.data.split(":", 1)[1]
    url = f"{BASE_URL}/cancel"
    try:
        requests.post(url, json={"rid": order_rid}, headers=headers, timeout=10)
        bot.answer_callback_query(call.id, text="অর্ডার বাতিল হয়েছে।")
        bot.send_message(call.message.chat.id, "❌ অর্ডার বাতিল করা হয়েছে।")
    except:
        bot.send_message(call.message.chat.id, "⚠️ বাতিল করা যায়নি।")

# --- বাকি handler গুলো আগের মতই ---
@bot.callback_query_handler(func=lambda call: call.data in ["w_bkash", "w_nagad"])
def process_withdraw_selection(call):
    chat_id = call.message.chat.id
    method = "বিকাশ" if call.data == "w_bkash" else "নগদ"
    current_bal = USER_BALANCES.get(chat_id, 0.0)
    if current_bal < MIN_WITHDRAW:
        bot.answer_callback_query(call.id, "ব্যালেন্স নেই!", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    USER_BALANCES[chat_id] = 0.0
    bot.send_message(chat_id, f"✅ **উইথড্র রিকোয়েস্ট:** `{current_bal:.3f}` Tk\n🏦 {method}\n🆔 `WD-{chat_id}-{int(time.time())}`")
    try: bot.send_message(GROUP_CHAT_ID, f"🚨 **WITHDRAW**\n👤 `{chat_id}`\n💰 `{current_bal:.3f}` Tk\n💳 {method}", parse_mode="Markdown")
    except: pass

@bot.callback_query_handler(func=lambda call: call.data == "change_range_action")
def change_range_callback(call):
    chat_id = call.message.chat.id
    if time.time() - USER_LAST_PURCHASE.get(chat_id, 0) < 30:
        remaining = int(30 - (time.time() - USER_LAST_PURCHASE.get(chat_id, 0)))
        bot.answer_callback_query(call.id, f"{remaining} sec wait koro", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    call.message.text = "📱 Get Number"
    handle_text_buttons(call.message)

# --- Netlify Handler - FIXED ---
def handler(event, context):
    if event.get('httpMethod') == 'GET':
        return {"statusCode": 200, "body": "Bot is running on Netlify"}
    try:
        body = event.get('body')
        if body:
            # body string hole json load korte hobe
            if isinstance(body, str):
                update_dict = json.loads(body)
            else:
                update_dict = body
            update = telebot.types.Update.de_json(update_dict)
            bot.process_new_updates([update])
        return {"statusCode": 200, "body": "OK"}
    except Exception as e:
        print(f"Handler Error: {e}")
        return {"statusCode": 200, "body": "OK"}
