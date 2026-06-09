from flask import Blueprint, render_template

bp = Blueprint("index", __name__, url_prefix="/")


@bp.route("/")
def index():
    return render_template(
        "index.html",
        announcements=[
            {
                "level": "info",
                "title": "This an INFO",
                "date": "now",
                "content": "Multi line\ncontent",
            },
            {
                "level": "importent",
                "title": "This is an IMPORTANT",
                "date": "tomorrow",
                "content": "THIS IS (not) VERY IMPORTANT",
            },
        ],
    )
