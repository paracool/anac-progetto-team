from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class SourceReference:
    kind: str
    mime_type: str
    path: str
    description: str = ""


@dataclass(frozen=True)
class WebSource:
    title: str
    publisher: str
    document_type: str
    mime_type: str
    url: str
    relation: str
    phase: str
    evidence: str
    summary: str
    verified_on: str


@dataclass(frozen=True)
class Participant:
    name: str
    role: str = ""
    subject_type: str = ""
    tax_code: str = ""
    winner: bool = False


@dataclass
class ContractRecord:
    cig: str
    title: str
    contract_type: str = ""
    status: str = ""
    contracting_authority: str = ""
    authority_city: str = ""
    region: str = ""
    province: str = ""
    tender_location: str = ""
    tender_amount: Decimal | None = None
    lot_amount: Decimal | None = None
    award_amount: Decimal | None = None
    creation_date: datetime | None = None
    publication_date: datetime | None = None
    offer_deadline: datetime | None = None
    award_date: datetime | None = None
    start_date: datetime | None = None
    expected_end_date: datetime | None = None
    cpv: list[str] = field(default_factory=list)
    participants: list[Participant] = field(default_factory=list)
    sources: list[SourceReference] = field(default_factory=list)
    web_sources: list[WebSource] = field(default_factory=list)
    xml_valid: bool = False
    xml_filename: str = ""
    raw_dates: dict[str, str] = field(default_factory=dict)
    raw_amounts: dict[str, str] = field(default_factory=dict)
    unparseable_dates: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("tender_amount", "lot_amount", "award_amount"):
            data[key] = str(data[key]) if data[key] is not None else None
        for key in (
            "creation_date",
            "publication_date",
            "offer_deadline",
            "award_date",
            "start_date",
            "expected_end_date",
        ):
            data[key] = data[key].isoformat() if data[key] else None
        return data
