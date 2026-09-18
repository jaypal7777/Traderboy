import os
import logging
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Credentials & Config ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8903313420:AAF7NvVa0RHQlFdMqNbuE0gsrBZDtcCshA8")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
ADMIN_ID = 609657351  # Tamaru Telegram User ID (Master / Owner)

# Approved Users list (Admin default approved che)
approved_users = {ADMIN_ID}

# Groq Client Initialization
groq_client = Groq(api_key=GROQ_API_KEY)

# Render Web Service Dummy Server (Render Port Binding & Free tier keep-alive)
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "kuchupuchu bot is alive and running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# --- Telegram Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Friend"
    
    if user_id == ADMIN_ID:
        await update.message.reply_text(f"Hii maru kuchupuchu ❤️\nTamaro bot ready che! Hu fakt tamara mate active chu.")
    elif user_id in approved_users:
        await update.message.reply_text(f"Kem cho {user_name}! Bot ma tamaru swagat che.")
    else:
        # Bijo koi use kare tyare admin ne request jase
        await update.message.reply_text("Aa private bot che. Tamari permission request admin ne moklva ma aavi che. Manzoori malya pachhi tame vaapari sakso.")
        
        # Admin ne alert moklo
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ Navo User Permission Mange Che:\nName: {user_name}\nUsername: @{update.effective_user.username}\nUser ID: `{user_id}`\n\nAa user ne approve karva mate niche no command moklo:\n/approve {user_id}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error alerting admin: {e}")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Tame admin nathi, tamari pase aa command chalavvano adhikar nathi.")
        return
        
    if not context.args:
        await update.message.reply_text("Krupa kari ne User ID lakho. Example: /approve 123456789")
        return
        
    try:
        new_user_id = int(context.args[0])
        approved_users.add(new_user_id)
        await update.message.reply_text(f"User ID {new_user_id} ne successfully approve kari didha che!")
        
        # New approved user ne intimation moklo
        try:
            await context.bot.send_message(chat_id=new_user_id, text="Tamari permission approve thai gayi che! Have tame bot vapari shako cho.")
        except Exception:
            pass
    except ValueError:
        await update.message.reply_text("Aamany User ID. Fakt number lakho.")

async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Friend"
    user_message = update.message.text
    
    # Permission Check
    if user_id not in approved_users and user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Tamari pase aa bot vaparvani permission nathi. Admin approval ni rah juo.")
        # Admin alert
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"Unauthorized access try:\nUser: {user_name} (ID: `{user_id}`)\nMessage: {user_message}\nApprove: `/approve {user_id}`",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Admin alert error: {e}")
        return

    # Groq AI Call
    try:
        system_prompt = (
            "You are a loving, helpful personal AI friend and trader assistant named 'kuchupuchu'. "
            "Reply naturally in Gujarati (or Gujarati in English/Latin alphabet like 'kem cho'). "
            "Keep the tone friendly, caring, and smart. Assist with trading concepts, daily news, or casual chats warmly."
        )
        
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        reply = completion.choices[0].message.content
        await update.message.reply_text(reply)
        
    except Exception as e:
        logger.error(f"Groq API Error: {e}")
        await update.message.reply_text("Reva dyo ne, connectivity issue che! Fari try karo.")

def main():
    # Render Web Server background thread ma chalu karo
    Thread(target=run_web, daemon=True).start()
    
    # Telegram Bot Polling
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat))
    
    logger.info("Bot starting polling...")
    app.run_polling()

if __name__ == "__main__":
    main()