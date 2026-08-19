from datetime import date
from html import escape

from playwright.async_api import async_playwright


def build_report_html(data: dict, orders: list[dict]) -> str:
    top_rows = "".join(
        f"""
        <tr>
            <td>{escape(row["product"])}</td>
            <td>{row["order_count"]}</td>
            <td>${row["revenue"]:.2f}</td>
        </tr>
        """
        for row in data["top_products"]
    )

    order_rows = "".join(
        f"""
        <tr>
            <td>{row["id"]}</td>
            <td>{escape(row["customer"])}</td>
            <td>{escape(row["product"])}</td>
            <td>${row["amount"]:.2f}</td>
            <td>{row["created_at"]}</td>
        </tr>
        """
        for row in orders
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Sales Report</title>

        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 32px;
                color: #222;
            }}

            h1 {{
                margin-bottom: 4px;
            }}

            .date {{
                color: #666;
                margin-bottom: 24px;
            }}

            .summary {{
                display: flex;
                gap: 20px;
                margin-bottom: 30px;
            }}

            .card {{
                border: 1px solid #ddd;
                padding: 16px;
                width: 200px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 30px;
            }}

            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}

            th {{
                background: #f3f3f3;
            }}

            tr {{
                break-inside: avoid;
                page-break-inside: avoid;
            }}

            thead {{
                display: table-header-group;
            }}
        </style>
    </head>

    <body>
        <h1>Sales Report</h1>
        <div class="date">Generated {date.today().isoformat()}</div>

        <div class="summary">
            <div class="card">
                <strong>Total Orders</strong>
                <div>{data["total_orders"]}</div>
            </div>

            <div class="card">
                <strong>Total Revenue</strong>
                <div>${data["total_revenue"]:.2f}</div>
            </div>
        </div>

        <h2>Top 5 Products by Revenue</h2>

        <table>
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Orders</th>
                    <th>Revenue</th>
                </tr>
            </thead>
            <tbody>
                {top_rows}
            </tbody>
        </table>

        <h2>All Orders</h2>

        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Customer</th>
                    <th>Product</th>
                    <th>Amount</th>
                    <th>Date</th>
                </tr>
            </thead>

            <tbody>
                {order_rows}
            </tbody>
        </table>
    </body>
    </html>
    """


async def render_pdf(html: str, output_path: str):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)

        page = await browser.new_page()

        await page.set_content(html)

        await page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
        )

        await browser.close()