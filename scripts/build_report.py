from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json

from src.processing.report_builder import compile_report, generate_report_fragments
from src.support.config import PATHS
from src.support.logging_utils import configure_logging


def main() -> None:
    configure_logging()
    analysis_path = PATHS.output_data / "analysis.json"
    if not analysis_path.exists():
        raise SystemExit("analysis.json non presente: eseguire prima python scripts/build.py")
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    generate_report_fragments(PATHS, analysis)
    if not compile_report(PATHS):
        raise SystemExit("Compilazione LaTeX non eseguita o fallita")


if __name__ == "__main__":
    main()
