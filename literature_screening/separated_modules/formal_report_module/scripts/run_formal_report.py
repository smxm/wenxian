from __future__ import annotations

import argparse
import sys
from pathlib import Path


def bootstrap_paths() -> None:
    module_root = Path(__file__).resolve().parents[1]
    project_root = module_root.parents[1]
    main_src = project_root / "src"
    detached_src = module_root / "src"

    if str(main_src) not in sys.path:
        sys.path.insert(0, str(main_src))

    import literature_screening

    detached_pkg_root = detached_src / "literature_screening"
    if str(detached_pkg_root) not in list(literature_screening.__path__):
        literature_screening.__path__.append(str(detached_pkg_root))

    from literature_screening.core.env import load_dotenv_file

    load_dotenv_file(project_root / ".env")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a detached formal report from an existing screening run.")
    parser.add_argument("--screening-output-dir", required=True, help="Existing screening output directory.")
    parser.add_argument("--report-output-dir", required=True, help="Directory for detached report outputs.")
    parser.add_argument("--project-topic", required=True, help="Research topic for the report.")
    parser.add_argument("--report-title-hint", default="", help="Optional title hint.")
    parser.add_argument("--provider", choices=["none", "kimi", "deepseek"], default="none")
    parser.add_argument("--model-name", default="")
    parser.add_argument("--api-base-url", default="")
    parser.add_argument("--api-key-env", default="")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--min-request-interval", type=float, default=2.0)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--retry-times", type=int, default=4)
    parser.add_argument("--card-batch-size", type=int, default=3)
    return parser


def main() -> int:
    bootstrap_paths()
    args = build_parser().parse_args()

    from literature_screening.core.models import ModelConfig
    from literature_screening.formal_report.pipeline import generate_formal_report_from_screening

    model_config = None
    if args.provider != "none":
        model_config = ModelConfig(
            provider=args.provider,
            model_name=args.model_name,
            api_base_url=args.api_base_url,
            api_key_env=args.api_key_env,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            min_request_interval_seconds=args.min_request_interval,
        )

    generate_formal_report_from_screening(
        screening_output_dir=Path(args.screening_output_dir).resolve(),
        report_output_dir=Path(args.report_output_dir).resolve(),
        project_topic=args.project_topic,
        report_title_hint=args.report_title_hint or f"{args.project_topic}文献整理报告",
        model_config=model_config,
        timeout_seconds=args.timeout_seconds,
        retry_times=args.retry_times,
        card_batch_size=args.card_batch_size,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
