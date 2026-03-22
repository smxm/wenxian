# Literature Screening

AI-assisted literature screening pipeline for merged BibTeX inputs.

## Quick Start

1. Create a virtual environment.
2. Install dependencies with `pip install -e .`.
3. Copy `.env.example` to `.env` and set `KIMI_API_KEY` or `DEEPSEEK_API_KEY`.
4. Adjust `configs/config.example.yaml`.
5. Run:

```bash
python -m literature_screening.main --config ./configs/config.example.yaml
```

## Current Scope

This repository is now focused on the initial screening workflow:

- merging multiple literature export files
- parsing `.bib`, `.ris`, `.enw`, and EndNote-style `.txt`
- deduplication
- batch screening with supported LLM providers
- exporting screening reports and retained bibliography files
- default retained-reference export in `.ris`, with optional `.bib` compatibility export

The current main pipeline does not generate the final polished report. That capability has been split out from the primary screening flow and moved under `separated_modules/formal_report_module`.

## Local Frontend

An interactive local frontend is now available under:

- `E:\wenxian\literature_screening\frontend_app`

Launch it with:

```bash
python -m streamlit run E:\wenxian\literature_screening\frontend_app\app.py
```

The frontend acts as an orchestration layer only:

- it calls the screening pipeline for initial screening
- it calls the detached simple-report module for the concise report
- it keeps UI-specific run records under `data/ui_runs`
