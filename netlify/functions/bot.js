const { Telegraf, Markup } = require('telegraf');
const fetch = require('node-fetch');

// --- কনফিগারেশন ---
const BOT_TOKEN = "8772570139:AAEqmJPmYrV3BQtiRMAqAKxDYdMQ-kT3Qgc";
const GROUP_CHAT_ID = -1004429028470;
const API_KEY = "MKR8MCYN7MZ";
const BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api";
const SUPPORT_LINK = "https://t.me/flpsupport_bot";

const bot = new Telegraf(BOT_TOKEN);

const headers = {
    "mauthapi": API_KEY,
    "Content-Type": "application/json"
};

const OTP_PRICE = 0.003;
const userBalances = {};
const processedOtps = new Set();
const userLastPurchase = {};
const sentOtpIds = new Set();
const sentConsoleIds = new Set();

function maskPhoneNumber(phone) {
    if (!phone || phone === "Unknown") return "Unknown";
    const phoneStr = String(phone);
    return phoneStr.length > 6 
        ? `${phoneStr.slice(0, 5)}★★★★★${phoneStr.slice(-3)}` 
        : `${phoneStr.slice(0, 2)}★★★★★${phoneStr.slice(-2)}`;
}

function getMainMenu() {
    return Markup.keyboard([
        ['📱 Get Number', '💰 Get Balance'],
        ['👨‍💻 Customer Support']
    ]).resize();
}

// --- ১. ব্যাকগ্রাউন্ড অটো চেকার ---
async function autoChecker() {
    console.log("🔄 কনসোল এবং ওটিপি ব্যাকগ্রাউন্ড ডিটেক্টর চালু হয়েছে...");
    while (true) {
        try {
            // === ক. ওটিপি চেক ===
            const otpResp = await fetch(`${BASE_URL}/success-otp`, { headers }).then(res => res.json());
            if (otpResp.meta && otpResp.meta.status === "ok" && otpResp.data && otpResp.data.otps) {
                for (const otpData of otpResp.data.otps) {
                    const oid = otpData.otp_id || otpData.message;
                    if (oid && !sentOtpIds.has(oid)) {
                        const maskedNum = maskPhoneNumber(otpData.number);
                        const msg = `⚡ **[AUTO SUCCESS] NEW OTP** ⚡\n` +
                                    `━━━━━━━━━━━━━━━━━━━\n` +
                                    `🆔 **RID:** \`${otpResp.rid || 'N/A'}\`\n` +
                                    `📱 **নম্বর:** \`${maskedNum}\`\n\n` +
                                    `💬 **MESSAGE:**\n\`${otpData.message}\`\n` +
                                    `━━━━━━━━━━━━━━━━━━━`;
                        try {
                            await bot.telegram.sendMessage(GROUP_CHAT_ID, msg, { parse_mode: 'Markdown' });
                        } catch (e) {}
                        sentOtpIds.add(oid);
                    }
                }
            }

            // === খ. কনসোল লগ চেক ===
            const consoleResp = await fetch(`${BASE_URL}/console`, { headers }).then(res => res.json());
            if (consoleResp.meta && consoleResp.meta.status === "ok" && consoleResp.data && consoleResp.data.hits) {
                for (const hit of consoleResp.data.hits) {
                    const consoleId = String(hit.time);
                    if (consoleId && !sentConsoleIds.has(consoleId)) {
                        const cNumber = hit.number || "Unknown";
                        const cMessage = hit.message || "No message content in console";
                        const maskedCNum = maskPhoneNumber(cNumber);

                        const msg = `🖥️ **[CONSOLE LOG] NEW UPDATE**\n` +
                                    `━━━━━━━━━━━━━━━━━━━\n` +
                                    `📱 **Range:** \`${hit.range}\`\n` +
                                    `📞 **নম্বর:** \`${maskedCNum}\`\n` +
                                    `🌍 **দেশ:** ${hit.country}\n\n` +
                                    `💬 **CONSOLE MESSAGE:**\n\`${cMessage}\`\n` +
                                    `━━━━━━━━━━━━━━━━━━━`;
                        try {
                            await bot.telegram.sendMessage(GROUP_CHAT_ID, msg, { parse_mode: 'Markdown' });
                        } catch (e) {}
                        sentConsoleIds.add(consoleId);
                    }
                }
            }
        } catch (e) {
            console.log(`❌ অটো চেকার এরর: ${e.message}`);
        }
        await new Promise(resolve => setTimeout(resolve, 8000));
    }
}

