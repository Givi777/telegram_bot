import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from bot.handlers import start, button
from web.app import app

def main():
    bot_token = os.getenv('BOT_TOKEN')
    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    # Start Flask in a separate thread
    from threading import Thread
    thread = Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))))
    thread.start()

    # Start polling the Telegram bot
    application.run_polling()

if __name__ == '__main__':
    main()
