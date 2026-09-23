import streamlit as st # type: ignore

NAV_ITEMS = [
    ("Home", "pages/home.py"),
    ("Teams", "pages/teams.py"),
    ("Players", "pages/players.py"),
    ("Points", "pages/points.py"),
    ("Fixtures", "pages/fixtures.py"),
    ("Graphs", "pages/graphs.py"),
    ("Leagues", "pages/leagues.py"),
    ("Models", "pages/models.py"),
]

THEME_STATE_KEY = "fpl_dark_mode"


THEMES = {
    False: {
        "page_bg": "linear-gradient(135deg, #37003c, #2b1e5b, #00cc6a)",
        "nav_bg": "rgba(14, 10, 28, 0.55)",
        "panel_bg": "rgba(255,255,255,0.12)",
        "panel_bg_strong": "rgba(255,255,255,0.15)",
        "panel_border": "rgba(255,255,255,0.20)",
        "soft_bg": "rgba(255,255,255,0.10)",
        "button_bg": "rgba(255,255,255,0.12)",
        "button_hover": "rgba(255,255,255,0.22)",
        "text": "#ffffff",
        "text_muted": "rgba(255,255,255,0.78)",
        "shadow": "0 14px 34px rgba(0,0,0,0.28)",
    },
    True: {
        "page_bg": (
            "radial-gradient(circle at 16% 12%, rgba(0,255,135,0.12), transparent 28%), "
            "radial-gradient(circle at 84% 10%, rgba(116,245,192,0.08), transparent 24%), "
            "linear-gradient(135deg, #230027 0%, #2a174d 52%, #102a20 100%)"
        ),
        "nav_bg": "rgba(33, 0, 46, 0.72)",
        "panel_bg": "rgba(42, 20, 72, 0.56)",
        "panel_bg_strong": "rgba(50, 24, 84, 0.70)",
        "panel_border": "rgba(191, 142, 255, 0.24)",
        "soft_bg": "rgba(255,255,255,0.08)",
        "button_bg": "rgba(255,255,255,0.10)",
        "button_hover": "rgba(191,142,255,0.18)",
        "text": "#f8fff9",
        "text_muted": "rgba(248,255,249,0.76)",
        "shadow": "0 18px 42px rgba(0,0,0,0.44)",
    },
}


def init_theme_state():
    if THEME_STATE_KEY not in st.session_state:
        st.session_state[THEME_STATE_KEY] = bool(st.session_state.get("dark_mode", True))

    st.session_state["dark_mode"] = st.session_state[THEME_STATE_KEY]


def set_theme_preference(is_dark):
    st.session_state[THEME_STATE_KEY] = bool(is_dark)
    st.session_state["dark_mode"] = bool(is_dark)


def theme_is_dark():
    return bool(st.session_state.get(THEME_STATE_KEY, st.session_state.get("dark_mode", True)))


