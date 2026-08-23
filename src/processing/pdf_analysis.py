from __future__ import annotations

import csv
import logging
from pathlib import Path

from src.support.config import ProjectPaths
from src.support.io_utils import ensure_dir, write_json

LOGGER = logging.getLogger(__name__)


def analyze_pdf(path: Path) -> dict:
    result = {"file": path.name, "pages": None, "text_chars": 0, "method": "none", "note": ""}
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        result["pages"] = len(reader.pages)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        result["text_chars"] = len(text.strip())
        result["method"] = "pypdf"
        if not result["text_chars"]:
            result["note"] = "PDF poco o non testuale; conservato come fonte originale."
        return result
    except Exception as first_error:
        result["note"] = f"pypdf: {first_error}"
    try:
        from pdfminer.high_level import extract_text

        text = extract_text(str(path)) or ""
        result["text_chars"] = len(text.strip())
        result["method"] = "pdfminer.six"
        return result
    except Exception as second_error:
        result["note"] += f"; pdfminer.six: {second_error}"
    return result


def analyze_pdfs(paths: ProjectPaths) -> list[dict]:
    rows = [analyze_pdf(path) for path in sorted(paths.pdf_dir.glob("*.pdf"))]
    ensure_dir(paths.output_data)
    write_json(paths.output_data / "pdf_analysis.json", rows)
    with (paths.output_data / "pdf_analysis.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["file", "pages", "text_chars", "method", "note"])
        writer.writeheader()
        writer.writerows(rows)
    LOGGER.info("Analisi PDF completata su %d file", len(rows))
    return rows
