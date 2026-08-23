import json

from pypdf import PdfReader

from src.support.html_utils import check_internal_links


def test_main_pages_generated(built_project):
    required = [
        "index.html",
        "progetto.html",
        "archivio.html",
        "report.html",
        "qualita-dati.html",
        "assets/css/app.css",
        "assets/css/sources.css",
        "assets/css/stile.css",
        "assets/js/app.js",
        "data/analysis.json",
        "downloads/documentazione/contratto_cig.dtd",
        "downloads/documentazione/fonti_web.json",
        "downloads/documentazione/prompts_utilizzati.md",
        ".nojekyll",
    ]
    for relative in required:
        assert (built_project.dist / relative).is_file(), relative
    assert not (built_project.dist / "_headers").exists()
    assert not (built_project.dist / "_redirects").exists()
    assert not (built_project.dist / "metodologia.html").exists()


def test_detail_pages_and_deploy_downloads(built_project):
    analysis = json.loads((built_project.output_data / "analysis.json").read_text(encoding="utf-8"))
    assert len(list((built_project.dist / "cig").glob("*.html"))) == analysis["metadata"]["record_count"]
    assert len(list((built_project.dist / "downloads" / "xml").glob("*.xml"))) == analysis["metadata"]["record_count"]
    for folder in ("json", "html", "pdf"):
        assert (built_project.dist / "downloads" / folder).is_dir()


def test_descriptive_pdf_is_linked_to_its_cig(built_project):
    detail = (built_project.dist / "cig" / "B6DD95EE23.html").read_text(encoding="utf-8")
    filename = "pn vsf15-25-sua_lettera inv.-disciplinare_indifferenziata_2025-26_frascati.pdf"
    assert filename in detail
    assert detail.count("../downloads/pdf/") >= 6
    assert "B6DD95EE23_determina_65.pdf" in detail
    assert "B6DD95EE23_determina_aggiudicazione_2475.pdf" in detail
    assert "B6DD95EE23_graduatoria.pdf" in detail
    assert "B6DD95EE23_verbale_aggiudicazione.pdf" in detail
    assert "Fonti web" in detail
    assert "Fonti web verificate" not in detail
    assert "Risorse esterne selezionate per ampliare il contesto" not in detail
    assert "determina, disciplinare, verbale, graduatoria ed esito" in detail
    assert 'target="_blank"' in detail
    assert "portalegare.cittametropolitanaroma.it" in detail


def test_navigation_uses_explicit_exam_labels(built_project):
    page = (built_project.dist / "index.html").read_text(encoding="utf-8")
    assert ">Progetto e metodo<" in page
    assert ">Analisi del campione<" in page
    assert ">PDF<" not in page
    assert ">Metodologia<" not in page


def test_no_broken_internal_links(built_project):
    assert check_internal_links(built_project.dist) == []


def test_analysis_contains_required_sections(built_project):
    analysis = json.loads((built_project.output_data / "analysis.json").read_text(encoding="utf-8"))
    web_catalog = json.loads(built_project.web_sources_file.read_text(encoding="utf-8"))
    expected_web_sources = sum(len(sources) for sources in web_catalog["records"].values())
    assert analysis["territorial"]["authority_cities"]["rows"]
    assert analysis["dates"]["coverage"]
    assert analysis["amounts"]["statistics"]["tender_amount"]["median"] is not None
    assert analysis["amounts"]["statistics"]["tender_amount"]["mean"] is not None
    pdf_coverage = next(row for row in analysis["metadata"]["source_coverage"] if row["format"] == "pdf")
    expected_pdf_files = len(list(built_project.pdf_dir.glob("*.pdf")))
    assert pdf_coverage == {
        "format": "pdf",
        "available": analysis["metadata"]["record_count"],
        "linked_files": expected_pdf_files,
        "missing": 0,
        "percent": 100.0,
    }
    assert analysis["metadata"]["web_source_coverage"] == {
        "available": analysis["metadata"]["record_count"],
        "linked_sources": expected_web_sources,
        "missing": 0,
        "percent": 100.0,
    }
    assert analysis["metadata"]["web_source_relations"]


def test_exam_output_constraints(built_project):
    analysis = json.loads((built_project.output_data / "analysis.json").read_text(encoding="utf-8"))
    microdata = json.loads((built_project.dist / "data" / "microdata_analysis.json").read_text(encoding="utf-8"))
    assert analysis["metadata"]["record_count"] >= 15
    assert analysis["metadata"]["valid_xml_count"] == analysis["metadata"]["record_count"]
    assert microdata["items"] >= 1
    assert len(PdfReader(str(built_project.report_dir / "report_progetto.pdf")).pages) <= 3
