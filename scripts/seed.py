import random
import sys
from datetime import date, timedelta
from pathlib import Path

# Allow importing from the project root when running:
# python scripts/seed.py
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db import get_connection, init_db


PRODUCTS = [
    "Laptop Stand",
    "Mechanical Keyboard",
    "Wireless Mouse",
    "USB-C Hub",
    "Webcam",
    "Desk Lamp",
]

CUSTOMERS = [
    "Alice",
    "Bob",
    "Charlie",
    "Diana",
    "Ethan",
    "Fatima",
    "George",
    "Hana",
]


def random_date():
    days_ago = random.randint(0, 29)
    return (date.today() - timedelta(days=days_ago)).isoformat()


def seed_orders(count: int = 200):
    init_db()

    orders = []

    for _ in range(count):
        orders.append(
            (
                random.choice(CUSTOMERS),
                random.choice(PRODUCTS),
                round(random.uniform(5, 200), 2),
                random_date(),
            )
        )

    with get_connection() as conn:
        # Makes the seed safe to run repeatedly.
        conn.execute("DELETE FROM orders")

        conn.executemany(
            """
            INSERT INTO orders (
                customer,
                product,
                amount,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            orders,
        )

        conn.commit()

        row = conn.execute(
            "SELECT COUNT(*) AS count FROM orders"
        ).fetchone()

        print(f"Seeded {row['count']} orders")


if __name__ == "__main__":
    seed_orders()