def render_theme_styles():
    init_theme_state()
    theme = THEMES[theme_is_dark()]
    st.markdown(
        f"""
<style>
.stApp {{
    --fpl-page-bg: {theme["page_bg"]};
    --fpl-nav-bg: {theme["nav_bg"]};
    --fpl-panel-bg: {theme["panel_bg"]};
    --fpl-panel-bg-strong: {theme["panel_bg_strong"]};
    --fpl-panel-border: {theme["panel_border"]};
    --fpl-soft-bg: {theme["soft_bg"]};
    --fpl-button-bg: {theme["button_bg"]};
    --fpl-button-hover: {theme["button_hover"]};
    --fpl-glass-bg: linear-gradient(135deg, rgba(255,255,255,0.17), rgba(255,255,255,0.07));
    --fpl-glass-bg-strong: linear-gradient(135deg, rgba(255,255,255,0.23), rgba(255,255,255,0.10));
    --fpl-glass-highlight: inset 0 1px 0 rgba(255,255,255,0.24);
    --fpl-text: {theme["text"]};
    --fpl-text-muted: {theme["text_muted"]};
    --fpl-shadow: {theme["shadow"]};
    background: var(--fpl-page-bg) !important;
    min-height: 100vh;
}}

.stMainBlockContainer {{
    max-width: none !important;
}}

h1, h2, h3, p, div, li, label {{
    color: var(--fpl-text) !important;
}}

.glass-box,
.glass-panel,
.points-box,
.leagues-box,
.matches-box,
.matches-header-box,
.matches-body-box,
.match-hero,
.player-chip,
.metric-card,
.data-row,
.mini-chart,
.profile-panel,
.mini-player-card,
.center-box,
.comp-head,
.comp-label,
.comp-cell,
div[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stExpander"] {{
    background: var(--fpl-panel-bg) !important;
    border-color: var(--fpl-panel-border) !important;
    box-shadow: var(--fpl-shadow) !important;
}}

div[data-testid="stMetric"] {{
    background: var(--fpl-soft-bg) !important;
    border: 1px solid var(--fpl-panel-border) !important;
    border-radius: 12px !important;
    padding: 10px !important;
}}

div[data-testid="stButton"] > button,
div[data-testid="stDownloadButton"] > button,
div[data-testid="stFormSubmitButton"] button,
div[data-testid="stLinkButton"] > a,
div[data-testid="stPageLink"] > a,
div[data-baseweb="select"] > div,
div[role="radiogroup"] label {{
    background: var(--fpl-glass-bg) !important;
    border-color: var(--fpl-panel-border) !important;
    color: var(--fpl-text) !important;
    backdrop-filter: blur(18px) saturate(145%) !important;
    -webkit-backdrop-filter: blur(18px) saturate(145%) !important;
    box-shadow: var(--fpl-glass-highlight), 0 8px 22px rgba(0,0,0,0.20) !important;
}}

div[data-testid="stButton"] > button:hover,
div[data-testid="stDownloadButton"] > button:hover,
div[data-testid="stFormSubmitButton"] button:hover,
div[data-testid="stLinkButton"] > a:hover,
div[data-testid="stPageLink"] > a:hover {{
    background: var(--fpl-glass-bg-strong) !important;
    color: var(--fpl-text) !important;
    border-color: rgba(255,255,255,0.38) !important;
    box-shadow: var(--fpl-glass-highlight), 0 10px 26px rgba(0,0,0,0.24) !important;
}}

div[data-testid="stButton"] > button:disabled,
div[data-testid="stDownloadButton"] > button:disabled,
div[data-testid="stFormSubmitButton"] button:disabled {{
    background: linear-gradient(135deg, rgba(255,255,255,0.09), rgba(255,255,255,0.035)) !important;
    border-color: rgba(255,255,255,0.11) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.10) !important;
}}

div[data-testid="stPageLink"] > a[aria-current="page"] {{
    background: linear-gradient(135deg, rgba(0,255,135,0.30), rgba(116,245,192,0.12)) !important;
    border-color: rgba(0,255,135,0.48) !important;
    color: var(--fpl-text) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.28), 0 8px 22px rgba(0,0,0,0.20) !important;
}}

/* Glass tables: Streamlit grids, native HTML tables, and league standings. */
div[data-testid="stDataFrame"],
div[data-testid="stDataEditor"],
div[data-testid="stTable"],
.league-standings-wrap,
table {{
    background: var(--fpl-glass-bg) !important;
    border: 1px solid var(--fpl-panel-border) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(18px) saturate(145%) !important;
    -webkit-backdrop-filter: blur(18px) saturate(145%) !important;
    box-shadow: var(--fpl-glass-highlight), 0 12px 30px rgba(0,0,0,0.24) !important;
}}

div[data-testid="stDataFrame"] > div,
div[data-testid="stDataEditor"] > div,
div[data-testid="stTable"] > div {{
    background: transparent !important;
}}

div[data-testid="stDataFrame"] [role="columnheader"],
div[data-testid="stDataFrame"] [role="rowheader"],
div[data-testid="stDataEditor"] [role="columnheader"],
div[data-testid="stDataEditor"] [role="rowheader"],
table thead,
.league-standings-header {{
    background: linear-gradient(135deg, rgba(255,255,255,0.20), rgba(255,255,255,0.09)) !important;
}}

div[data-testid="stDataFrame"] [role="gridcell"],
div[data-testid="stDataEditor"] [role="gridcell"],
table tbody tr,
.league-standings-row {{
    background: rgba(255,255,255,0.045) !important;
}}

table tbody tr:hover,
.league-standings-row:hover {{
    background: rgba(255,255,255,0.10) !important;
}}

.panel-sub,
.team-meta,
.metric-note,
.fixture-meta,
.fixture-date,
.chip-meta,
.empty-note,
.empty-stat,
.page-caption,
.profile-meta,
.profile-news,
.mini-player-meta,
.mini-stat-row {{
    color: var(--fpl-text-muted) !important;
}}

.rank-gold,
.league-cell.rank.rank-gold,
.league-cell.last-rank.rank-gold {{
    color: #ffd700 !important;
    font-weight: 900 !important;
    text-shadow: 0 0 12px rgba(255, 215, 0, 0.35) !important;
}}

.rank-silver,
.league-cell.rank.rank-silver,
.league-cell.last-rank.rank-silver {{
    color: #d7dde7 !important;
    font-weight: 900 !important;
    text-shadow: 0 0 12px rgba(215, 221, 231, 0.28) !important;
}}

.rank-bronze,
.league-cell.rank.rank-bronze,
.league-cell.last-rank.rank-bronze {{
    color: #cd7f32 !important;
    font-weight: 900 !important;
    text-shadow: 0 0 12px rgba(205, 127, 50, 0.32) !important;
}}

div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPageLink"]) {{
    background: var(--fpl-nav-bg) !important;
    border-color: var(--fpl-panel-border) !important;
}}

div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPageLink"]) div[data-testid="stCheckbox"],
div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPageLink"]) div[data-testid="stToggle"] {{
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    min-height: 32px !important;
    height: 32px !important;
    padding: 0 !important;
    margin: 0 !important;
}}

div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPageLink"]) div[data-testid="stCheckbox"] label,
div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPageLink"]) div[data-testid="stToggle"] label {{
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    margin: 0 !important;
    padding: 0 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    line-height: 1 !important;
    color: var(--fpl-text) !important;
}}

div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPageLink"]) div[data-testid="stCheckbox"] label > div,
div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPageLink"]) div[data-testid="stToggle"] label > div,
div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPageLink"]) div[data-testid="stWidgetLabel"] {{
    display: flex !important;
    align-items: center !important;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}}

div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPageLink"]) div[data-testid="stWidgetLabel"] p {{
    line-height: 1 !important;
    margin: 0 !important;
}}
</style>
""",
        unsafe_allow_html=True,
    )


