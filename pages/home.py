import streamlit as st # type: ignore
import streamlit.components.v1 as components # type: ignore
import json
import urllib.request
import ssl
import certifi
import os
import tempfile
import html
from datetime import datetime, timezone
from nav import render_top_nav

st.set_page_config(page_title="FPL Home", layout="wide")

is_guest = st.session_state.get("guest", False)
if "manager_id" not in st.session_state and not is_guest:
    st.warning("No manager ID found. Go back to Dashboard and connect your team.")
    if st.button("Go to Dashboard"):
        st.switch_page("live_dashboard.py")
    st.stop()

st.markdown("""
<style>
/* ── App background ── */
.stApp {
    background: linear-gradient(135deg, #37003c, #2b1e5b, #00cc6a) !important;
    min-height: 100vh;
}
.stMainBlockContainer {
    padding-top: 3.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: none !important;
}

/* Gap between left (points) column and right (leagues) column */
div[data-testid="stHorizontalBlock"]:first-of-type {
    gap: 24px !important;
    align-items: flex-start !important;
}

/* ── Glassmorphism card ── */
.glass-box {
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    color: white;
    border: 1px solid rgba(255,255,255,0.2);
}

/* ── Points box ── */
.points-box {
    text-align: center;
    border-radius: 22px 22px 0 0;
    padding: 30px 30px 24px 30px;
    box-shadow: 0 20px 45px rgba(0,0,0,0.35);
    margin-top: 20px;
    font-size: 1.25rem; /* base font size up */
}

.team-name { font-size: 18px; font-weight: 800; opacity: 0.92; margin-bottom: 4px; }
.gw-label  { font-size: 15px; opacity: 0.8;   margin-bottom: 12px; }

.points-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 30px;
}

.big-points { font-size: 70px; font-weight: 900; line-height: 1; color: white; }

.side-points { display: flex; flex-direction: column; align-items: center; }
.side-label  { font-size: 14px; opacity: 0.8; margin-bottom: 2px; }
.side-value  { font-size: 30px; font-weight: 700; color: rgba(255,255,255,0.85); }

/* ── Leagues box ── */
.leagues-box {
    padding: 24px;
    border-radius: 22px;
    box-shadow: 0 20px 45px rgba(0,0,0,0.35);
    margin-top: 20px;
}

/* ── Countdown and matches (left column) ── */
.matches-box {
    padding: 18px 16px;
    border-radius: 22px;
    box-shadow: 0 20px 45px rgba(0,0,0,0.35);
    margin-top: 14px;
}

/* Fixtures burger layout */
.matches-header-box {
    padding: 14px 16px 10px 16px;
    border-radius: 22px 22px 0 0;
    box-shadow: 0 20px 45px rgba(0,0,0,0.35);
    margin-top: 14px;
    margin-bottom: 0;
    border-bottom: 1px solid rgba(255,255,255,0.18);
}

.matches-body-box {
    padding: 10px 16px 14px 16px;
    border-radius: 0 0 22px 22px;
    box-shadow: 0 20px 45px rgba(0,0,0,0.35);
    margin-top: 0;
}

.matches-section-title {
    font-size: 15px;
    font-weight: 700;
    opacity: 0.92;
    margin: 0;
    color: #ffffff;
    text-align: center;
}

.st-key-see_fixtures {
    margin-top: 15.5px !important;
    margin-bottom: 0 !important;
    border-radius: 0 !important;
}

.st-key-see_fixtures button {
    width: 100% !important;
    min-width: 0 !important;
    padding: 10px 14px !important;
    border-radius: 0 !important;
    border: 1px solid rgba(0,255,135,0.55) !important;
    background: linear-gradient(135deg, rgba(0,255,135,0.22), rgba(255,255,255,0.12)) !important;
    color: #00ff87 !important;
    font-size: 14px !important;
    font-weight: 800 !important;
    box-shadow: 0 6px 16px rgba(0,0,0,0.25) !important;
    margin: 0 !important;
}

.st-key-see_fixtures button:hover {
    background: linear-gradient(135deg, rgba(0,255,135,0.3), rgba(255,255,255,0.18)) !important;
    color: #ffffff !important;
}

.st-key-see_leagues {
    margin-top: 15.5px !important;
    margin-bottom: 0 !important;
    border-radius: 0 !important;
}

.st-key-see_leagues button {
    width: 100% !important;
    min-width: 0 !important;
    padding: 10px 14px !important;
    border-radius: 0 !important;
    border: 1px solid rgba(0,255,135,0.55) !important;
    background: linear-gradient(135deg, rgba(0,255,135,0.22), rgba(255,255,255,0.12)) !important;
    color: #00ff87 !important;
    font-size: 14px !important;
    font-weight: 800 !important;
    box-shadow: 0 6px 16px rgba(0,0,0,0.25) !important;
    margin: 0 !important;
}

.st-key-see_leagues button:hover {
    background: linear-gradient(135deg, rgba(0,255,135,0.3), rgba(255,255,255,0.18)) !important;
    color: #ffffff !important;
}

.section-title {
    font-size: 15px;
    font-weight: 700;
    opacity: 0.92;
    margin-bottom: 12px;
    text-align: center;
    border-bottom: 1px solid rgba(255,255,255,0.2);
    padding-bottom: 8px;
}

.match-row {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 8px;
    padding: 10px;
    margin-bottom: 8px;
    border-radius: 12px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
}

.match-head {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    padding: 0 10px;
}

.match-head-side {
    font-size: 11px;
    font-weight: 700;
    opacity: 0.75;
}

.match-head-side.right {
    text-align: right;
}

.team-cell {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
}

.team-cell.right {
    justify-content: flex-end;
}

.team-logo {
    width: 20px;
    height: 20px;
    object-fit: contain;
    flex-shrink: 0;
}

.team-name-small {
    font-size: 15px;
    font-weight: 700;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.score-cell {
    text-align: center;
    min-width: 90px;
}

.score-main {
    font-size: 15px;
    font-weight: 800;
    color: #ffffff;
}

.score-sub {
    font-size: 11px;
    opacity: 0.75;
    margin-top: 2px;
}

.leagues-sections { display: flex; gap: 20px; }
.league-section   { flex: 1; min-width: 0; }

.leagues-header-box {
    padding: 14px 16px 10px 16px;
    border-radius: 22px 22px 0 0;
    box-shadow: 0 20px 45px rgba(0,0,0,0.35);
    margin-top: 20px;
    margin-bottom: 0;
    border-bottom: 1px solid rgba(255,255,255,0.18);
}

.leagues-body-box {
    padding: 10px 16px 14px 16px;
    border-radius: 0 0 22px 22px;
    box-shadow: 0 20px 45px rgba(0,0,0,0.35);
    margin-top: 0;
}

.leagues-headings {
    display: flex;
    gap: 20px;
}

.leagues-title {
    font-size: 18px;
    font-weight: 700;
    margin: 0;
    text-align: center;
    padding-bottom: 0;
    color: white;
}

.league-reorder-heading {
    margin: 0 0 8px;
    font-size: 13px;
    font-weight: 800;
    opacity: 0.82;
}

.league-reorder-name {
    min-height: 38px;
    display: flex;
    align-items: center;
    font-size: 13px;
    font-weight: 700;
    overflow-wrap: anywhere;
}

[data-testid="stPopover"] [data-testid="stCheckbox"] label > div:first-child {
    border-radius: 50% !important;
    border-color: #00ff87 !important;
    background: #00ff87 !important;
}

[data-testid="stPopover"] [data-testid="stCheckbox"] input:disabled + div {
    opacity: 1 !important;
}

.league-show-indicator {
    width: 20px;
    height: 20px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border: 2px solid rgba(255,255,255,0.28);
    border-radius: 50%;
    box-sizing: border-box;
    color: #10251a;
    font-size: 14px;
    font-weight: 900;
    line-height: 1;
}

.league-show-indicator.visible {
    border-color: #00ff87;
    background: #00ff87;
}

.league-show-indicator.hidden {
    background: transparent;
}

.st-key-see_leagues,
[data-testid="stPopover"] {
    margin-top: 8px !important;
}

.st-key-league_actions {
    margin-top: 8px !important;
}

.st-key-league_actions > div[data-testid="stHorizontalBlock"] {
    align-items: stretch !important;
}

.st-key-league_actions .st-key-see_leagues,
.st-key-league_actions [data-testid="stPopover"] {
    margin-top: 10px !important;
    height: 44px !important;
}

.st-key-league_actions .st-key-see_leagues button,
.st-key-league_actions [data-testid="stPopover"] button {
    box-sizing: border-box !important;
    width: 100% !important;
    height: 44px !important;
    min-height: 44px !important;
    padding: 10px 14px !important;
    line-height: 22px !important;
    border-radius: 0 !important;
    border: 1px solid rgba(0,255,135,0.55) !important;
    background: linear-gradient(135deg, rgba(0,255,135,0.22), rgba(255,255,255,0.12)) !important;
    color: #00ff87 !important;
    font-size: 14px !important;
    font-weight: 800 !important;
}

.st-key-league_actions .st-key-see_leagues button:hover,
.st-key-league_actions .st-key-see_leagues button:focus,
.st-key-league_actions .st-key-see_leagues button:active,
.st-key-league_actions [data-testid="stPopover"] button:hover,
.st-key-league_actions [data-testid="stPopover"] button:focus,
.st-key-league_actions [data-testid="stPopover"] button:active {
    background: linear-gradient(135deg, rgba(0,255,135,0.30), rgba(255,255,255,0.18)) !important;
    color: #ffffff !important;
    border-radius: 0 !important;
    border-color: rgba(0,255,135,0.55) !important;
}

.st-key-league_actions [data-testid="stPopover"] button {
    background: linear-gradient(135deg, rgba(0,255,135,0.30), rgba(255,255,255,0.18)) !important;
    color: #ffffff !important;
}

.st-key-league_actions [data-testid="stPopover"] {
    border-radius: 0 !important;
}

.st-key-league_actions [data-testid="stPopover"] > div,
.st-key-league_actions [data-testid="stPopover"] > div > button {
    width: 100% !important;
    border-radius: 0 !important;
}

.st-key-league_actions .st-key-see_leagues button,
.st-key-league_actions .st-key-see_leagues button:hover,
.st-key-league_actions .st-key-see_leagues button:focus,
.st-key-league_actions .st-key-see_leagues button:active {
    border-radius: 0 !important;
}

[data-testid="stPopover"] [data-testid="stSelectbox"] label {
    display: block !important;
    font-size: 11px !important;
    opacity: 0.7;
}

[data-testid="stPopover"] [data-testid="stCheckbox"] label p {
    white-space: nowrap !important;
}

.league-reorder-public-heading {
    margin-top: 22px;
}

.league-row {
    padding: 12px;
    margin-bottom: 8px;
    background: rgba(255,255,255,0.08);
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.15);
    color: white;
}

.league-name  { font-size: 15px; font-weight: 700; margin-bottom: 6px; }

.league-ranks {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 13px;
    flex-wrap: wrap;
}

.rank-label { opacity: 0.7; font-size: 12px; }
.rank-arrow { font-size: 20px; font-weight: 700; margin-left: auto; }
.rank-arrow.up { color: #00ff87 !important; }
.rank-arrow.down { color: #f64646 !important; }
.rank-arrow.flat { color: #999 !important; }

.total-managers {
    font-size: 12px;
    color: rgba(255,255,255,0.6);
    margin-top: 6px;
    font-style: normal;
}

.trends-wrap {
    margin-top: 56px;
}

.trend-box {
    padding: 14px 14px 12px 14px;
    border-radius: 16px;
    min-height: 340px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.28);
}

/* Restore gap for the 3-card trends row in the right column */
div[data-testid="stColumn"]:nth-of-type(2)
  > div[data-testid="stVerticalBlock"]
  > div[data-testid="stHorizontalBlock"] {
        gap: 32px !important;
}

.trend-title {
    margin: 0 0 8px 0;
    text-align: center;
    font-size: 15px;
    font-weight: 800;
    color: #ffffff;
}

.trend-subtitle {
    margin: 0 0 10px 0;
    text-align: center;
    font-size: 11px;
    opacity: 0.78;
}

.trend-list {
    margin: 0;
    padding: 0;
    list-style: none;
}

.trend-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    padding: 8px 10px !important;
    margin-bottom: 7px;
    border-radius: 10px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.14);
}

.trend-player-info {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 1;
    min-width: 0;
}

.trend-num {
    font-size: 14px;
    font-weight: 700;
    opacity: 0.8;
    min-width: 18px;
    text-align: right;
}

.trend-player {
    font-size: 15px;
    font-weight: 700;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex-grow: 1;
    text-align: center;
}

.trend-value {
    font-size: 12px;
    font-weight: 800;
    color: #00ff87;
    flex-shrink: 0;
}

.trend-empty {
    text-align: center;
    font-size: 12px;
    opacity: 0.75;
    padding: 18px 8px;
}

/* ── Premier League standings ── */
.standings-wrap {
    margin-top: 32px;
    margin-bottom: 28px;
}

.standings-box {
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 16px 36px rgba(0,0,0,0.30);
}

.standings-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 16px;
    padding: 18px 22px 14px;
    border-bottom: 1px solid rgba(255,255,255,0.16);
}

.standings-title {
    margin: 0;
    color: #ffffff;
    font-size: 20px;
    font-weight: 850;
}

.standings-updated {
    color: rgba(255,255,255,0.66);
    font-size: 12px;
    white-space: nowrap;
}

.standings-scroll {
    width: 100%;
    overflow-x: auto;
}

.standings-table {
    width: 100%;
    min-width: 900px;
    border-collapse: collapse;
    color: #ffffff;
    font-size: 13px;
}

.standings-table th {
    padding: 10px 9px;
    color: rgba(255,255,255,0.68);
    background: rgba(19,4,45,0.26);
    border-bottom: 1px solid rgba(255,255,255,0.14);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.035em;
    text-align: center;
    text-transform: uppercase;
    white-space: nowrap;
}

.standings-table th.club-heading {
    text-align: left;
}

.standings-table td {
    padding: 9px;
    border-bottom: 1px solid rgba(255,255,255,0.09);
    text-align: center;
    font-variant-numeric: tabular-nums;
}

.standings-table tbody tr:last-child td {
    border-bottom: 0;
}

.standings-table tbody tr:hover {
    background: rgba(255,255,255,0.08);
}

.standings-position {
    width: 30px;
    font-weight: 850;
}

.standings-row.champions .standings-position { box-shadow: inset 6px 0 0 #00ff87; }
.standings-row.europe .standings-position { box-shadow: inset 6px 0 0 #39b9ff; }
.standings-row.relegation .standings-position { box-shadow: inset 6px 0 0 #ff4b5c; }

.standings-club {
    min-width: 180px;
    text-align: left !important;
}

.standings-club-inner {
    display: flex;
    align-items: center;
    gap: 10px;
}

.standings-logo {
    width: 24px;
    height: 24px;
    object-fit: contain;
    flex: 0 0 24px;
}

.standings-club-name {
    overflow: hidden;
    font-size: 14px;
    font-weight: 750;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.standings-form {
    min-width: 170px;
}

.standings-form-heading {
    min-width: 170px;
}

.form-gw-labels {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    margin-top: 5px;
    color: rgba(255,255,255,0.52);
    font-size: 8px;
    font-weight: 750;
    letter-spacing: 0;
}

.form-gw-labels span {
    width: 27px;
    text-align: center;
}

.standings-form-list {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
}

.form-result {
    width: 27px;
    height: 27px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    color: #ffffff;
    font-size: 11px;
    font-weight: 900;
    line-height: 1;
}

.form-result.win { background: #00e887; color: #10251a; }
.form-result.draw { background: #8f86a8; }
.form-result.loss { background: #ff4f70; }
.form-result.empty { background: rgba(255,255,255,0.10); color: rgba(255,255,255,0.40); }

.standings-gd.positive { color: #00ff87; font-weight: 800; }
.standings-gd.negative { color: #ff7885; font-weight: 800; }
.standings-points { color: #00ff87; font-size: 15px; font-weight: 900; }

@media (max-width: 900px) {
    .standings-wrap { margin-top: 22px; }
    .standings-header { padding: 15px 16px 12px; }
    .standings-title { font-size: 18px; }
}

/* Zero gap and padding on column layout rows */
div[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}
div[data-testid="stColumn"] {
    padding: 0 !important;
    min-width: 0 !important;
}
div[data-testid="stColumn"] > div {
    padding: 0 !important;
    gap: 0 !important;
}
/* Restore gap on the outermost layout row only */
div[data-testid="stMain"] > div > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]:first-of-type {
    gap: 24px !important;
}

/* ── Nav buttons ── */
div[data-testid="stButton"] > button {
    padding: 14px 0 !important;
    background: rgba(255,255,255,0.12) !important;
    color: #00ff87 !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    border: none !important;
    border-top: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 0 !important;
    margin: 0 !important;
    width: 100% !important;
    transition: background 0.2s ease !important;
}
div[data-testid="stButton"] > button:hover {
    background: rgba(0,255,135,0.2) !important;
    color: white !important;
}
/* Points — bottom-left curve only */
div[data-testid="stColumn"]:nth-of-type(1) div[data-testid="stButton"] > button {
    border-radius: 0 0 0 22px !important;
    border-right: 1px solid rgba(255,255,255,0.15) !important;
}
/* Graphs — bottom-right curve only */
div[data-testid="stColumn"]:nth-of-type(2) div[data-testid="stButton"] > button {
    border-radius: 0 0 22px 0 !important;
}

/* Keep Fixtures button fully uncurved (override column corner rules) */
div[data-testid="stColumn"]:nth-of-type(1) .st-key-see_fixtures div[data-testid="stButton"] > button,
div[data-testid="stColumn"]:nth-of-type(2) .st-key-see_fixtures div[data-testid="stButton"] > button,
div[data-testid="stColumn"]:nth-of-type(1) .st-key-see_fixtures div[data-testid="stButton"] > button:hover,
div[data-testid="stColumn"]:nth-of-type(2) .st-key-see_fixtures div[data-testid="stButton"] > button:hover,
div[data-testid="stColumn"]:nth-of-type(1) .st-key-see_fixtures div[data-testid="stButton"] > button:focus,
div[data-testid="stColumn"]:nth-of-type(2) .st-key-see_fixtures div[data-testid="stButton"] > button:focus,
div[data-testid="stColumn"]:nth-of-type(1) .st-key-see_fixtures div[data-testid="stButton"] > button:active,
div[data-testid="stColumn"]:nth-of-type(2) .st-key-see_fixtures div[data-testid="stButton"] > button:active {
    border-radius: 0 !important;
    border-bottom-left-radius: 0 !important;
    border-bottom-right-radius: 0 !important;
    border-right: 1px solid rgba(255,255,255,0.35) !important;
    border-left: 1px solid rgba(255,255,255,0.35) !important;
}

/* Keep Mini Leagues button fully uncurved too */
div[data-testid="stColumn"]:nth-of-type(1) .st-key-see_leagues div[data-testid="stButton"] > button,
div[data-testid="stColumn"]:nth-of-type(2) .st-key-see_leagues div[data-testid="stButton"] > button,
div[data-testid="stColumn"]:nth-of-type(1) .st-key-see_leagues div[data-testid="stButton"] > button:hover,
div[data-testid="stColumn"]:nth-of-type(2) .st-key-see_leagues div[data-testid="stButton"] > button:hover,
div[data-testid="stColumn"]:nth-of-type(1) .st-key-see_leagues div[data-testid="stButton"] > button:focus,
div[data-testid="stColumn"]:nth-of-type(2) .st-key-see_leagues div[data-testid="stButton"] > button:focus,
div[data-testid="stColumn"]:nth-of-type(1) .st-key-see_leagues div[data-testid="stButton"] > button:active,
div[data-testid="stColumn"]:nth-of-type(2) .st-key-see_leagues div[data-testid="stButton"] > button:active {
    border-radius: 0 !important;
    border-bottom-left-radius: 0 !important;
    border-bottom-right-radius: 0 !important;
    border-right: 1px solid rgba(255,255,255,0.35) !important;
    border-left: 1px solid rgba(255,255,255,0.35) !important;
}
</style>
""", unsafe_allow_html=True)

