from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

from lxml import etree

from src.processing.source_discovery import discover_document_sources
from src.processing.web_sources import load_web_sources
from src.support.config import ProjectPaths
from src.support.io_utils import read_json
from src.support.models import SourceReference, WebSource
from src.support.normalization import clean_identifier, clean_text
from src.support.parsing import combine_date_time

LOGGER = logging.getLogger(__name__)


def _first(mapping: dict[str, Any] | None, *keys: str) -> str:
    if not isinstance(mapping, dict):
        return ""
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return clean_text(value)
    return ""


def _add(parent: etree._Element, tag: str, text: object | None = None, **attributes: object) -> etree._Element:
    element = etree.SubElement(parent, tag)
    for key, value in attributes.items():
        if value not in (None, ""):
            element.set(key, str(value))
    cleaned = clean_text(text)
    if cleaned:
        element.text = cleaned
    return element


def _load_csv_rows(paths: ProjectPaths) -> dict[str, dict[str, str]]:
    csv_files = sorted(paths.csv_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"Nessun CSV trovato in {paths.csv_dir}")
    rows: dict[str, dict[str, str]] = {}
    for csv_file in csv_files:
        with csv_file.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            for row in reader:
                normalized = {str(key): clean_text(value) for key, value in row.items() if key is not None}
                cig = clean_identifier(normalized.get("CIG", ""))
                if cig:
                    rows[cig] = normalized
    return rows


def _load_json_details(paths: ProjectPaths) -> dict[str, dict[str, Any]]:
    details: dict[str, dict[str, Any]] = {}
    for json_file in sorted(paths.json_dir.glob("CIG_*.json")):
        data = read_json(json_file)
        cig = clean_identifier(data.get("bando", {}).get("CIG") or json_file.stem.removeprefix("CIG_"))
        if cig:
            details[cig] = data
    return details


def _add_sources(root: etree._Element, sources_for_cig: list[SourceReference]) -> None:
    sources = _add(root, "fonti")
    for source in sources_for_cig:
        _add(
            sources,
            "fonte",
            source.description,
            tipo=source.kind,
            formato=source.mime_type,
            percorso=source.path,
        )


def _add_web_sources(root: etree._Element, web_sources_for_cig: list[WebSource]) -> None:
    container = _add(root, "approfondimentiWeb")
    for source in web_sources_for_cig:
        item = etree.SubElement(
            container,
            "fonteWeb",
            tipo=source.document_type,
            formato=source.mime_type,
            url=source.url,
            relazione=source.relation,
            verificataIl=source.verified_on,
        )
        item.text = "La fonte "
        title = etree.SubElement(item, "titoloFonte")
        title.text = source.title
        title.tail = ", pubblicata da "
        publisher = etree.SubElement(item, "enteFonte")
        publisher.text = source.publisher
        publisher.tail = ", riguarda la fase "
        phase = etree.SubElement(item, "faseFonte")
        phase.text = source.phase
        phase.tail = ". Il nesso verificato con la gara è il seguente: "
        evidence = etree.SubElement(item, "nessoFonte")
        evidence.text = source.evidence
        evidence.tail = ". In sintesi, "
        summary = etree.SubElement(item, "datoFonte")
        summary.text = source.summary
        summary.tail = "."


def _add_description(root: etree._Element, contract_type: str, title: str, location: str, cpv_description: str, category: str) -> None:
    description = etree.SubElement(root, "descrizioneDocumentale")
    description.text = "Procedura relativa a "
    type_node = etree.SubElement(description, "tipologia")
    type_node.text = (contract_type or "contratto pubblico").lower()
    type_node.tail = " avente per oggetto "
    object_node = etree.SubElement(description, "oggetto")
    object_node.text = title or "oggetto non disponibile"
    object_node.tail = ". "
    if cpv_description:
        term = etree.SubElement(description, "termine")
        term.text = cpv_description.lower()
        term.tail = ". "
    if category:
        category_node = etree.SubElement(description, "categoria")
        category_node.text = category.lower()
        category_node.tail = ". "
    if location:
        place = etree.SubElement(description, "luogo")
        place.text = location
        place.tail = "."


