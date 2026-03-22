from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from services import CriteriaDraft
from services import ModelDraft
from services import PROJECT_ROOT
from services import ReportJobRequest
from services import ScreeningJobRequest
from services import api_key_available
from services import generate_simple_report_job
from services import list_ui_runs
from services import load_existing_screening_run
from services import load_text_file
from services import parse_criteria_markdown_text
from services import read_text_file
from services import run_screening_job
from services import save_uploaded_file_bytes
from services import scan_supported_input_files
from styles import GLOBAL_CSS


st.set_page_config(
    page_title="Literature Screening Studio",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _init_state() -> None:
    defaults = {
        "criteria_topic": "",
        "criteria_inclusion": "",
        "criteria_exclusion": "",
        "criteria_path": str(PROJECT_ROOT.parent / "robot" / "筛选标准.md"),
        "input_folder": str(PROJECT_ROOT.parent / "robot"),
        "latest_screening_result": None,
        "latest_report_result": None,
        "cached_input_paths": [],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _render_hero() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero-shell">
            <div class="hero-eyebrow">Literature Screening Studio</div>
            <h1 class="hero-title">把初筛和整理报告放进一个可直接交互的工作台</h1>
            <p class="hero-body">
                这个界面只做交互编排，不直接掺入底层业务逻辑。
                主项目继续负责初筛，独立报告模块继续负责简洁报告，
                前端通过单独服务层衔接两边，后续模块参数变化时也更容易同步。
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar() -> ModelDraft:
    with st.sidebar:
        st.markdown("### 运行设置")
        provider = st.selectbox("模型提供方", ["deepseek", "kimi"], index=0)
        model_name = st.text_input("模型名称", value="deepseek-chat" if provider == "deepseek" else "moonshot-v1-8k")
        api_base_url = st.text_input(
            "API Base URL",
            value="https://api.deepseek.com/v1" if provider == "deepseek" else "https://api.moonshot.cn/v1",
        )
        api_key_env = st.text_input(
            "API Key 环境变量",
            value="DEEPSEEK_API_KEY" if provider == "deepseek" else "KIMI_API_KEY",
        )
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.0, step=0.1)
        max_tokens = st.number_input("Max tokens", min_value=512, max_value=8192, value=1536, step=256)
        min_interval = st.number_input("请求间隔（秒）", min_value=0.0, max_value=20.0, value=2.0, step=0.5)

        available = api_key_available(api_key_env)
        st.caption(f"当前环境变量状态：{'已检测到' if available else '未检测到'} `{api_key_env}`")

        with st.expander("界面说明", expanded=False):
            st.write("建议先完成初筛，再在第三个标签页里生成简洁报告。")
            st.write("历史结果可以在第四个标签页回载，不必重跑。")

    return ModelDraft(
        provider=provider,
        model_name=model_name,
        api_base_url=api_base_url,
        api_key_env=api_key_env,
        temperature=temperature,
        max_tokens=int(max_tokens),
        min_request_interval_seconds=float(min_interval),
    )


def _load_criteria_from_path(path_text: str) -> None:
    path = Path(path_text).expanduser()
    criteria = parse_criteria_markdown_text(load_text_file(path), source_path=str(path))
    st.session_state["criteria_topic"] = criteria.topic
    st.session_state["criteria_inclusion"] = "\n".join(criteria.inclusion)
    st.session_state["criteria_exclusion"] = "\n".join(criteria.exclusion)


def _section_card(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="section-card">
            <div class="section-title">{title}</div>
            <p class="section-copy">{copy}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_input_sources() -> list[Path]:
    input_mode = st.radio("文献输入方式", ["本地文件夹", "上传文件"], horizontal=True)
    selected_paths: list[Path] = []

    if input_mode == "本地文件夹":
        folder = st.text_input("文献文件夹路径", key="input_folder")
        if st.button("扫描文件夹", use_container_width=True) or folder:
            try:
                selected_paths = scan_supported_input_files(Path(folder))
                st.session_state["cached_input_paths"] = selected_paths
                st.success(f"已识别 {len(selected_paths)} 个支持文件。")
            except Exception as exc:
                st.error(str(exc))
                selected_paths = []
        else:
            selected_paths = st.session_state.get("cached_input_paths", [])
    else:
        uploaded_files = st.file_uploader(
            "上传文献文件",
            type=["bib", "ris", "enw", "txt"],
            accept_multiple_files=True,
        )
        if uploaded_files:
            temp_dir = PROJECT_ROOT / "data" / "ui_upload_cache"
            selected_paths = save_uploaded_file_bytes(
                [(item.name, item.getvalue()) for item in uploaded_files],
                temp_dir,
            )
            st.session_state["cached_input_paths"] = selected_paths
            st.success(f"已暂存 {len(selected_paths)} 个上传文件。")
        else:
            selected_paths = st.session_state.get("cached_input_paths", [])

    if selected_paths:
        st.markdown("".join([f'<span class=\"path-pill\">{path.name}</span>' for path in selected_paths]), unsafe_allow_html=True)
    return selected_paths


def _render_criteria_editor() -> CriteriaDraft:
    st.text_input("筛选标准 Markdown 路径", key="criteria_path")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("从 Markdown 读取标准", use_container_width=True):
            try:
                _load_criteria_from_path(st.session_state["criteria_path"])
                st.success("已载入筛选标准。")
            except Exception as exc:
                st.error(f"读取筛选标准失败：{exc}")
    with col2:
        if st.button("清空当前标准", use_container_width=True):
            st.session_state["criteria_topic"] = ""
            st.session_state["criteria_inclusion"] = ""
            st.session_state["criteria_exclusion"] = ""

    topic = st.text_input("主题名称", key="criteria_topic")
    inclusion = st.text_area("纳入标准（每行一条）", height=180, key="criteria_inclusion")
    exclusion = st.text_area("排除标准（每行一条）", height=180, key="criteria_exclusion")

    inclusion_items = [line.strip() for line in inclusion.splitlines() if line.strip()]
    exclusion_items = [line.strip() for line in exclusion.splitlines() if line.strip()]
    return CriteriaDraft(
        topic=topic.strip() or "未命名文献主题",
        inclusion=inclusion_items,
        exclusion=exclusion_items,
        source_path=st.session_state["criteria_path"],
    )


def _render_summary_metrics(summary: dict) -> None:
    st.markdown(
        f"""
        <div class="metric-strip">
            <div class="metric-card"><div class="metric-label">原始条目</div><div class="metric-value">{summary.get('raw_entries_count', 0)}</div></div>
            <div class="metric-card"><div class="metric-label">去重后</div><div class="metric-value">{summary.get('deduped_entries_count', 0)}</div></div>
            <div class="metric-card"><div class="metric-label">纳入</div><div class="metric-value">{summary.get('included_count', 0)}</div></div>
            <div class="metric-card"><div class="metric-label">不确定</div><div class="metric-value">{summary.get('uncertain_count', 0)}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_results(result) -> None:
    _render_summary_metrics(result.summary)
    st.caption(f"输出目录：`{result.output_dir}`")
    st.caption(f"配置文件：`{result.config_path}`")

    decision_tabs = st.tabs(["纳入", "剔除", "不确定", "文件预览"])
    records_df = pd.DataFrame(result.records)

    with decision_tabs[0]:
        include_df = records_df[records_df["decision"] == "include"] if not records_df.empty else pd.DataFrame()
        st.dataframe(include_df, use_container_width=True, hide_index=True)
    with decision_tabs[1]:
        exclude_df = records_df[records_df["decision"] == "exclude"] if not records_df.empty else pd.DataFrame()
        st.dataframe(exclude_df, use_container_width=True, hide_index=True)
    with decision_tabs[2]:
        uncertain_df = records_df[records_df["decision"] == "uncertain"] if not records_df.empty else pd.DataFrame()
        st.dataframe(uncertain_df, use_container_width=True, hide_index=True)
    with decision_tabs[3]:
        for label, path in result.reports.items():
            if path.exists():
                with st.expander(label, expanded=False):
                    if path.suffix.lower() == ".md":
                        st.markdown(read_text_file(path))
                    else:
                        content = path.read_text(encoding="utf-8", errors="ignore")
                        st.code(content[:4000] or "(空文件)")
                    st.download_button(
                        label=f"下载 {path.name}",
                        data=path.read_bytes(),
                        file_name=path.name,
                        use_container_width=True,
                    )


def _render_history() -> None:
    runs = list_ui_runs()
    if not runs:
        st.info("目前还没有 UI 工作台生成的运行记录。")
        return

    options = {run.name: run for run in runs}
    selected = st.selectbox("历史运行", list(options.keys()))
    run_root = options[selected]
    screening_dir = run_root / "screening_output"
    if screening_dir.exists():
        st.caption(f"运行目录：`{run_root}`")
        if st.button("载入这次初筛结果", key=f"load-{selected}"):
            st.session_state["latest_screening_result"] = load_existing_screening_run(screening_dir)
            st.success("已载入该初筛结果。")


def main() -> None:
    _init_state()
    _render_hero()
    model = _render_sidebar()

    tab_run, tab_results, tab_report, tab_history = st.tabs(["初筛配置", "初筛结果", "简洁报告", "历史记录"])
    current_topic = st.session_state.get("criteria_topic", "")
    latest_screening_result = st.session_state.get("latest_screening_result")
    if latest_screening_result is not None and latest_screening_result.criteria_topic:
        current_topic = latest_screening_result.criteria_topic

    with tab_run:
        left, right = st.columns([1.15, 1], gap="large")

        with left:
            _section_card(
                "文献输入",
                "你可以直接指向一个本地文件夹，也可以临时上传一批 `.bib`、`.ris`、`.enw` 或 EndNote 风格 `.txt` 文件。",
            )
            input_paths = _render_input_sources()

        with right:
            _section_card(
                "筛选标准",
                "优先从现有 Markdown 标准中自动读取，再按需要手工微调。前端会把主题、纳入标准和排除标准统一转换成稳定配置。",
            )
            criteria = _render_criteria_editor()

        with st.expander("高级初筛设置", expanded=False):
            col1, col2, col3 = st.columns(3)
            batch_size = col1.number_input("每批篇数", min_value=1, max_value=20, value=5)
            target_count = col2.number_input("目标纳入数量", min_value=1, max_value=9999, value=9999)
            timeout_seconds = col3.number_input("请求超时（秒）", min_value=60, max_value=600, value=240, step=30)
            col4, col5, col6 = st.columns(3)
            stop_when_target = col4.toggle("达到目标后停止", value=False)
            allow_uncertain = col5.toggle("保留 uncertain", value=True)
            retry_times = col6.number_input("重试次数", min_value=0, max_value=10, value=8)

        project_name = st.text_input("本次运行名称", value="robot-ui-run", help="会用于生成 UI 工作台下的运行目录名。")

        if st.button("运行初筛", use_container_width=True):
            if not input_paths:
                st.error("请先准备文献输入文件。")
            elif not criteria.inclusion or not criteria.exclusion:
                st.error("请先补齐筛选标准。")
            else:
                request = ScreeningJobRequest(
                    project_name=project_name,
                    input_paths=input_paths,
                    criteria=criteria,
                    model=model,
                    batch_size=int(batch_size),
                    target_include_count=int(target_count),
                    stop_when_target_reached=bool(stop_when_target),
                    allow_uncertain=bool(allow_uncertain),
                    retry_times=int(retry_times),
                    request_timeout_seconds=int(timeout_seconds),
                )
                with st.status("正在运行初筛...", expanded=True) as status:
                    st.write("1. 整理输入文件并生成本次运行配置")
                    st.write("2. 合并文献、去重并按批次送给模型")
                    st.write("3. 收集初筛结果并输出筛选报告")
                    result = run_screening_job(request)
                    status.update(label="初筛完成", state="complete")

                st.session_state["latest_screening_result"] = result
                st.session_state["latest_report_result"] = None
                st.success("初筛已完成，结果已经载入到“初筛结果”标签页。")

    with tab_results:
        if latest_screening_result is None:
            st.info("先运行一次初筛，或到“历史记录”标签页载入已有结果。")
        else:
            _section_card(
                "当前结果",
                "这里展示本次初筛的统计、筛选明细和导出文件。你可以在确认结果后再去生成独立报告模块的简洁整理稿。",
            )
            _render_results(latest_screening_result)

    with tab_report:
        if latest_screening_result is None:
            st.info("请先完成初筛，报告模块会直接基于当前初筛输出目录生成整理稿。")
        else:
            _section_card(
                "简洁报告",
                "这一页只调用独立报告模块，默认生成三段式整理稿：总体情况、类型划分、逐篇总结分析。",
            )
            report_topic = st.text_input("报告主题", value=current_topic)
            report_name = st.text_input("报告目录名", value="simple_report")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"将使用当前初筛输出：`{latest_screening_result.output_dir}`")
            with col2:
                generate_clicked = st.button("生成简洁报告", use_container_width=True)

            if generate_clicked:
                request = ReportJobRequest(
                    screening_output_dir=latest_screening_result.output_dir,
                    project_topic=report_topic.strip() or "未命名文献主题",
                    model=model,
                    report_name=report_name.strip() or "simple_report",
                )
                with st.status("正在生成简洁报告...", expanded=True) as status:
                    st.write("1. 读取纳入文献和初筛理由")
                    st.write("2. 生成逐篇总结与分析")
                    st.write("3. 汇总为可直接阅读的整理报告")
                    report_result = generate_simple_report_job(request)
                    status.update(label="简洁报告完成", state="complete")
                st.session_state["latest_report_result"] = report_result
                st.success("简洁报告已经生成。")

            report_result = st.session_state.get("latest_report_result")
            if report_result is not None:
                st.caption(f"报告目录：`{report_result.report_output_dir}`")
                st.download_button(
                    label="下载 literature_report.md",
                    data=report_result.report_path.read_bytes(),
                    file_name=report_result.report_path.name,
                    use_container_width=True,
                )
                st.markdown(report_result.markdown)

    with tab_history:
        _section_card(
            "历史运行",
            "这里会列出通过前端工作台创建的运行目录。后续如果需要继续做比对、复查或二次生成报告，可以直接回载。",
        )
        _render_history()


if __name__ == "__main__":
    main()
