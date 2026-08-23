from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

from lxml import html


_LOCAL_ATTRS = ("href", "src", "data-src")


def slugify(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-").lower()


def check_internal_links(dist_dir: Path) -> list[str]:
    errors: list[str] = []
    for html_path in sorted(dist_dir.rglob("*.html")):
        try:
            document = html.fromstring(html_path.read_bytes())
        except Exception as exc:
            errors.append(f"{html_path.relative_to(dist_dir)}: HTML non interpretabile: {exc}")
            continue
        for element in document.iter():
            for attribute in _LOCAL_ATTRS:
                value = element.get(attribute)
                if not value:
                    continue
                parts = urlsplit(value)
                if parts.scheme or parts.netloc or value.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
                    continue
                local_path = unquote(parts.path)
                if not local_path:
                    continue
                candidate = (html_path.parent / local_path).resolve()
                try:
                    candidate.relative_to(dist_dir.resolve())
                except ValueError:
                    errors.append(f"{html_path.relative_to(dist_dir)}: riferimento esterno a dist: {value}")
                    continue
                if candidate.is_dir():
                    candidate = candidate / "index.html"
                if not candidate.exists():
                    errors.append(f"{html_path.relative_to(dist_dir)}: file inesistente: {value}")
    return errors


def assert_internal_links(dist_dir: Path) -> None:
    errors = check_internal_links(dist_dir)
    if errors:
        message = "Collegamenti interni non validi:\n- " + "\n- ".join(errors)
        raise RuntimeError(message)
