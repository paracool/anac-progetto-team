from __future__ import annotations

import logging
import shutil
import subprocess
from decimal import Decimal
from pathlib import Path

from src.support.config import ProjectPaths
from src.support.formatting import format_currency_it, format_decimal_it, format_percent
from src.support.io_utils import ensure_dir, write_text

LOGGER = logging.getLogger(__name__)


def latex_escape(value: object) -> str:
    text = "" if value is None else str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def _currency(value: str | None) -> str:
    return latex_escape(format_currency_it(Decimal(value) if value is not None else None))


def _write_statistics(paths: ProjectPaths, analysis: dict) -> None:
    stats = analysis["amounts"]["statistics"]
    rows = []
    labels = {
        "tender_amount": "Importo gara",
        "lot_amount": "Importo lotto",
        "award_amount": "Importo aggiudicazione",
    }
    for key, label in labels.items():
        row = stats[key]
        rows.append(
            f"{latex_escape(label)} & {row['available']} & {row['missing']} & {_currency(row['sum'])} & {_currency(row['mean'])} & {_currency(row['median'])} & {_currency(row['q1'])} & {_currency(row['q3'])} \\\\"
        )
    content = """\\begin{table}[htbp]
\\centering
\\small
\\caption{Statistiche economiche del campione}
\\begin{tabular}{lrrrrrrr}
\\toprule
Campo & Disponibili & Mancanti & Somma & Media & Mediana & Q1 & Q3 \\\\
\\midrule
%s
\\bottomrule
\\end{tabular}
\\end{table}
""" % "\n".join(rows)
    write_text(paths.report_generated / "statistiche.tex", content)


def _write_coverage(paths: ProjectPaths, analysis: dict) -> None:
    source_rows = [
        f"{latex_escape(row['format'].upper())} & {row['available']} & {row['linked_files']} & {row['missing']} & {latex_escape(format_percent(row['percent']))} \\\\"
        for row in analysis["metadata"]["source_coverage"]
    ]
    date_rows = [
        f"{latex_escape(row['field'])} & {row['available']} & {row['missing']} & {latex_escape(format_percent(row['percent']))} \\\\"
        for row in analysis["dates"]["coverage"]
    ]
    web = analysis["metadata"]["web_source_coverage"]
    content = """\\begin{table}[htbp]
\\centering
\\caption{Copertura delle fonti}
\\begin{tabular}{lrrrr}
\\toprule
Formato & CIG coperti & File collegati & Mancanti & Copertura \\\\
\\midrule
%s
\\bottomrule
\\end{tabular}
\\end{table}

\\begin{table}[htbp]
\\centering
\\caption{Copertura delle fonti web qualificate}
\\begin{tabular}{rrrr}
\\toprule
CIG coperti & Risorse collegate & Mancanti & Copertura \\\\
\\midrule
%s & %s & %s & %s \\\\
\\bottomrule
\\end{tabular}
\\end{table}

\\begin{table}[htbp]
\\centering
\\small
\\caption{Copertura dei campi data}
\\begin{tabular}{lrrr}
\\toprule
Campo & Disponibili & Mancanti & Copertura \\\\
\\midrule
%s
\\bottomrule
\\end{tabular}
\\end{table}
""" % (
        "\n".join(source_rows),
        web["available"],
        web["linked_sources"],
        web["missing"],
        latex_escape(format_percent(web["percent"])),
        "\n".join(date_rows),
    )
    write_text(paths.report_generated / "copertura.tex", content)


def _write_anomalies(paths: ProjectPaths, analysis: dict) -> None:
    rows = []
    labels = {
        "scadenza_anteriore_pubblicazione": "Scadenza anteriore alla pubblicazione",
        "aggiudicazione_anteriore_pubblicazione": "Aggiudicazione anteriore alla pubblicazione",
        "aggiudicazione_anteriore_scadenza": "Aggiudicazione anteriore alla scadenza",
        "data_mancante": "Data mancante",
        "data_non_interpretabile": "Data non interpretabile",
    }
    for anomaly in analysis["dates"]["anomalies"]:
        dates = anomaly["dates"]
        rows.append(
            f"{latex_escape(anomaly['cig'])} & {latex_escape(labels.get(anomaly['type'], anomaly['type']))} & {latex_escape(dates.get('publication_date') or 'n.d.')} & {latex_escape(dates.get('offer_deadline') or 'n.d.')} & {latex_escape(dates.get('award_date') or 'n.d.')} \\\\"
        )
    if not rows:
        rows.append(r"\multicolumn{5}{c}{Nessuna anomalia rilevata} \\")
    content = """\\begin{longtable}{p{2.3cm}p{4.7cm}p{2.5cm}p{3.2cm}p{2.5cm}}
\\caption{Segnalazioni cronologiche}\\\\
\\toprule
CIG & Segnalazione & Pubblicazione & Scadenza & Aggiudicazione \\\\
\\midrule
\\endfirsthead
\\toprule
CIG & Segnalazione & Pubblicazione & Scadenza & Aggiudicazione \\\\
\\midrule
\\endhead
%s
\\bottomrule
\\end{longtable}
""" % "\n".join(rows)
    write_text(paths.report_generated / "anomalie.tex", content)


def _write_territory(paths: ProjectPaths, analysis: dict) -> None:
    city_rows = []
    city_distribution = {row["label"]: row for row in analysis["territorial"]["authority_cities"]["rows"]}
    for row in analysis["territorial"]["amounts_by_city"]:
        distribution = city_distribution.get(row["label"], {})
        city_rows.append(
            f"{latex_escape(row['label'])} & {row['records']} & {latex_escape(format_percent(distribution.get('percent', 0)))} & {_currency(row['sum'])} & {_currency(row['median'])} \\\\"
        )
    content = """\\begin{table}[htbp]
\\centering
\\small
\\caption{Distribuzione e importi per città della stazione appaltante}
\\begin{tabular}{lrrrr}
\\toprule
Città & CIG & Percentuale & Importo complessivo & Mediana \\\\
\\midrule
%s
\\bottomrule
\\end{tabular}
\\end{table}
""" % "\n".join(city_rows)
    write_text(paths.report_generated / "territorio.tex", content)


def generate_report_fragments(paths: ProjectPaths, analysis: dict) -> list[Path]:
    ensure_dir(paths.report_generated)
    _write_statistics(paths, analysis)
    _write_coverage(paths, analysis)
    _write_anomalies(paths, analysis)
    _write_territory(paths, analysis)
    files = sorted(paths.report_generated.glob("*.tex"))
    LOGGER.info("Generati %d frammenti LaTeX", len(files))
    return files


def compile_report(paths: ProjectPaths) -> bool:
    executable = shutil.which("pdflatex")
    if not executable:
        LOGGER.warning("pdflatex non disponibile: compilazione PDF omessa")
        return False
    command = [executable, "-interaction=nonstopmode", "-halt-on-error", "report_progetto.tex"]
    for _ in range(2):
        completed = subprocess.run(command, cwd=paths.report_dir, capture_output=True, text=True)
        if completed.returncode != 0:
            LOGGER.error("Compilazione LaTeX fallita:\n%s", completed.stdout[-5000:] + completed.stderr[-1000:])
            return False
    LOGGER.info("Report PDF compilato: %s", paths.report_dir / "report_progetto.pdf")
    return True
