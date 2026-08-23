from __future__ import annotations

import logging

from src.processing.analysis import analyze_records
from src.processing.extraction import extract_records
from src.processing.microdata_analysis import verify_microdata
from src.processing.pdf_analysis import analyze_pdfs
from src.processing.preparation import prepare_dataset
from src.processing.report_builder import compile_report, generate_report_fragments
from src.processing.site_builder import build_site
from src.processing.source_discovery import merge_document_sources
from src.processing.text_analysis import analyze_text
from src.processing.validation import validate_documents
from src.support.config import ProjectPaths
from src.support.html_utils import assert_internal_links
from src.support.io_utils import write_json

LOGGER = logging.getLogger(__name__)


def build(paths: ProjectPaths, *, prepare: bool = False, compile_pdf: bool = False) -> dict:
    if prepare:
        prepare_dataset(paths)
    validation = validate_documents(paths)
    invalid = [result for result in validation if not result.valid]
    if invalid:
        details = "; ".join(f"{item.path.name}: {item.error}" for item in invalid)
        raise RuntimeError(f"La build si interrompe: XML non validi: {details}")
    records = extract_records(validation)
    merge_document_sources(paths, records)
    analysis = analyze_records(records)
    write_json(paths.output_data / "analysis.json", analysis)
    pdf_analysis = analyze_pdfs(paths)
    text_analysis = analyze_text(paths)
    generate_report_fragments(paths, analysis)
    if compile_pdf:
        compile_report(paths)
    build_site(paths, analysis, pdf_analysis, text_analysis)
    microdata = verify_microdata(paths)
    assert_internal_links(paths.dist)
    LOGGER.info("Microdata verificati: %d item in %d pagine", microdata["items"], microdata["files"])
    return analysis
