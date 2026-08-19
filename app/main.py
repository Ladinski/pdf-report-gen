from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from app.db import get_connection, init_db
from app.renderer import build_report_html, render_pdf
from app.reports import get_all_orders, get_report_data


app = FastAPI(title="PDF Report Generator")

BASE_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = BASE_DIR / "reports"


class ReportRequest(BaseModel):
    force: bool = False


@app.on_event("startup")
def startup():
    init_db()
    REPORTS_DIR.mkdir(exist_ok=True)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reports")
async def create_report(
    response: Response,
    request: ReportRequest | None = None,
):
    force = request.force if request else False
    today = datetime.now().date().isoformat()

    # Reuse today's completed report unless force=True.
    if not force:
        with get_connection() as conn:
            existing = conn.execute(
                """
                SELECT id, path, created_at
                FROM reports
                WHERE date(created_at) = ?
                  AND path != 'pending'
                ORDER BY id DESC
                LIMIT 1
                """,
                (today,),
            ).fetchone()

        if existing:
            response.status_code = 200

            return {
                "id": existing["id"],
                "file": f"/reports/{existing['id']}/file",
            }

    created_at = datetime.now().isoformat()

    # Create the report record first so we have an ID
    # to use for the PDF filename.
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

    # Query the data.
    data = get_report_data()
    orders = get_all_orders()

    # Convert the data into HTML.
    html = build_report_html(data, orders)

    # Playwright uses the synchronous API, so run it
    # outside FastAPI's main async event loop.
    await run_in_threadpool(
        render_pdf,
        html,
        str(output_path),
    )

    # Store the finished artifact path.
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

    response.status_code = 201

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

    if report["path"] == "pending":
        raise HTTPException(
            status_code=409,
            detail="Report is still being generated",
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