from flask import Flask
from app.config import Config
from app.extensions import db, migrate
from app.routes import register_routes
from app import models

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register routes
    register_routes(app)

    return app