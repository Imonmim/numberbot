const BOT_TOKEN = process.env.BOT_TOKEN || "8701736168:AAHhfQUelJm-Fl3BCGQmQ55biNdzYP6_EXw";
const API_KEY = process.env.API_KEY || "MKR8MCYN7MZ";
const GROUP_CHAT_ID = -1004429028470;
const BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api";
const SUPPORT_LINK = "https://t.me/flpsupport_bot";
const lastPurchase = new Map();

exports.handler = async (event) => {
  if (event.httpMethod === "GET") return { statusCode: 200, body: "Bot.js running - Same logic" };
  try {
    const update = JSON.parse(event.body);

    if (update.message && update.message.text === "/start") {
      await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: update.message.chat.id, text: "👋 হ্যালো! নাম্বার বোটে স্বাগতম।\n\n📱 Get Number চাপুন।", reply_markup: { keyboard: [[{ text: "📱 Get Number" }],[{ text: "👨‍💻 Customer Support" }]], resize_keyboard: true } })
      });
    }

    if (update.message && update.message.text === "📱 Get Number") {
      await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chat_id: update.message.chat.id, text: "🔍 সক্রিয় নাম্বার রেঞ্জ খোঁজা হচ্ছে..." }) });
      let res = await fetch(`${BASE_URL}/console`, { headers: { "mauthapi": API_KEY } }).then(r=>r.json());
      if (res.meta?.status === "ok") {
        let ranges = [...new Set((res.data?.hits || []).map(h=>h.range).filter(Boolean))].sort();
        if (ranges.length > 0) {
          let kb = ranges.map(r=>[{ text: `📱 Range: ${r}`, callback_data: `buy:${r}` }]);
          await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chat_id: update.message.chat.id, text: "🔥 **বর্তমানে লাইভ থাকা রেঞ্জসমূহ:**", reply_markup: { inline_keyboard: kb }, parse_mode: "Markdown" }) });
        } else {
          await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chat_id: update.message.chat.id, text: "ℹ️ কোনো সক্রিয় রেঞ্জ পাওয়া যায়নি।" }) });
        }
      }
    }

    if (update.message && update.message.text === "👨‍💻 Customer Support") {
      await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chat_id: update.message.chat.id, text: "🤝 Support:", reply_markup: { inline_keyboard: [[{ text: "💬 Contact Admin", url: SUPPORT_LINK }]] } }) });
    }

    if (update.callback_query && update.callback_query.data.startsWith("buy:")) {
      let range = update.callback_query.data.split(":")[1];
      let chatId = update.callback_query.message.chat.id;
      let res = await fetch(`${BASE_URL}/getnum`, { method: "POST", headers: { "mauthapi": API_KEY, "Content-Type": "application/json" }, body: JSON.stringify({ rid: range }) }).then(r=>r.json());
      if (res.meta?.status === "ok") {
        let full = res.data.full_number;
        let rid = res.rid;
        lastPurchase.set(chatId, Date.now());
        await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chat_id: chatId, text: `✅ **নাম্বার রেডি!**\n\n📱 \`${full}\`\n🌍 ${res.data.country}\n🔢 \`${range}\``, reply_markup: { inline_keyboard: [[{ text: "🔄 ওটিপি চেক করুন", callback_data: `check:${rid}:${range}:${full}` }],[{ text: "❌ বাতিল করুন", callback_data: `cancel:${rid}` }]] }, parse_mode: "Markdown" }) });
      }
    }

    if (update.callback_query && update.callback_query.data.startsWith("check:")) {
      let [, rid, range, full] = update.callback_query.data.split(":");
      let chatId = update.callback_query.message.chat.id;
      let res = await fetch(`${BASE_URL}/success-otp?rid=${rid}`, { headers: { "mauthapi": API_KEY } }).then(r=>r.json());
      if (res.meta?.status === "ok" && res.data?.otps?.length > 0) {
        let msg = res.data.otps[0].message;
        await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chat_id: chatId, text: `🎉 **OTP:**\n\`${msg}\`\n\n✅ Success!`, reply_markup: { inline_keyboard: [[{ text: "🔄 Same Range Auto Buy", callback_data: `buy:${range}` }],[{ text: "📱 Change Range", callback_data: "change_range_action" }]] }, parse_mode: "Markdown" }) });
      } else {
        await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chat_id: chatId, text: "⏳ OTP এখনো আসেনি।", reply_markup: { inline_keyboard: [[{ text: "🔄 Try Again", callback_data: `check:${rid}:${range}:${full}` }]] } }) });
      }
    }

    if (update.callback_query && update.callback_query.data === "change_range_action") {
      let chatId = update.callback_query.message.chat.id;
      let last = lastPurchase.get(chatId) || 0;
      if (Date.now() - last < 30000) {
        await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/answerCallbackQuery`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ callback_query_id: update.callback_query.id, text: "⚠️ 30s পর Change করুন", show_alert: true }) });
      } else {
        let res = await fetch(`${BASE_URL}/console`, { headers: { "mauthapi": API_KEY } }).then(r=>r.json());
        let ranges = [...new Set((res.data?.hits || []).map(h=>h.range).filter(Boolean))].sort();
        let kb = ranges.map(r=>[{ text: `📱 Range: ${r}`, callback_data: `buy:${r}` }]);
        await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chat_id: chatId, text: "🔥 **Live Range:**", reply_markup: { inline_keyboard: kb }, parse_mode: "Markdown" }) });
      }
    }

    if (update.callback_query && update.callback_query.data.startsWith("cancel:")) {
      let rid = update.callback_query.data.split(":")[1];
      await fetch(`${BASE_URL}/cancel`, { method: "POST", headers: { "mauthapi": API_KEY, "Content-Type": "application/json" }, body: JSON.stringify({ rid }) });
      await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chat_id: update.callback_query.message.chat.id, text: "❌ বাতিল করা হয়েছে।" }) });
    }

    return { statusCode: 200, body: "OK" };
  } catch(e) { return { statusCode: 200, body: "OK" }; }
};
