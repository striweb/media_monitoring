from flask import Flask
from pymongo import MongoClient

def create_app():
    app = Flask(__name__)
    client = MongoClient('mongodb://mongodb:27017/')
    db = client['media_monitoring']
    app.db = db

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
