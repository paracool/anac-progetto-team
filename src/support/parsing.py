from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

_NULLS = {"", "-", "n.d.", "nd", "null", "none", "nan", "non disponibile"}


def is_missing(value: object | None) -> bool:
    return value is None or str(value).strip().casefold() in _NULLS


def parse_decimal(value: object | None) -> Decimal | None:
    if is_missing(value):
        return None
    raw = str(value).strip().replace("€", "").replace("EUR", "").replace("eur", "")
    raw = re.sub(r"\s+", "", raw)
    raw = re.sub(r"[^0-9,\.\-+]", "", raw)
    if not raw or raw in {"-", "+", ".", ","}:
        return None

    comma = raw.rfind(",")
    dot = raw.rfind(".")
    if comma >= 0 and dot >= 0:
        decimal_sep = "," if comma > dot else "."
        thousands_sep = "." if decimal_sep == "," else ","
        raw = raw.replace(thousands_sep, "").replace(decimal_sep, ".")
    elif comma >= 0:
        tail = raw.split(",")[-1]
        if len(tail) in {1, 2}:
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", "")
    elif dot >= 0:
        parts = raw.split(".")
        if len(parts) > 2:
            if len(parts[-1]) in {1, 2}:
                raw = "".join(parts[:-1]) + "." + parts[-1]
            else:
                raw = "".join(parts)
        elif len(parts[-1]) == 3 and len(parts[0].lstrip("+-")) <= 3:
            raw = raw.replace(".", "")
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def parse_datetime(value: object | None) -> datetime | None:
    if is_missing(value):
        return None
    raw = str(value).strip()
    normalized = raw.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass
    formats = (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
    )
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def parse_date(value: object | None) -> date | None:
    parsed = parse_datetime(value)
    return parsed.date() if parsed else None


def combine_date_time(date_value: object | None, time_value: object | None) -> str:
    date_text = "" if is_missing(date_value) else str(date_value).strip()
    time_text = "" if is_missing(time_value) else str(time_value).strip()
    if not date_text:
        return ""
    if "T" in date_text or not time_text:
        return date_text
    return f"{date_text}T{time_text}"
