from __future__ import annotations

import sys
from pathlib import Path


TEST_ROOT = Path(__file__).resolve().parents[1]
if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))

from services import parse_criteria_markdown_text
from services import scan_supported_input_files


def test_parse_criteria_markdown_text_extracts_topic_and_items() -> None:
    text = """
# Role

我正在撰写一篇关于【地下机器人机制分类与应用】的论文。

* 纳入标准 (Inclusion Criteria)：必须涉及主动钻探机器人；必须有地下场景验证。
* 排除标准 (Exclusion Criteria)：排除深空挖掘机器人；排除纯生物学研究。
"""

    draft = parse_criteria_markdown_text(text)

    assert draft.topic == "地下机器人机制分类与应用"
    assert "必须涉及主动钻探机器人" in draft.inclusion
    assert "必须有地下场景验证" in draft.inclusion
    assert "排除深空挖掘机器人" in draft.exclusion
    assert "排除纯生物学研究" in draft.exclusion


def test_scan_supported_input_files_filters_extensions(tmp_path: Path) -> None:
    (tmp_path / "a.bib").write_text("", encoding="utf-8")
    (tmp_path / "b.enw").write_text("", encoding="utf-8")
    (tmp_path / "c.ris").write_text("", encoding="utf-8")
    (tmp_path / "d.txt").write_text("", encoding="utf-8")
    (tmp_path / "ignore.pdf").write_text("", encoding="utf-8")

    files = scan_supported_input_files(tmp_path)

    assert [path.name for path in files] == ["a.bib", "b.enw", "c.ris", "d.txt"]