// --- ২. বট হ্যান্ডলারসমূহ ---
bot.start((ctx) => {
    const chatId = ctx.chat.id;
    if (!(chatId in userBalances)) userBalances[chatId] = 0.0;
    ctx.reply("👋 হ্যালো! নাম্বার বোটে আপনাকে স্বাগতম।\n\nনাম্বার নিতে নিচের **📱 Get Number** বাটনে চাপুন。", getMainMenu());
});

bot.hears("💰 Get Balance", (ctx) => {
    const chatId = ctx.chat.id;
    if (!(chatId in userBalances)) userBalances[chatId] = 0.0;
    ctx.reply(`💳 **আপনার বর্তমান ব্যালেন্স:** \`${userBalances[chatId].toFixed(3)}\` Tk\n(প্রতি ওটিপি/মেসেজ রেট: \`${OTP_PRICE}\` Tk)`, { parse_mode: 'Markdown' });
});

bot.hears("👨‍💻 Customer Support", (ctx) => {
    ctx.reply("🤝 যেকোনো সমস্যা বা সাহায্যের জন্য নিচের বাটনে ক্লিক করে সরাসরি আমাদের এডমিনের সাথে যোগাযোগ করুন:", 
        Markup.inlineKeyboard([
            [Markup.button.url("💬 Contact Admin (সাপোর্ট)", SUPPORT_LINK)]
        ])
    );
});

bot.hears("📱 Get Number", async (ctx) => {
    const chatId = ctx.chat.id;
    if (!(chatId in userBalances)) userBalances[chatId] = 0.0;
    
    await ctx.reply("🔍 সক্রিয় নাম্বার রেঞ্জ খোঁজা হচ্ছে...");
    try {
        const response = await fetch(`${BASE_URL}/console`, { headers }).then(res => res.json());
        if (response.meta && response.meta.status === "ok") {
            const hits = response.data.hits || [];
            const uniqueRanges = [...new Set(hits.map(h => h.range).filter(Boolean))];

            if (uniqueRanges.length > 0) {
                let buttons = uniqueRanges.map(r => Markup.button.callback(`📱 Range: ${r}`, `buy_${r}`));
                let keyboard = Markup.inlineKeyboard(chunkArray(buttons, 2));
                await ctx.reply("🔥 **বর্তমানে লাইভ থাকা রেঞ্জসমূহ:**\nনিচের যেকোনো একটি রেঞ্জের ওপর ক্লিক করে নাম্বার নিন:", { parse_mode: 'Markdown', ...keyboard });
            } else {
                await ctx.reply("ℹ️ এই মুহূর্তে কনসোল লগে কোনো সক্রিয় নাম্বার রেঞ্জ পাওয়া যায়নি।");
            }
        } else {
            await ctx.reply("❌ সার্ভার কনসোল থেকে ডেটা পাওয়া যায়নি।");
        }
    } catch (e) {
        await ctx.reply(`⚠️ ত্রুটি ঘটেছে: ${e.message}`);
    }
});

