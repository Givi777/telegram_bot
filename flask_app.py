from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "<h1>Heroku Python Flask Test Page</h1><p>Your Flask app is running successfully on Heroku!</p>"

def tgbot():
    return app
