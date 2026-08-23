from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from src.processing.pipeline import build
from src.support.config import PATHS


@pytest.fixture(scope="session")
def built_project():
    build(PATHS, prepare=False, compile_pdf=False)
    return PATHS
