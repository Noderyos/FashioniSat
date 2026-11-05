import os
import json
import cbor2
import sqlite3

from .utils import hash_file, is_image, BASE_PATH, parse_folder_name

from . import LOGGER


def infer_dataset(conn: sqlite3.Connection, relative_path: str) -> int:
    cur = conn.cursor()
    cur.execute("SELECT id FROM dataset WHERE path = ?", (relative_path,))
    res = cur.fetchone()
    if res:
        return res[0]
    
    folder_name = os.path.basename(relative_path)
    satellite, timestamp = parse_folder_name(folder_name)
    
    cur.execute(
        "INSERT INTO dataset(path, sha1, satellite, timestamp) VALUES (?, ?, ?, ?)",
        (relative_path, "0"*40, satellite, timestamp)
    )
    return cur.lastrowid


def infer_product(conn: sqlite3.Connection, relative_path: str) -> int:
    cur = conn.cursor()
    cur.execute("SELECT id FROM product WHERE path = ?", (relative_path,))
    res = cur.fetchone()
    if res:
        return res[0]
        
    parent_relative = os.path.dirname(relative_path)
    if not parent_relative:
        dataset_relative = relative_path
        instrument = "Unknown"
    else:
        dataset_relative = parent_relative
        instrument = os.path.basename(relative_path)
        
    cur.execute("SELECT id, satellite, timestamp FROM dataset WHERE path = ?", (dataset_relative,))
    ds_res = cur.fetchone()
    
    if ds_res:
        dataset_id = ds_res[0]
        satellite = ds_res[1]
        timestamp = ds_res[2]
    else:
        dataset_id = None
        satellite, timestamp = parse_folder_name(os.path.basename(dataset_relative))
        
    cur.execute(
        "INSERT INTO product(dataset_id, path, sha1, instrument, satellite, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (dataset_id, relative_path, "0"*40, instrument, satellite, timestamp)
    )
    return cur.lastrowid

def process_cadu(conn: sqlite3.Connection, cadu_path: str):
    cur = conn.cursor()
    cadu = os.path.basename(cadu_path)
    cadu_hash = hash_file(cadu_path)
    dataset_folder = os.path.dirname(cadu_path)
    relative = os.path.relpath(dataset_folder, BASE_PATH)
    

    dataset_id = infer_dataset(conn, relative)
    
    # Link orphaned products
    cur.execute("UPDATE product SET dataset_id = ? WHERE path LIKE ? AND dataset_id IS NULL", (dataset_id, relative + "/%"))
    
    cur.execute("SELECT sha1 FROM cadu_file WHERE dataset_id = ? AND file = ?", (dataset_id, cadu))
    res = cur.fetchone()
    if not res:
        LOGGER.debug(f"New cadu {relative}/{cadu}")
        cur.execute(
            "INSERT INTO cadu_file(dataset_id, file, sha1) VALUES (?, ?, ?)",
            (dataset_id, cadu, cadu_hash)
        )
    elif res[0] != cadu_hash:
        LOGGER.debug(f"Updating cadu {relative}/{cadu}")
        cur.execute(
            "UPDATE cadu_file SET sha1 = ? WHERE dataset_id = ? AND file = ?",
            (cadu_hash, dataset_id, cadu)
        )
    
    cur.close()
    conn.commit()


def process_image(conn: sqlite3.Connection, image_path: str, from_product: bool):
    cur = conn.cursor()

    image = os.path.basename(image_path)
    image_hash = hash_file(image_path)

    relative = os.path.relpath(image_path, BASE_PATH)
    prod_relative = os.path.dirname(relative)
    cur.execute("SELECT id FROM product WHERE path = ?", (prod_relative,))
    result = cur.fetchone()
    if not result:
        prod_id = infer_product(conn, prod_relative)
    else:
        (prod_id,) = result

    cur.execute(
        "SELECT sha1 FROM image WHERE product_id = ? AND file = ?", (prod_id, image)
    )
    result = cur.fetchone()
    if not result:
        LOGGER.debug(f"New image {relative}")
        # from_product will be updated if product.cbor is updated
        cur.execute(
            "INSERT INTO image(product_id, file, sha1, thumb_file, from_product) "
            "VALUES (?, ?, ?, ?, ?)",
            (prod_id, image, image_hash, None, from_product),
        )
    elif image_hash != result[0]:
        LOGGER.debug(f"Updating image {relative}")
        if from_product:
            cur.execute(
                "UPDATE image SET sha1 = ?, thumb_file = ?, from_product = ?"
                "WHERE product_id = ? AND file = ?",
                (image_hash, None, True, prod_id, image),
            )
        else:
            cur.execute(
                "UPDATE image SET sha1 = ?, thumb_file = ?"
                "WHERE product_id = ? AND file = ?",
                (image_hash, None, prod_id, image),
            )

    cur.close()
    conn.commit()


