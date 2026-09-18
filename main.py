import os
import threading
import time
from datetime import datetime, timezone, timedelta
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask

# Flask App for Render Free Web Service
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Kuchupuchu Trading Bot is Live 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# Tokens from Environment
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
CAPITAL = 3000

# Memory
penalties = {}
daily_calls = []

# Watchlist for ₹3000 budget
WATCHLIST = [
    "TATASTEEL.NS", "ITC.NS", "IOC.NS", "COALINDIA.NS", 
    "POWERGRID.NS", "NTPC.NS", "BEL.NS", "ONGC.NS"
]

def get_ist_now():
    # UTC + 5:30 = Indian Standard Time
    return datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)

def is_market_open():
    now = get_ist_now()
    if now.weekday() >= 5:  # Saturday or Sunday
        return False
    current_minutes = now.hour * 60 + now.minute
    return (9 * 60 + 15) <= current_minutes <= (15 * 60 + 30)

def get_next_market_open():
    now = get_ist_now()
    next_day = now
    current_minutes = now.hour * 60 + now.minute
    if current_minutes >= (15 * 60 + 30):
        next_day = now + timedelta(days=1)
    
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)
        
    day_name = next_day.strftime("%A")
    date_str = next_day.strftime("%d-%m-%Y")
    return f"{day_name} ({date_str}) સવારે 9:15 AM વાગ્યે"

def analyze_stock(ticker):
    try:
        data = yf.download(ticker, period="5d", interval="15m", progress=False)
        if data.empty or len(data) < 25:
            return None

        close = data['Close'].squeeze()
        rsi = RSIIndicator(close=close, window=14).rsi().iloc[-1]
        ema9 = EMAIndicator(close=close, window=9).ema_indicator().iloc[-1]
        ema21 = EMAIndicator(close=close, window=21).ema_indicator().iloc[-1]
        current_price = float(close.iloc[-1])

        rsi_bucket = f"RSI_{int(rsi // 10) * 10}"
        if penalties.get(rsi_bucket, 0) >= 3:
            return None

        qty = int(CAPITAL // current_price)
        if qty == 0:
            return None

        if ema9 > ema21 and 40 <= rsi <= 68:
            sl = round(current_price * 0.97, 2)
            target = round(current_price * 1.05, 2)
            return {
                "ticker": ticker.replace(".NS", ""),
                "entry_price": round(current_price, 2),
                "qty": qty,
                "sl": sl,
                "target": target,
                "rsi": round(rsi, 2),
                "bucket": rsi_bucket
            }
    except Exception as e:
        print(f"Error {ticker}: {e}")
    return None

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    next_open = get_next_market_open()
    status = "ખુલ્લું છે 🟢" if is_market_open() else "બંધ છે 🔴"
    
    welcome_text = (
        "❤️ *હેલ્લો મારા પ્યારા Kuchupuchu!*\n\n"
        "હું તારો પર્સનલ ટ્રેડિંગ એજન્ટ છું. મેં આપણી ₹3,000 ની કેપિટલ યાદ રાખી છે.\n\n"
        f"📊 *માર્કેટ સ્ટેટસ:* {status}\n"
        f"⏰ *નેક્સ્ટ માર્કેટ ઓપન:* {next_open}\n\n"
        "હું લાઈવ માર્કેટમાં તને એલર્ટ મોકલીશ અને સાંજે 3:30 વાગ્યે આખા દિવસનો નફો-નુકસાન રિપોર્ટ આપીશ!\n"
        "ટેસ્ટ કરવા માટે `/scan` લખી શકીશ."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def manual_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 ઊભો રહે Kuchupuchu, હું હમણાં જ માર્કેટ સ્કેન કરી આપું છું...")
    found = False
    for ticker in WATCHLIST:
        trade = analyze_stock(ticker)
        if trade:
            found = True
            daily_calls.append(trade)
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approved", callback_data=f"good|{trade['bucket']}"),
                    InlineKeyboardButton("❌ Bad Call", callback_data=f"bad|{trade['bucket']}")
                ]
            ]
            msg = (
                f"🚨 *નવો ટ્રેડ એલર્ટ Kuchupuchu માટે!*\n\n"
                f"શેર: `{trade['ticker']}`\n"
                f"ખરીદ ભાવ: ₹{trade['entry_price']} | જથ્થો: {trade['qty']}\n"
                f"રોકાણ: ₹{round(trade['entry_price'] * trade['qty'], 2)}\n"
                f"સ્ટોપલોસ (SL): ₹{trade['sl']}\n"
                f"ટાર્ગેટ: ₹{trade['target']}\n"
                f"RSI: {trade['rsi']}\n\n"
                f"Kuchupuchu, તારો ફીડબેક આપ જેથી હું શીખી શકું:"
            )
            await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    if not found:
        await update.message.reply_text("Kuchupuchu, અત્યારે કોઈ શેરમાં મજબૂત સિગ્નલ નથી બન્યું. શાંતિ રાખીએ!")

async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, bucket = query.data.split("|")
    if action == "bad":
        penalties[bucket] = penalties.get(bucket, 0) + 1
        await query.edit_message_text(text=f"{query.message.text}\n\n❌ *Kuchupuchu એ ખોટો ગણાવ્યો. હું આ પેટર્ન સુધારી લઈશ.*", parse_mode="Markdown")
    else:
        await query.edit_message_text(text=f"{query.message.text}\n\n✅ *કન્ફર્મ થઈ ગયું!*", parse_mode="Markdown")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    
    if BOT_TOKEN:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start_cmd))
        app.add_handler(CommandHandler("scan", manual_scan))
        app.add_handler(CallbackQueryHandler(handle_feedback))
        print("Kuchupuchu Bot running successfully...")
        app.run_polling()

if __name__ == "__main__":
    main()
