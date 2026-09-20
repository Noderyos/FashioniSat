from flask import Blueprint, render_template, jsonify
import requests
from config_loader import config

bp = Blueprint("monitor", __name__, url_prefix="/monitor")

@bp.route("/")
def index():
    return render_template("monitor.html")

@bp.route("/api/data")
def api_data():
    try:
        response = requests.get(config.SATDUMP_URL + "/api", timeout=2)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
