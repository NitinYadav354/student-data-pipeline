"""Deterministic CSV cleaning rules for the student roster."""

from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from typing import Any

import pandas as pd
from rapidfuzz import fuzz, process

REQUIRED_COLUMNS = ("Name", "Gender", "Grade", "Math", "Science", "English")
SCORE_COLUMNS = ("Math", "Science", "English")


@dataclass
class CleaningResult:
    students: list[dict[str, Any]]
    report: dict[str, Any]


def _text(value: object) -> str:
    return "" if pd.isna(value) else str(value).strip()


def _name(value: object) -> str:
    return re.sub(r"\s+", " ", _text(value).strip(" '\"`" )).title()


def _gender(value: object) -> str:
    token = _text(value).casefold()
    if token in {"m", "male", "boy"}:
        return "Male"
    if token in {"f", "female", "girl"}:
        return "Female"
    return "Unknown"


def _grade(value: object) -> int | None:
    match = re.search(r"\d+", _text(value))
    return int(match.group()) if match else None


def _score(value: object) -> float | None:
    match = re.search(r"-?\d+(?:\.\d+)?", _text(value))
    if not match:
        return None
    score = float(match.group())
    return score if 0 <= score <= 100 else None


def clean_csv(contents: bytes) -> CleaningResult:
    try:
        raw = pd.read_csv(BytesIO(contents), dtype=object)
    except Exception as exc:  # pandas provides useful parser errors to the client
        raise ValueError("The uploaded file is not a readable CSV.") from exc

    raw.columns = [str(column).strip() for column in raw.columns]
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in raw.columns]
    if missing_columns:
        raise ValueError(f"Missing required column(s): {', '.join(missing_columns)}.")

    rejected: list[dict[str, Any]] = []
    normalized: list[dict[str, Any]] = []
    unknown_gender = 0
    total_corrected = 0
    for row_number, (_, row) in enumerate(raw.iterrows(), start=2):
        name, grade = _name(row["Name"]), _grade(row["Grade"])
        scores = {column: _score(row[column]) for column in SCORE_COLUMNS}
        reasons = []
        if not name:
            reasons.append("missing name")
        if grade is None:
            reasons.append("invalid or missing grade")
        bad_scores = [column for column, value in scores.items() if value is None]
        if bad_scores:
            reasons.append(f"invalid, missing, or out-of-range score: {', '.join(bad_scores)}")
        if reasons:
            rejected.append({"row": row_number, "reason": "; ".join(reasons)})
            continue
        gender = _gender(row["Gender"])
        unknown_gender += gender == "Unknown"
        total = round(sum(scores.values()), 2)
        source_total = _score(row["Total"]) if "Total" in raw.columns else None
        total_corrected += source_total != total
        normalized.append({"name": name, "gender": gender, "grade": grade, **scores, "total": total})

    unique: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    duplicate_count = 0
    for student in normalized:
        signature = tuple(student[key] for key in ("name", "gender", "grade", *SCORE_COLUMNS))
        if signature in seen:
            duplicate_count += 1
            continue
        seen.add(signature)
        unique.append(student)

    review_flags: list[dict[str, str]] = []
    names = [student["name"] for student in unique]
    for index, name in enumerate(names):
        match = process.extractOne(name, names[index + 1 :], scorer=fuzz.ratio, score_cutoff=88)
        if match:
            review_flags.append({"name": name, "possible_match": match[0], "similarity": str(round(match[1]))})

    students = [{"id": index + 1, **student, "status": "Active"} for index, student in enumerate(unique)]
    report = {
        "input_rows": len(raw), "accepted_rows": len(students), "rejected_rows": len(rejected),
        "exact_duplicates_removed": duplicate_count, "totals_recalculated": total_corrected,
        "unknown_gender_normalized": unknown_gender, "rejected": rejected[:100],
        "possible_duplicate_review": review_flags[:50],
        "rules": [
            "Names are trimmed, surrounding stray quotes are removed, and title-cased.",
            "Gender values M/male and F/female are standardized; unknown values become Unknown.",
            "Grade numbers are extracted from labels such as 'Grade 11'.",
            "Scores accept a numeric value embedded in text (for example '28 marks'); values outside 0-100 and missing scores reject the row.",
            "Total is recalculated from the three validated subject scores; the uploaded Total is never trusted.",
            "Only exact normalized duplicate records are removed. Similar names are flagged for review, never merged automatically.",
        ],
    }
    return CleaningResult(students=students, report=report)
