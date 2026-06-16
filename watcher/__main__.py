import os
import sqlite3

from .process import process_product, process_dataset, process_image
from .utils import is_image, BASE_PATH

from .watcher import run_filewatcher, run_updater
from .thumbnails import run_thumbnail

from . import LOGGER

from config_loader import config


def list_files_walk(base_path: str) -> None:
    conn = sqlite3.connect(os.path.join(config.DATA_FOLDER, "db.sqlite"))
    for root, dirs, files in os.walk(base_path):
        for file in files:
            full_path = os.path.join(root, file)
            if file == "product.cbor":
                process_product(conn, full_path)
            elif file == "dataset.json":
                process_dataset(conn, full_path)
            elif is_image(file):
                process_image(conn, full_path, False)
    conn.close()


def main():
    LOGGER.info(f"Scanning {BASE_PATH} ...")
    list_files_walk(BASE_PATH)

    LOGGER.info(f"Starting updater ...")
    updater = run_updater()

    LOGGER.info(f"Starting watcher thread ...")
    observer = run_filewatcher()

    LOGGER.info(f"Starting thumbnail thread ...")
    thumbnail = run_thumbnail()

    updater.join()
    observer.join()
    thumbnail.join()


if __name__ == "__main__":
    main()
