import os
import hashlib
from config_loader import config

BASE_PATH = os.path.abspath(config.SATDUMP_FOLDER)


def is_image(name: str) -> bool:
    return not (name.endswith(".cbor") or name.endswith(".json"))


def hash_file(path: str, mode="sha1") -> str:
    h = hashlib.new(mode)
    with open(path, "rb") as file:
        block = file.read(config.HASH_BUFFER_SIZE)
        while block:
            h.update(block)
            block = file.read(config.HASH_BUFFER_SIZE)
    return h.hexdigest()