render_top_nav()

@st.cache_data(ttl=60)
def fetch_live_points(gw):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = f"https://fantasy.premierleague.com/api/event/{gw}/live/"
    with urllib.request.urlopen(url, context=ctx) as r:
        data = json.loads(r.read())
    return {e["id"]: e["stats"]["total_points"] for e in data["elements"]}

@st.cache_data(ttl=60)
def fetch_gw_stats(gw):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    with urllib.request.urlopen(url, context=ctx) as r:
        bootstrap = json.loads(r.read())
    for event in bootstrap.get("events", []):
        if event["id"] == gw:
            return round(event.get("average_entry_score") or 0), (event.get("highest_score") or 0)
    return 0, 0

@st.cache_data(ttl=300)
def fetch_bootstrap_data():
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    with urllib.request.urlopen(url, context=ctx) as r:
        return json.loads(r.read())

@st.cache_data(ttl=120)
def fetch_fixtures(event_id):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = f"https://fantasy.premierleague.com/api/fixtures/?event={event_id}"
    with urllib.request.urlopen(url, context=ctx) as r:
        return json.loads(r.read())

@st.cache_data(ttl=300)
def fetch_season_fixtures():
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = "https://fantasy.premierleague.com/api/fixtures/"
    with urllib.request.urlopen(url, context=ctx) as r:
        return json.loads(r.read())

