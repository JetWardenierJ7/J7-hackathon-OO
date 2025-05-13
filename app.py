from flask import Flask
import os
from main import bp as main_bp

def create_app(db_url=None):
    app = Flask(__name__)

    app.config["API_TITLE"] = "J7-hackathon-OO"
    app.config["API_VERSION"] = "1.0.0"
    app.config["API_DESCRIPTION"] = "A simple API for the J7 hackathon"

    app.register_blueprint(main_bp)

    return app