bot.action(/^buy_(.+)/, async (ctx) => {
    await ctx.answerCbQuery();
    const chatId = ctx.chat.id;
    const selectedRange = ctx.match[1];

    await ctx.reply(`⏳ \`${selectedRange}\` রেঞ্জ থেকে নাম্বার বরাদ্দ (Allocate) করা হচ্ছে...`, { parse_mode: 'Markdown' });
    try {
        const response = await fetch(`${BASE_URL}/getnum`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ rid: selectedRange })
        }).then(res => res.json());

        if (response.meta && response.meta.status === "ok") {
            const { full_number, country } = response.data;
            const orderRid = response.rid;
            userLastPurchase[chatId] = Date.now();
            const maskedNumber = maskPhoneNumber(full_number);

            try {
                await bot.telegram.sendMessage(GROUP_CHAT_ID, 
                    `📱 **নতুন নাম্বার বরাদ্দ!**\n` +
                    `━━━━━━━━━━━━━━━━━━\n` +
                    `🆔 **RID:** \`${orderRid}\`\n` +
                    `📱 **নাম্বার:** \`${maskedNumber}\`\n` +
                    `🌍 **দেশ:** ${country}\n` +
                    `━━━━━━━━━━━━━━━━━━`, 
                    { parse_mode: 'Markdown' }
                );
            } catch (e) {}

            await ctx.reply(
                `✅ **নাম্বার রেডি!**\n\n` +
                `📱 **নাম্বার:** \`${full_number}\`\n` +
                `🌍 **দেশ:** ${country}\n` +
                `🔢 **ব্যবহৃত রেঞ্জ:** \`${selectedRange}\`\n\n` +
                `নাম্বারটি আপনার অ্যাপে বসিয়ে কোড পাঠান। তারপর নিচের ওটিপি বাটনে চাপুন।`,
                {
                    parse_mode: 'Markdown',
                    ...Markup.inlineKeyboard([
                        [Markup.button.callback("🔄 ওটিপি (OTP) চেক করুন", `check_${orderRid}_${selectedRange}_${full_number}`)],
                        [Markup.button.callback("❌ বাতিল করুন", `cancel_${orderRid}`)]
                    ])
                }
            );
        } else {
            await ctx.reply(`❌ দুঃখিত: ${response.message || 'এই রেঞ্জে কোনো নাম্বার খালি নেই।'}`);
        }
    } catch (e) {
        await ctx.reply(`⚠️ সমস্যা হয়েছে: ${e.message}`);
    }
});

