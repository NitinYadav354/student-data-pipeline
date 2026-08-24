from __future__ import annotations

import csv
from io import StringIO

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from app.pipeline import clean_csv

router = APIRouter(tags=["students"])
_students: list[dict] = []
_report: dict | None = None


class StatusUpdate(BaseModel):
    status: str


def _require_roster() -> None:
    if _report is None:
        raise HTTPException(404, "Upload a CSV before requesting roster data.")


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)) -> dict:
    global _students, _report
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Please upload a .csv file.")
    try:
        result = clean_csv(await file.read())
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    _students, _report = result.students, result.report
    return {"students": _students, "report": _report}


@router.get("/students")
def students() -> dict:
    _require_roster()
    return {"students": _students, "report": _report}


@router.patch("/students/{student_id}/status")
def update_status(student_id: int, update: StatusUpdate) -> dict:
    _require_roster()
    if update.status not in {"Active", "Debarred"}:
        raise HTTPException(422, "Status must be Active or Debarred.")
    for student in _students:
        if student["id"] == student_id:
            student["status"] = update.status
            return student
    raise HTTPException(404, "Student not found.")


@router.get("/shortlist")
def shortlist(min_total: float = 0) -> dict:
    _require_roster()
    matches = [s for s in _students if s["status"] == "Active" and s["total"] >= min_total]
    average = round(sum(s["total"] for s in matches) / len(matches), 2) if matches else 0
    return {"students": matches, "stats": {"matched_count": len(matches), "average_total": average}}


@router.get("/shortlist/export")
def export_shortlist(min_total: float = 0) -> Response:
    rows = shortlist(min_total)["students"]
    stream = StringIO()
    writer = csv.DictWriter(stream, fieldnames=["source_row", "name", "gender", "grade", "Math", "Science", "English", "total", "status"])
    writer.writeheader()
    for student in rows:
        writer.writerow({"source_row": student["source_row"], "name": student["name"], "gender": student["gender"], "grade": student["grade"], "Math": student["Math"], "Science": student["Science"], "English": student["English"], "total": student["total"], "status": student["status"]})
    return Response(stream.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=shortlist.csv"})
