from __future__ import annotations

import logging
import re
from collections import defaultdict
from pathlib import Path

from src.support.config import ProjectPaths
from src.support.models import SourceReference

LOGGER = logging.getLogger(__name__)

_SOURCE_TYPES = {
    ".csv": ("csv", "text/csv"),
    ".htm": ("html", "text/html"),
    ".html": ("html", "text/html"),
    ".json": ("json", "application/json"),
    ".md": ("markdown", "text/markdown"),
    ".pdf": ("pdf", "application/pdf"),
    ".txt": ("text", "text/plain"),
    ".xml": ("xml", "application/xml"),
}

_TYPE_ORDER = {name: index for index, name in enumerate(("csv", "html", "json", "pdf", "xml", "markdown", "text"))}


def _extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as first_error:
        LOGGER.warning("Estrazione pypdf non riuscita per %s: %s", path.name, first_error)
    try:
        from pdfminer.high_level import extract_text

        return extract_text(str(path)) or ""
    except Exception as second_error:
        LOGGER.warning("Estrazione pdfminer non riuscita per %s: %s", path.name, second_error)
        return ""


def _read_searchable_text(path: Path) -> str:
    if path.suffix.casefold() == ".pdf":
        return _extract_pdf_text(path)
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError as error:
        LOGGER.warning("Lettura non riuscita per %s: %s", path, error)
        return ""


def _matched_cigs(path: Path, known_cigs: set[str]) -> set[str]:
    name = path.name.casefold()
    filename_matches = {cig for cig in known_cigs if cig.casefold() in name}
    if filename_matches:
        return filename_matches

    content = _read_searchable_text(path).casefold()
    return {cig for cig in known_cigs if cig.casefold() in content}


def _source_description(path: Path, kind: str, cig: str) -> str:
    if kind == "csv":
        return "Riga del CSV esportato dal cruscotto ANAC"
    canonical_names = {f"cig_{cig}".casefold(), f"dati-cig-{cig}".casefold()}
    if path.stem.casefold() in canonical_names:
        return f"Fonte originale {kind.upper()} del CIG"

    title = re.sub(r"[_-]+", " ", path.stem)
    title = " ".join(title.split())
    return f"Documento {kind.upper()} collegato al CIG: {title}"


def discover_document_sources(paths: ProjectPaths, known_cigs) -> dict[str, list[SourceReference]]:
    """Associa le fonti ai CIG usando prima il nome e poi il contenuto testuale.

    Il criterio non dipende da un singolo CIG né da nomi di file rigidi: un nuovo
    allegato viene collegato se il suo nome o il testo estraibile contiene uno dei
    CIG presenti nel dataset.
    """

    cigs = {str(cig).strip().upper() for cig in known_cigs if str(cig).strip()}
    discovered: dict[str, list[SourceReference]] = defaultdict(list)
    if not paths.sources.exists():
        return {cig: [] for cig in cigs}

    for source in sorted(path for path in paths.sources.rglob("*") if path.is_file()):
        if source.resolve() == paths.web_sources_file.resolve():
            # Il manifesto descrive collegamenti esterni: non è una fonte locale
            # da duplicare nell'elenco dei file scaricabili di ciascun CIG.
            continue
        source_type = _SOURCE_TYPES.get(source.suffix.casefold())
        if source_type is None:
            continue
        kind, mime_type = source_type
        for cig in sorted(_matched_cigs(source, cigs)):
            discovered[cig].append(
                SourceReference(
                    kind=kind,
                    mime_type=mime_type,
                    path=source.relative_to(paths.root).as_posix(),
                    description=_source_description(source, kind, cig),
                )
            )

    for cig in cigs:
        unique = {source.path: source for source in discovered[cig]}
        discovered[cig] = sorted(
            unique.values(),
            key=lambda source: (_TYPE_ORDER.get(source.kind, 99), source.path.casefold()),
        )
    return dict(discovered)


def merge_document_sources(paths: ProjectPaths, records):
    """Integra nel modello intermedio le fonti scoperte, anche senza rigenerare gli XML."""

    discovered = discover_document_sources(paths, (record.cig for record in records))
    for record in records:
        merged = {source.path: source for source in record.sources}
        merged.update({source.path: source for source in discovered.get(record.cig, [])})
        record.sources = sorted(
            merged.values(),
            key=lambda source: (_TYPE_ORDER.get(source.kind, 99), source.path.casefold()),
        )
    return records
