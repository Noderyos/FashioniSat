import os
import time
from queue import Queue

import pyvips
import sqlite3
import threading
from threading import Thread

from config_loader import config

from . import LOGGER

THUMBNAILS_PATH = os.path.join(config.DATA_FOLDER, "thumbnails")

thumbnails_queues: list[Queue] = []


def thumbnails_worker(idx: int):
    while True:
        prod_id, file, path = thumbnails_queues[idx].get()
        image_path = os.path.join(config.SATDUMP_FOLDER, path, file)
        LOGGER.debug(f"Processing thumbnail for {image_path}")

        img = pyvips.Image.new_from_file(str(image_path), access="sequential")
        resized = img.resize(config.THUMBNAIL_WIDTH / img.width)

        thumb_name = os.urandom(16).hex() + ".webp"
        out_path = os.path.join(THUMBNAILS_PATH, thumb_name)
        resized.write_to_file(out_path, Q=config.THUMBNAIL_Q)

        conn = sqlite3.connect(os.path.join(config.DATA_FOLDER, "db.sqlite"))
        conn.execute(
            "UPDATE image SET thumb_file = ? WHERE product_id = ? AND file = ?",
            (thumb_name, prod_id, file),
        )
        conn.commit()
        conn.close()


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n))


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

        to_process = cur.fetchall()
        for i, els in enumerate(split(to_process, config.THUMBNAIL_THREADS)):
            conn.executemany(
                 "UPDATE image "
                 "SET thumb_file = '__processing__' "
                 "WHERE product_id = ? "
                 "AND file = ?",
                [(prod_id, file) for prod_id, file, _ in els]
            )
            for el in els:
                thumbnails_queues[i].put(el)

        cur.close()
        conn.close()

        time.sleep(config.THUMBNAIL_UPDATE_RATE)


def run_thumbnail() -> Thread:
    if not os.path.exists(THUMBNAILS_PATH):
        os.mkdir(THUMBNAILS_PATH)

    for i in range(config.THUMBNAIL_THREADS):
        thumbnails_queues.append(Queue())
        worker = threading.Thread(target=thumbnails_worker, args=(i,))
        worker.start()

    update_thread = threading.Thread(target=thumbnails_updater)
    update_thread.start()
    return update_thread
