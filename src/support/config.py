from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    sources: Path
    csv_dir: Path
    json_dir: Path
    html_dir: Path
    pdf_dir: Path
    web_sources_file: Path
    xml_dir: Path
    dtd_file: Path
    output_data: Path
    dist: Path
    templates: Path
    assets: Path
    report_dir: Path
    report_generated: Path

    @classmethod
    def from_root(cls, root: Path | None = None) -> "ProjectPaths":
        project_root = (root or Path(__file__).resolve().parents[2]).resolve()
        sources = project_root / "fonti_originali"
        report_dir = project_root / "report"
        return cls(
            root=project_root,
            sources=sources,
            csv_dir=sources / "csv",
            json_dir=sources / "json",
            html_dir=sources / "html",
            pdf_dir=sources / "pdf",
            web_sources_file=sources / "web" / "fonti_web.json",
            xml_dir=project_root / "documenti_xml",
            dtd_file=project_root / "schema" / "contratto_cig.dtd",
            output_data=project_root / "output_data",
            dist=project_root / "dist",
            templates=project_root / "site" / "templates",
            assets=project_root / "site" / "assets",
            report_dir=report_dir,
            report_generated=report_dir / "generated",
        )


PATHS = ProjectPaths.from_root()
