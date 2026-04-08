from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def api_runs_root() -> Path:
    return repo_root() / "literature_screening" / "data" / "api_runs"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_project_tasks(root: Path, project_ids: set[str]) -> list[str]:
    tasks_root = root / "tasks"
    task_ids: set[str] = set()

    for task_file in tasks_root.glob("*/task.json"):
        payload = load_json(task_file)
        project_id = payload.get("project_id") or payload.get("metadata", {}).get("project_id")
        if project_id in project_ids:
            task_ids.add(task_file.parent.name)

    for project_id in project_ids:
        datasets_dir = root / "projects" / project_id / "datasets"
        if not datasets_dir.exists():
            continue
        for dataset_file in datasets_dir.glob("*.json"):
            payload = load_json(dataset_file)
            task_id = payload.get("task_id")
            if task_id:
                task_ids.add(task_id)

    return sorted(task_ids)


def copy_path(src: Path, dst: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def export_all(root: Path, output_path: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="api-runs-export-") as temp_dir:
        staging_root = Path(temp_dir) / "api_runs_export"
        copy_path(root, staging_root / "api_runs")

        manifest = {
            "mode": "all",
            "source_api_runs_root": str(root),
            "notes": [
                "This archive contains the full api_runs state.",
                "Existing task and dataset metadata may still contain Windows absolute paths.",
                "Run scripts/repair-api-runs-paths.py on the destination machine after extraction.",
            ],
        }
        (staging_root / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        archive_base = output_path.with_suffix("")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.make_archive(str(archive_base), "zip", root_dir=staging_root)


def export_selected_projects(root: Path, project_ids: list[str], output_path: Path) -> None:
    projects_root = root / "projects"
    missing = [project_id for project_id in project_ids if not (projects_root / project_id / "project.json").exists()]
    if missing:
        raise SystemExit(f"Project ids not found: {', '.join(missing)}")

    selected_ids = set(project_ids)
    task_ids = find_project_tasks(root, selected_ids)

    with tempfile.TemporaryDirectory(prefix="api-runs-export-") as temp_dir:
        staging_root = Path(temp_dir) / "api_runs_export"
        staged_api_runs = staging_root / "api_runs"

        for project_id in project_ids:
            copy_path(projects_root / project_id, staged_api_runs / "projects" / project_id)

        for task_id in task_ids:
            copy_path(root / "tasks" / task_id, staged_api_runs / "tasks" / task_id)

        templates_dir = root / "templates"
        if templates_dir.exists():
            copy_path(templates_dir, staged_api_runs / "templates")

        project_summaries = []
        for project_id in project_ids:
            project_payload = load_json(projects_root / project_id / "project.json")
            project_summaries.append(
                {
                    "id": project_payload["id"],
                    "name": project_payload.get("name", ""),
                    "updated_at": project_payload.get("updated_at"),
                }
            )

        manifest = {
            "mode": "selected_projects",
            "source_api_runs_root": str(root),
            "projects": project_summaries,
            "task_ids": task_ids,
            "notes": [
                "This archive contains only the selected projects plus tasks that belong to them.",
                "Existing task and dataset metadata may still contain Windows absolute paths.",
                "Run scripts/repair-api-runs-paths.py on the destination machine after extraction.",
            ],
        }
        (staging_root / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        archive_base = output_path.with_suffix("")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.make_archive(str(archive_base), "zip", root_dir=staging_root)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export api_runs data for migration.")
    parser.add_argument("--output", required=True, help="Output .zip path")
    parser.add_argument(
        "--project-id",
        action="append",
        dest="project_ids",
        default=[],
        help="Project id to export. Repeat to export multiple projects.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Export the entire api_runs tree.",
    )
    args = parser.parse_args()

    root = api_runs_root()
    output_path = Path(args.output).resolve()

    if args.all and args.project_ids:
        raise SystemExit("Use either --all or --project-id, not both.")
    if not args.all and not args.project_ids:
        raise SystemExit("Provide --all or at least one --project-id.")

    if args.all:
        export_all(root, output_path)
        print(f"Created full export: {output_path}")
        return

    export_selected_projects(root, args.project_ids, output_path)
    print(f"Created project export: {output_path}")


if __name__ == "__main__":
    main()
