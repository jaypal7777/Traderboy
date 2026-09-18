import os
import threading
import asyncio
from datetime import datetime, time as dtime, timedelta
import pytz
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask

# Flask App for Render 24/7 Free Hosting
web_app = Flask(_name_)

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

# Memory & Daily Tracking
penalties = {}
daily_calls = []  # Aajna badha calls track karva mate
market_closed_notified = False

# Watchlist for ₹3000 budget
WATCHLIST = [
    "TATASTEEL.NS", "ITC.NS", "IOC.NS", "COALINDIA.NS", 
    "POWERGRID.NS", "NTPC.NS", "BEL.NS", "ONGC.NS"
]

IST = pytz.timezone('Asia/Kolkata')

def is_market_open():
    now = datetime.now(IST)
    if now.weekday() >= 5:  # Saturday or Sunday
        return False
    market_start = dtime(9, 15)
    market_end = dtime(15, 30)
    current_time = now.time()
    return market_start <= current_time <= market_end

def get_next_market_open():
    now = datetime.now(IST)
    # Market open 9:15 AM
    next_day = now
    if now.time() >= dtime(15, 30):
        next_day = now + timedelta(days=1)
    
    while next_day.weekday() >= 5:  # Weekend bypass
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

        # Buy Setup
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

# /start Command
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    next_open = get_next_market_open()
    status = "ખુલ્લું છે 🟢" if is_market_open() else "બંધ છે 🔴"
    
    welcome_text = (
        "❤️ હેલ્લો મારા પ્યારા Kuchupuchu!\n\n"
        "હું તારો પર્સનલ ટ્રેડિંગ એજન્ટ છું. મેં આપણી ₹3,000 ની કેપિટલ યાદ રાખી છે.\n\n"
        f"📊 માર્કેટ સ્ટેટસ: {status}\n"
        f"⏰ નેક્સ્ટ માર્કેટ ઓપન: {next_open}\n\n"
        "હું લાઈવ માર્કેટમાં તને એલર્ટ મોકલીશ અને સાંજે 3:30 વાગ્યે આખા દિવસનો નફો-નુકસાન રિપોર્ટ આપીશ!\n"
        "ટેસ્ટ કરવા માટે /scan લખી શકીશ."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# /scan Command
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
                f"🚨 નવો ટ્રેડ એલર્ટ Kuchupuchu માટે!\n\n"
                f"શેર: {trade['ticker']}\n"
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

# Feedback Handler
async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, bucket = query.data.split("|")
    if action == "bad":
        penalties[bucket] = penalties.get(bucket, 0) + 1
        await query.edit_message_text(text=f"{query.message.text}\n\n❌ Kuchupuchu એ ખોટો ગણાવ્યો. હું આ પેટર્ન સુધારી લઈશ.", parse_mode="Markdown")
    else:
        await query.edit_message_text(text=f"{query.message.text}\n\n✅ કન્ફર્મ થઈ ગયું!", parse_mode="Markdown")

# Daily Closing Report Loop
async def market_scheduler(app):
    global daily_calls, market_closed_notified
    while True:
        await asyncio.sleep(60)  # Check every minute
        now = datetime.now(IST)
        
        # New day reset at 9:00 AM
        if now.time().hour == 9 and now.time().minute == 0:
            daily_calls = []
            market_closed_notified = False

        # Market Close Trigger (At 3:30 PM on weekdays)
        if now.weekday() < 5 and now.time().hour == 15 and now.time().minute >= 30 and not market_closed_notified:
            market_closed_notified = True
            total_calls = len(daily_calls)
            net_pnl = 0
            details = ""

            for idx, call in enumerate(daily_calls, start=1):
                # Calculate current price for P&L
                ticker_obj = yf.Ticker(call['ticker'] + ".NS")
                last_price = ticker_obj.fast_info.get('last_price', call['entry_price'])
                pnl = (last_price - call['entry_price']) * call['qty']
                
                # Groww brokerage & tax estimation (~Rs. 45 per buy-sell pair)
                groww_charge = 45.0
                net_call_pnl = pnl - groww_charge
                net_pnl += net_call_pnl
                
                status_icon = "🟢" if net_call_pnl >= 0 else "🔴"
                details += (
                    f"{idx}. {call['ticker']}: ભાવ ₹{call['entry_price']} -> ₹{round(last_price, 2)}\n"
                    f"   જથ્થો: {call['qty']} | Net P&L: {status_icon} ₹{round(net_call_pnl, 2)} (ચાર્જ બાદ)\n"
                )

            next_open = get_next_market_open()
            report_msg = (
                f"🔔 Today Market Closed, Kuchupuchu!\n\n"
                f"આજે માર્કેટ પૂર્ણ થયું છે. આ રહ્યો આપણો દૈનિક હિસાબ:\n\n"
                f"📋 કુલ અપાયેલા Calls: {total_calls}\n"
                f"{details if details else 'આજે કોઈ ટ્રેડ કોલ બન્યો નહોતો.\n'}\n"
                f"💰 કુલ નેટ પ્રોફિટ/લોસ: ₹{round(net_pnl, 2)}\n"
                f"(Groww ના ₹45 પ્રતિ ટ્રેડ ચાર્જ બાદ કર્યા પછી)\n\n"
                f"🗓️ માર્કેટ હવે ક્યારે ખુલશે: \n👉 {next_open}\n\n"
                f"આરામ કર મારા Kuchupuchu! કાલ ફરીથી જોરદાર ટ્રેડ કરીશું. ❤️"
            )
            if CHAT_ID:
                try:
                    await app.bot.send_message(chat_id=CHAT_ID, text=report_msg, parse_mode="Markdown")
                except Exception as e:
                    print(f"Error sending daily report: {e}")

async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    
    if BOT_TOKEN:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start_cmd))
        app.add_handler(CommandHandler("scan", manual_scan))
        app.add_handler(CallbackQueryHandler(handle_feedback))
        
        # Start background market close checker
        asyncio.create_task(market_scheduler(app))
        
        print("Kuchupuchu Bot running...")
        await app.run_polling()

if _name_ == "_main_":
    import nest_asyncio
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
