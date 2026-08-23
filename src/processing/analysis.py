from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from statistics import mean, median
from typing import Callable, Iterable

from src.support.models import ContractRecord
from src.support.normalization import canonical_key


def _decimal(value: Decimal | int | float | None) -> str | None:
    return str(value) if value is not None else None


def percentile(values: list[Decimal], fraction: Decimal) -> Decimal | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = fraction * Decimal(len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - Decimal(lower)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def amount_statistics(values: Iterable[Decimal | None], total_records: int | None = None) -> dict:
    available = sorted(value for value in values if value is not None)
    total = total_records if total_records is not None else len(available)
    missing = total - len(available)
    if not available:
        return {
            "available": 0,
            "missing": missing,
            "sum": None,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "q1": None,
            "q3": None,
            "iqr": None,
        }
    q1 = percentile(available, Decimal("0.25"))
    q3 = percentile(available, Decimal("0.75"))
    return {
        "available": len(available),
        "missing": missing,
        "sum": _decimal(sum(available, Decimal("0"))),
        "mean": _decimal(sum(available, Decimal("0")) / Decimal(len(available))),
        "median": _decimal(Decimal(str(median(available)))),
        "min": _decimal(available[0]),
        "max": _decimal(available[-1]),
        "q1": _decimal(q1),
        "q3": _decimal(q3),
        "iqr": _decimal(q3 - q1 if q1 is not None and q3 is not None else None),
    }


def _distribution(records: list[ContractRecord], getter: Callable[[ContractRecord], str]) -> dict:
    total = len(records)
    counts = Counter(getter(record) or "Dati mancanti" for record in records)
    rows = [
        {"label": label, "count": count, "percent": round((count / total * 100) if total else 0, 2)}
        for label, count in counts.most_common()
    ]
    missing = counts.get("Dati mancanti", 0)
    return {
        "rows": rows,
        "missing": missing,
        "missing_percent": round((missing / total * 100) if total else 0, 2),
        "top": next((row for row in rows if row["label"] != "Dati mancanti"), None),
    }


def _group_amounts(records: list[ContractRecord], getter: Callable[[ContractRecord], str]) -> list[dict]:
    groups: dict[str, list[Decimal]] = defaultdict(list)
    counts: Counter[str] = Counter()
    for record in records:
        label = getter(record) or "Dati mancanti"
        counts[label] += 1
        if record.tender_amount is not None:
            groups[label].append(record.tender_amount)
    output = []
    for label, count in counts.most_common():
        stats = amount_statistics(groups[label], total_records=count)
        output.append({"label": label, "records": count, **stats})
    return output


def _cross_distribution(records: list[ContractRecord], geography: Callable[[ContractRecord], str]) -> list[dict]:
    rows: dict[tuple[str, str], int] = Counter()
    for record in records:
        rows[(geography(record) or "Dati mancanti", record.contract_type or "Dati mancanti")] += 1
    return [
        {"area": area, "contract_type": contract_type, "count": count}
        for (area, contract_type), count in sorted(rows.items(), key=lambda item: (-item[1], item[0]))
    ]


def classify_chronology(record: ContractRecord) -> list[dict]:
    anomalies: list[dict] = []
    for field in record.unparseable_dates:
        anomalies.append({"type": "data_non_interpretabile", "fields": [field]})

    core = {
        "publication_date": record.publication_date,
        "offer_deadline": record.offer_deadline,
        "award_date": record.award_date,
    }
    missing = [field for field, value in core.items() if value is None and field not in record.unparseable_dates]
    if missing:
        anomalies.append({"type": "data_mancante", "fields": missing})

    if record.publication_date and record.offer_deadline and record.offer_deadline.date() < record.publication_date.date():
        anomalies.append({"type": "scadenza_anteriore_pubblicazione", "fields": ["publication_date", "offer_deadline"]})
    if record.publication_date and record.award_date and record.award_date.date() < record.publication_date.date():
        anomalies.append({"type": "aggiudicazione_anteriore_pubblicazione", "fields": ["publication_date", "award_date"]})
    if record.offer_deadline and record.award_date and record.award_date.date() < record.offer_deadline.date():
        anomalies.append({"type": "aggiudicazione_anteriore_scadenza", "fields": ["offer_deadline", "award_date"]})
    if not anomalies:
        anomalies.append({"type": "sequenza_cronologica_coerente", "fields": []})
    return anomalies


def _duration_days(start: datetime | None, end: datetime | None) -> int | None:
    if not start or not end:
        return None
    delta = (end.date() - start.date()).days
    return delta if delta >= 0 else None


def _median_number(values: list[int]) -> float | None:
    return float(median(values)) if values else None


def _date_analysis(records: list[ContractRecord]) -> dict:
    fields = (
        "creation_date",
        "publication_date",
        "offer_deadline",
        "award_date",
        "start_date",
        "expected_end_date",
    )
    coverage = []
    for field in fields:
        count = sum(getattr(record, field) is not None for record in records)
        coverage.append({
            "field": field,
            "available": count,
            "missing": len(records) - count,
            "percent": round(count / len(records) * 100, 2) if records else 0,
        })

    anomalies = []
    anomaly_counts: Counter[str] = Counter()
    valid_publication_deadline: list[int] = []
    valid_deadline_award: list[int] = []
    valid_publication_award: list[int] = []
    for record in records:
        classifications = classify_chronology(record)
        for classification in classifications:
            anomaly_counts[classification["type"]] += 1
            if classification["type"] != "sequenza_cronologica_coerente":
                anomalies.append({
                    "cig": record.cig,
                    "type": classification["type"],
                    "fields": classification["fields"],
                    "dates": record.raw_dates,
                })
        first = _duration_days(record.publication_date, record.offer_deadline)
        second = _duration_days(record.offer_deadline, record.award_date)
        third = _duration_days(record.publication_date, record.award_date)
        if first is not None:
            valid_publication_deadline.append(first)
        if second is not None:
            valid_deadline_award.append(second)
        if third is not None:
            valid_publication_award.append(third)

    publication_months = Counter(
        record.publication_date.strftime("%Y-%m") for record in records if record.publication_date
    )
    deadline_months = Counter(
        record.offer_deadline.strftime("%Y-%m") for record in records if record.offer_deadline
    )

    return {
        "coverage": coverage,
        "anomaly_counts": [{"type": key, "count": value} for key, value in anomaly_counts.most_common()],
        "anomalies": anomalies,
        "durations": {
            "publication_to_deadline": {
                "count": len(valid_publication_deadline),
                "mean": mean(valid_publication_deadline) if valid_publication_deadline else None,
                "median": _median_number(valid_publication_deadline),
            },
            "deadline_to_award": {
                "count": len(valid_deadline_award),
                "mean": mean(valid_deadline_award) if valid_deadline_award else None,
                "median": _median_number(valid_deadline_award),
            },
            "publication_to_award": {
                "count": len(valid_publication_award),
                "mean": mean(valid_publication_award) if valid_publication_award else None,
                "median": _median_number(valid_publication_award),
            },
        },
        "publication_months": [{"label": key, "count": value} for key, value in sorted(publication_months.items())],
        "deadline_months": [{"label": key, "count": value} for key, value in sorted(deadline_months.items())],
    }


def _amount_bands(records: list[ContractRecord]) -> list[dict]:
    bands = [
        ("Meno di 50.000 €", Decimal("0"), Decimal("50000")),
        ("50.000–99.999 €", Decimal("50000"), Decimal("100000")),
        ("100.000–249.999 €", Decimal("100000"), Decimal("250000")),
        ("250.000–499.999 €", Decimal("250000"), Decimal("500000")),
        ("500.000 € e oltre", Decimal("500000"), None),
    ]
    counts = Counter()
    missing = 0
    for record in records:
        amount = record.tender_amount
        if amount is None:
            missing += 1
            continue
        for label, lower, upper in bands:
            if amount >= lower and (upper is None or amount < upper):
                counts[label] += 1
                break
    rows = [{"label": label, "count": counts[label]} for label, _, _ in bands]
    if missing:
        rows.append({"label": "Dati mancanti", "count": missing})
    return rows


def _amount_analysis(records: list[ContractRecord]) -> dict:
    fields = {
        "tender_amount": [record.tender_amount for record in records],
        "lot_amount": [record.lot_amount for record in records],
        "award_amount": [record.award_amount for record in records],
    }
    statistics = {name: amount_statistics(values, len(records)) for name, values in fields.items()}

    tender_values = [record.tender_amount for record in records if record.tender_amount is not None]
    q1 = percentile(tender_values, Decimal("0.25"))
    q3 = percentile(tender_values, Decimal("0.75"))
    outliers = []
    if q1 is not None and q3 is not None:
        iqr = q3 - q1
        lower = q1 - Decimal("1.5") * iqr
        upper = q3 + Decimal("1.5") * iqr
        outliers = [
            {"cig": record.cig, "title": record.title, "amount": str(record.tender_amount)}
            for record in records
            if record.tender_amount is not None and (record.tender_amount < lower or record.tender_amount > upper)
        ]

    comparisons = []
    absolute_differences: list[Decimal] = []
    percentage_differences: list[Decimal] = []
    unchanged = lower_award = higher_award = 0
    for record in records:
        if record.tender_amount is None or record.award_amount is None or record.tender_amount <= 0:
            continue
        difference = record.tender_amount - record.award_amount
        percentage = difference / record.tender_amount * Decimal("100")
        absolute_differences.append(difference)
        percentage_differences.append(percentage)
        if difference == 0:
            unchanged += 1
        elif difference > 0:
            lower_award += 1
        else:
            higher_award += 1
        comparisons.append({
            "cig": record.cig,
            "tender_amount": str(record.tender_amount),
            "award_amount": str(record.award_amount),
            "difference": str(difference),
            "difference_percent": str(percentage),
        })

    differences = {
        "available": len(comparisons),
        "mean_absolute": _decimal(sum(absolute_differences, Decimal("0")) / Decimal(len(absolute_differences))) if absolute_differences else None,
        "median_absolute": _decimal(Decimal(str(median(absolute_differences)))) if absolute_differences else None,
        "mean_percent": _decimal(sum(percentage_differences, Decimal("0")) / Decimal(len(percentage_differences))) if percentage_differences else None,
        "median_percent": _decimal(Decimal(str(median(percentage_differences)))) if percentage_differences else None,
        "unchanged": unchanged,
        "award_lower": lower_award,
        "award_higher": higher_award,
        "records": comparisons,
    }

    highest = sorted(
        (
            {"cig": record.cig, "title": record.title, "amount": str(record.tender_amount)}
            for record in records if record.tender_amount is not None
        ),
        key=lambda row: Decimal(row["amount"]),
        reverse=True,
    )[:5]

    return {
        "statistics": statistics,
        "bands": _amount_bands(records),
        "by_contract_type": _group_amounts(records, lambda record: record.contract_type),
        "by_city": _group_amounts(records, lambda record: record.authority_city),
        "by_region": _group_amounts(records, lambda record: record.region),
        "highest": highest,
        "outliers": outliers,
        "comparisons": differences,
    }


def analyze_records(records: list[ContractRecord]) -> dict:
    total = len(records)
    locations = _distribution(records, lambda record: record.tender_location)
    cities = _distribution(records, lambda record: record.authority_city)
    regions = _distribution(records, lambda record: record.region)
    source_file_counts = Counter(source.kind for record in records for source in record.sources)
    source_record_counts = Counter(
        kind
        for record in records
        for kind in {source.kind for source in record.sources}
    )
    source_coverage = [
        {
            "format": kind,
            "available": source_record_counts.get(kind, 0),
            "linked_files": source_file_counts.get(kind, 0),
            "missing": total - source_record_counts.get(kind, 0),
            "percent": round(source_record_counts.get(kind, 0) / total * 100, 2) if total else 0,
        }
        for kind in ("csv", "json", "html", "pdf")
    ]
    web_linked_sources = sum(len(record.web_sources) for record in records)
    web_available = sum(bool(record.web_sources) for record in records)
    web_relations = Counter(source.relation for record in records for source in record.web_sources)
    web_types = Counter(source.document_type for record in records for source in record.web_sources)
    web_formats = Counter(source.mime_type for record in records for source in record.web_sources)

    differences = []
    for record in records:
        if not record.tender_location or not record.authority_city:
            continue
        if canonical_key(record.tender_location) != canonical_key(record.authority_city):
            differences.append({
                "cig": record.cig,
                "tender_location": record.tender_location,
                "authority_city": record.authority_city,
            })

    return {
        "metadata": {
            "record_count": total,
            "valid_xml_count": sum(record.xml_valid for record in records),
            "source_coverage": source_coverage,
            "web_source_coverage": {
                "available": web_available,
                "linked_sources": web_linked_sources,
                "missing": total - web_available,
                "percent": round(web_available / total * 100, 2) if total else 0,
            },
            "web_source_relations": [
                {"relation": relation, "count": count}
                for relation, count in sorted(web_relations.items())
            ],
            "web_source_types": [
                {"type": source_type, "count": count}
                for source_type, count in sorted(web_types.items())
            ],
            "web_source_formats": [
                {"format": mime_type, "count": count}
                for mime_type, count in sorted(web_formats.items())
            ],
        },
        "territorial": {
            "tender_locations": locations,
            "authority_cities": cities,
            "regions": regions,
            "contract_types_by_city": _cross_distribution(records, lambda record: record.authority_city),
            "contract_types_by_region": _cross_distribution(records, lambda record: record.region),
            "amounts_by_city": _group_amounts(records, lambda record: record.authority_city),
            "amounts_by_region": _group_amounts(records, lambda record: record.region),
            "location_authority_differences": differences,
        },
        "dates": _date_analysis(records),
        "amounts": _amount_analysis(records),
        "records": [record.to_dict() for record in records],
        "methodology_notes": {
            "sample": "Il campione coincide con i documenti inclusi nel progetto e non è rappresentativo dell'intero sistema degli appalti pubblici.",
            "dates": "Le incongruenze sono segnalate senza attribuirle automaticamente a errori della fonte: alcune date possono riferirsi a eventi o pubblicazioni successive alla procedura effettiva.",
            "amounts": "Le differenze tra importo iniziale e importo di aggiudicazione sono descrittive e non sono denominate automaticamente ribassi.",
            "web_sources": "Le fonti web sono qualificate mediante un nesso esplicito. Le fonti di contesto, di accordo quadro o di fase antecedente non sono presentate come atti recanti il CIG esatto.",
        },
    }
