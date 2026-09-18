import os
import threading
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes
from flask import Flask

# Flask એપ (જેથી Render આને ફ્રીમાં 24/7 ચલાવે)
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Trader Bot is Running 24/7 Free!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# ટેલિગ્રામ ટોકન અને આઈડી
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")

# લર્નિંગ મેમરી
penalties = {}

async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, bucket = query.data.split("|")
    if action == "bad":
        penalties[bucket] = penalties.get(bucket, 0) + 1
        await query.edit_message_text(text=f"{query.message.text}\n\n❌ તમે ખોટો ગણાવ્યો. બોટ આ પેટર્ન યાદ રાખશે.")
    else:
        await query.edit_message_text(text=f"{query.message.text}\n\n✅ સિગ્નલ કન્ફર્મ થયું.")

if __name__ == "__main__":
    # વેબ સર્વર ચાલુ કરવું
    threading.Thread(target=run_flask, daemon=True).start()
    
    # બોટ ચાલુ કરવો
    if BOT_TOKEN:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CallbackQueryHandler(handle_feedback))
        print("બોટ શરૂ થઈ ગયો છે...")
        app.run_polling()
