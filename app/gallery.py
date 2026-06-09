from collections import defaultdict

from flask import Blueprint, render_template, send_from_directory, request
from datetime import datetime
import sqlite3
import os
from config_loader import config

bp = Blueprint("gallery", __name__, url_prefix="/gallery")


def get_gallery(page_idx: int) -> list:
    conn = sqlite3.connect(os.path.join(config.DATA_FOLDER, "db.sqlite"))
    cur = conn.cursor()

    query = """
        WITH elements AS (
            SELECT COALESCE(p.dataset_id, -p.id) AS gid, *
            FROM product p
        )
        SELECT
            e.gid,
            e.id AS product_id,
            e.path,
            e.timestamp,
            e.satellite,
            e.instrument
        FROM elements e
        WHERE e.gid IN (
            SELECT DISTINCT e.gid
            FROM elements e
            ORDER BY e.timestamp DESC
            LIMIT ? OFFSET ?
        )
        ORDER BY timestamp DESC;
    """

    cur.execute(query, (5, page_idx * 5))
    products = cur.fetchall()

    data = []
    dataset = {}

    if products:
        prod_id_to_path = {
            prod_id: prod_path for _, prod_id, prod_path, _, _, _ in products
        }
        prod_ids = tuple(prod_id_to_path.keys())

        cur.execute(
            f"SELECT product_id, file, thumb_file FROM image WHERE product_id IN ({",".join("?" * len(prod_ids))})",
            prod_ids,
        )

        images_by_prod = defaultdict(list)
        for prod_id, file, thumb_file in cur.fetchall():
            path = prod_id_to_path[prod_id]
            images_by_prod[prod_id].append(
                {
                    "name": file,
                    "data": f"data/{path}/{file}",
                    "thumb": f"thumbnails/{thumb_file}" if thumb_file else "",
                }
            )

        current_dataset = None
        for dat_id, prod_id, prod_path, timestamp, sat, instr in products:
            images = images_by_prod.get(prod_id, [])

            if not images:
                print(f"No images for {prod_path}")
                continue

            date_str = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S")
            product_info = {"instrument": instr, "images": images}

            if dat_id != current_dataset:
                if dataset:
                    data.append(dataset)
                current_dataset = dat_id
                dataset = {
                    "is_dataset": dat_id > 0,
                    "satellite": sat,
                    "date": date_str,
                    "products": [],
                }

            if dat_id is None:
                dataset["products"] = [product_info]
            else:
                dataset["products"].append(product_info)
        data.append(dataset)

    cur.close()
    conn.close()

    return data


@bp.route("/")
def index():
    page_idx_str = request.args.get("page", "1")
    page_idx = 0
    if page_idx_str.isdigit():
        page_idx = max(0, int(page_idx_str) - 1)

    data = get_gallery(page_idx)
    return render_template("gallery.html", data=data)


@bp.route("/thumbnails/<name>")
def thumbnails(name):
    return send_from_directory(os.path.join(config.DATA_FOLDER, "thumbnails"), name)


@bp.route("/data/<path:path>")
def data(path):
    return send_from_directory(config.SATDUMP_FOLDER, path)
