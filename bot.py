import os
from dotenv import load_dotenv
from flask import Flask
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from bot.handlers import start, button

load_dotenv()

bot_token = os.getenv('BOT_TOKEN')

app = Flask(__name__)

def main():
    print("Starting the bot...")
    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    from threading import Thread
    thread = Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001))))
    thread.start()

    application.run_polling()

if __name__ == '__main__':
    main()
