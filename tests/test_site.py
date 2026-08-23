import json

from src.support.html_utils import check_internal_links


def test_main_pages_generated(built_project):
    required = [
        "index.html",
        "archivio.html",
        "report.html",
        "metodologia.html",
        "qualita-dati.html",
        "assets/css/app.css",
        "assets/js/app.js",
        "data/analysis.json",
        ".nojekyll",
    ]
    for relative in required:
        assert (built_project.dist / relative).is_file(), relative
    assert not (built_project.dist / "_headers").exists()
    assert not (built_project.dist / "_redirects").exists()


def test_detail_pages_and_deploy_downloads(built_project):
    analysis = json.loads((built_project.output_data / "analysis.json").read_text(encoding="utf-8"))
    assert len(list((built_project.dist / "cig").glob("*.html"))) == analysis["metadata"]["record_count"]
    assert len(list((built_project.dist / "downloads" / "xml").glob("*.xml"))) == analysis["metadata"]["record_count"]
    for folder in ("json", "html", "pdf"):
        assert (built_project.dist / "downloads" / folder).is_dir()


def test_no_broken_internal_links(built_project):
    assert check_internal_links(built_project.dist) == []


def test_analysis_contains_required_sections(built_project):
    analysis = json.loads((built_project.output_data / "analysis.json").read_text(encoding="utf-8"))
    assert analysis["territorial"]["authority_cities"]["rows"]
    assert analysis["dates"]["coverage"]
    assert analysis["amounts"]["statistics"]["tender_amount"]["median"] is not None
    assert analysis["amounts"]["statistics"]["tender_amount"]["mean"] is not None
