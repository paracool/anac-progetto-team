from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import zipfile

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.processing.charts import write_bar_chart
from src.support.config import ProjectPaths
from src.support.formatting import format_currency_it, format_date_it, format_datetime_it, format_decimal_it, format_percent
from src.support.html_utils import assert_internal_links
from src.support.io_utils import copy_file, copy_tree, ensure_dir, reset_dir, write_json, write_text
from src.support.parsing import parse_datetime

LOGGER = logging.getLogger(__name__)

_DATE_LABELS = {
    "creation_date": "Creazione",
    "publication_date": "Pubblicazione",
    "offer_deadline": "Scadenza offerte",
    "award_date": "Aggiudicazione",
    "start_date": "Avvio",
    "expected_end_date": "Fine prevista",
}

_ANOMALY_LABELS = {
    "sequenza_cronologica_coerente": "Sequenza cronologica coerente",
    "scadenza_anteriore_pubblicazione": "Scadenza anteriore alla pubblicazione",
    "aggiudicazione_anteriore_pubblicazione": "Aggiudicazione anteriore alla pubblicazione",
    "aggiudicazione_anteriore_scadenza": "Aggiudicazione anteriore alla scadenza",
    "data_mancante": "Data mancante",
    "data_non_interpretabile": "Data non interpretabile",
}

_WEB_RELATION_LABELS = {
    "cig-esatto": "CIG esatto",
    "cig-padre-lotto": "CIG padre / lotto",
    "accordo-quadro": "Accordo quadro",
    "cup-oggetto": "CUP e oggetto",
    "procedura-oggetto": "Procedura e oggetto",
    "oggetto-ente": "Oggetto ed ente",
    "fase-antecedente": "Fase antecedente",
    "contesto-tecnico": "Contesto tecnico",
    "contesto-istituzionale": "Contesto istituzionale",
    "repository-istituzionale": "Repertorio istituzionale",
}


def _to_decimal(value):
    return Decimal(value) if value not in (None, "") else None


def _render_record(record: dict) -> dict:
    enriched = dict(record)
    for field in ("tender_amount", "lot_amount", "award_amount"):
        enriched[f"{field}_formatted"] = format_currency_it(_to_decimal(record.get(field)))
    for field in _DATE_LABELS:
        parsed = parse_datetime(record.get(field))
        enriched[f"{field}_formatted"] = format_datetime_it(parsed) if field == "offer_deadline" else format_date_it(parsed)
    enriched["date_rows"] = [
        {"label": label, "value": enriched[f"{field}_formatted"], "raw": record.get("raw_dates", {}).get(field, "")}
        for field, label in _DATE_LABELS.items()
    ]
    enriched["source_downloads"] = [
        {
            **source,
            "label": source.get("description") or f"Fonte {source['kind'].upper()}",
            "href": f"../downloads/{source['kind']}/{Path(source['path']).name}.zip" if source["kind"] == "html" else f"../downloads/{source['kind']}/{Path(source['path']).name}",
        }
        for source in record.get("sources", [])
    ]
    enriched["web_source_links"] = [
        {
            **source,
            "relation_label": _WEB_RELATION_LABELS.get(
                source.get("relation", ""),
                source.get("relation", "").replace("-", " ").capitalize(),
            ),
        }
        for source in record.get("web_sources", [])
    ]
    return enriched


