from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.processing.pipeline import build
from src.support.config import PATHS
from src.support.logging_utils import configure_logging


def main() -> None:
    configure_logging()
    build(PATHS, prepare=True, compile_pdf=True)


if __name__ == "__main__":
    main()