@st.cache_data(ttl=300)
def fetch_leagues(manager_id):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/"
    with urllib.request.urlopen(url, context=ctx) as r:
        data = json.loads(r.read())
    all_leagues    = data.get("leagues", {}).get("classic", [])
    mini_leagues   = []
    public_leagues = []
    for l in all_leagues:
        ld = {k: l.get(k) for k in ("name","id","entry_rank","entry_last_rank","league_type","admin_entry","start_event","scoring")}
        (mini_leagues if l.get("league_type") == "x" else public_leagues).append(ld)
    return mini_leagues, public_leagues


LEAGUE_ORDER_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "league_orders.json")


def load_league_order(manager_id, mini_leagues, public_leagues):
    try:
        with open(LEAGUE_ORDER_FILE, encoding="utf-8") as order_file:
            saved = json.load(order_file).get(str(manager_id), {})
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        saved = {}

    def apply_order(leagues, key):
        by_id = {str(league.get("id")): league for league in leagues}
        ordered_ids = [str(league_id) for league_id in saved.get(key, [])]
        ordered = [by_id.pop(league_id) for league_id in ordered_ids if league_id in by_id]
        return ordered + list(by_id.values())

    return apply_order(mini_leagues, "mini"), apply_order(public_leagues, "public")


def save_league_order(manager_id, mini_leagues, public_leagues):
    os.makedirs(os.path.dirname(LEAGUE_ORDER_FILE), exist_ok=True)
    try:
        with open(LEAGUE_ORDER_FILE, encoding="utf-8") as order_file:
            all_orders = json.load(order_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        all_orders = {}

    all_orders[str(manager_id)] = {
        "mini": [league.get("id") for league in mini_leagues],
        "public": [league.get("id") for league in public_leagues],
    }
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=os.path.dirname(LEAGUE_ORDER_FILE), delete=False) as temp_file:
            json.dump(all_orders, temp_file, indent=2)
            temp_path = temp_file.name
        os.replace(temp_path, LEAGUE_ORDER_FILE)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def render_reorder_popover(manager_id, mini_leagues, public_leagues):
    popover_version = st.session_state.get("league_reorder_version", 0)
    with st.popover(
        "Reorder Leagues",
        use_container_width=True,
        width="large",
        disabled=is_guest,
        key=f"league_reorder_popover_{popover_version}",
    ):
        st.markdown('<div class="league-reorder-heading">Choose up to 4 and set their order</div>', unsafe_allow_html=True)
        choices = []
        for section_index, (title, leagues, order_key, max_visible) in enumerate(
            (
                ("Mini Leagues", mini_leagues, "mini", 4),
                ("Public Leagues", public_leagues, "public", 5),
            )
        ):
            heading_class = "league-reorder-heading"
            if section_index == 1:
                heading_class += " league-reorder-public-heading"
            st.markdown(f'<div class="{heading_class}">{title}</div>', unsafe_allow_html=True)
            for index, league in enumerate(leagues):
                league_id = league.get("id")
                choice_key = f"league_show_{order_key}_{league_id}"
                rank_key = f"league_rank_v2_{order_key}_{league_id}"
                row_col, show_col, rank_col = st.columns([5, 1.8, 1.6], gap="small", vertical_alignment="center")
                with row_col:
                    st.markdown(f'<div class="league-reorder-name">{league.get("name", "Unknown")}</div>', unsafe_allow_html=True)
                with show_col:
                    indicator_state = "visible" if index < max_visible else "hidden"
                    indicator_mark = "&#10003;" if index < max_visible else ""
                    indicator_title = "Shown" if index < max_visible else "Hidden"
                    st.markdown(
                        f'<div class="league-show-indicator {indicator_state}" title="{indicator_title}">{indicator_mark}</div>',
                        unsafe_allow_html=True,
                    )
                with rank_col:
                    rank_options = ["-"] + list(range(1, max_visible + 1))
                    st.selectbox(
                        "Rank",
                        options=rank_options,
                        index=index + 1 if index < max_visible else 0,
                        key=rank_key,
                        label_visibility="visible",
                    )
                choices.append((order_key, league, choice_key, rank_key, index))

        if st.button("Apply order", key="apply_league_order", type="primary", use_container_width=True):
            for order_key, leagues in (("mini", mini_leagues), ("public", public_leagues)):
                category_choices = [choice for choice in choices if choice[0] == order_key]
                selected = [choice for choice in category_choices if st.session_state.get(choice[3]) != "-"]
                if len(selected) > 4:
                    st.error(f"Select no more than 4 {order_key} leagues.")
                    break
            else:
                for order_key, leagues in (("mini", mini_leagues), ("public", public_leagues)):
                    category_choices = [choice for choice in choices if choice[0] == order_key]
                    selected = [choice for choice in category_choices if st.session_state.get(choice[3]) != "-"]
                    selected.sort(
                        key=lambda choice: (
                            st.session_state[choice[3]] == "-",
                            st.session_state[choice[3]] if st.session_state[choice[3]] != "-" else 5,
                            choice[4],
                        )
                    )
                    selected_ids = {choice[1].get("id") for choice in selected}
                    leagues[:] = [choice[1] for choice in selected]
                    leagues.extend(choice[1] for choice in category_choices if choice[1].get("id") not in selected_ids)
                save_league_order(manager_id, mini_leagues, public_leagues)
                st.session_state.league_reorder_version = popover_version + 1
                st.rerun()

