import os
import threading
import logging
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from google import genai

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ----------------- FLASK SERVER (Render Port Binding) -----------------
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Traderboy Bot Live Che!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)
# ----------------------------------------------------------------------

# ----------------- CONFIGURATION -----------------
TELEGRAM_BOT_TOKEN = "8903313420:AAF7NvVa0RHQlFdMqNbuE0gsrBZDtcCshA8"
GEMINI_API_KEY = "AQ.Ab8RN6IJ5SW8zTD23TZr9KrLLnda0CiLFMoDaeEdXFHOhIQSjQ"
ALLOWED_USERS = [609657351]
# -------------------------------------------------

# New Google GenAI Client
client = genai.Client(api_key=GEMINI_API_KEY)

def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_USERS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("Maaf karjo! Aa private bot che.")
        return

    msg = (
        "❤️ hii my Kuchupuchu!\n\n"
        "હું તારો પર્સનલ ટ્રેડિંગ એજન્ટ છું. મેં આપણી ₹3,000 ની કેપિટલ યાદ રાખી છે.\n\n"
        "📊 માર્કેટ સ્ટેટસ: બંધ છે 🔴\n"
        "⏰ નેક્સ્ટ માર્કેટ ઓપન: Monday સવારે 9:15 AM વાગ્યે\n\n"
        "હું લાઈવ માર્કેટમાં તને એલર્ટ મોકલીશ અને સાંજે 3:30 વાગ્યે આખા દિવસનો નફો-નુકસાન રિપોર્ટ આપીશ!\n"
        "ટેસ્ટ કરવા માટે /scan લખી શકીશ."
    )
    await update.message.reply_text(msg)

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("Maaf karjo! Aa private bot che.")
        return

    await update.message.reply_text("🔍 માર્કેટ સ્કેન થઈ રહ્યું છે... હાલમાં કોઈ નવો ટ્રેડ એલર્ટ નથી!")

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("Maaf karjo! Aa private bot che.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    user_text = update.message.text
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_text,
            config={
                "system_instruction": "તમે એક સ્માર્ટ ગુજરાતી ટ્રેડિંગ આસિસ્ટન્ટ છો. Kuchupuchu સાથે પ્રેમથી, સરળ ગુજરાતીમાં ટૂંકા જવાબો આપો."
            }
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:300]}")

def main():
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat))

    print("Bot chalu thai gayo che...")
    app.run_polling()

if __name__ == '__main__':
    main()
