from __future__ import annotations

import argparse
from pathlib import Path

from literature_screening.core.config import load_run_config
from literature_screening.pipeline.run_pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the literature screening pipeline.")
    parser.add_argument("--config", required=True, help="Path to the YAML configuration file.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config and initialize output layout without calling the model.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config_path = Path(args.config).resolve()
    run_config = load_run_config(config_path)
    run_pipeline(run_config, dry_run=args.dry_run)
    return 0

