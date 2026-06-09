from flask import Flask
from .extensions import login_manager


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev"

    login_manager.init_app(app)

    from . import gallery, admin, index

    app.register_blueprint(gallery.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(index.bp)

    @app.context_processor
    def inject_navigation():
        nav_items = [
            {"endpoint": "index.index", "label": "announcements"},
            {"endpoint": "gallery.index", "label": "gallery"},
        ]
        return dict(nav_items=nav_items)

    return app
