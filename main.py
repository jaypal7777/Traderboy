import os
import logging
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Credentials & Config ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8903313420:AAF7NvVa0RHQlFdMqNbuE0gsrBZDtcCshA8")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
ADMIN_ID = 609657351  # Master Owner Telegram ID

approved_users = {ADMIN_ID}
groq_client = Groq(api_key=GROQ_API_KEY)

# Render dummy web server (Port binding mate)
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "kuchupuchu bot is alive and running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# --- Active Model Finder ---
def get_available_groq_model():
    """Groq na server par thi active chat model automatically shodhi lese"""
    try:
        models = groq_client.models.list()
        for m in models.data:
            # Whisper સિવાયનું કોઈ પણ ટેક્સ્ટ મોડેલ પકડી લેશે
            if "whisper" not in m.id.lower():
                logger.info(f"Using auto-detected Groq model: {m.id}")
                return m.id
    except Exception as e:
        logger.error(f"Error fetching model list: {e}")
    return "llama3-8b-8192"

ACTIVE_MODEL = get_available_groq_model()

# --- Telegram Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
        
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Dost"
    
    if user_id == ADMIN_ID:
        await update.message.reply_text("Hii maru kuchupuchu ❤️\nTamaro bot fully ready che! Hu fakt tamara mate active chu.")
    elif user_id in approved_users:
        await update.message.reply_text(f"Kem cho {user_name}! Bot ma tamaru swagat che.")
    else:
        await update.message.reply_text("Aa private bot che. Tamari request admin ne mokli didhi che.")
        try:
            username_tag = f"@{update.effective_user.username}" if update.effective_user.username else "Nathi"
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"⚠️ Navo user permission mange che:\n"
                    f"Name: {user_name}\n"
                    f"Username: {username_tag}\n"
                    f"User ID: `{user_id}`\n\n"
                    f"Approve karva aa command moklo:\n`/approve {user_id}`"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Admin alert failure: {e}")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
        
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Tamari pase aa command chalavvano adhikar nathi.")
        return
        
    if not context.args:
        await update.message.reply_text("Krupaya User ID lakho. Example: `/approve 123456789`", parse_mode="Markdown")
        return
        
    try:
        target_id = int(context.args[0])
        approved_users.add(target_id)
        await update.message.reply_text(f"User ID `{target_id}` ne approve kari didha che!", parse_mode="Markdown")
        
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text="Tamari permission accept thai gayi che! Have tame bot vapari shako cho."
            )
        except Exception:
            pass
    except ValueError:
        await update.message.reply_text("Krupaya sacho number ID lakho.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ACTIVE_MODEL
    if not update.effective_user or not update.message or not update.message.text:
        return
        
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Dost"
    user_msg = update.message.text
    
    # Security check
    if user_id not in approved_users and user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Tamari pase permission nathi. Admin approval ni rah juo.")
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"Unauthorized prayatna:\n"
                    f"User: {user_name} (`{user_id}`)\n"
                    f"Message: {user_msg}\n"
                    f"Approve: `/approve {user_id}`"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error alerting admin: {e}")
        return

    # Groq AI call (Direct Active Model Call)
    try:
        system_prompt = (
            "You are a loving, reliable personal AI trading partner and friend named 'kuchupuchu'. "
            "Reply naturally in Gujarati or Gujarati Latin script (e.g. 'kem cho', 'hu maja ma chu'). "
            "Help with trading discipline, risk management, calculations, and daily chats warmly and smartly."
        )
        
        completion = groq_client.chat.completions.create(
            model=ACTIVE_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.7,
            max_tokens=700
        )
        
        reply = completion.choices[0].message.content
        await update.message.reply_text(reply)
        
    except Exception as e:
        logger.error(f"Groq API Error on {ACTIVE_MODEL}: {e}")
        # જો મોડેલમાં હજુ પણ વાંધો હોય તો ફરી લિસ્ટમાંથી નવું મોડેલ ખેંચશે
        ACTIVE_MODEL = get_available_groq_model()
        await update.message.reply_text("Reva dyo ne, hal connectivity issue che! Fari try karo.")

def main():
    Thread(target=run_web, daemon=True).start()
    
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot starting polling smoothly...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
