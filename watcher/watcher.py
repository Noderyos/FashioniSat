import os
import time
import sqlite3
import threading
from threading import Thread

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver

from .utils import is_image, BASE_PATH
from .process import process_product, process_dataset, process_image, process_cadu

from config_loader import config

COOLDOWN = 10

update_queue = {}
update_lock = threading.Lock()


def update_puller():
    while True:
        now = time.time()
        to_process = []

        with update_lock:
            for path, timestamp in list(update_queue.items()):
                if now - timestamp >= COOLDOWN:
                    to_process.append(path)
                    del update_queue[path]

        if to_process:
            db_path = os.path.join(config.DATA_FOLDER, "db.sqlite")
            conn = sqlite3.connect(db_path)

            for path in to_process:
                file = os.path.basename(path)

                if file == "product.cbor":
                    process_product(conn, path)
                elif file.endswith(".cadu"):
                    process_cadu(conn, path)
                elif file == "dataset.json":
                    process_dataset(conn, path)
                elif is_image(file):
                    process_image(conn, path, False)
            conn.commit()
            conn.close()

        time.sleep(COOLDOWN)

class Handler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            with update_lock:
                update_queue[event.src_path] = time.time()


def run_filewatcher() -> BaseObserver:
    event_handler = Handler()
    observer = Observer()
    observer.schedule(event_handler, BASE_PATH, recursive=True)
    observer.start()
    return observer


def run_updater() -> Thread:
    update_thread = threading.Thread(target=update_puller)
    update_thread.start()
    return update_thread
