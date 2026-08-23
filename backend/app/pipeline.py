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
