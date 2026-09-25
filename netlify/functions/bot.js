exports.handler = async (event) => {
  const BOT_TOKEN = process.env.BOT_TOKEN;
  const API_KEY = process.env.API_KEY;
  const GROUP_CHAT_ID = -1004378025853;
  const BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api";
  const map = global.numberMap || (global.numberMap = new Map());

  if (event.httpMethod === "GET") return { statusCode: 200, body: "Bot running JS - Only Number" };

  try {
    const update = JSON.parse(event.body);

    // Group OTP auto
    if (update.message && update.message.chat.id === GROUP_CHAT_ID) {
      const text = update.message.text || "";
      const nums = text.match(/\d{8,15}/g) || [];
      const otp = text.match(/\b\d{4,8}\b/);
      for (let n of nums) {
        if (map.has(n.slice(-8))) {
          await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ chat_id: map.get(n.slice(-8)), text: `🎉 AUTO OTP!\n📱 ${n}\n🔑 ${otp? otp[0] : text}\n\n${text}`, parse_mode: "Markdown" })
          });
        }
      }
    }

    if (update.message?.text === "/start") {
      await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: update.message.chat.id, text: "👋 Number bot - Press Get Number", reply_markup: { keyboard: [[{ text: "📱 Get Number" }]], resize_keyboard: true } })
      });
    }

    if (update.message?.text === "📱 Get Number") {
      let res = await fetch(`${BASE_URL}/console`, { headers: { "mauthapi": API_KEY } }).then(r=>r.json());
      let ranges = [...new Set((res.data?.hits || []).map(h=>h.range).filter(Boolean))];
      let kb = ranges.map(r=>[{ text: `📱 ${r}`, callback_data: `buy:${r}` }]);
      await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: update.message.chat.id, text: "🔥 Live Range:", reply_markup: { inline_keyboard: kb } })
      });
    }

    if (update.callback_query?.data?.startsWith("buy:")) {
      let range = update.callback_query.data.split(":")[1];
      let chatId = update.callback_query.message.chat.id;
      let res = await fetch(`${BASE_URL}/getnum`, { method: "POST", headers: { "mauthapi": API_KEY, "Content-Type": "application/json" }, body: JSON.stringify({ rid: range }) }).then(r=>r.json());
      if (res.meta?.status === "ok") {
        let full = String(res.data.full_number);
        map.set(full.slice(-8), chatId);
        map.set(full, chatId);
        await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ chat_id: chatId, text: `✅ Number: ${full}\n⏳ OTP auto asbe...`, parse_mode: "Markdown" })
        });
      }
    }

    return { statusCode: 200, body: "OK" };
  } catch(e) { return { statusCode: 200, body: "OK" }; }
};
