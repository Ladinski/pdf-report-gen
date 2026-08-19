from datetime import date, timedelta

from app.db import get_connection


def get_report_data():
    seven_days_ago = (date.today() - timedelta(days=6)).isoformat()

    with get_connection() as conn:
        total_orders = conn.execute(
            """
            SELECT COUNT(*) AS total_orders
            FROM orders
            """
        ).fetchone()["total_orders"]

        total_revenue = conn.execute(
            """
            SELECT ROUND(SUM(amount), 2) AS total_revenue
            FROM orders
            """
        ).fetchone()["total_revenue"]

        top_products = conn.execute(
            """
            SELECT
                product,
                COUNT(*) AS order_count,
                ROUND(SUM(amount), 2) AS revenue
            FROM orders
            GROUP BY product
            ORDER BY revenue DESC
            LIMIT 5
            """
        ).fetchall()

        orders_per_day = conn.execute(
            """
            SELECT
                created_at AS day,
                COUNT(*) AS order_count,
                ROUND(SUM(amount), 2) AS revenue
            FROM orders
            WHERE created_at >= ?
            GROUP BY created_at
            ORDER BY created_at ASC
            """,
            (seven_days_ago,),
        ).fetchall()

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "top_products": [dict(row) for row in top_products],
        "orders_per_day": [dict(row) for row in orders_per_day],
    }

def get_all_orders():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                customer,
                product,
                amount,
                created_at
            FROM orders
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]