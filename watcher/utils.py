import os
import hashlib
from config_loader import config

BASE_PATH = os.path.abspath(config.SATDUMP_FOLDER)


def is_image(name: str) -> bool:
    exts = (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif", ".tiff", ".tif")
    return name.lower().endswith(exts)


def hash_file(path: str, mode="sha1") -> str:
    h = hashlib.new(mode)
    with open(path, "rb") as file:
        block = file.read(config.HASH_BUFFER_SIZE)
        while block:
            h.update(block)
            block = file.read(config.HASH_BUFFER_SIZE)
    return h.hexdigest()

from datetime import datetime

def parse_folder_name(folder_name: str):
    parts = folder_name.split("_")
    if len(parts) >= 3:
        date_str = f"{parts[0]}_{parts[1]}"
        satellite = parts[2]
        try:
            timestamp = int(datetime.strptime(date_str, "%Y-%m-%d_%H-%M").timestamp())
            return satellite, timestamp
        except ValueError:
            pass
    return "Unknown", 0
