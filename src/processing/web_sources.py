from __future__ import annotations

from datetime import date
from urllib.parse import urlparse

from src.support.config import ProjectPaths
from src.support.io_utils import read_json
from src.support.models import WebSource
from src.support.normalization import clean_identifier, clean_text

_REQUIRED_FIELDS = {
    "title",
    "publisher",
    "document_type",
    "mime_type",
    "url",
    "relation",
    "phase",
    "evidence",
    "summary",
}

_ALLOWED_RELATIONS = {
    "accordo-quadro",
    "cig-esatto",
    "cig-padre-lotto",
    "contesto-istituzionale",
    "contesto-tecnico",
    "cup-oggetto",
    "fase-antecedente",
    "oggetto-ente",
    "procedura-oggetto",
    "repository-istituzionale",
}


def _validated_text(item: dict, field: str, cig: str) -> str:
    value = clean_text(item.get(field, ""))
    if not value:
        raise ValueError(f"Fonte web {cig}: campo obbligatorio '{field}' mancante")
    return value


def load_web_sources(paths: ProjectPaths, known_cigs) -> dict[str, list[WebSource]]:
    """Carica il catalogo web e ne garantisce copertura, provenienza e URL validi."""
    payload = read_json(paths.web_sources_file)
    if payload.get("schema_version") != 1:
        raise ValueError("Versione non supportata del catalogo delle fonti web")

    verified_on = clean_text(payload.get("verified_on", ""))
    try:
        date.fromisoformat(verified_on)
    except ValueError as exc:
        raise ValueError("Data di verifica delle fonti web non valida") from exc

    raw_records = payload.get("records")
    if not isinstance(raw_records, dict):
        raise ValueError("Il catalogo delle fonti web deve contenere un oggetto 'records'")

    expected = {clean_identifier(cig) for cig in known_cigs}
    actual = {clean_identifier(cig) for cig in raw_records}
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        raise ValueError(
            "Catalogo web non allineato al dataset: "
            f"CIG mancanti={missing or 'nessuno'}, CIG inattesi={unexpected or 'nessuno'}"
        )

    result: dict[str, list[WebSource]] = {}
    for raw_cig, raw_sources in raw_records.items():
        cig = clean_identifier(raw_cig)
        if not isinstance(raw_sources, list) or not raw_sources:
            raise ValueError(f"Il CIG {cig} deve avere almeno una fonte web")

        sources: list[WebSource] = []
        urls: set[str] = set()
        for item in raw_sources:
            if not isinstance(item, dict):
                raise ValueError(f"Fonte web {cig}: ogni voce deve essere un oggetto")
            missing_fields = sorted(_REQUIRED_FIELDS - item.keys())
            if missing_fields:
                raise ValueError(f"Fonte web {cig}: campi mancanti {missing_fields}")

            url = _validated_text(item, "url", cig)
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError(f"Fonte web {cig}: URL non valido '{url}'")
            if url in urls:
                raise ValueError(f"Fonte web {cig}: URL duplicato '{url}'")
            urls.add(url)

            relation = _validated_text(item, "relation", cig)
            if relation not in _ALLOWED_RELATIONS:
                raise ValueError(f"Fonte web {cig}: relazione non riconosciuta '{relation}'")

            sources.append(
                WebSource(
                    title=_validated_text(item, "title", cig),
                    publisher=_validated_text(item, "publisher", cig),
                    document_type=_validated_text(item, "document_type", cig),
                    mime_type=_validated_text(item, "mime_type", cig),
                    url=url,
                    relation=relation,
                    phase=_validated_text(item, "phase", cig),
                    evidence=_validated_text(item, "evidence", cig),
                    summary=_validated_text(item, "summary", cig),
                    verified_on=verified_on,
                )
            )
        result[cig] = sources
    return result
