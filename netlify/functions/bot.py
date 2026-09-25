import telebot
import requests
import time
import threading

# --- কনফিগারেশন ---
BOT_TOKEN = "8772570139:AAEqmJPmYrV3BQtiRMAqAKxDYdMQ-kT3Qgc"  # আপনার বট টোকেন
GROUP_CHAT_ID = -1004429028470          # আপনার টেলিগ্রাম সুপারগ্রুপ আইডি (মাইনাসসহ)
API_KEY = "MKR8MCYN7MZ"                 # আপনার লাইভ এপিআই কি
BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"

SUPPORT_LINK = "https://t.me/flpsupport_bot" # আপনার সাপোর্ট লিঙ্ক

bot = telebot.TeleBot(BOT_TOKEN)

# রিকোয়েস্ট পাঠানোর হেডার
headers = {
    "mauthapi": API_KEY,
    "Content-Type": "application/json"
}

# প্রতিটি ওটিপি/মেসেজ রিসিভের প্রাইস
OTP_PRICE = 0.003  

# মেমরিতে ডেটা রাখার জন্য ডিকশনারি
USER_BALANCES = {}
PROCESSED_OTPS = set()
USER_LAST_PURCHASE = {}

# ডুপ্লিকেট মেসেজ আটকানোর ট্র্যাকার (অটো চেকারের জন্য)
sent_otp_ids = set()
sent_console_ids = set()

# নাম্বারের মাঝখানের অংশ হাইড করার ফাংশন
def mask_phone_number(phone):
    if not phone or phone == "Unknown": return "Unknown"
    phone_str = str(phone)
    return f"{phone_str[:5]}★★★★★{phone_str[-3:]}" if len(phone_str) > 6 else f"{phone_str[:2]}★★★★★{phone_str[-2:]}"

def get_main_menu_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_get_num = telebot.types.KeyboardButton("📱 Get Number")
    btn_balance = telebot.types.KeyboardButton("💰 Get Balance")
    btn_support = telebot.types.KeyboardButton("👨‍💻 Customer Support")
    markup.add(btn_get_num, btn_balance)
    markup.add(btn_support)
    return markup


# --- ১. ব্যাকগ্রাউন্ড অটো চেকার ---
def auto_checker():
    print("🔄 কনসোল এবং ওটিপি ব্যাকগ্রাউন্ড ডিটেক্টর চালু হয়েছে...")
    while True:
        try:
            # === ক. ওটিপি লগ চেক ===
            otp_resp = requests.get(f"{BASE_URL}/success-otp", headers=headers, timeout=10).json()
            if otp_resp.get("meta", {}).get("status") == "ok":
                for otp_data in otp_resp.get("data", {}).get("otps", []):
                    oid = otp_data.get("otp_id") or otp_data.get("message")
                    if oid and oid not in sent_otp_ids:
                        masked_num = mask_phone_number(otp_data.get('number'))
                        msg = (f"⚡ **[AUTO SUCCESS] NEW OTP** ⚡\n"
                               f"━━━━━━━━━━━━━━━━━━━\n"
                               f"🆔 **RID:** `{otp_resp.get('rid', 'N/A')}`\n"
                               f"📱 **নম্বর:** `{masked_num}`\n\n"
                               f"💬 **MESSAGE:**\n`{otp_data.get('message')}`\n"
                               f"━━━━━━━━━━━━━━━━━━━")
                        try:
                            bot.send_message(GROUP_CHAT_ID, msg, parse_mode="Markdown")
                        except:
                            pass
                        sent_otp_ids.add(oid)

            # === খ. কনসোল লগ চেক ===
            console_resp = requests.get(f"{BASE_URL}/console", headers=headers, timeout=10).json()
            if console_resp.get("meta", {}).get("status") == "ok":
                for hit in console_resp.get("data", {}).get("hits", []):
                    console_id = str(hit.get("time"))
                    if console_id and console_id not in sent_console_ids:
                        c_number = hit.get("number", "Unknown")
                        c_message = hit.get("message", "No message content in console")
                        masked_c_num = mask_phone_number(c_number)
                        
                        msg = (f"🖥️ **[CONSOLE LOG] NEW UPDATE**\n"
                               f"━━━━━━━━━━━━━━━━━━━\n"
                               f"📱 **Range:** `{hit.get('range')}`\n"
                               f"📞 **নম্বর:** `{masked_c_num}`\n"
                               f"🌍 **দেশ:** {hit.get('country')}\n\n"
                               f"💬 **CONSOLE MESSAGE:**\n`{c_message}`\n"
                               f"━━━━━━━━━━━━━━━━━━━")
                        try:
                            bot.send_message(GROUP_CHAT_ID, msg, parse_mode="Markdown")
                        except:
                            pass
                        sent_console_ids.add(console_id)

        except Exception as e:
            print(f"❌ অটো চেকার এরর: {e}")
            
        time.sleep(8)


