from flask import Blueprint, render_template

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    message = "Your Flask app is running successfully on Heroku!"
    return render_template('index.html', message=message)
