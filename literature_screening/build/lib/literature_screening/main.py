from pathlib import Path

from literature_screening.cli import main
from literature_screening.core.env import load_dotenv_file


if __name__ == "__main__":
    load_dotenv_file(Path(__file__).resolve().parents[2] / ".env")
    raise SystemExit(main())