def render_top_nav():
    st.markdown(
        """
<style>
/* ── Fixed top nav ── */

/* Hide Streamlit's own header to reclaim space */
header[data-testid="stHeader"] {
    display: none !important;
}

/* The nav horizontal block: pulled out of flow and pinned to the top */
div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPageLink"]) {
    position: fixed !important;
    top: 60px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: calc(100% - 32px) !important;
    max-width: 1400px !important;
    z-index: 9999 !important;
    margin: 0 !important;
    padding: 4px 10px !important;
    gap: 10px !important;
    min-height: 46px !important;
    align-items: center !important;
    border-radius: 16px !important;
    background: rgba(14, 10, 28, 0.75) !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
    backdrop-filter: blur(20px) saturate(150%) !important;
    -webkit-backdrop-filter: blur(20px) saturate(150%) !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.35) !important;
}

/* Push page content down so it clears the fixed nav (bar bottom ~106px + 20px gap) */
div[data-testid="stAppViewBlockContainer"],
.stMainBlockContainer {
    padding-top: 70px !important;
    padding-top: 80px !important;
}

div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPageLink"]) > div[data-testid="stColumn"] {
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
}

div[data-testid="stPageLink"] > a {
    display: block !important;
    text-align: center !important;
    padding: 6px 12px !important;
    border-radius: 999px !important;
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.16) !important;
    color: rgba(255,255,255,0.85) !important;
    font-size: 12.5px !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px !important;
    text-decoration: none !important;
    transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease !important;
}

div[data-testid="stPageLink"] > a:hover {
    background: rgba(255,255,255,0.16) !important;
    color: #ffffff !important;
    border-color: rgba(255,255,255,0.4) !important;
}

div[data-testid="stPageLink"] > a[aria-current="page"] {
    color: #0b1a13 !important;
    background: linear-gradient(135deg, #00ff87, #74f5c0) !important;
    border-color: rgba(0,255,135,0.65) !important;
}

@media (max-width: 768px) {
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPageLink"]) {
        top: 60px !important;
        width: calc(100% - 16px) !important;
        padding: 4px 8px !important;
        gap: 6px !important;
        min-height: 42px !important;
        border-radius: 14px !important;
    }

    div[data-testid="stPageLink"] > a {
        font-size: 11.5px !important;
        padding: 6px 9px !important;
    }

    .stMainBlockContainer {
        padding-top: 126px !important;
    }
}
</style>
""",
        unsafe_allow_html=True,
    )

    init_theme_state()
    render_theme_styles()

    nav_cols = st.columns([1] * len(NAV_ITEMS) + [0.85], gap="small")
    for col, (label, path) in zip(nav_cols[:-1], NAV_ITEMS):
        with col:
            st.page_link(path, label=label)

    with nav_cols[-1]:
        selected_dark = st.toggle("Dark", value=theme_is_dark())

    if selected_dark != theme_is_dark():
        set_theme_preference(selected_dark)
        st.rerun()
