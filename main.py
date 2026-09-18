import logging
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Tamari Keys & Token
TELEGRAM_BOT_TOKEN = "8903313420:AAF7NvVa0RHQlFdMqNbuE0gsrBZDtcCshA8"
GEMINI_API_KEY = "AQ.Ab8RN6IJ5SW8zTD23TZr9KrLLnda0CiLFMoDaeEdXFHOhIQSjQ"

# Gemini Client setup
client = genai.Client(api_key=GEMINI_API_KEY)

# Updated Model Name
MODEL_NAME = "gemini-3.6-flash"

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "⏰ નેક્સ્ટ માર્કેટ ઓપન: Monday સવારે 9:15 AM વાગ્યે\n\n"
        "હું લાઈવ માર્કેટમાં તને એલર્ટ મોકલીશ અને સાંજે 3:30 વાગ્યે આખા દિવસનો નફો-નુકસાન રિપોર્ટ આપીશ!\n"
        "ટેસ્ટ કરવા માટે /scan લખી શકીશ."
    )
    await update.message.reply_text(welcome_text)

# /scan command handler
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 માર્કેટ સ્કેન થઈ રહ્યું છે... હાલ કોઈ નવો બ્રેકઆઉટ નથી.")

# Normal message handler (Gemini Response)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_text,
        )
        reply_text = response.text
    except Exception as e:
        logging.error(f"Error: {e}")
        reply_text = "Reva dyo ne, hal connectivity issue che! Fari try karo."

    await update.message.reply_text(reply_text)

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Kuchupuchu Bot chalu thai gyo che...")
    app.run_polling()

if __name__ == "__main__":
    main()
