from flask import Flask
from web.routes import web_bp

app = Flask(__name__)

app.register_blueprint(web_bp)
