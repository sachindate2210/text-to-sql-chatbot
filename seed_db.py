"""Create a small sample sales database (SQLite) to query in plain English."""
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).with_name("sales.db")

CUSTOMERS = [
    ("Asha Traders", "Mumbai", "Retail"), ("Bharat Foods", "Pune", "Wholesale"),
    ("Cosmo Mart", "Nagpur", "Retail"), ("Delta Pharma", "Hyderabad", "Healthcare"),
    ("Evergreen Agro", "Indore", "Wholesale"), ("Fusion Tech", "Bengaluru", "Corporate"),
    ("Galaxy Stores", "Chennai", "Retail"), ("Horizon Labs", "Bengaluru", "Healthcare"),
    ("Indus Infra", "Delhi", "Corporate"), ("Jai Hind Kirana", "Nagpur", "Retail"),
]
PRODUCTS = [
    ("Laptop Pro 14", "Electronics", 72000), ("Wireless Mouse", "Accessories", 900),
    ("27-inch Monitor", "Electronics", 18500), ("Office Chair", "Furniture", 11000),
    ("Standing Desk", "Furniture", 26000), ("USB-C Dock", "Accessories", 6500),
    ("Noise-cancel Headset", "Accessories", 8200), ("Tablet 11", "Electronics", 34000),
]


def build(db_path: Path = DB_PATH, seed: int = 42) -> Path:
    random.seed(seed)
    db_path.unlink(missing_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript(
        """
        CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, city TEXT, segment TEXT);
        CREATE TABLE products  (id INTEGER PRIMARY KEY, name TEXT, category TEXT, unit_price INTEGER);
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(id),
            product_id  INTEGER REFERENCES products(id),
            quantity INTEGER,
            order_date TEXT,          -- YYYY-MM-DD
            status TEXT               -- delivered | shipped | cancelled
        );
        """
    )
    con.executemany("INSERT INTO customers(name, city, segment) VALUES (?,?,?)", CUSTOMERS)
    con.executemany("INSERT INTO products(name, category, unit_price) VALUES (?,?,?)", PRODUCTS)
    start = date(2025, 1, 1)
    orders = []
    for _ in range(400):
        orders.append((
            random.randint(1, len(CUSTOMERS)),
            random.randint(1, len(PRODUCTS)),
            random.randint(1, 12),
            (start + timedelta(days=random.randint(0, 364))).isoformat(),
            random.choices(["delivered", "shipped", "cancelled"], weights=[80, 12, 8])[0],
        ))
    con.executemany(
        "INSERT INTO orders(customer_id, product_id, quantity, order_date, status) VALUES (?,?,?,?,?)", orders
    )
    con.commit()
    con.close()
    return db_path


if __name__ == "__main__":
    print("Created", build())
