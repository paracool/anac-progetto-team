from __future__ import annotations

import html
import re
import unicodedata
from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data:
            self.parts.append(data)


def clean_text(value: object | None) -> str:
    if value is None:
        return ""
    raw = str(value)
    parser = _TextExtractor()
    try:
        parser.feed(raw)
        raw = " ".join(part.strip() for part in parser.parts if part.strip()) or raw
    except Exception:
        pass
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()


def normalize_string(value: object | None) -> str:
    return clean_text(value)


def normalize_place(value: object | None) -> str:
    text = clean_text(value)
    if not text:
        return ""
    # Mantiene le barre nelle denominazioni bilingui, ad esempio Bolzano/Bozen.
    parts = [part.strip() for part in text.split("/")]
    normalized = "/".join(_title_place(part) for part in parts)
    return normalized


def _title_place(value: str) -> str:
    small_words = {"di", "del", "della", "dei", "delle", "da", "in", "sul", "sulla"}
    words = []
    for index, token in enumerate(value.lower().split()):
        if index > 0 and token in small_words:
            words.append(token)
            continue
        pieces = token.split("-")
        words.append("-".join(piece[:1].upper() + piece[1:] for piece in pieces))
    return " ".join(words)


def canonical_key(value: object | None) -> str:
    text = normalize_place(value)
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", ascii_text).strip().casefold()


def clean_identifier(value: object | None) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", clean_text(value)).strip("_")
