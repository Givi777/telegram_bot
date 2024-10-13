import os
from dotenv import load_dotenv
from bot_commands import setup_bot
from flask_app import create_flask_app
from threading import Thread

load_dotenv()

def main():
    print("Starting the bot...")

    flask_app = create_flask_app()
    thread = Thread(target=lambda: flask_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))))
    thread.start()

    setup_bot()

if __name__ == '__main__':
    main()
