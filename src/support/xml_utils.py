from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from lxml import etree


@dataclass(frozen=True)
class ValidationResult:
    path: Path
    well_formed: bool
    valid: bool
    error: str = ""


def load_dtd(path: Path) -> etree.DTD:
    with path.open("r", encoding="utf-8") as stream:
        return etree.DTD(stream)


def parse_xml(path: Path) -> etree._ElementTree:
    parser = etree.XMLParser(resolve_entities=False, no_network=True, remove_blank_text=False)
    return etree.parse(str(path), parser)


def validate_xml(path: Path, dtd: etree.DTD) -> ValidationResult:
    try:
        document = parse_xml(path)
    except (OSError, etree.XMLSyntaxError) as exc:
        return ValidationResult(path, False, False, str(exc))
    valid = dtd.validate(document)
    error = ""
    if not valid and dtd.error_log:
        error = "; ".join(str(item) for item in dtd.error_log.filter_from_errors())
    return ValidationResult(path, True, valid, error)


def xpath_text(tree: etree._ElementTree, xpath: str, default: str = "") -> str:
    value = tree.xpath(f"string({xpath})")
    return (value or default).strip()


def xpath_texts(tree: etree._ElementTree, xpath: str) -> list[str]:
    return [str(value).strip() for value in tree.xpath(xpath) if str(value).strip()]
