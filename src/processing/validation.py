from __future__ import annotations

import logging
from datetime import date
from lxml import etree

from src.support.config import ProjectPaths
from src.support.io_utils import ensure_dir
from src.support.xml_utils import ValidationResult, load_dtd, validate_xml

LOGGER = logging.getLogger(__name__)


def validate_documents(paths: ProjectPaths) -> list[ValidationResult]:
    ensure_dir(paths.output_data)
    dtd = load_dtd(paths.dtd_file)
    results = [validate_xml(path, dtd) for path in sorted(paths.xml_dir.glob("*.xml"))]

    report = etree.Element(
        "validazione",
        date=date.today().isoformat(),
        docs_dir=paths.xml_dir.relative_to(paths.root).as_posix(),
    )
    for result in results:
        item = etree.SubElement(
            report,
            "file",
            name=result.path.name,
            wellformed=str(result.well_formed).lower(),
            valid=str(result.valid).lower(),
        )
        if result.error:
            etree.SubElement(item, "errore").text = result.error
    etree.ElementTree(report).write(
        paths.output_data / "validation.xml",
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=True,
    )
    valid_count = sum(result.valid for result in results)
    LOGGER.info("Validazione completata: %d/%d XML validi", valid_count, len(results))
    return results
