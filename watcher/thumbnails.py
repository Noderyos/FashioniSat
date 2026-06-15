import os
import time
import pyvips
import sqlite3
import threading
from threading import Thread

from config_loader import config

THUMBNAILS_PATH = os.path.join(config.DATA_FOLDER, "thumbnails")

def thumbnails_updater():
    while True:
        conn = sqlite3.connect(os.path.join(config.DATA_FOLDER, "db.sqlite"))
        cur = conn.cursor()
        cur.execute(
            "SELECT image.product_id, image.file, product.path "
            "FROM image "
            "JOIN product ON product.id = image.product_id "
            "WHERE thumb_file IS NULL"
        )


        for prod_id, file, path in cur.fetchall():
            image_path = os.path.join(config.SATDUMP_FOLDER, path, file)
            print(f"[INFO] Processing thumbnail for {image_path}")

            img = pyvips.Image.new_from_file(str(image_path), access="sequential")
            resized = img.resize(config.THUMBNAIL_WIDTH / img.width)

            thumb_name = os.urandom(16).hex() + ".webp"
            out_path = os.path.join(THUMBNAILS_PATH, thumb_name)
            resized.write_to_file(out_path, Q=config.THUMBNAIL_Q)

            cur.execute(
                "UPDATE image SET thumb_file = ? WHERE product_id = ? AND file = ?",
                (thumb_name, prod_id, file),
            )

        cur.close()
        conn.commit()
        conn.close()
        time.sleep(config.THUMBNAIL_UPDATE_RATE)

def run_thumbnail() -> Thread:
    if not os.path.exists(THUMBNAILS_PATH):
        os.mkdir(THUMBNAILS_PATH)

    update_thread = threading.Thread(target=thumbnails_updater)
    update_thread.start()
    return update_thread
