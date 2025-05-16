"""Initiates the Flask application"""

import os
from functools import wraps
from flask import Flask, jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager, get_jwt, verify_jwt_in_request
from flask_migrate import Migrate
from flask_cors import CORS
import models
import secrets
from blocklist import BLOCKLIST
from db import db
from flask_sslify import SSLify

from resources.user import blp as UserBlueprint
from resources.search import blp as SearchBlueprint
from resources.timeline import blp as TimelineBlueprint
from resources.chat import blp as ChatBlueprint

from dotenv import load_dotenv


def create_app(db_url=None):
    """Creates the Flask application"""

    app = Flask(__name__)
    app.config["API_TITLE"] = "API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"

    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 10,
        "pool_recycle": 60,
        "pool_pre_ping": True,
    }

    load_dotenv()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["JWT_SECRET_KEY"] = os.getenv("HACKETON_SECRET_KEY")

    db.init_app(app)
    migrate = Migrate(app, db)
    api = Api(app)
    CORS(app)
    # SSLify(app)
    jwt = JWTManager(app)

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {"message": "The token has been revoked.", "error": "token_revoked"}
            ),
            401,
        )

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify({"message": "The token has expired.", "error": "token_expired"}),
            401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                {"message": "Signature verification failed.", "error": "invalid_token"}
            ),
            401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {
                    "description": "Request does not contain an access token.",
                    "error": "authorization_required",
                }
            ),
            401,
        )

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    "description": "The token is not fresh.",
                    "error": "fresh_token_required",
                }
            ),
            401,
        )

    @app.after_request
    def apply_caching(response):
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        return response

    api.register_blueprint(UserBlueprint)
    api.register_blueprint(SearchBlueprint)
    api.register_blueprint(TimelineBlueprint)
    api.register_blueprint(ChatBlueprint)

    return app
