exports.handler = async (event) => {
  const BOT_TOKEN = process.env.BOT_TOKEN;
  if (event.httpMethod !== "POST") {
    return { statusCode: 200, body: "Bot is running - JS version OK" };
  }
  try {
    const update = JSON.parse(event.body);
    if (update.message) {
      const chatId = update.message.chat.id;
      const text = update.message.text || "";
      let reply = `You: ${text}`;
      if (text === "/start") reply = "✅ Bot LIVE! /start kaj kortese";
      
      await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: chatId, text: reply })
      });
    }
    return { statusCode: 200, body: "ok" };
  } catch (e) {
    return { statusCode: 200, body: "ok" };
  }
};
