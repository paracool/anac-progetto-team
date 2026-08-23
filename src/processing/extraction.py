from __future__ import annotations

from pathlib import Path

from src.support.models import ContractRecord, Participant, SourceReference, WebSource
from src.support.normalization import normalize_place, normalize_string
from src.support.parsing import parse_datetime, parse_decimal
from src.support.xml_utils import parse_xml, xpath_text

_DATE_XPATHS = {
    "creation_date": "/contratto/pubblicazioni/dataCreazione",
    "publication_date": "/contratto/pubblicazioni/dataPubblicazione",
    "offer_deadline": "/contratto/informazioniGara/scadenzaOfferte",
    "award_date": "/contratto/informazioniGara/dataAggiudicazione",
    "start_date": "/contratto/contrattoEsecuzione/dataAvvio",
    "expected_end_date": "/contratto/contrattoEsecuzione/dataFinePrevista",
}


def extract_record(xml_path: Path, *, xml_valid: bool) -> ContractRecord:
    tree = parse_xml(xml_path)
    root = tree.getroot()
    raw_dates = {name: xpath_text(tree, xpath) for name, xpath in _DATE_XPATHS.items()}
    parsed_dates = {name: parse_datetime(value) for name, value in raw_dates.items()}
    unparseable = [name for name, value in raw_dates.items() if value and parsed_dates[name] is None]

    raw_amounts = {
        "tender_amount": xpath_text(tree, "/contratto/informazioniGara/importoGara"),
        "lot_amount": xpath_text(tree, "/contratto/informazioniGara/importoLotto"),
        "award_amount": xpath_text(tree, "/contratto/aggiudicazione/aggiudicatario[1]/importoAggiudicazione"),
    }

    sources = [
        SourceReference(
            kind=node.get("tipo", ""),
            mime_type=node.get("formato", ""),
            path=node.get("percorso", ""),
            description=" ".join(node.itertext()).strip(),
        )
        for node in tree.xpath("/contratto/fonti/fonte")
    ]
    web_sources = [
        WebSource(
            title=(node.findtext("titoloFonte") or "").strip(),
            publisher=(node.findtext("enteFonte") or "").strip(),
            document_type=node.get("tipo", ""),
            mime_type=node.get("formato", ""),
            url=node.get("url", ""),
            relation=node.get("relazione", ""),
            phase=(node.findtext("faseFonte") or "").strip(),
            evidence=(node.findtext("nessoFonte") or "").strip(),
            summary=(node.findtext("datoFonte") or "").strip(),
            verified_on=node.get("verificataIl", ""),
        )
        for node in tree.xpath("/contratto/approfondimentiWeb/fonteWeb")
    ]
    participants = []
    for node in tree.xpath("/contratto/partecipanti/partecipante"):
        flag = (node.get("aggiudicatario", "") or "").casefold()
        participants.append(
            Participant(
                name="".join(node.xpath("string(denominazione)")).strip(),
                role="".join(node.xpath("string(ruolo)")).strip(),
                subject_type="".join(node.xpath("string(tipoSoggetto)")).strip(),
                tax_code="".join(node.xpath("string(codiceFiscale)")).strip(),
                winner=flag in {"1", "true", "s", "si", "sì"},
            )
        )

    cpv = []
    for node in tree.xpath("/contratto/cpv/voceCpv"):
        code = "".join(node.xpath("string(codice)")).strip()
        description = "".join(node.xpath("string(descrizione)")).strip()
        value = " — ".join(part for part in (code, description) if part)
        if value:
            cpv.append(value)

    return ContractRecord(
        cig=root.get("cig", ""),
        title=normalize_string(xpath_text(tree, "/contratto/informazioniGara/oggettoGara")),
        contract_type=normalize_string(xpath_text(tree, "/contratto/informazioniGara/tipologiaContratto")),
        status=normalize_string(xpath_text(tree, "/contratto/informazioniGara/stato")),
        contracting_authority=normalize_string(xpath_text(tree, "/contratto/stazioneAppaltante/denominazione")),
        authority_city=normalize_place(xpath_text(tree, "/contratto/stazioneAppaltante/citta")),
        region=normalize_place(xpath_text(tree, "/contratto/stazioneAppaltante/regione")),
        province=normalize_place(xpath_text(tree, "/contratto/informazioniGara/provincia")),
        tender_location=normalize_place(xpath_text(tree, "/contratto/informazioniGara/localizzazione")),
        tender_amount=parse_decimal(raw_amounts["tender_amount"]),
        lot_amount=parse_decimal(raw_amounts["lot_amount"]),
        award_amount=parse_decimal(raw_amounts["award_amount"]),
        creation_date=parsed_dates["creation_date"],
        publication_date=parsed_dates["publication_date"],
        offer_deadline=parsed_dates["offer_deadline"],
        award_date=parsed_dates["award_date"],
        start_date=parsed_dates["start_date"],
        expected_end_date=parsed_dates["expected_end_date"],
        cpv=cpv,
        participants=participants,
        sources=sources,
        web_sources=web_sources,
        xml_valid=xml_valid,
        xml_filename=xml_path.name,
        raw_dates=raw_dates,
        raw_amounts=raw_amounts,
        unparseable_dates=unparseable,
    )


def extract_records(validation_results) -> list[ContractRecord]:
    return [extract_record(result.path, xml_valid=result.valid) for result in validation_results if result.valid]
