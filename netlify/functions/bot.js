const CHANNEL_USERNAME = "@TOMAR_CHANNEL_USERNAME"; // @ diye channel username
const GROUP_LINK = "https://t.me/+xxxxxxxx"; // tomar group link
const ADMIN_ID = 123456789; // tomar Telegram ID ( @userinfobot e paba )

exports.handler = async (event) => {
  const BOT_TOKEN = process.env.BOT_TOKEN;
  if (event.httpMethod !== "POST") {
    return { statusCode: 200, body: "NumberBot is running" };
  }

  try {
    const update = JSON.parse(event.body);
    
    // Contact Share handle
    if (update.message && update.message.contact) {
      const chatId = update.message.chat.id;
      const phone = update.message.contact.phone_number;
      const name = update.message.from.first_name;

      // 1. Group join check
      let isJoined = false;
      try {
        const check = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/getChatMember?chat_id=${CHANNEL_USERNAME}&user_id=${chatId}`);
        const data = await check.json();
        if (data.ok && ["member","administrator","creator"].includes(data.result.status)) isJoined = true;
      } catch(e){}

      if (!isJoined) {
        await send(BOT_TOKEN, chatId, `❌ Number save korte hole age channel e join korte hobe:\n${CHANNEL_USERNAME}\n\nJoin kore abar /start likhun`, {
          inline_keyboard: [[{text:"📢 Join Channel", url:`https://t.me/${CHANNEL_USERNAME.replace('@','')}`}]]
        });
        return { statusCode: 200, body: "ok" };
      }

      // 2. Number save success
      await send(BOT_TOKEN, chatId, `✅ Dhonnobad ${name}!\nTomar number: ${phone} save hoyeche.\n\nEkhon group e join koro:`, {
        inline_keyboard: [[{text:"👥 Join Group", url: GROUP_LINK}]]
      });

      // 3. Admin ke notify
      if (ADMIN_ID) {
        await send(BOT_TOKEN, ADMIN_ID, `📞 New Number:\nName: ${name}\nNumber: ${phone}\nID: ${chatId}`);
      }

      return { statusCode: 200, body: "ok" };
    }

    // /start handle
    if (update.message && update.message.text) {
      const chatId = update.message.chat.id;
      const text = update.message.text;

      if (text === "/start") {
        await send(BOT_TOKEN, chatId, `👋 Welcome!\n\nBot use korte hole tomar number share koro:`, {
          keyboard: [[{text:"📱 Share My Number", request_contact: true}]],
          resize_keyboard: true,
          one_time_keyboard: true
        });
      }
    }

    return { statusCode: 200, body: "ok" };
  } catch (e) {
    console.log(e);
    return { statusCode: 200, body: "ok" };
  }
};

async function send(token, chat_id, text, reply_markup) {
  await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id, text, reply_markup })
  });
}
