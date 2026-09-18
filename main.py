import time
import logging
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Credentials
TELEGRAM_BOT_TOKEN = "8903313420:AAF7NvVa0RHQlFdMqNbuE0gsrBZDtcCshA8"
GEMINI_API_KEY = "AQ.Ab8RN6IJ5SW8zTD23TZr9KrLLnda0CiLFMoDaeEdXFHOhIQSjQ"
USER_CHAT_ID = "609657351"

# Gemini Client setup
client = genai.Client(api_key=GEMINI_API_KEY)

# જો એક મોડેલમાં હાઈ ડિમાન્ડ (503) આવે તો કોડ ઓટોમેટિક બીજા મોડેલ પર જશે
BACKUP_MODELS = [
    "gemini-3.6-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash"
]

# Bot chalu thata j automatic samethi message moklashe
async def on_startup(app):
    try:
        await app.bot.send_message(
            chat_id=USER_CHAT_ID,
            text="Hii maru kuchupuchu ♥️"
        )
    except Exception as e:
        logging.error(f"Startup message error: {e}")

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

# Smart Message Handler with Auto-Retry & Fallback
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    reply_text = None

    # મોડેલ્સ એક પછી એક ટ્રાય કરશે જેથી ક્યારેય 503 કે 404 ના લીધે બોટ અટકે નહીં
    for model_name in BACKUP_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_text,
            )
            if response and response.text:
                reply_text = response.text
                break  # જવાબ મળી ગયો એટલે લૂપ બંધ થશે
        except Exception as err:
            logging.warning(f"Model {model_name} failed with error: {err}. Trying backup model...")
            time.sleep(0.5)
            continue

    if not reply_text:
        reply_text = "હાલમાં AI સર્વર પર ભારે ટ્રાફિક છે, કૃપા કરીને 1 મિનિટ પછી ફરી મેસેજ કરો."

    await update.message.reply_text(reply_text)

def main():
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(on_startup)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Kuchupuchu Bot chalu thai gyo che...")
    app.run_polling()

if __name__ == "__main__":
    main()