def process_dataset(conn: sqlite3.Connection, dataset_path: str):
    cur = conn.cursor()

    with open(dataset_path, "r") as f:
        raw_data = f.read()

    dataset_hash = hash_file(dataset_path)
    dataset_folder = os.path.dirname(dataset_path)
    relative = os.path.relpath(dataset_folder, BASE_PATH)

    cur.execute(
        "SELECT COUNT(*) FROM dataset WHERE path = ? AND sha1 = ?",
        (relative, dataset_hash),
    )
    need_update = cur.fetchone()[0] == 0
    if not need_update:
        return

    LOGGER.debug(f"Updating dataset {relative}")

    json_data = json.loads(raw_data)
    satellite = json_data.get("satellite", None)
    timestamp = json_data.get("timestamp", 0)

    cur.execute("SELECT COUNT(*) FROM dataset WHERE path = ?", (relative,))

    if cur.fetchone()[0] == 0:
        LOGGER.debug(f"New dataset {relative}")
        cur.execute(
            "INSERT INTO dataset(path, sha1, satellite, timestamp)"
            "VALUES (?, ?, ?, ?)",
            (relative, dataset_hash, satellite, timestamp),
        )
    else:
        LOGGER.info(f"Existing dataset {relative}")
        cur.execute(
            "UPDATE dataset SET "
            "sha1 = ?, satellite = ?, timestamp = ?"
            "WHERE path = ?",
            (dataset_hash, satellite, timestamp, relative),
        )

    cur.execute("SELECT id FROM dataset WHERE path = ?", (relative,))
    dataset_id = cur.fetchone()[0]

    for product in json_data["products"]:
        prod_path = os.path.join(relative, product)
        prod_path = os.path.normpath(prod_path)
        cur.execute("SELECT COUNT(*) FROM product WHERE path = ?", (prod_path,))
        if cur.fetchone()[0]:
            cur.execute(
                "UPDATE product SET dataset_id = ? WHERE path = ?",
                (dataset_id, prod_path),
            )
        else:
            cur.execute(
                "INSERT INTO product(dataset_id, path, sha1, timestamp) VALUES (?, ?, ?, ?)",
                (dataset_id, prod_path, "0" * 40, timestamp),
            )

    cur.close()
    conn.commit()


def process_product(conn: sqlite3.Connection, product_path: str):
    cur = conn.cursor()

    with open(product_path, "rb") as f:
        raw_data = f.read()

    product_hash = hash_file(product_path)
    product_folder = os.path.dirname(product_path)
    relative = os.path.relpath(product_folder, BASE_PATH)

    cur.execute(
        "SELECT COUNT(*) FROM product WHERE path = ? AND sha1 = ?",
        (relative, product_hash),
    )
    need_update = cur.fetchone()[0] == 0
    if not need_update:
        return

    LOGGER.info(f"Updating product {relative}")

    cbor = cbor2.loads(raw_data)

    instrument = cbor["instrument"]
    satellite = cbor.get("product_source", None)
    timestamp = max(0, cbor.get("product_timestamp", 0))

    cur.execute("SELECT COUNT(*) FROM product WHERE path = ?", (relative,))

    if cur.fetchone()[0] == 0:
        LOGGER.info(f"New product {relative}")
        cur.execute(
            "INSERT INTO product(path, sha1, instrument, satellite, timestamp)"
            "VALUES (?, ?, ?, ?, ?)",
            (relative, product_hash, instrument, satellite, timestamp),
        )
    else:
        LOGGER.info(f"Existing product {relative}")
        if timestamp:
            cur.execute(
                "UPDATE product SET "
                "sha1 = ?, instrument = ?, satellite = ?, timestamp = ?"
                "WHERE path = ?",
                (product_hash, instrument, satellite, timestamp, relative),
            )
        else:
            cur.execute(
                "UPDATE product SET "
                "sha1 = ?, instrument = ?, satellite = ?"
                "WHERE path = ?",
                (product_hash, instrument, satellite, relative),
            )

    cur.close()
    conn.commit()

    if "images" in cbor:
        product_imgs = set(a["file"] for a in cbor["images"])
        images = set(
            (image, image in product_imgs)
            for image in os.listdir(product_folder)
            if is_image(image)
        )

        for image, from_product in images:
            image_path = os.path.join(product_folder, image)
            process_image(conn, image_path, from_product)
