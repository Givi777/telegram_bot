from flask import Flask

def tgbot():
    app = Flask(__name__)

    @app.route('/')
    def index():
        return "<h1>Heroku Python Flask Test Page</h1><p>Your Flask app is running successfully on Heroku!</p>"

    return app
