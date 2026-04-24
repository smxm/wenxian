# Screening and Data Pipeline

## Owns

- input parsing across supported bibliography formats
- normalization and deduplication before screening
- batch formation, prompt building, LLM calls, response parsing, and validation
- screening-output artifacts that downstream review, fulltext, and reporting depend on
- target included-paper stopping and partial-output semantics as they affect downstream artifacts

## Main Files

| File | Responsibility |
| --- | --- |
| `literature_screening/src/literature_screening/bibtex/parser.py` | parse `.bib`, `.ris`, `.enw`, and PubMed text inputs |
| `literature_screening/src/literature_screening/bibtex/normalizer.py` | normalize titles and textual fields |
| `literature_screening/src/literature_screening/bibtex/deduper.py` | DOI and title-based deduplication |
| `literature_screening/src/literature_screening/bibtex/exporter.py` | export RIS and BibTeX artifacts |
| `literature_screening/src/literature_screening/screening/batcher.py` | split records into model-sized batches |
| `literature_screening/src/literature_screening/screening/prompt_builder.py` | build screening prompts |
| `literature_screening/src/literature_screening/screening/llm_client.py` | provider/model invocation wrapper |
| `literature_screening/src/literature_screening/screening/response_parser.py` | parse raw model decisions |
| `literature_screening/src/literature_screening/screening/validator.py` | validate paper ids and batch completeness |
| `literature_screening/src/literature_screening/pipeline/run_pipeline.py` | execute the end-to-end screening flow |

## Start Here When

- imported files are read incorrectly
- dedup counts or paper ids look wrong
- screening batches, retry behavior, or prompt content need to change
- generated screening artifacts are malformed downstream
- a stopped or deleted screening round still appears in cumulative/fulltext/report datasets incorrectly

## Typical Changes

- extend input format support or text cleanup
- tune dedup heuristics and export behavior
- change batch size, retry, timeout, or prompt wording
- harden response parsing or validation around malformed model output
- adjust stop-target behavior while preserving enough run output for review/workbench handoff

## Watch-Outs

- paper identity flows into review, workbench, fulltext, and reporting, so be careful with `paper_id` behavior
- export changes can quietly break downstream consumers that assume specific file names or fields
- a fix in `screening/` may still require an orchestration or API metadata change if the UI needs to know about it
- stopping after a target include count should be checked in both pipeline execution and task persistence, not just in the frontend form

## Common Verifications

- `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src /Users/mao/Documents/langchain/literature_screening/.venv311-codex/bin/python -m pytest literature_screening/tests/test_screening_pipeline.py literature_screening/tests/test_api_app.py`
- inspect generated `screening_output` artifacts for shape regressions when changing exporters or parsers
