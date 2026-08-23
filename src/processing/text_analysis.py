from __future__ import annotations

import re
from collections import Counter

from src.support.config import ProjectPaths
from src.support.io_utils import write_json
from src.support.xml_utils import parse_xml, xpath_text

_STOPWORDS = {
    "di", "a", "da", "in", "con", "su", "per", "tra", "fra", "e", "o", "il", "lo", "la", "i", "gli",
    "le", "del", "della", "dei", "delle", "un", "una", "uno", "al", "alla", "alle", "agli", "nel", "nella",
    "nelle", "degli", "che", "avente", "relativa", "procedura",
}


def analyze_text(paths: ProjectPaths) -> dict:
    texts = [xpath_text(parse_xml(path), "/contratto/descrizioneDocumentale") for path in sorted(paths.xml_dir.glob("*.xml"))]
    tokens = [
        token for text in texts for token in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+", text.casefold())
        if len(token) > 2 and token not in _STOPWORDS
    ]
    result = {
        "documents": len(texts),
        "tokens": len(tokens),
        "top_terms": [{"term": term, "count": count} for term, count in Counter(tokens).most_common(30)],
    }
    write_json(paths.output_data / "text_analysis.json", result)
    return result
