# Hoi
from flask import Flask, jsonify, Blueprint

blp = Blueprint("main", __name__)


@blp.route("/test")
def home():
    return jsonify({"message": "Hello from inside Docker!"})
