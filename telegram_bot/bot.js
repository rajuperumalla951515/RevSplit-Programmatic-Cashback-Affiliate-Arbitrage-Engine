import { Bot, InlineKeyboard } from 'grammy';
import fetch from 'node-fetch';
import dotenv from 'dotenv';

dotenv.config();

const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || 'MOCK_BOT_TOKEN_REVSPLIT';
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

let bot = null;

if (BOT_TOKEN && BOT_TOKEN !== 'MOCK_BOT_TOKEN_REVSPLIT') {
  bot = new Bot(BOT_TOKEN);

  bot.command('start', async (ctx) => {
    const keyboard = new InlineKeyboard()
      .text('💰 View Balance', 'cmd_wallet')
      .text('⚡ AI Best Deals', 'cmd_deals');

    await ctx.reply(
      `👋 *Welcome to RevSplit Arbitrage Bot!*\n\n` +
      `Paste any product link (Amazon or Flipkart) below, and I will instantly tokenize it with dynamic cashback tracking!\n\n` +
      `*Commands:*\n` +
      `• Send URL to monetize\n` +
      `• /wallet - Check cashback balance\n` +
      `• /deals - Run AI deal discovery agent`,
      { parse_mode: 'Markdown', reply_markup: keyboard }
    );
  });

  bot.command('wallet', async (ctx) => {
    await ctx.reply(
      `💰 *Your RevSplit Wallet Summary*\n\n` +
      `• *Available Balance:* ₹1,450.00 (Liquid)\n` +
      `• *Pending Cashback:* ₹350.00 (70% Split)\n` +
      `• *Total Earned:* ₹1,800.00`,
      { parse_mode: 'Markdown' }
    );
  });

  bot.on('message:text', async (ctx) => {
    const text = ctx.message.text.trim();
    if (text.startsWith('/')) return;

    if (text.includes('amazon') || text.includes('flipkart') || text.startsWith('http')) {
      const merchant_slug = text.includes('flipkart') ? 'flipkart' : 'amazon';
      
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/links/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: '8f9e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c',
            merchant_slug: merchant_slug,
            original_url: text.startsWith('http') ? text : `https://www.${merchant_slug}.in/dp/sample`
          })
        });

        const data = await res.json();
        if (res.ok) {
          const link = `${API_BASE_URL}${data.redirect_gateway_url}`;
          const keyboard = new InlineKeyboard().url('🛒 Shop & Earn 70% Cashback', link);
          
          await ctx.reply(
            `✅ *Tracking Link Ready!*\n\n` +
            `• *Sub ID:* \`${data.sub_id}\`\n` +
            `• *Cashback Split:* 70% User / 30% Platform\n` +
            `• *Status:* Active in Redis & Kafka`,
            { parse_mode: 'Markdown', reply_markup: keyboard }
          );
        } else {
          await ctx.reply(`⚠️ Error: ${data.detail || 'Could not generate link.'}`);
        }
      } catch (err) {
        await ctx.reply(`⚠️ API Error: Ensure backend is running on ${API_BASE_URL}`);
      }
    }
  });
} else {
  console.log('ℹ️ Telegram Bot running in MOCK mode (To enable live Telegram polling, set a valid TELEGRAM_BOT_TOKEN in .env)');
}

if (process.argv[1].endsWith('bot.js')) {
  if (bot) {
    console.log('🤖 Starting Telegram Bot polling...');
    bot.start().catch((err) => {
      console.warn('⚠️ Telegram Bot Polling Notice:', err.message);
    });
  } else {
    console.log('🤖 RevSplit Telegram Bot Standby Ready.');
  }
}

export { bot };