bot.action(/^check_(.+)_(.+)_(.*)/, async (ctx) => {
    const chatId = ctx.chat.id;
    const orderRid = ctx.match[1];
    const selectedRange = ctx.match[2];
    const fullNumber = ctx.match[3] || "";

    await ctx.answerCbQuery("ওটিপি খোঁজা হচ্ছে...");
    try {
        const response = await fetch(`${BASE_URL}/success-otp?rid=${orderRid}`, { headers }).then(res => res.json());
        if (response.meta && response.meta.status === "ok") {
            const otpsList = response.data.otps || [];
            if (otpsList.length > 0) {
                const latestOtp = otpsList[0];
                const otpMessage = latestOtp.message || "No content";
                const dataPhone = String(latestOtp.number || "").trim();
                const otpId = latestOtp.otp_id || orderRid;

                const cleanDataPhone = dataPhone.replace(/\D/g, '');
                const cleanFullNumber = fullNumber.replace(/\D/g, '');

                if (cleanFullNumber && cleanDataPhone.slice(-8) !== cleanFullNumber.slice(-8)) {
                    await ctx.reply("⏳ ওটিপি লগে আপনার বর্তমান নম্বরের জন্য কোনো কোড পাওয়া যায়নি। অনুগ্রহ করে কিছুক্ষণ অপেক্ষা করে আবার চেষ্টা করুন।",
                        Markup.inlineKeyboard([
                            [Markup.button.callback("🔄 Try Again", `check_${orderRid}_${selectedRange}_${fullNumber}`)],
                            [Markup.button.callback("❌ বাতিল করুন", `cancel_${orderRid}`)]
                        ])
                    );
                    return;
                }

                const maskedNumber = maskPhoneNumber(dataPhone);
                let balanceAddedText = "";

                if (!processedOtps.has(otpId)) {
                    if (!(chatId in userBalances)) userBalances[chatId] = 0.0;
                    userBalances[chatId] += OTP_PRICE;
                    processedOtps.add(otpId);
                    balanceAdded_text = `💰 আপনার অ্যাকাউন্টে \`+${OTP_PRICE}\` Tk যোগ করা হয়েছে।`;
                } else {
                    balanceAdded_text = "ℹ️ এই ওটিপির ব্যালেন্স ইতোমধ্যে একবার যোগ করা হয়েছে।";
                }

                try {
                    await bot.telegram.sendMessage(GROUP_CHAT_ID,
                        `🎉 **USER CHECKED OTP!** 🎉\n` +
                        `━━━━━━━━━━━━━━━━━━━\n` +
                        `🆔 **RID:** \`${orderRid}\`\n` +
                        `📱 **নম্বর:** \`${maskedNumber}\`\n\n` +
                        `💬 **FULL MESSAGE:**\n\`${otpMessage}\`\n` +
                        `━━━━━━━━━━━━━━━━━━━`,
                        { parse_mode: 'Markdown' }
                    );
                } catch (e) {}

                let inlineButtons = [];
                if (selectedRange) {
                    inlineButtons.push([Markup.button.callback("🔄 Same Range Auto Buy", `buy_${selectedRange}`)]);
                }
                inlineButtons.push([Markup.button.callback("📱 Change Range", "change_range_action")]);

                await ctx.reply(
                    `🎉 **আপনাদের সম্পূর্ণ ওটিপি মেসেজ:**\n\`${otpMessage}\`\n\n` +
                    `✅ **Otp Received Successfully!**\n` +
                    `${balanceAdded_text}\n` +
                    `💳 **মোট ব্যালেন্স:** \`${userBalances[chatId].toFixed(3)}\` Tk`,
                    { parse_mode: 'Markdown', ...Markup.inlineKeyboard(inlineButtons) }
                );
            } else {
                await ctx.reply("⏳ ওটিপি কোডটি এখনো আসেনি। অনুগ্রহ করে কিছুক্ষণ অপেক্ষা করে আবার চেষ্টা করুন।",
                    Markup.inlineKeyboard([
                        [Markup.button.callback("🔄 Try Again", `check_${orderRid}_${selectedRange}_${fullNumber}`)],
                        [Markup.button.callback("❌ বাতিল করুন", `cancel_${orderRid}`)]
                    ])
                );
            }
        } else {
            await ctx.reply("⏳ ওটিপি লগে এখনও কোনো ডেটা পাওয়া যায়নি। অনুগ্রহ করে অপেক্ষা করুন।");
        }
    } catch (e) {
        await ctx.reply(`⚠️ ওটিপি চেক করার সময় সমস্যা হয়েছে: ${e.message}`);
    }
});

bot.action("change_range_action", async (ctx) => {
    const chatId = ctx.chat.id;
    const lastPurchaseTime = userLastPurchase[chatId] || 0;
    const timeElapsed = (Date.now() - lastPurchaseTime) / 1000;

    if (timeElapsed < 30) {
        const remainingTime = Math.ceil(30 - timeElapsed);
        await ctx.answerCbQuery(`⚠️ দুঃখিত! নম্বর নেওয়ার ৩০ সেকেন্ডের মধ্যে নম্বর পরিবর্তন করা যাবে না। আরও ${remainingTime} সেকেন্ড অপেক্ষা করুন।`, { show_alert: true });
        return;
    }

    await ctx.answerCbQuery();
    // Simulate Get Number action
    ctx.message = { chat: { id: chatId } };
    // Trigger get number function logic directly or call handler
});

bot.action(/^cancel_(.+)/, async (ctx) => {
    const orderRid = ctx.match[1];
    try {
        await fetch(`${BASE_URL}/cancel`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ rid: orderRid })
        });
        await ctx.answerCbQuery("অর্ডার বাতিল করা হয়েছে।");
        await ctx.reply("❌ আপনার অর্ডারটি বাতিল করা হয়েছে।");
    } catch (e) {
        await ctx.reply("⚠️ অর্ডার বাতিল করা যায়নি।");
    }
});

function chunkArray(arr, size) {
    let result = [];
    for (let i = 0; i < arr.length; i += size) {
        result.push(arr.slice(i, i + size));
    }
    return result;
}

// Start Bot and Background Checker
bot.launch().then(() => {
    console.log("🤖 Node.js বট সফলভাবে চালু হয়েছে...");
    autoChecker();
});

process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
