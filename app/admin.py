from flask import Blueprint, request, redirect, url_for
from .extensions import login_manager, User
from flask_login import current_user, login_user, login_required, logout_user

bp = Blueprint("admin", __name__, url_prefix="/admin")

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)
