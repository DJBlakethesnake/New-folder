import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()

DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)

    BASE_DIR = "/home/students/even/2028/bdavis80/public_html/New-folder"
    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

    os.makedirs(INSTANCE_DIR, exist_ok=True)

    app.config["SECRET_KEY"] = "change-this-secret-key"

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///" +
        os.path.join(INSTANCE_DIR, DB_NAME)
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")

    from .models import User

    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app

