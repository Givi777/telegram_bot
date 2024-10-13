from web import create_app
from bot.bot import run_bot
from threading import Thread
import os

def main():
    # Start Flask app
    app = create_app()

    # Start Telegram bot in a separate thread
    thread = Thread(target=run_bot)
    thread.start()

    # Run the Flask app
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

if __name__ == "__main__":
    main()