# --- ২. টেলিগ্রাম বট হ্যান্ডলারসমূহ ---
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id not in USER_BALANCES:
        USER_BALANCES[chat_id] = 0.0
        
    welcome_text = "👋 হ্যালো! নাম্বার বোটে আপনাকে স্বাগতম।\n\nনাম্বার নিতে নিচের **📱 Get Number** বাটনে চাপুন।"
    bot.send_message(chat_id, welcome_text, reply_markup=get_main_menu_keyboard())


@bot.message_handler(func=lambda message: message.text in ["📱 Get Number", "💰 Get Balance", "👨‍💻 Customer Support"])
def handle_text_buttons(message):
    chat_id = message.chat.id
    if chat_id not in USER_BALANCES:
        USER_BALANCES[chat_id] = 0.0

    if message.text == "💰 Get Balance":
        current_bal = USER_BALANCES[chat_id]
        bot.send_message(chat_id, f"💳 **আপনার বর্তমান ব্যালেন্স:** `{current_bal:.3f}` Tk\n(প্রতি ওটিপি/মেসেজ রেট: `{OTP_PRICE}` Tk)", parse_mode="Markdown")
        
    elif message.text == "👨‍💻 Customer Support":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("💬 Contact Admin (সাপোর্ট)", url=SUPPORT_LINK))
        bot.send_message(chat_id, "🤝 যেকোনো সমস্যা বা সাহায্যের জন্য নিচের বাটনে ক্লিক করে সরাসরি আমাদের এডমিনের সাথে যোগাযোগ করুন:", reply_markup=markup)

    elif message.text == "📱 Get Number":
        bot.send_message(chat_id, "🔍 সক্রিয় নাম্বার রেঞ্জ খোঁজা হচ্ছে...")
        url = f"{BASE_URL}/console"
        
        try:
            response = requests.get(url, headers=headers).json()
            if response.get("meta", {}).get("status") == "ok":
                hits = response.get("data", {}).get("hits", [])
                unique_ranges = set()
                for hit in hits:
                    range_code = hit.get("range")
                    if range_code:
                        unique_ranges.add(range_code)
                
                markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                if unique_ranges:
                    for r_code in sorted(list(unique_ranges)):
                        markup.add(telebot.types.InlineKeyboardButton(f"📱 Range: {r_code}", callback_data=f"buy_{r_code}"))
                    
                    bot.send_message(chat_id, "🔥 **বর্তমানে লাইভ থাকা রেঞ্জসমূহ:**\nনিচের যেকোনো একটি রেঞ্জের ওপর ক্লিক করে নাম্বার নিন:", reply_markup=markup, parse_mode="Markdown")
                else:
                    bot.send_message(chat_id, "ℹ️ এই মুহূর্তে কনসোল লগে কোনো সক্রিয় নাম্বার রেঞ্জ পাওয়া যায়নি।")
            else:
                bot.send_message(chat_id, "❌ সার্ভার কনসোল থেকে ডেটা পাওয়া যায়নি।")
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ ত্রুটি ঘটেছে: {str(e)}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def process_number_purchase(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    selected_range = call.data.split("_")[1]
    
    bot.send_message(chat_id, f"⏳ `{selected_range}` রেঞ্জ থেকে নাম্বার বরাদ্দ (Allocate) করা হচ্ছে...", parse_mode="Markdown")
    url = f"{BASE_URL}/getnum"
    payload = {"rid": selected_range}
    
    try:
        response = requests.post(url, json=payload, headers=headers).json()
        if response.get("meta", {}).get("status") == "ok":
            data = response.get("data", {})
            full_number = data.get("full_number")
            country = data.get("country")
            order_rid = response.get("rid")
            
            USER_LAST_PURCHASE[chat_id] = time.time()
            masked_number = mask_phone_number(full_number)
            
            group_msg = (
                f"📱 **নতুন নাম্বার বরাদ্দ!**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🆔 **RID:** `{order_rid}`\n"
                f"📱 **নাম্বার:** `{masked_number}`\n"
                f"🌍 **দেশ:** {country}\n"
                f"━━━━━━━━━━━━━━━━━━"
            )
            try:
                bot.send_message(GROUP_CHAT_ID, group_msg, parse_mode="Markdown")
            except:
                pass
            
            success_msg = (
                f"✅ **নাম্বার রেডি!**\n\n"
                f"📱 **নাম্বার:** `{full_number}`\n"
                f"🌍 **দেশ:** {country}\n"
                f"🔢 **ব্যবহৃত রেঞ্জ:** `{selected_range}`\n\n"
                f"নাম্বারটি আপনার অ্যাপে বসিয়ে কোড পাঠান। তারপর নিচের ওটিপি বাটনে চাপুন।"
            )
            
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(
                telebot.types.InlineKeyboardButton("🔄 ওটিপি (OTP) চেক করুন", callback_data=f"check_{order_rid}_{selected_range}_{full_number}"),
                telebot.types.InlineKeyboardButton("❌ বাতিল করুন", callback_data=f"cancel_{order_rid}")
            )
            bot.send_message(chat_id, success_msg, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(chat_id, f"❌ দুঃখিত: {response.get('message', 'এই রেঞ্জে কোনো নাম্বার খালি নেই।')}")
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ সমস্যা হয়েছে: {str(e)}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("check_"))
def check_otp_callback(call):
    chat_id = call.message.chat.id
    data_parts = call.data.split("_")
    
    order_rid = data_parts[1]
    selected_range = data_parts[2]
    full_number = str(data_parts[3]).strip() if len(data_parts) > 3 else ""
    
    bot.answer_callback_query(call.id, text="ওটিপি খোঁজা হচ্ছে...")
    url = f"{BASE_URL}/success-otp?rid={order_rid}"
    
    try:
        response = requests.get(url, headers=headers).json()
        if response.get("meta", {}).get("status") == "ok":
            data = response.get("data", {})
            otps_list = data.get("otps", [])
            
            if otps_list and len(otps_list) > 0:
                latest_otp = otps_list[0]
                otp_message = latest_otp.get("message", "No content")
                data_phone = str(latest_otp.get("number", "")).strip()
                otp_id = latest_otp.get("otp_id", order_rid) 
                
                clean_data_phone = ''.join(filter(str.isdigit, data_phone))
                clean_full_number = ''.join(filter(str.isdigit, full_number))
                
                if clean_full_number and clean_data_phone[-8:] != clean_full_number[-8:]:
                    markup = telebot.types.InlineKeyboardMarkup()
                    markup.add(
                        telebot.types.InlineKeyboardButton("🔄 Try Again (আবার চেষ্টা করুন)", callback_data=f"check_{order_rid}_{selected_range}_{full_number}"),
                        telebot.types.InlineKeyboardButton("❌ বাতিল করুন", callback_data=f"cancel_{order_rid}")
                    )
                    bot.send_message(chat_id, "⏳ ওটিপি লগে আপনার বর্তমান নম্বরের জন্য কোনো কোড পাওয়া যায়নি। অনুগ্রহ করে কিছুক্ষণ অপেক্ষা করে আবার চেষ্টা করুন।", reply_markup=markup)
                    return

                masked_number = mask_phone_number(data_phone)
                balance_added_text = ""
                
                if otp_id not in PROCESSED_OTPS:
                    if chat_id not in USER_BALANCES:
                        USER_BALANCES[chat_id] = 0.0
                    USER_BALANCES[chat_id] += OTP_PRICE
                    PROCESSED_OTPS.add(otp_id)
                    balance_added_text = f"💰 আপনার অ্যাকাউন্টে `+{OTP_PRICE}` Tk যোগ করা হয়েছে।"
                else:
                    balance_added_text = "ℹ️ এই ওটিপির ব্যালেন্স ইতোমধ্যে একবার যোগ করা হয়েছে।"
                
                group_success_text = (
                    f"🎉 **USER CHECKED OTP!** 🎉\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🆔 **RID:** `{order_rid}`\n"
                    f"📱 **নম্বর:** `{masked_number}`\n\n"
                    f"💬 **FULL MESSAGE:**\n"
                    f"`{otp_message}`\n"
                    f"━━━━━━━━━━━━━━━━━━━"
                )
                try:
                    bot.send_message(GROUP_CHAT_ID, group_success_text, parse_mode="Markdown")
                except:
                    pass
                
                otp_success_text = (
                    f"🎉 **আপনাদের সম্পূর্ণ ওটিপি মেসেজ:**\n`{otp_message}`\n\n"
                    f"✅ **Otp Received Successfully!**\n"
                    f"{balance_added_text}\n"
                    f"💳 **মোট ব্যালেন্স:** `{USER_BALANCES.get(chat_id, 0.0):.3f}` Tk"
                )
                
                next_markup = telebot.types.InlineKeyboardMarkup()
                if selected_range:
                    next_markup.add(telebot.types.InlineKeyboardButton("🔄 Same Range Auto Buy", callback_data=f"buy_{selected_range}"))
                next_markup.add(telebot.types.InlineKeyboardButton("📱 Change Range", callback_data="change_range_action"))
                
                bot.send_message(chat_id, otp_success_text, parse_mode="Markdown", reply_markup=next_markup)
            else:
                markup = telebot.types.InlineKeyboardMarkup()
                markup.add(
                    telebot.types.InlineKeyboardButton("🔄 Try Again (আবার চেষ্টা করুন)", callback_data=f"check_{order_rid}_{selected_range}_{full_number}"),
                    telebot.types.InlineKeyboardButton("❌ বাতিল করুন", callback_data=f"cancel_{order_rid}")
                )
                bot.send_message(chat_id, "⏳ ওটিপি কোডটি এখনো আসেনি। অনুগ্রহ করে কিছুক্ষণ অপেক্ষা করে আবার চেষ্টা করুন।", reply_markup=markup)
        else:
            bot.send_message(chat_id, "⏳ ওটিপি লগে এখনও কোনো ডেটা পাওয়া যায়নি। অনুগ্রহ করে অপেক্ষা করুন।")
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ ওটিপি চেক করার সময় সমস্যা হয়েছে: {str(e)}")


@bot.callback_query_handler(func=lambda call: call.data == "change_range_action")
def change_range_callback(call):
    chat_id = call.message.chat.id
    last_purchase_time = USER_LAST_PURCHASE.get(chat_id, 0)
    time_elapsed = time.time() - last_purchase_time
    
    if time_elapsed < 30:
        remaining_time = int(30 - time_elapsed)
        bot.answer_callback_query(
            call.id, 
            text=f"⚠️ দুঃখিত! নম্বর নেওয়ার ৩০ সেকেন্ডের মধ্যে নম্বর পরিবর্তন করা যাবে না। আরও {remaining_time} সেকেন্ড অপেক্ষা করুন।", 
            show_alert=True
        )
        return

    bot.answer_callback_query(call.id)
    call.message.text = "📱 Get Number"
    handle_text_buttons(call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_"))
def cancel_order_callback(call):
    chat_id = call.message.chat.id
    order_rid = call.data.split("_")[1]
    
    url = f"{BASE_URL}/cancel"
    payload = {"rid": order_rid}
    try:
        requests.post(url, json=payload, headers=headers)
        bot.answer_callback_query(call.id, text="অর্ডার বাতিল করা হয়েছে।")
        bot.send_message(chat_id, "❌ আপনার অর্ডারটি বাতিল করা হয়েছে।")
    except:
        bot.send_message(chat_id, "⚠️ অর্ডার বাতিল করা যায়নি।")


# --- মূল প্রোগ্রাম এক্সিকিউশন ---
if __name__ == "__main__":
    try:
        bot.remove_webhook()
    except:
        pass

    checker_thread = threading.Thread(target=auto_checker, daemon=True)
    checker_thread.start()
    
    print("🤖 সম্পূর্ণ বট এবং অটো চেকার সফলভাবে রানিং রয়েছে...")
    bot.infinity_polling()
