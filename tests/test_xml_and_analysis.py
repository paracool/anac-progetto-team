from datetime import datetime
from decimal import Decimal

from src.processing.analysis import amount_statistics, classify_chronology
from src.processing.extraction import extract_record
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


def test_dtd_validation():
    dtd = load_dtd(PATHS.dtd_file)
    path = sorted(PATHS.xml_dir.glob("*.xml"))[0]
    result = validate_xml(path, dtd)
    assert result.well_formed
    assert result.valid


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