def _environment(paths: ProjectPaths) -> Environment:
    environment = Environment(
        loader=FileSystemLoader(paths.templates),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters["currency"] = lambda value: format_currency_it(_to_decimal(value))
    environment.filters["number"] = lambda value: format_decimal_it(Decimal(str(value))) if value is not None else "n.d."
    environment.filters["percent"] = lambda value: format_percent(value)
    environment.globals["anomaly_label"] = lambda value: _ANOMALY_LABELS.get(value, value.replace("_", " ").capitalize())
    environment.globals["web_relation_label"] = lambda value: _WEB_RELATION_LABELS.get(
        value,
        value.replace("-", " ").capitalize(),
    )
    return environment


def _copy_downloads(paths: ProjectPaths) -> None:
    copy_tree(paths.xml_dir, paths.dist / "downloads" / "xml")
    copy_tree(paths.csv_dir, paths.dist / "downloads" / "csv")
    copy_tree(paths.json_dir, paths.dist / "downloads" / "json")
    html_downloads = ensure_dir(paths.dist / "downloads" / "html")
    for source in sorted(paths.html_dir.glob("*.html")):
        archive = html_downloads / f"{source.name}.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            bundle.write(source, arcname=source.name)
    copy_tree(paths.pdf_dir, paths.dist / "downloads" / "pdf")
    report_pdf = paths.report_dir / "report_progetto.pdf"
    if report_pdf.exists():
        copy_file(report_pdf, paths.dist / "downloads" / "report" / report_pdf.name)
    copy_file(paths.dtd_file, paths.dist / "downloads" / "documentazione" / paths.dtd_file.name)
    copy_file(
        paths.web_sources_file,
        paths.dist / "downloads" / "documentazione" / paths.web_sources_file.name,
    )
    prompts = paths.report_dir / "prompts_utilizzati.md"
    if prompts.exists():
        copy_file(prompts, paths.dist / "downloads" / "documentazione" / prompts.name)


def _generate_charts(paths: ProjectPaths, analysis: dict) -> None:
    charts = paths.dist / "assets" / "images"
    territorial = analysis["territorial"]
    dates = analysis["dates"]
    amounts = analysis["amounts"]
    write_bar_chart(
        charts / "citta.svg",
        "CIG per città della stazione appaltante",
        "Grafico a barre con i conteggi assoluti dei CIG per città della stazione appaltante.",
        territorial["authority_cities"]["rows"],
    )
    write_bar_chart(
        charts / "regioni.svg",
        "CIG per regione",
        "Grafico a barre con i conteggi assoluti dei CIG per regione.",
        territorial["regions"]["rows"],
    )
    write_bar_chart(
        charts / "fasce-importo.svg",
        "Distribuzione per fascia di importo",
        "Grafico a barre degli importi di gara raggruppati per fascia.",
        amounts["bands"],
    )
    write_bar_chart(
        charts / "scadenze-mensili.svg",
        "Scadenze per mese",
        "Grafico a barre del numero di scadenze delle offerte per mese.",
        dates["deadline_months"],
    )


def build_site(paths: ProjectPaths, analysis: dict, pdf_analysis: list[dict], text_analysis: dict) -> Path:
    reset_dir(paths.dist)
    copy_tree(paths.assets, paths.dist / "assets")
    _copy_downloads(paths)
    ensure_dir(paths.dist / "data")
    write_json(paths.dist / "data" / "analysis.json", analysis)
    write_json(paths.dist / "data" / "pdf_analysis.json", pdf_analysis)
    write_json(paths.dist / "data" / "text_analysis.json", text_analysis)
    copy_file(paths.output_data / "validation.xml", paths.dist / "data" / "validation.xml")
    _generate_charts(paths, analysis)

    environment = _environment(paths)
    records = [_render_record(record) for record in analysis["records"]]
    records_by_cig = {record["cig"]: record for record in records}
    generated_at = datetime.now().astimezone().strftime("%d/%m/%Y %H:%M")
    report_available = (paths.dist / "downloads" / "report" / "report_progetto.pdf").exists()
    common = {
        "generated_at": generated_at,
        "record_count": analysis["metadata"]["record_count"],
        "report_available": report_available,
        "web_manifest_available": (
            paths.dist / "downloads" / "documentazione" / paths.web_sources_file.name
        ).exists(),
    }

    pages = {
        "index.html": ("index.html", {"analysis": analysis, "records": records[:5], "base": "", **common}),
        "archivio.html": ("archive.html", {"records": records, "analysis": analysis, "base": "", **common}),
        "report.html": ("report.html", {"analysis": analysis, "base": "", **common}),
        "progetto.html": ("project.html", {"analysis": analysis, "pdf_analysis": pdf_analysis, "text_analysis": text_analysis, "base": "", **common}),
        "qualita-dati.html": ("quality.html", {"analysis": analysis, "base": "", **common}),
    }
    for output_name, (template_name, context) in pages.items():
        write_text(paths.dist / output_name, environment.get_template(template_name).render(**context))

    detail_template = environment.get_template("detail.html")
    details_dir = ensure_dir(paths.dist / "cig")
    anomaly_map: dict[str, list[dict]] = {}
    for anomaly in analysis["dates"]["anomalies"]:
        anomaly_map.setdefault(anomaly["cig"], []).append(anomaly)
    for cig, record in records_by_cig.items():
        html = detail_template.render(
            record=record,
            anomalies=anomaly_map.get(cig, []),
            base="../",
            **common,
        )
        write_text(details_dir / f"{cig}.html", html)

    write_text(paths.dist / ".nojekyll", "")
    assert_internal_links(paths.dist)
    LOGGER.info("Sito statico generato in %s", paths.dist)
    return paths.dist
