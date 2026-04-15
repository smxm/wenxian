from __future__ import annotations

from pathlib import Path

from literature_screening.storage_paths import resolve_stored_path, rewrite_storage_payload


def test_resolve_stored_path_remaps_foreign_windows_api_runs(tmp_path: Path) -> None:
    storage_root = tmp_path / "api_runs"
    target = storage_root / "tasks" / "abc123" / "screening_run" / "screening_output" / "included.ris"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("ok", encoding="utf-8")

    foreign = r"E:\old\literature_screening\data\api_runs\tasks\abc123\screening_run\screening_output\included.ris"
    resolved = resolve_stored_path(foreign, storage_root=storage_root)
    assert resolved == target

    hydrated = rewrite_storage_payload({"path": foreign}, storage_root=storage_root, mode="hydrate")
    assert hydrated["path"] == str(target)

