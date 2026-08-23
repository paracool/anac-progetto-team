from __future__ import annotations

from lxml import html

from src.support.config import ProjectPaths
from src.support.io_utils import write_json


def verify_microdata(paths: ProjectPaths) -> dict:
    rows = []
    total = 0
    for path in sorted((paths.dist / "cig").glob("*.html")):
        document = html.fromstring(path.read_bytes())
        items = document.xpath("//*[@itemscope]")
        types = [item.get("itemtype", "") for item in items]
        total += len(items)
        rows.append({"file": path.name, "items": len(items), "types": types})
    result = {"files": len(rows), "items": total, "rows": rows}
    write_json(paths.output_data / "microdata_analysis.json", result)
    write_json(paths.dist / "data" / "microdata_analysis.json", result)
    return result
