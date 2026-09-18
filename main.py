import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import google.generativeai as genai

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ----------------- CONFIGURATION -----------------
TELEGRAM_BOT_TOKEN = "8903313420:AAF7NvVa0RHQ1FdMqnNbuE0gsrBZDtcCshA8"
GEMINI_API_KEY = "AQ.Ab8RN6IUFVLNSPbYJ0-6W-g4_79jOPggPod3bv_OIH1On9Ylug"
ALLOWED_USERS = [609657351]
# -------------------------------------------------

genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="તમે એક સ્માર્ટ ગુજરાતી ટ્રેડિંગ આસિસ્ટન્ટ છો. Kuchupuchu સાથે પ્રેમથી, સરળ ગુજરાતીમાં ટૂંકા જવાબો આપો."
)

def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_USERS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("માફ કરજો! આ પ્રાઇવેટ બોટ છે. તમે આ બોટ વાપરી શકતા નથી.")
        return

    msg = (
        "❤️ હેલ્લો મારૂ Kuchupuchu!\n\n"
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
        await update.message.reply_text("માફ કરજો! આ પ્રાઇવેટ બોટ છે.")
        return

    await update.message.reply_text("🔍 માર્કેટ સ્કેન થઈ રહ્યું છે... હાલમાં કોઈ નવો ટ્રેડ એલર્ટ નથી!")

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("માફ કરજો! આ પ્રાઇવેટ બોટ છે. તમે આ બોટ વાપરી શકતા નથી.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    user_text = update.message.text
    try:
        response = ai_model.generate_content(user_text)
        await update.message.reply_text(response.text)
    except Exception:
        await update.message.reply_text("અત્યારે કનેક્શનમાં થોડી સમસ્યા છે, ફરી ટ્રાય કરો.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat))

    print("Bot chalu thai gayo che...")
    app.run_polling()

if __name__ == '__main__':
    main()

