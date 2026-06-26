from __future__ import annotations

import math
import re
import unicodedata
from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd


EMPTY_MARKERS = {"", "....", "...", "-", "--", "nan", "none", "null"}


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return "" if text.lower() in EMPTY_MARKERS else text


def normalize_key(value: Any) -> str:
    text = strip_accents(clean_text(value).lower())
    text = text.replace("º", "").replace("°", "")
    text = re.sub(r"[^a-z0-9/ ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_value(value: Any) -> Any:
    text = clean_text(value)
    if not text:
        return None
    return text


def parse_int(value: Any) -> int | None:
    text = clean_text(value)
    if not text:
        return None
    match = re.search(r"-?\d+", text)
    return int(match.group()) if match else None


def parse_date(value: Any) -> date | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = clean_text(value)
    if not text:
        return None
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def format_br_date(value: Any) -> str | None:
    parsed = parse_date(value)
    return parsed.strftime("%d/%m/%Y") if parsed else None


def add_days(start: date, days: int) -> date:
    return start + timedelta(days=max(days - 1, 0))


def date_range_overlaps(start_a: date, end_a: date, start_b: date, end_b: date) -> bool:
    return start_a <= end_b and start_b <= end_a
