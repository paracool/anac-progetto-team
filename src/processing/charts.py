from __future__ import annotations

from html import escape
from pathlib import Path

from src.support.io_utils import ensure_dir, write_text


def write_bar_chart(path: Path, title: str, description: str, rows: list[dict], *, max_rows: int = 10) -> None:
    data = rows[:max_rows]
    width = 920
    left = 255
    right = 90
    top = 90
    row_height = 42
    height = max(220, top + row_height * len(data) + 70)
    max_value = max((float(row.get("count", 0)) for row in data), default=1.0)
    chart_width = width - left - right

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escape(title)}</title>',
        f'<desc id="desc">{escape(description)}</desc>',
        '<style>.label{font:15px system-ui,sans-serif;fill:#17202a}.value{font:bold 14px system-ui,sans-serif;fill:#17202a}.bar{fill:#1f5f74}.grid{stroke:#d7e0e5;stroke-width:1}.chart-title{font:bold 22px system-ui,sans-serif;fill:#17202a}</style>',
        f'<text class="chart-title" x="20" y="35">{escape(title)}</text>',
    ]
    for index, row in enumerate(data):
        y = top + index * row_height
        value = float(row.get("count", 0))
        bar_width = 0 if max_value == 0 else value / max_value * chart_width
        label = str(row.get("label", ""))
        svg.extend([
            f'<line class="grid" x1="{left}" x2="{width-right}" y1="{y+24}" y2="{y+24}"/>',
            f'<text class="label" x="20" y="{y+20}">{escape(label[:33])}</text>',
            f'<rect class="bar" x="{left}" y="{y+3}" width="{bar_width:.1f}" height="24" rx="4"><title>{escape(label)}: {value:g}</title></rect>',
            f'<text class="value" x="{min(left+bar_width+9, width-right+10):.1f}" y="{y+21}">{value:g}</text>',
        ])
    svg.append("</svg>")
    ensure_dir(path.parent)
    write_text(path, "\n".join(svg))