def build_xml_record(
    cig: str,
    row: dict[str, str],
    data: dict[str, Any],
    sources_for_cig: list[SourceReference],
    web_sources_for_cig: list[WebSource],
) -> etree._Element:
    bando = data.get("bando", {})
    authority = data.get("stazioneAppaltante", {})
    publications = data.get("pubblicazioni", {})
    award_rows = data.get("aggiudicazione", []) or []
    execution_rows = data.get("avvioContratto", []) or []

    title = _first(bando, "OGGETTO_GARA", "OGGETTO_LOTTO") or row.get("OGGETTO", "")
    lot_title = _first(bando, "OGGETTO_LOTTO")
    contract_type = row.get("TIPOLOGIA CONTRATTO", "") or _first(bando, "OGGETTO_PRINCIPALE_CONTRATTO")
    location = row.get("LOCALIZZAZIONE", "")
    deadline = combine_date_time(_first(bando, "DATA_SCADENZA_OFFERTA"), _first(bando, "ORA_SCADENZA_OFFERTA"))
    award_date = _first(award_rows[0] if award_rows else {}, "DATA_AGGIUDICAZIONE_DEFINITIVA") or row.get("DATA AGGIUDICAZIONE", "")
    award_amount = _first(award_rows[0] if award_rows else {}, "IMPORTO_AGGIUDICAZIONE") or row.get("VALORE AGGIUDICAZIONE", "")

    root = etree.Element("contratto", cig=cig, fonte="ANAC")
    _add_sources(root, sources_for_cig)
    _add_web_sources(root, web_sources_for_cig)

    info = _add(root, "informazioniGara")
    _add(info, "numeroGara", _first(bando, "NUMERO_GARA"))
    _add(info, "tipoCig", _first(bando, "TIPO_CIG"))
    _add(info, "stato", _first(bando, "STATO", "DETTAGLIO_STATO"))
    _add(info, "oggettoGara", title)
    _add(info, "oggettoLotto", lot_title)
    _add(info, "importoGara", _first(bando, "IMPORTO_COMPLESSIVO_GARA") or row.get("VALORE A BASE D’ASTA", "") or row.get("VALORE A BASE D'ASTA", ""), valuta="EUR")
    _add(info, "importoLotto", _first(bando, "IMPORTO_LOTTO"), valuta="EUR")
    _add(info, "provincia", _first(bando, "SIGLA_PROVINCIA"))
    _add(info, "settore", _first(bando, "SETTORE"))
    _add(info, "cup", _first(bando, "CUP"))
    _add(info, "oggettoPrincipaleContratto", _first(bando, "OGGETTO_PRINCIPALE_CONTRATTO"))
    _add(info, "tipologiaContratto", contract_type)
    _add(info, "localizzazione", location)
    _add(info, "scadenzaOfferte", deadline)
    _add(info, "dataAggiudicazione", award_date)

    station = _add(root, "stazioneAppaltante")
    _add(station, "codiceFiscale", _first(authority, "CF_AMMINISTRAZIONE_APPALTANTE"))
    _add(station, "denominazione", _first(authority, "DENOMINAZIONE_AMMINISTRAZIONE_APPALTANTE") or row.get("AMMINISTRAZIONE APPALTANTE", ""))
    _add(station, "centroCosto", _first(authority, "DENOMINAZIONE_CENTRO_COSTO"))
    _add(station, "citta", _first(authority, "CITTA"))
    _add(station, "regione", _first(authority, "REGIONE"))
    _add(station, "indirizzo", _first(authority, "INDIRIZZO"))

    officials = data.get("incaricati", []) or []
    if not officials and row.get("RUP"):
        officials = [{"NOME": row["RUP"], "DESCRIZIONE_RUOLO": "Responsabile unico del procedimento"}]
    if officials:
        officials_node = _add(root, "incaricati")
        for item in officials:
            official = _add(officials_node, "incaricato", ruolo=_first(item, "DESCRIZIONE_RUOLO", "COD_RUOLO"))
            _add(official, "nome", _first(item, "NOME"))
            _add(official, "cognome", _first(item, "COGNOME"))
            _add(official, "codiceFiscale", _first(item, "CODICE_FISCALE"))

    publication_node = _add(root, "pubblicazioni")
    _add(publication_node, "dataCreazione", _first(publications, "DATA_CREAZIONE"))
    _add(publication_node, "dataPubblicazione", _first(publications, "DATA_PUBBLICAZIONE") or row.get("DATA PUBBLICAZIONE", ""))

    participant_rows = data.get("partecipanti", []) or []
    if participant_rows:
        participants = _add(root, "partecipanti")
        for item in participant_rows:
            participant = _add(participants, "partecipante", aggiudicatario=_first(item, "FLAG_AGGIUDICATARIO"))
            _add(participant, "denominazione", _first(item, "DENOMINAZIONE"))
            _add(participant, "tipoSoggetto", _first(item, "TIPO_SOGGETTO"))
            _add(participant, "codiceFiscale", _first(item, "CODICE_FISCALE"))
            _add(participant, "ruolo", _first(item, "RUOLO", "COD_RUOLO"))

    if award_rows or award_amount:
        award_node = _add(root, "aggiudicazione")
        rows = award_rows or [{}]
        for item in rows:
            winner = _add(award_node, "aggiudicatario")
            winner_name = ""
            winner_tax_code = ""
            for participant in participant_rows:
                flag = str(participant.get("FLAG_AGGIUDICATARIO", "")).casefold()
                if flag in {"1", "true", "s", "si", "sì"}:
                    winner_name = _first(participant, "DENOMINAZIONE")
                    winner_tax_code = _first(participant, "CODICE_FISCALE")
                    break
            _add(winner, "denominazione", winner_name)
            _add(winner, "codiceFiscale", winner_tax_code)
            _add(winner, "importoAggiudicazione", _first(item, "IMPORTO_AGGIUDICAZIONE") or award_amount, valuta="EUR")

    if execution_rows:
        execution = _add(root, "contrattoEsecuzione")
        first_execution = execution_rows[0]
        start = _first(
            first_execution,
            "DATA_INIZIO_EFFETTIVA",
            "DATA_VERBALE_PRIMA_CONSEGNA",
            "DATA_VERBALE_CONSEGNA_DEFINITIVA",
            "DATA_STIPULA_CONTRATTO",
        )
        expected_end = _first(first_execution, "DATA_TERMINE_CONTRATTUALE")
        _add(execution, "dataAvvio", start)
        _add(execution, "dataFinePrevista", expected_end)

    economic_rows = data.get("quadroEconomico", []) or []
    if economic_rows:
        framework = _add(root, "quadroEconomico")
        for item in economic_rows:
            for key, value in item.items():
                if key.startswith("IMPORTO_") or key == "SOMME_A_DISPOSIZIONE":
                    if clean_text(value) not in {"", "0", "0.0"}:
                        _add(framework, "voceEconomica", value, nome=key, valuta="EUR")

    category_description = ""
    category_rows = data.get("categorieOpera", []) or []
    if category_rows:
        categories = _add(root, "categorieOpera")
        for item in category_rows:
            category = _add(categories, "categoriaOpera", tipo=_first(item, "DESCRIZIONE_TIPO_CATEGORIA", "COD_TIPO_CATEGORIA"))
            _add(category, "idCategoria", _first(item, "ID_CATEGORIA"))
            description = _first(item, "DESCRIZIONE")
            category_description = category_description or description
            _add(category, "descrizione", description)

    cpv_description = ""
    cpv_rows = bando.get("CPV", []) if isinstance(bando, dict) else []
    if cpv_rows:
        cpv_node = _add(root, "cpv")
        for item in cpv_rows:
            is_main = str(item.get("FLAG_PREVALENTE", "")).casefold() in {"1", "true", "s", "si", "sì"}
            cpv = _add(cpv_node, "voceCpv", tipo="Prevalente" if is_main else "Secondario")
            _add(cpv, "codice", _first(item, "COD_CPV"))
            description = _first(item, "DESCRIZIONE_CPV")
            cpv_description = cpv_description or description
            _add(cpv, "descrizione", description)

    _add_description(root, contract_type, lot_title or title, location, cpv_description, category_description)
    return root


def prepare_dataset(paths: ProjectPaths) -> list[Path]:
    rows = _load_csv_rows(paths)
    details = _load_json_details(paths)
    if not details:
        raise RuntimeError("La preparazione richiede almeno una fonte JSON per individuare il perimetro del dataset.")
    sources_by_cig = discover_document_sources(paths, details)
    web_sources_by_cig = load_web_sources(paths, details)
    paths.xml_dir.mkdir(parents=True, exist_ok=True)
    for old in paths.xml_dir.glob("*.xml"):
        old.unlink()

    outputs: list[Path] = []
    for cig, data in sorted(details.items()):
        row = rows.get(cig, {})
        if not row:
            LOGGER.warning("CIG %s non trovato nel CSV: XML generato con i soli dati JSON", cig)
        root = build_xml_record(
            cig,
            row,
            data,
            sources_by_cig.get(cig, []),
            web_sources_by_cig[cig],
        )
        output = paths.xml_dir / f"CIG_{cig}.xml"
        etree.ElementTree(root).write(output, encoding="utf-8", xml_declaration=True, pretty_print=True)
        outputs.append(output)
    LOGGER.info("Creati %d XML in %s", len(outputs), paths.xml_dir)
    return outputs
