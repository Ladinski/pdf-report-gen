from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool
from app.db import get_connection, init_db
from app.renderer import build_report_html, render_pdf
from app.reports import get_all_orders, get_report_data
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsProactorEventLoopPolicy()
    )

app = FastAPI(title="PDF Report Generator")

REPORTS_DIR = Path("reports")


@app.on_event("startup")
def startup():
    init_db()
    REPORTS_DIR.mkdir(exist_ok=True)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reports", status_code=201)
async def create_report():
    created_at = datetime.now().isoformat()

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO reports (path, created_at)
            VALUES (?, ?)
            """,
            ("pending", created_at),
        )

        report_id = cursor.lastrowid
        conn.commit()

    output_path = REPORTS_DIR / f"{report_id}.pdf"

    data = get_report_data()
    orders = get_all_orders()

    html = build_report_html(data, orders)

    await run_in_threadpool(
    render_pdf,
    html,
    str(output_path),
)

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE reports
            SET path = ?
            WHERE id = ?
            """,
            (str(output_path), report_id),
        )
        conn.commit()

    return {
        "id": report_id,
        "file": f"/reports/{report_id}/file",
    }


@app.get("/reports/{report_id}")
def get_report(report_id: int):
    with get_connection() as conn:
        report = conn.execute(
            """
            SELECT id, path, created_at
            FROM reports
            WHERE id = ?
            """,
            (report_id,),
        ).fetchone()

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return {
        "id": report["id"],
        "created_at": report["created_at"],
        "file": f"/reports/{report_id}/file",
    }


@app.get("/reports/{report_id}/file")
def download_report(report_id: int):
    with get_connection() as conn:
        report = conn.execute(
            """
            SELECT path
            FROM reports
            WHERE id = ?
            """,
            (report_id,),
        ).fetchone()

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    path = Path(report["path"])

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Report file not found",
        )

    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename=f"report-{report_id}.pdf",
    )