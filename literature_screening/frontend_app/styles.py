from __future__ import annotations


GLOBAL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

    :root {
        --page-bg: linear-gradient(180deg, #f6f1e8 0%, #efe4d3 40%, #f8f7f3 100%);
        --panel-bg: rgba(255, 253, 248, 0.84);
        --panel-border: rgba(52, 84, 61, 0.14);
        --accent: #245a46;
        --ink: #1d2a28;
        --muted: #5f6b67;
        --shadow: 0 18px 42px rgba(70, 60, 44, 0.09);
        --radius: 22px;
    }

    .stApp {
        background: var(--page-bg);
        color: var(--ink);
        font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
    }

    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 4rem;
        max-width: 1280px;
    }

    .hero-shell {
        background:
            radial-gradient(circle at top right, rgba(36, 90, 70, 0.18), transparent 32%),
            radial-gradient(circle at bottom left, rgba(184, 106, 42, 0.16), transparent 26%),
            rgba(255, 251, 245, 0.92);
        border: 1px solid var(--panel-border);
        border-radius: 28px;
        box-shadow: var(--shadow);
        padding: 1.8rem 2rem;
        margin-bottom: 1.25rem;
    }

    .hero-eyebrow {
        font-size: 0.85rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--accent);
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .hero-title {
        font-family: "Noto Serif SC", "Songti SC", serif;
        font-size: 2.15rem;
        line-height: 1.25;
        margin: 0 0 0.6rem 0;
        color: var(--ink);
    }

    .hero-body {
        color: var(--muted);
        font-size: 1rem;
        line-height: 1.7;
        margin: 0;
    }

    .section-card {
        background: var(--panel-bg);
        border: 1px solid var(--panel-border);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        padding: 1.15rem 1.25rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
    }

    .section-title {
        font-family: "Noto Serif SC", "Songti SC", serif;
        color: var(--ink);
        font-size: 1.1rem;
        margin: 0 0 0.5rem 0;
    }

    .section-copy {
        color: var(--muted);
        margin: 0;
        line-height: 1.65;
    }

    .metric-strip {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.8rem;
        margin: 0.3rem 0 1.1rem 0;
    }

    .metric-card {
        background: rgba(255, 255, 255, 0.78);
        border: 1px solid rgba(36, 90, 70, 0.1);
        border-radius: 18px;
        padding: 0.9rem 1rem;
        box-shadow: var(--shadow);
    }

    .metric-label {
        font-size: 0.82rem;
        color: var(--muted);
        margin-bottom: 0.25rem;
    }

    .metric-value {
        font-size: 1.5rem;
        line-height: 1.2;
        color: var(--ink);
        font-weight: 700;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.4rem;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.55);
        border-radius: 999px;
        padding-left: 1rem;
        padding-right: 1rem;
        border: 1px solid rgba(36, 90, 70, 0.08);
    }

    .stTabs [aria-selected="true"] {
        background: rgba(36, 90, 70, 0.12) !important;
        color: var(--accent) !important;
    }

    .stButton > button,
    .stDownloadButton > button {
        border-radius: 999px;
        border: 1px solid rgba(36, 90, 70, 0.14);
        background: linear-gradient(135deg, #245a46 0%, #2f7358 100%);
        color: white;
        font-weight: 600;
        padding: 0.55rem 1rem;
        box-shadow: 0 12px 22px rgba(36, 90, 70, 0.18);
    }

    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        border-radius: 16px !important;
    }

    .path-pill {
        display: inline-block;
        background: rgba(36, 90, 70, 0.08);
        color: var(--accent);
        padding: 0.32rem 0.7rem;
        border-radius: 999px;
        font-size: 0.86rem;
        margin-right: 0.35rem;
        margin-bottom: 0.35rem;
    }
</style>
"""
