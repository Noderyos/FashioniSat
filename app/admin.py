from flask import Blueprint, request, redirect, url_for
from .extensions import login_manager, User
from flask_login import current_user, login_user, login_required, logout_user
import sqlite3
import os
from hashlib import sha1
from config_loader import config

bp = Blueprint("admin", __name__, url_prefix="/admin")


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@bp.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("admin.login"))
    return f"Logged in as {current_user.id}"


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(os.path.join(config.DATA_FOLDER, "db.sqlite"))
        cur = conn.cursor()

        cur.execute("SELECT user.passwd_hash FROM user WHERE username=?", (username,))
        result = cur.fetchone()

        if result is None:
            return False

        (passwd_hash,) = result

        if passwd_hash == sha1(password.encode()).hexdigest():
            login_user(User(username))
            return redirect(url_for("admin.index"))

        return "Invalid credentials", 401

    return """
    <form method="post">
        <input name="username" placeholder="Username">
        <input name="password" type="password" placeholder="Password">
        <button type="submit">Login</button>
    </form>
    """


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("admin.index"))
