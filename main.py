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
ADMIN_ID = 609657351  # Tamaru master Telegram ID

# Approved users set
approved_users = {ADMIN_ID}

# Groq Client
groq_client = Groq(api_key=GROQ_API_KEY)

# Render dummy web server (Port bind mate)
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "kuchupuchu bot is running smoothly!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
        
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Dost"
    
    if user_id == ADMIN_ID:
        await update.message.reply_text("Hii maru kuchupuchu ❤️\nTamaro bot ready che! Hu fakt tamara mate active chu.")
    elif user_id in approved_users:
        await update.message.reply_text(f"Kem cho {user_name}! Bot ma tamaru swagat che.")
    else:
        await update.message.reply_text("Aa private bot che. Tamari request admin ne mokli didhi che. Approval pachi vapari shaksho.")
        try:
            username_tag = f"@{update.effective_user.username}" if update.effective_user.username else "Nathi"
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"⚠️ Navo user bot vaparva mange che:\n"
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
        await update.message.reply_text("Krupa kari User ID aapo. Jethi: `/approve 123456789`", parse_mode="Markdown")
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
    if not update.effective_user or not update.message or not update.message.text:
        return
        
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Dost"
    user_msg = update.message.text
    
    # Permission verification
    if user_id not in approved_users and user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Tamari pase permission nathi. Admin na approval ni rah juo.")
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

    # Groq AI call
    try:
        system_prompt = (
            "You are a loving, helpful personal AI friend and trader assistant named 'kuchupuchu'. "
            "Reply naturally in Gujarati or Gujarati written in English/Latin letters (like 'kem cho', 'hu maja ma chu'). "
            "Be sweet, helpful, smart, and direct."
        )
        
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.7,
            max_tokens=700
        )
        
        answer = completion.choices[0].message.content
        await update.message.reply_text(answer)
        
    except Exception as e:
        logger.error(f"Groq API Error: {e}")
        await update.message.reply_text("Reva dyo ne, hal connectivity issue che! Fari try karo.")

def main():
    # Flask thread start karo
    server_thread = Thread(target=run_web, daemon=True)
    server_thread.start()
    
    # Telegram polling
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot sharu thayi gayo che...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
