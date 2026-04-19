# flask app factory
import os
from flask import Flask
from .database import init_db, close_db


def create_app(testing=False):
    # set up and return the flask app
    app = Flask(__name__)

    # Configuration
    app.config["DATABASE"] = os.path.join(
        app.instance_path, "taskmanager.db"
    )
    app.config["TESTING"] = testing

    if testing:
        app.config["DATABASE"] = ":memory:"

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize database
    init_db(app)

    # Register teardown
    app.teardown_appcontext(close_db)

    # Register routes
    from .routes import api_bp
    app.register_blueprint(api_bp)

    return app
