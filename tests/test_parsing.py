from datetime import datetime
from decimal import Decimal

from src.support.normalization import normalize_place
from src.support.parsing import parse_datetime, parse_decimal


def test_parse_decimal_formats():
    expected = Decimal("1234.56")
    for value in ("1234.56", "1234,56", "1.234,56", "1,234.56", "€ 1.234,56", "1 234,56 EUR"):
        assert parse_decimal(value) == expected
    assert parse_decimal("") is None
    assert parse_decimal("non numerico") is None


def test_parse_dates():
    assert parse_datetime("2025-04-28") == datetime(2025, 4, 28)
    assert parse_datetime("28/04/2025") == datetime(2025, 4, 28)
    assert parse_datetime("2025-04-28T12:30") == datetime(2025, 4, 28, 12, 30)
    assert parse_datetime("data errata") is None


def test_normalize_places_preserves_bilingual_name():
    assert normalize_place("  BOLZANO/BOZEN ") == "Bolzano/Bozen"
    assert normalize_place("SAN   FRATELLO") == "San Fratello"
