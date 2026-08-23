import json
from datetime import datetime
from decimal import Decimal

from lxml import etree

from src.processing.analysis import amount_statistics, classify_chronology
from src.processing.extraction import extract_record
from src.processing.source_discovery import discover_document_sources, merge_document_sources
from src.processing.web_sources import load_web_sources
from src.support.config import PATHS
from src.support.models import ContractRecord
from src.support.xml_utils import load_dtd, validate_xml


def test_extract_record():
    path = sorted(PATHS.xml_dir.glob("*.xml"))[0]
    record = extract_record(path, xml_valid=True)
    assert record.cig
    assert record.title
    assert record.xml_valid is True
    assert any(source.kind == "json" for source in record.sources)
    assert record.web_sources


def test_dtd_validation():
    dtd = load_dtd(PATHS.dtd_file)
    path = sorted(PATHS.xml_dir.glob("*.xml"))[0]
    result = validate_xml(path, dtd)
    assert result.well_formed
    assert result.valid


def test_mixed_content_model_is_declared_and_used():
    dtd = PATHS.dtd_file.read_text(encoding="utf-8")
    assert "<!ELEMENT descrizioneDocumentale (#PCDATA | tipologia | oggetto | categoria | termine | luogo)*>" in dtd
    assert "<!ELEMENT fonteWeb (#PCDATA | titoloFonte | enteFonte | faseFonte | nessoFonte | datoFonte)*>" in dtd
    record = extract_record(PATHS.xml_dir / "CIG_B6DD95EE23.xml", xml_valid=True)
    assert record.title
    tree = etree.parse(str(PATHS.xml_dir / "CIG_B6DD95EE23.xml"))
    description = tree.xpath("/contratto/descrizioneDocumentale")[0]
    assert description.text and description.text.strip()
    assert len(description) >= 2
    web_source = tree.xpath("/contratto/approfondimentiWeb/fonteWeb")[0]
    assert web_source.text and web_source.text.strip()
    assert len(web_source) == 5
    assert web_source.get("url", "").startswith("https://")


def test_web_source_manifest_covers_every_cig():
    known_cigs = {path.stem.removeprefix("CIG_") for path in PATHS.json_dir.glob("CIG_*.json")}
    catalog = load_web_sources(PATHS, known_cigs)
    raw_catalog = json.loads(PATHS.web_sources_file.read_text(encoding="utf-8"))
    assert set(catalog) == known_cigs
    assert len(catalog) == 15
    assert sum(len(sources) for sources in catalog.values()) >= len(catalog)
    assert all(sources for sources in catalog.values())
    assert raw_catalog["methodology"]


def test_b6dd_web_source_exposes_official_gara_acts():
    record = extract_record(PATHS.xml_dir / "CIG_B6DD95EE23.xml", xml_valid=True)
    source = record.web_sources[0]
    assert "determina" in source.title.casefold()
    assert "aggiudicazione" in source.summary.casefold()
    assert "cittametropolitanaroma.it" in source.url


def test_chronology_classification():
    record = ContractRecord(
        cig="TEST",
        title="Test",
        publication_date=datetime(2025, 5, 10),
        offer_deadline=datetime(2025, 5, 9),
        award_date=datetime(2025, 5, 8),
    )
    types = {item["type"] for item in classify_chronology(record)}
    assert "scadenza_anteriore_pubblicazione" in types
    assert "aggiudicazione_anteriore_pubblicazione" in types
    assert "aggiudicazione_anteriore_scadenza" in types


def test_amount_statistics_distinguishes_mean_and_median():
    stats = amount_statistics([Decimal("10"), Decimal("20"), Decimal("1000")], total_records=4)
    assert stats["available"] == 3
    assert stats["missing"] == 1
    assert Decimal(stats["mean"]) != Decimal(stats["median"])
    assert Decimal(stats["median"]) == Decimal("20")


def test_source_discovery_uses_embedded_cig_for_descriptive_documents():
    known_cigs = {path.stem.removeprefix("CIG_") for path in PATHS.xml_dir.glob("CIG_*.xml")}
    sources = discover_document_sources(PATHS, known_cigs)
    linked_pdfs = [source.path for source in sources["B6DD95EE23"] if source.kind == "pdf"]
    assert len(linked_pdfs) >= 6
    assert any(path.startswith("fonti_originali/pdf/pn vsf15-25-sua_") for path in linked_pdfs)
    assert all(any(source.kind == "pdf" for source in sources[cig]) for cig in known_cigs)
    assert all(
        source.path != "fonti_originali/web/fonti_web.json"
        for cig_sources in sources.values()
        for source in cig_sources
    )


def test_discovered_sources_are_merged_without_xml_regeneration():
    record = extract_record(PATHS.xml_dir / "CIG_B6DD95EE23.xml", xml_valid=True)
    record.sources = [source for source in record.sources if source.path.endswith("CIG_B6DD95EE23.pdf")]
    merge_document_sources(PATHS, [record])
    assert len([source for source in record.sources if source.kind == "pdf"]) >= 6