def get_league_size(league_id):
    if not league_id:
        return None
    try:
        ctx = ssl.create_default_context(cafile=certifi.where())
        req = urllib.request.Request(
            f"https://fantasy.premierleague.com/api/leagues-classic/{league_id}/standings/",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            data = json.loads(r.read())
        li   = data.get("league", {})
        size = li.get("size") or li.get("max_entries") or len(data.get("standings", {}).get("results", []))
        return size if size and size > 0 else None
    except Exception:
        return None

def fmt(rank):
    return f"{rank:,}" if rank is not None else "N/A"

def rank_style(rank):
    if rank == 1:
        return "rank-gold", "20px"
    if rank == 2:
        return "rank-silver", "20px"
    if rank == 3:
        return "rank-bronze", "20px"
    return "", "16px"

def parse_deadline(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None

def next_deadline_info(events, current_gw):
    if not events:
        return None, None

    next_event = next((e for e in events if e.get("is_next")), None)
    if not next_event:
        next_event = next((e for e in events if (e.get("id") or 0) > current_gw), None)

    if not next_event:
        return None, None

    return next_event.get("id"), parse_deadline(next_event.get("deadline_time"))

def current_gw_from_events(events):
    if not events:
        return 0
    current = next((e.get("id") for e in events if e.get("is_current")), None)
    if current:
        return current
    return max((e.get("id") or 0 for e in events), default=0)

def logo_url(team_code):
    if not team_code:
        return ""
    return f"https://resources.premierleague.com/premierleague/badges/50/t{team_code}.png"

def kickoff_label(kickoff_str):
    dt = parse_deadline(kickoff_str)
    if not dt:
        return "Kickoff TBC"
    return dt.strftime("%d %b %H:%M UTC")

def safe_int(value):
    try:
        return int(value)
    except Exception:
        return 0

def safe_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0

def build_top5_trends(bootstrap, gw):
    elements = bootstrap.get("elements", [])
    events = bootstrap.get("events", [])

    player_by_id = {p.get("id"): p for p in elements if p.get("id") is not None}

    subbed_in = sorted(elements, key=lambda p: safe_int(p.get("transfers_in_event")), reverse=True)[:5]
    subbed_out = sorted(elements, key=lambda p: safe_int(p.get("transfers_out_event")), reverse=True)[:5]

    current_event = next((e for e in events if e.get("id") == gw), {})
    most_captained_id = current_event.get("most_captained")

    top_by_ownership = sorted(elements, key=lambda p: safe_float(p.get("selected_by_percent")), reverse=True)
    captained = []
    seen_ids = set()

    if most_captained_id in player_by_id:
        captained.append(player_by_id[most_captained_id])
        seen_ids.add(most_captained_id)

    for player in top_by_ownership:
        pid = player.get("id")
        if pid in seen_ids:
            continue
        captained.append(player)
        seen_ids.add(pid)
        if len(captained) == 5:
            break

    def player_name(player):
        return player.get("web_name") or player.get("second_name") or "Unknown"

    def estimate_captain_percent(ownership_percent, rank):
        weights = [0.40, 0.32, 0.26, 0.22, 0.18]
        weight = weights[rank - 1] if 1 <= rank <= len(weights) else 0.35
        estimate = ownership_percent * weight
        return max(0.0, min(estimate, 100.0))

    captained_rows = [
        {
            "name": player_name(p),
            "value": f"{estimate_captain_percent(safe_float(p.get('selected_by_percent')), idx):.1f}%",
        }
        for idx, p in enumerate(captained[:5], start=1)
    ]

    subbed_in_rows = [
        {
            "name": player_name(p),
            "value": f"{safe_int(p.get('transfers_in_event')):,}",
        }
        for p in subbed_in
    ]

    subbed_out_rows = [
        {
            "name": player_name(p),
            "value": f"{safe_int(p.get('transfers_out_event')):,}",
        }
        for p in subbed_out
    ]

    return captained_rows, subbed_in_rows, subbed_out_rows

def build_trend_box_html(title, subtitle, rows):
    if not rows:
        rows_html = '<div class="trend-empty">No data available.</div>'
    else:
        items = []
        for idx, row in enumerate(rows, start=1):
            items.append(
                f'<li class="trend-row">'
                f'  <div class="trend-player-info">'
                f'    <span class="trend-num">{idx}.</span>'
                f'    <span class="trend-player">{row["name"]}</span>'
                f'  </div>'
                f'  <span class="trend-value">{row["value"]}</span>'
                f'</li>'
            )
        rows_html = f'<ol class="trend-list">{"".join(items)}</ol>'

    subtitle_html = f'<p class="trend-subtitle">{subtitle}</p>' if subtitle else ""

    return (
        f'<div class="glass-box trend-box">'
        f'  <h4 class="trend-title">{title}</h4>'
        f'  {subtitle_html}'
        f'  {rows_html}'
        f'</div>'
    )

def build_standings(teams, season_fixtures):
    """Build the league table from completed FPL fixtures."""
    calculated = {
        team.get("id"): {
            "played": 0,
            "win": 0,
            "draw": 0,
            "loss": 0,
            "gf": 0,
            "ga": 0,
            "form": [],
        }
        for team in teams
        if team.get("id") is not None
    }

    completed_fixtures = sorted(
        (fixture for fixture in season_fixtures if fixture.get("finished")),
        key=lambda fixture: (fixture.get("kickoff_time") or "", fixture.get("id") or 0),
    )

    for fixture in completed_fixtures:
        home_id = fixture.get("team_h")
        away_id = fixture.get("team_a")
        home_score = fixture.get("team_h_score")
        away_score = fixture.get("team_a_score")
        if home_id not in calculated or away_id not in calculated:
            continue
        if home_score is None or away_score is None:
            continue

        home = calculated[home_id]
        away = calculated[away_id]
        home["played"] += 1
        away["played"] += 1
        home["gf"] += safe_int(home_score)
        home["ga"] += safe_int(away_score)
        away["gf"] += safe_int(away_score)
        away["ga"] += safe_int(home_score)

        if home_score > away_score:
            home["win"] += 1
            away["loss"] += 1
            home["form"].append("W")
            away["form"].append("L")
        elif home_score < away_score:
            away["win"] += 1
            home["loss"] += 1
            home["form"].append("L")
            away["form"].append("W")
        else:
            home["draw"] += 1
            away["draw"] += 1
            home["form"].append("D")
            away["form"].append("D")

    rows = []
    for team in teams:
        team_id = team.get("id")
        totals = calculated.get(team_id, {})
        played = totals.get("played", 0)
        wins = totals.get("win", 0)
        draws = totals.get("draw", 0)
        losses = totals.get("loss", 0)
        points = (wins * 3) + draws
        gf = totals.get("gf", 0)
        ga = totals.get("ga", 0)

        rows.append({
            "official_position": safe_int(team.get("position")),
            "name": team.get("name") or "Unknown",
            "code": team.get("code"),
            "played": played,
            "win": wins,
            "draw": draws,
            "loss": losses,
            "gf": gf,
            "ga": ga,
            "gd": gf - ga,
            "points": safe_int(points),
            "form": totals.get("form", [])[-5:],
        })

    rows.sort(
        key=lambda row: (
            row["points"],
            row["gd"],
            row["gf"],
            -row["official_position"],
        ),
        reverse=True,
    )
    return rows

def build_standings_html(standings, gw):
    body_rows = []
    team_count = len(standings)
    current_gw = max(1, safe_int(gw))
    visible_gameweeks = list(range(max(1, current_gw - 4), current_gw + 1))
    gameweek_slots = ([None] * (5 - len(visible_gameweeks))) + visible_gameweeks
    gameweek_labels = "".join(
        f'<span>{f"GW{gameweek}" if gameweek is not None else ""}</span>'
        for gameweek in gameweek_slots
    )

    for position, row in enumerate(standings, start=1):
        if position == 1:
            status_class = "champions"
        elif position <= 5:
            status_class = "europe"
        elif position >= max(18, team_count - 2):
            status_class = "relegation"
        else:
            status_class = ""

        gd = row["gd"]
        gd_class = "positive" if gd > 0 else "negative" if gd < 0 else ""
        gd_text = f"{gd:+d}" if gd else "0"
        club_name = html.escape(str(row["name"]))
        badge = logo_url(row.get("code"))
        recent_form = row.get("form", [])[-5:]
        form_slots = ([None] * (5 - len(recent_form))) + recent_form
        form_html = "".join(
            (
                '<span class="form-result empty" aria-label="No result">&ndash;</span>'
                if result is None
                else f'<span class="form-result {"win" if result == "W" else "draw" if result == "D" else "loss"}" '
                     f'aria-label="{"Won" if result == "W" else "Drawn" if result == "D" else "Lost"}">{result}</span>'
            )
            for result in form_slots
        )
        body_rows.append(
            f'<tr class="standings-row {status_class}">'
            f'<td class="standings-position">{position}</td>'
            f'<td class="standings-club"><div class="standings-club-inner">'
            f'<img class="standings-logo" src="{badge}" alt="" loading="lazy">'
            f'<span class="standings-club-name">{club_name}</span></div></td>'
            f'<td class="standings-form"><div class="standings-form-list">{form_html}</div></td>'
            f'<td>{row["played"]}</td>'
            f'<td>{row["win"]}</td>'
            f'<td>{row["draw"]}</td>'
            f'<td>{row["loss"]}</td>'
            f'<td>{row["gf"]}</td>'
            f'<td>{row["ga"]}</td>'
            f'<td class="standings-gd {gd_class}">{gd_text}</td>'
            f'<td class="standings-points">{row["points"]}</td>'
            f'</tr>'
        )

    if not body_rows:
        body_rows.append('<tr><td colspan="11">Standings are currently unavailable.</td></tr>')

    return (
        '<div class="standings-wrap">'
        '<div class="glass-box standings-box">'
        '<div class="standings-header">'
        '<h3 class="standings-title">Premier League Table</h3>'
        f'<span class="standings-updated">Gameweek {gw}</span>'
        '</div>'
        '<div class="standings-scroll">'
        '<table class="standings-table">'
        '<thead><tr>'
        '<th scope="col">Pos</th><th scope="col" class="club-heading">Club</th>'
        f'<th scope="col" class="standings-form-heading"><div>Last 5</div>'
        f'<div class="form-gw-labels">{gameweek_labels}</div></th>'
        '<th scope="col">Played</th><th scope="col">Won</th>'
        '<th scope="col">Drawn</th><th scope="col">Lost</th>'
        '<th scope="col" title="Goals for">GF</th><th scope="col" title="Goals against">GA</th>'
        '<th scope="col" title="Goal difference">GD</th><th scope="col">Points</th>'
        '</tr></thead>'
        f'<tbody>{"".join(body_rows)}</tbody>'
        '</table></div></div></div>'
    )

bootstrap_data = fetch_bootstrap_data()
events = bootstrap_data.get("events", [])
teams = bootstrap_data.get("teams", [])

if is_guest:
    gw = current_gw_from_events(events)
    team_name = "Guest"
    manager_id = None
    live_pts = {}
    avg_points = "-"
    highest_points = "-"
    gw_points = "-"
    picks = []
    starters = []
    mini_leagues, public_leagues = [], []
else:
    gw         = st.session_state.gw
    entry      = st.session_state.entry
    team_name  = entry["name"]
    manager_id = st.session_state.manager_id
    live_pts = fetch_live_points(gw)
    avg_points, highest_points = fetch_gw_stats(gw)
    picks    = sorted(st.session_state.picks["picks"], key=lambda x: x["position"])
    starters = picks[:11]
    gw_points = sum(live_pts.get(p["element"], 0) * p.get("multiplier", 1) for p in starters)
    mini_leagues, public_leagues = fetch_leagues(manager_id)
    mini_leagues, public_leagues = load_league_order(manager_id, mini_leagues, public_leagues)

next_gw, next_deadline = next_deadline_info(events, gw)

team_map = {
    t.get("id"): {
        "name": t.get("name", "Unknown"),
        "code": t.get("code")
    }
    for t in teams
}

fixtures = fetch_fixtures(gw)
season_fixtures = fetch_season_fixtures()
captained_top5, subbed_in_top5, subbed_out_top5 = build_top5_trends(bootstrap_data, gw)
standings = build_standings(teams, season_fixtures)

def build_league_html(leagues, show_total=False, max_count=4):
    html = ""
    if not leagues:
        return (
            '<div class="league-row">'
            '<div class="league-name">-</div>'
            '<div class="league-ranks">'
            '<span class="rank-label">Current:</span>'
            '<span style="color:#999;font-weight:700;font-size:16px;font-family:sans-serif;">-</span>'
            '<span class="rank-label">Previous:</span>'
            '<span style="color:#999;font-weight:700;font-size:16px;font-family:sans-serif;">-</span>'
            '<span class="rank-arrow" style="color:#999;">—</span>'
            '</div></div>'
        )
    for league in leagues[:max_count]:
        name   = league.get("name", "Unknown")
        lid    = league.get("id")
        cur    = league.get("entry_rank")
        prev   = league.get("entry_last_rank")

        total_line = ""
        if show_total and lid:
            size = get_league_size(lid)
            total_line = f'<div class="total-managers">Total managers: {fmt(size)}</div>'

        if cur and prev:
            if cur < prev:
                arrow, arrow_class, default_cc = "↑", "up", "#00ff87"
            elif cur > prev:
                arrow, arrow_class, default_cc = "↓", "down", "#f64646"
            else:
                arrow, arrow_class, default_cc = "—", "flat", "#999"
        else:
            arrow, arrow_class, default_cc = "—", "flat", "#999"

        cur_rank_class, cur_size = rank_style(cur)
        prev_rank_class, prev_size = rank_style(prev)
        cur_style = (
            f"font-weight:900;font-size:{cur_size};font-family:sans-serif;"
            if cur_rank_class
            else f"color:{default_cc};font-weight:700;font-size:{cur_size};font-family:sans-serif;"
        )
        prev_style = (
            f"font-weight:900;font-size:{prev_size};font-family:sans-serif;"
            if prev_rank_class
            else f"color:#999;font-weight:700;font-size:{prev_size};font-family:sans-serif;"
        )

        html += (
            f'<div class="league-row">'
            f'<div class="league-name">{name}</div>'
            f'<div class="league-ranks">'
            f'<span class="rank-label">Current:</span>'
            f'<span class="{cur_rank_class}" style="{cur_style}">{fmt(cur)}</span>'
            f'<span class="rank-label">Previous:</span>'
            f'<span class="{prev_rank_class}" style="{prev_style}">{fmt(prev)}</span>'
            f'<span class="rank-arrow {arrow_class}">{arrow}</span>'
            f'</div>{total_line}</div>'
        )
    return html

mini_html   = build_league_html(mini_leagues,   show_total=True, max_count=4)
public_html = build_league_html(public_leagues, show_total=False, max_count=5)

matches_html = ""
for fx in fixtures:
    home_id = fx.get("team_h")
    away_id = fx.get("team_a")
    home = team_map.get(home_id, {"name": "Home", "code": None})
    away = team_map.get(away_id, {"name": "Away", "code": None})

    hs = fx.get("team_h_score")
    aas = fx.get("team_a_score")
    finished = fx.get("finished")

    if hs is not None and aas is not None:
        score_text = f"{hs} - {aas}"
    else:
        score_text = "vs"

    sub_text = "FT" if finished else kickoff_label(fx.get("kickoff_time"))

    matches_html += (
        f'<div class="match-row">'
        f'  <div class="team-cell">'
        f'    <img class="team-logo" src="{logo_url(home.get("code"))}" alt="{home.get("name")}">'
        f'    <div class="team-name-small">{home.get("name")}</div>'
        f'  </div>'
        f'  <div class="score-cell">'
        f'    <div class="score-main">{score_text}</div>'
        f'    <div class="score-sub">{sub_text}</div>'
        f'  </div>'
        f'  <div class="team-cell right">'
        f'    <div class="team-name-small">{away.get("name")}</div>'
        f'    <img class="team-logo" src="{logo_url(away.get("code"))}" alt="{away.get("name")}">'
        f'  </div>'
        f'</div>'
    )

if not matches_html:
    matches_html = '<div class="score-sub" style="text-align:center;padding:10px;">No fixtures found for this gameweek.</div>'

left_col, right_col = st.columns([1, 2])

with left_col:
    st.markdown(f"""
    <div class="glass-box points-box">
        <div class="team-name">{team_name}</div>
        <div class="gw-label">Gameweek {gw}</div>
        <div class="points-row">
            <div class="side-points">
                <div class="side-label">Average</div>
                <div class="side-value">{avg_points}</div>
            </div>
            <div class="big-points">{gw_points}</div>
            <div class="side-points">
                <div class="side-label">Highest</div>
                <div class="side-value">{highest_points}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='height: 32px;'></div>
    """, unsafe_allow_html=True)
    btn1, btn2 = st.columns(2)
    st.markdown("""
    <style>
    /* Target the inner button row specifically — override Streamlit inline gap */
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]
    div[data-testid="stHorizontalBlock"] {
        gap: 0px !important;
        column-gap: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    with btn1:
        if st.button("Points →", key="nav_points", use_container_width=True):
            st.switch_page("pages/points.py")
    with btn2:
        if st.button("Graphs →", key="nav_graphs", use_container_width=True):
            st.switch_page("pages/graphs.py")

    deadline_iso = next_deadline.isoformat() if next_deadline else ""
    next_gw_label = next_gw if next_gw else (gw + 1)
    components.html(
        f"""
        <div style="
            margin-top: 14px;
            border-radius: 22px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            box-shadow: 0 20px 45px rgba(0,0,0,0.35);
            color: #fff;
            text-align:center;
            padding: 16px 12px 1px 1px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        ">
            <div style="font-size:15px;font-weight:700;opacity:0.92;margin-bottom:10px;">Deadline Countdown (GW {next_gw_label})</div>
            <div id="deadline-countdown" style="font-size:32px;font-weight:800;letter-spacing:1px;color:#00ff87;">--:--:--</div>
            <div id="deadline-format" style="font-size:11px;opacity:0.7;margin-top:4px;">(Days:Hours:Minutes:Seconds)</div>
            <div id="deadline-sub" style="font-size:12px;opacity:0.8;margin-top:6px;">Calculating...</div>
        </div>
        <script>
            const deadlineIso = "{deadline_iso}";
            const target = deadlineIso ? new Date(deadlineIso) : null;
            const valueEl = document.getElementById("deadline-countdown");
            const formatEl = document.getElementById("deadline-format");
            const subEl = document.getElementById("deadline-sub");

            function pad(n) {{ return String(n).padStart(2, "0"); }}

            function tick() {{
                if (!target || isNaN(target.getTime())) {{
                    valueEl.textContent = "N/A";
                    formatEl.textContent = "Days : Hours : Minutes : Seconds";
                    subEl.textContent = "Next deadline unavailable";
                    return;
                }}

                const now = new Date();
                let diff = Math.floor((target - now) / 1000);

                if (diff <= 0) {{
                    valueEl.textContent = "00:00:00";
                    formatEl.textContent = " Hours : Minutes : Seconds ";
                    subEl.textContent = "Deadline passed";
                    return;
                }}

                const days = Math.floor(diff / 86400);
                diff %= 86400;
                const hours = Math.floor(diff / 3600);
                diff %= 3600;
                const mins = Math.floor(diff / 60);
                const secs = diff % 60;

                let display = '';
                if (days > 0) {{
                    display = `${{days}}:${{pad(hours)}}:${{pad(mins)}}:${{pad(secs)}}`;
                    formatEl.textContent = " Days : Hours : Minutes : Seconds ";
                }} else {{
                    display = `${{pad(hours)}}:${{pad(mins)}}:${{pad(secs)}}`;
                    formatEl.textContent = " Hours : Minutes : Seconds ";
                }}
                valueEl.textContent = display;
                // Format deadline as 12-hour time with AM/PM
                const options = {{ month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true, timeZone: 'UTC' }};
                const formattedDeadline = target.toLocaleString('en-US', options) + ' UTC';
                subEl.textContent = `Deadline: ${{formattedDeadline}}`;
            }}

            tick();
            setInterval(tick, 1000);
        </script>
        """,
        height=150,
    )

    st.markdown(f"""
    <div class="glass-box matches-header-box">
        <div class="matches-section-title">Fixtures & Results GW{gw}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("See All Stats", key="see_fixtures", use_container_width=True):
        st.switch_page("pages/fixtures.py")

    st.markdown(f"""
    <div class="glass-box matches-body-box">
        <div class="match-head">
            <div class="match-head-side">Home</div>
            <div></div>
            <div class="match-head-side right">Away</div>
        </div>
        {matches_html}
    </div>
    """, unsafe_allow_html=True)

with right_col:
    st.markdown(f"""
    <div class="glass-box leagues-header-box">
        <div class="leagues-headings">
            <div class="league-section">
                <div class="leagues-title">Mini Leagues</div>
            </div>
            <div class="league-section">
                <div class="leagues-title">Public Leagues</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.container(key="league_actions"):
        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if st.button("See All League Details", key="see_leagues", use_container_width=True, disabled=is_guest):
                st.switch_page("pages/leagues.py")
        with action_col2:
            render_reorder_popover(manager_id, mini_leagues, public_leagues)

    st.markdown(f"""
    <div class="glass-box leagues-body-box">
        <div class="leagues-sections">
            <div class="league-section">{mini_html}</div>
            <div class="league-section">{public_html}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="trends-wrap"></div>', unsafe_allow_html=True)
    t1, gap1, t2, gap2, t3 = st.columns([1, 0.06, 1, 0.06, 1])

    with t1:
        st.markdown(
            build_trend_box_html(
                f"Most Captained for GW{gw}",
                "",
                captained_top5,
            ),
            unsafe_allow_html=True,
        )

    with t2:
        st.markdown(
            build_trend_box_html(
                f"Most Subbed In for GW{gw}",
                "",
                subbed_in_top5,
            ),
            unsafe_allow_html=True,
        )

    with t3:
        st.markdown(
            build_trend_box_html(
                f"Most Subbed Out for GW{gw}",
                "",
                subbed_out_top5,
            ),
            unsafe_allow_html=True,
        )

    st.markdown(build_standings_html(standings, gw), unsafe_allow_html=True)
