import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.renderer import build_report_html, render_pdf
from app.reports import get_all_orders, get_report_data


async def main():
    data = get_report_data()
    orders = get_all_orders()

    html = build_report_html(data, orders)

    output_path = "reports/test.pdf"

    await render_pdf(html, output_path)

    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())