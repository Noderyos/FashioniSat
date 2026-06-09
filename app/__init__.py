from flask import Flask
from .extensions import login_manager

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev"

    login_manager.init_app(app)

    from . import gallery, admin

    app.register_blueprint(gallery.bp)
    app.register_blueprint(admin.bp)

    return app
