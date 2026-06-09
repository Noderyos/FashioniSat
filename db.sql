CREATE TABLE IF NOT EXISTS dataset (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    sha1 CHAR(40) NOT NULL,
    satellite TEXT,
    timestamp DATETIME
);

CREATE TABLE IF NOT EXISTS product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER,
    path TEXT NOT NULL UNIQUE,
    sha1 CHAR(40) NOT NULL,
    instrument TEXT,
    satellite TEXT,
    timestamp DATETIME,
    FOREIGN KEY (dataset_id) REFERENCES dataset(id),
    FOREIGN KEY (instrument) REFERENCES instrument(instrument)
);

CREATE TABLE IF NOT EXISTS image (
    product_id INT NOT NULL,
    file TEXT NOT NULL,
    sha1 CHAR(40) NOT NULL,
    thumb_file TEXT,
    PRIMARY KEY (product_id, file),
    FOREIGN KEY (product_id) REFERENCES product(id)
);

CREATE TABLE IF NOT EXISTS instrument (
    instrument TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY,
    username VARCHAR(32) UNIQUE NOT NULL,
    passwd_hash CHAR(40) NOT NULL
);