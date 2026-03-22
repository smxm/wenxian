from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_loads_without_exceptions() -> None:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    at = AppTest.from_file(str(app_path))
    at.run(timeout=30)

    assert len(at.tabs) == 4
    assert len(at.exception) == 0
