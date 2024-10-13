from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from bot.handlers import start, button
import os

def run_bot():
    bot_token = os.getenv('BOT_TOKEN')
    application = Application.builder().token(bot_token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    # Start polling for updates
    application.run_polling()
