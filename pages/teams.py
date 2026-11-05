import html
import json
import ssl
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import certifi
import streamlit as st # type: ignore
from nav import render_top_nav
from team_details import team_detail_panels, TEAM_PANEL_ALIGNMENT_SCRIPT


st.set_page_config(page_title="FPL Teams", layout="wide")

is_guest = st.session_state.get("guest", False)
if "manager_id" not in st.session_state and not is_guest:
    st.warning("No manager ID found. Go back to Dashboard and connect your team.")
    if st.button("Go to Dashboard"):
        st.switch_page("live_dashboard.py")
    st.stop()


ROOT_DIR = Path(__file__).resolve().parents[1]
LOCAL_BOOTSTRAP_PATH = ROOT_DIR / "data" / "raw" / "bootstrap_static.json"
LOCAL_FIXTURES_PATH = ROOT_DIR / "data" / "raw" / "fixtures.json"
BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
FIXTURES_URL = "https://fantasy.premierleague.com/api/fixtures/"


def esc(value):
    if value is None:
        return ""
    return html.escape(str(value))


def clean_html(markup):
    return "\n".join(
        line.strip()
        for line in str(markup).splitlines()
        if line.strip()
    )


def to_float(value, fallback=0.0):
    if value in (None, ""):
        return fallback
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def to_int(value, fallback=0):
    if value in (None, ""):
        return fallback
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def clamp(value, low, high):
    return max(low, min(high, value))


def fmt_float(value, digits=1):
    return f"{to_float(value):.{digits}f}"


def fmt_pct(value):
    return f"{to_float(value) * 100:.0f}%"


def parse_dt(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def kickoff_label(kickoff_time):
    dt = parse_dt(kickoff_time)
    if not dt:
        return "TBC"
    return dt.strftime("%d %b %H:%M UTC")


def logo_url(team_code):
    if not team_code:
        return ""
    return f"https://resources.premierleague.com/premierleague/badges/70/t{team_code}.png"


def load_local_json(path, fallback):
    if not path.exists():
        return fallback
    with path.open() as f:
        return json.load(f)


def save_local_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(payload, f)


def fetch_json(url):
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, context=ctx, timeout=8) as response:
        return json.loads(response.read())


@st.cache_data(ttl=900, show_spinner=False)
def fetch_bootstrap_data():
    try:
        data = fetch_json(BOOTSTRAP_URL)
        save_local_json(LOCAL_BOOTSTRAP_PATH, data)
        return data
    except Exception:
        return load_local_json(LOCAL_BOOTSTRAP_PATH, {})


@st.cache_data(ttl=900, show_spinner=False)
def fetch_fixtures_data():
    try:
        data = fetch_json(FIXTURES_URL)
        save_local_json(LOCAL_FIXTURES_PATH, data)
        return data
    except Exception:
        return load_local_json(LOCAL_FIXTURES_PATH, [])


st.markdown(
    """
<style>
.stApp {
    background: linear-gradient(135deg, #37003c, #2b1e5b, #00cc6a) !important;
    min-height: 100vh;
}
.stMainBlockContainer {
    max-width: none !important;
    padding-top: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

h1, h2, h3, p, div, span, li, label {
    color: white;
}

div[data-testid="stSelectbox"] label,
div[data-testid="stRadio"] label {
    color: rgba(255,255,255,0.86) !important;
    font-size: 12px !important;
    font-weight: 800 !important;
}

div[data-baseweb="select"] > div,
div[role="radiogroup"] label {
    background: rgba(255,255,255,0.12) !important;
    border-color: rgba(255,255,255,0.25) !important;
    color: white !important;
}

.glass-panel {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 14px 34px rgba(0,0,0,0.28);
    color: white;
    min-height: 100%;
}

.panel-title {
    font-size: 16px;
    font-weight: 800;
    margin-bottom: 8px;
}

.panel-sub {
    font-size: 13px;
    opacity: 0.8;
}

.kicker {
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-size: 11px;
    font-weight: 700;
    color: rgba(255,255,255,0.7);
}

.team-head {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 8px 0 14px 0;
}

.team-logo-large {
    width: 52px;
    height: 52px;
    object-fit: contain;
    flex-shrink: 0;
}

.team-name-main {
    font-size: 24px;
    line-height: 1.05;
    font-weight: 900;
}

.team-meta {
    font-size: 12px;
    margin-top: 4px;
    color: rgba(255,255,255,0.72);
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    margin-top: 12px;
}

.metric-card {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 12px;
    padding: 10px;
    min-height: 80px;
}

.metric-label {
    font-size: 11px;
    color: rgba(255,255,255,0.72);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.metric-value {
    font-size: 24px;
    font-weight: 900;
    margin-top: 4px;
    color: #00ff87;
}

.metric-note {
    font-size: 11px;
    color: rgba(255,255,255,0.70);
    margin-top: 3px;
}

.result-row,
.fixture-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
    align-items: center;
}

.result-badge {
    border-radius: 999px;
    padding: 4px 9px;
    font-size: 11px;
    font-weight: 900;
    color: #111;
}

.result-win { background: #00ff87; }
.result-draw { background: #ffb500; }
.result-loss { background: #ff4f6d; color: white; }

.fixture-pill {
    border-radius: 12px;
    padding: 8px 9px;
    min-width: 86px;
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.13);
}

.fixture-opp {
    font-size: 13px;
    font-weight: 900;
}

.fixture-meta,
.fixture-date {
    font-size: 11px;
    color: rgba(255,255,255,0.68);
    margin-top: 2px;
}

.fdr-1, .fdr-2 { color: #00ff87; }
.fdr-3 { color: #ffb500; }
.fdr-4, .fdr-5 { color: #ff4f6d; }

.mini-chart {
    margin-top: 14px;
    border-radius: 12px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    padding: 10px 12px 14px 12px;
}

.chart-label-row {
    display: flex;
    justify-content: space-between;
    gap: 6px;
    margin-top: 6px;
    padding: 0 40px 2px 40px;
    width: 100%;
    box-sizing: border-box;
    overflow: hidden;
}

.chart-label {
    flex: 1;
    text-align: center;
    font-size: 10px;
    color: rgba(255,255,255,0.64);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;}

.comparison-row {
    display: grid;
    grid-template-columns: minmax(96px, 1fr) 2fr minmax(80px, auto) 2fr minmax(96px, 1fr);
    align-items: center;
    gap: 10px;
    margin-top: 11px;
}

.comparison-label {
    font-size: 12px;
    font-weight: 800;
    color: rgba(255,255,255,0.78);
}

.comparison-value {
    font-size: 13px;
    font-weight: 900;
}

.comparison-value.right {
    text-align: right;
}

.bar-track {
    height: 9px;
    border-radius: 999px;
    background: rgba(255,255,255,0.11);
    overflow: hidden;
}

.bar-fill {
    height: 100%;
    border-radius: 999px;
    background: #00ff87;
}

.bar-fill.away {
    margin-left: auto;
    background: #05f0ff;
}

.data-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    margin-top: 12px;
}

.data-row {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.13);
    border-radius: 12px;
    padding: 10px 11px;
}

.data-label {
    font-size: 11px;
    color: rgba(255,255,255,0.68);
    text-transform: uppercase;
    letter-spacing: 0.45px;
    font-weight: 800;
}

.data-value {
    font-size: 16px;
    font-weight: 900;
    margin-top: 3px;
}

.small-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 12px;
}

.small-table th,
.small-table td {
    padding: 7px 6px;
    border-bottom: 1px solid rgba(255,255,255,0.12);
    font-size: 12px;
}

.small-table th {
    text-align: left;
    color: rgba(255,255,255,0.70);
    font-weight: 800;
}

.small-table td:last-child,
.small-table th:last-child {
    text-align: right;
}

.empty-note {
    margin-top: 12px;
    font-size: 13px;
    color: rgba(255,255,255,0.72);
}

.column-section-gap {
    height: 20px;
}

.team-squad-panel,
.team-form-panel { min-height: 0; min-width: 0; box-sizing: border-box; }
.team-squad-panel { display: flex; flex-direction: column; }
.team-squad-scroll { width: 100%; overflow-x: auto; flex: 1; display: flex; }
.team-squad-table { min-width: 580px; flex: 1; }
.team-squad-table th,
.team-squad-table td { text-align: center; padding: 10px 8px; }
.team-squad-table th:first-child,
.team-squad-table .squad-player { text-align: left; font-weight: 800; }
.team-squad-table th:last-child,
.team-squad-table td:last-child { text-align: center; }
.team-squad-table .squad-points { color: #00ff87 !important; font-weight: 900; }
.squad-status { font-size: 11px; white-space: nowrap; }
.squad-status.available { color: #00ff87; }
.squad-status.flagged { color: #ffd166; }
.team-form-panel { display: flex; flex-direction: column; gap: 16px; }
.team-form-metrics { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.team-form-chart { margin-top: 0; }
.team-form-history { flex: 1; display: flex; flex-direction: column; }
.team-form-results { list-style: none; padding: 0 !important; margin: 0 !important; flex: 1; display: flex; flex-direction: column; gap: 8px; }
.team-form-result {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 1;
    min-height: 38px;
    box-sizing: border-box;
    padding: 8px 10px !important;
    margin: 0 !important;
    background: var(--fpl-soft-bg);
    border: 1px solid var(--fpl-panel-border);
    border-radius: 12px;
}
.team-form-gameweek { font-size: 11px; opacity: 0.75; }
.team-form-opponent { flex: 1; min-width: 0; font-size: 13px; font-weight: 700; overflow-wrap: anywhere; }
.team-form-score { font-size: 13px; font-weight: 900; white-space: nowrap; }

@media (max-width: 900px) {
    .metric-grid,
    .data-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .comparison-row {
        grid-template-columns: 1fr;
        gap: 5px;
    }

    .comparison-value.right {
        text-align: left;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

render_top_nav()

bootstrap_data = fetch_bootstrap_data()
fixtures = fetch_fixtures_data()
teams = sorted(bootstrap_data.get("teams", []), key=lambda t: t.get("name", ""))
elements = bootstrap_data.get("elements", [])

if not teams:
    st.error("No Premier League team data was found in the FPL bootstrap data.")
    st.stop()

team_lookup = {team.get("id"): team for team in teams}
team_ids = [team.get("id") for team in teams if team.get("id") is not None]
team_name_to_id = {team.get("name"): team.get("id") for team in teams}


def resolve_current_event():
    if st.session_state.get("gw"):
        return to_int(st.session_state.gw, 1)

    events = bootstrap_data.get("events", [])
    for flag in ("is_current", "is_next", "is_previous"):
        for event in events:
            if event.get(flag):
                return to_int(event.get("id"), 1)
    return 1


current_event = resolve_current_event()


def team_short(team_id):
    return team_lookup.get(team_id, {}).get("short_name", "UNK")


def team_name(team_id):
    return team_lookup.get(team_id, {}).get("name", "Unknown")


def strength_value(team_id, key):
    team = team_lookup.get(team_id, {})
    return to_float(team.get(key), to_float(team.get("strength"), 3) * 250)


def avg_strength(key):
    values = [strength_value(team_id, key) for team_id in team_ids]
    values = [value for value in values if value > 0]
    return sum(values) / len(values) if values else 1000


AVG_ATTACK_HOME = avg_strength("strength_attack_home")
AVG_ATTACK_AWAY = avg_strength("strength_attack_away")
AVG_DEFENCE_HOME = avg_strength("strength_defence_home")
AVG_DEFENCE_AWAY = avg_strength("strength_defence_away")
AVG_OVERALL_HOME = avg_strength("strength_overall_home")
AVG_OVERALL_AWAY = avg_strength("strength_overall_away")


def fixture_sort_key(match):
    dt = parse_dt(match.get("kickoff_time"))
    return (
        to_int(match.get("event"), 99),
        dt or datetime.max.replace(tzinfo=timezone.utc),
        to_int(match.get("id"), 0),
    )


def derived_fdr(team_id, opponent_id, is_home):
    if not opponent_id:
        return 3

    opponent_overall = strength_value(
        opponent_id,
        "strength_overall_away" if is_home else "strength_overall_home",
    )
    league_average = AVG_OVERALL_AWAY if is_home else AVG_OVERALL_HOME
    venue_bump = 0 if is_home else 0.25
    raw = 3 + ((opponent_overall - league_average) / 220) + venue_bump
    return int(round(clamp(raw, 1, 5)))


def normalize_fixture_for_team(fixture, team_id):
    home_id = fixture.get("team_h")
    away_id = fixture.get("team_a")
    if team_id not in (home_id, away_id):
        return None

    is_home = team_id == home_id
    opponent_id = away_id if is_home else home_id
    side = "h" if is_home else "a"
    gf = fixture.get("team_h_score") if is_home else fixture.get("team_a_score")
    ga = fixture.get("team_a_score") if is_home else fixture.get("team_h_score")
    finished = bool(fixture.get("finished")) and gf is not None and ga is not None

    result = None
    points = None
    if finished:
        if gf > ga:
            result = "W"
            points = 3
        elif gf == ga:
            result = "D"
            points = 1
        else:
            result = "L"
            points = 0

    fdr = to_int(fixture.get(f"team_{side}_difficulty"), 0)
    if not fdr:
        fdr = derived_fdr(team_id, opponent_id, is_home)

    return {
        "id": fixture.get("id"),
        "event": fixture.get("event"),
        "kickoff_time": fixture.get("kickoff_time"),
        "is_home": is_home,
        "opponent_id": opponent_id,
        "gf": gf,
        "ga": ga,
        "finished": finished,
        "result": result,
        "points": points,
        "clean_sheet": finished and ga == 0,
        "difficulty": fdr,
    }


def matches_for_team(team_id):
    rows = []
    for fixture in fixtures:
        row = normalize_fixture_for_team(fixture, team_id)
        if row:
            rows.append(row)
    return sorted(rows, key=fixture_sort_key)


MATCHES_BY_TEAM = {team_id: matches_for_team(team_id) for team_id in team_ids}


def completed_matches(team_id):
    return [match for match in MATCHES_BY_TEAM.get(team_id, []) if match.get("finished")]


def upcoming_matches(team_id, limit=None):
    rows = [match for match in MATCHES_BY_TEAM.get(team_id, []) if not match.get("finished")]
    return rows if limit is None else rows[:limit]


def aggregate_players(team_id):
    players = [
        player
        for player in elements
        if player.get("team") == team_id and not player.get("removed")
    ]
    sorted_by_minutes = sorted(
        players,
        key=lambda player: to_float(player.get("minutes")),
        reverse=True,
    )
    top_minutes = sorted_by_minutes[:11]
    set_piece_players = [
        player
        for player in players
        if any(
            player.get(field)
            for field in (
                "corners_and_indirect_freekicks_order",
                "direct_freekicks_order",
                "penalties_order",
            )
        )
    ]

    xg = sum(to_float(player.get("expected_goals")) for player in players)
    xa = sum(to_float(player.get("expected_assists")) for player in players)
    xgi = sum(to_float(player.get("expected_goal_involvements")) for player in players)
    if not xgi:
        xgi = xg + xa

    creativity = sum(to_float(player.get("creativity")) for player in players)
    threat = sum(to_float(player.get("threat")) for player in players)
    squad_form = sum(to_float(player.get("form")) for player in top_minutes)
    total_points = sum(to_int(player.get("total_points")) for player in players)
    total_minutes = sum(to_int(player.get("minutes")) for player in players)
    top_minutes_total = sum(to_int(player.get("minutes")) for player in top_minutes)

    raw_set_piece = sum(
        to_float(player.get("threat")) * 0.35
        + to_float(player.get("creativity")) * 0.28
        + (
            to_float(player.get("expected_goals"))
            + to_float(player.get("expected_assists"))
        )
        * 20
        + to_float(player.get("starts")) * 1.5
        for player in set_piece_players
    )
    top_set_piece = sorted(
        set_piece_players,
        key=lambda player: (
            to_float(player.get("threat"))
            + to_float(player.get("creativity"))
            + (
                to_float(player.get("expected_goals"))
                + to_float(player.get("expected_assists"))
            )
            * 20
        ),
        reverse=True,
    )[:4]

    return {
        "players": players,
        "xg": xg,
        "xa": xa,
        "xgi": xgi,
        "creativity": creativity,
        "threat": threat,
        "squad_form": squad_form,
        "total_points": total_points,
        "total_minutes": total_minutes,
        "top_minutes_total": top_minutes_total,
        "raw_set_piece": raw_set_piece,
        "top_set_piece": top_set_piece,
    }


def scale_score(value, values):
    values = [to_float(item) for item in values]
    high = max(values) if values else 0
    low = min(values) if values else 0
    if high == low:
        return 50
    return round(35 + (to_float(value) - low) * 65 / (high - low), 1)


raw_player_stats = {team_id: aggregate_players(team_id) for team_id in team_ids}
raw_chance_values = [
    stats["xa"] * 12 + stats["creativity"] / 90 + stats["xgi"] * 2
    for stats in raw_player_stats.values()
]
raw_set_piece_values = [stats["raw_set_piece"] for stats in raw_player_stats.values()]

TEAM_ANALYTICS = {}
for team_id in team_ids:
    stats = raw_player_stats[team_id]
    completed = completed_matches(team_id)
    match_count = max(len(completed), current_event - 1, 1)
    clean_sheets = sum(1 for match in completed if match.get("clean_sheet"))
    xg_per_match = stats["xg"] / match_count if match_count else 0
    xa_per_match = stats["xa"] / match_count if match_count else 0
    chance_raw = stats["xa"] * 12 + stats["creativity"] / 90 + stats["xgi"] * 2
    expected_top_minutes = match_count * 90 * 11
    minute_reliability = (
        stats["top_minutes_total"] / expected_top_minutes
        if expected_top_minutes
        else 0
    )

    TEAM_ANALYTICS[team_id] = {
        **stats,
        "matches_played": match_count,
        "clean_sheets": clean_sheets,
        "clean_sheet_rate": clean_sheets / len(completed) if completed else 0.30,
        "xg_per_match": xg_per_match,
        "xa_per_match": xa_per_match,
        "chance_score": scale_score(chance_raw, raw_chance_values),
        "set_piece_score": scale_score(stats["raw_set_piece"], raw_set_piece_values),
        "minute_reliability": clamp(minute_reliability, 0, 1),
    }

league_xg_values = [
    stats["xg_per_match"] for stats in TEAM_ANALYTICS.values() if stats["xg_per_match"] > 0
]
LEAGUE_XG_PER_MATCH = (
    sum(league_xg_values) / len(league_xg_values) if league_xg_values else 1.35
)


def project_goals(team_id, opponent_id, is_home):
    if not opponent_id:
        return TEAM_ANALYTICS.get(team_id, {}).get("xg_per_match", LEAGUE_XG_PER_MATCH)

    base_xg = TEAM_ANALYTICS.get(team_id, {}).get("xg_per_match") or LEAGUE_XG_PER_MATCH
    team_attack = strength_value(
        team_id,
        "strength_attack_home" if is_home else "strength_attack_away",
    )
    opponent_defence = strength_value(
        opponent_id,
        "strength_defence_away" if is_home else "strength_defence_home",
    )
    avg_attack = AVG_ATTACK_HOME if is_home else AVG_ATTACK_AWAY
    avg_defence = AVG_DEFENCE_AWAY if is_home else AVG_DEFENCE_HOME
    venue_factor = 1.06 if is_home else 0.94

    strength_projection = (
        LEAGUE_XG_PER_MATCH
        * (team_attack / avg_attack if avg_attack else 1)
        * (avg_defence / opponent_defence if opponent_defence else 1)
        * venue_factor
    )
    return clamp((base_xg * 0.62) + (strength_projection * 0.38), 0.25, 3.8)


def clean_sheet_probability(team_id, opponent_id, is_home):
    if not opponent_id:
        return 0.28

    team_defence = strength_value(
        team_id,
        "strength_defence_home" if is_home else "strength_defence_away",
    )
    opponent_attack = strength_value(
        opponent_id,
        "strength_attack_away" if is_home else "strength_attack_home",
    )
    avg_defence = AVG_DEFENCE_HOME if is_home else AVG_DEFENCE_AWAY
    recent_rate = TEAM_ANALYTICS.get(team_id, {}).get("clean_sheet_rate", 0.30)
    strength_delta = (team_defence - opponent_attack) / avg_defence if avg_defence else 0
    probability = (
        0.28
        + (0.18 * strength_delta)
        + (0.20 * (recent_rate - 0.30))
        + (0.02 if is_home else -0.02)
    )
    return clamp(probability, 0.06, 0.68)


def split_summary(team_id):
    summary = {
        "home_count": 0,
        "home_points": 0,
        "away_count": 0,
        "away_points": 0,
    }
    for match in completed_matches(team_id):
        key = "home" if match["is_home"] else "away"
        summary[f"{key}_count"] += 1
        summary[f"{key}_points"] += to_int(match.get("points"))

    home_ppg = (
        summary["home_points"] / summary["home_count"]
        if summary["home_count"]
        else 0
    )
    away_ppg = (
        summary["away_points"] / summary["away_count"]
        if summary["away_count"]
        else 0
    )
    return home_ppg, away_ppg


def days_rest(team_id, next_match):
    if not next_match:
        return None

    next_dt = parse_dt(next_match.get("kickoff_time"))
    if not next_dt:
        return None

    previous = [
        match
        for match in completed_matches(team_id)
        if parse_dt(match.get("kickoff_time"))
        and parse_dt(match.get("kickoff_time")) < next_dt
    ]
    if not previous:
        return None

    previous_dt = parse_dt(previous[-1].get("kickoff_time"))
    if not previous_dt:
        return None
    return max(0, (next_dt - previous_dt).days)


def fdr_class(fdr):
    return f"fdr-{clamp(to_int(fdr, 3), 1, 5)}"


def run_label(fixtures_run):
    if not fixtures_run:
        return "No run"
    avg_fdr = sum(to_int(match.get("difficulty"), 3) for match in fixtures_run) / len(fixtures_run)
    if avg_fdr <= 2.4:
        return "Easy"
    if avg_fdr >= 3.6:
        return "Hard"
    return "Mixed"


def result_badges_html(team_id):
    recent = completed_matches(team_id)[-5:]
    if not recent:
        return "<div class='empty-note'>No completed fixtures loaded yet.</div>"

    badges = []
    badges.append("<span class='kicker'>Latest |</span>")
    for match in recent:
        result = match.get("result") or "-"
        cls = {"W": "result-win", "D": "result-draw", "L": "result-loss"}.get(
            result,
            "result-draw",
        )
        score = f"{match.get('gf', '-')} - {match.get('ga', '-')}"
        badges.append(
            f"""
            <span class="result-badge {cls}" title="{esc(team_short(match.get('opponent_id')))} {esc(score)}">
                {esc(result)}
            </span>
            """
        )
    return f"<div class='result-row'>{''.join(badges)}</div>"


def fixture_pills_html(team_id, limit=5):
    upcoming = upcoming_matches(team_id, limit)
    if not upcoming:
        return "<div class='empty-note'>No upcoming fixtures loaded.</div>"

    pills = []
    for match in upcoming:
        venue = "H" if match["is_home"] else "A"
        fdr = to_int(match.get("difficulty"), 3)
        gw = to_int(match.get("event"), 0)
        gw_label = f"GW{gw}" if gw else "GW?"
        pills.append(
            f"""
            <div class="fixture-pill">
            <div class="fixture-opp">{esc(team_short(match.get("opponent_id")))} ({venue}) | {esc(gw_label)}</div>
                <div class="fixture-meta">Fixture Difficulty: <span class="{fdr_class(fdr)}">{fdr}</span></div>
                <div class="fixture-date">{esc(kickoff_label(match.get("kickoff_time")))}</div>
            </div>
            """
        )
    return f"<div class='fixture-row'>{''.join(pills)}</div>"


def sparkline_svg(values):
    if not values:
        return ""

    if len(values) == 1:
        values = [values[0], values[0]]

    width = 420
    height = 104
    pad_x = 18
    pad_y = 14
    low = min(values)
    high = max(values)
    if high == low:
        low -= 0.5
        high += 0.5

    points = []
    fill_points = []
    for index, value in enumerate(values):
        x = pad_x + index * ((width - pad_x * 2) / (len(values) - 1))
        y = height - pad_y - ((value - low) / (high - low)) * (height - pad_y * 2)
        points.append(f"{x:.1f},{y:.1f}")
        fill_points.append((x, y))

    fill_path = (
        f"M {fill_points[0][0]:.1f},{height - pad_y:.1f} "
        + " ".join(f"L {x:.1f},{y:.1f}" for x, y in fill_points)
        + f" L {fill_points[-1][0]:.1f},{height - pad_y:.1f} Z"
    )
    circles = "".join(
        f"<circle cx='{x:.1f}' cy='{y:.1f}' r='3.5' fill='#00ff87' />"
        for x, y in fill_points
    )
    return f"""
    <svg viewBox="0 0 {width} {height}" width="100%" height="104" aria-hidden="true">
        <line x1="{pad_x}" y1="{height - pad_y}" x2="{width - pad_x}" y2="{height - pad_y}" stroke="rgba(255,255,255,0.18)" />
        <line x1="{pad_x}" y1="{pad_y}" x2="{pad_x}" y2="{height - pad_y}" stroke="rgba(255,255,255,0.12)" />
        <path d="{fill_path}" fill="rgba(0,255,135,0.12)" />
        <polyline points="{' '.join(points)}" fill="none" stroke="#00ff87" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
        {circles}
    </svg>
    """


def positions_sparkline_svg(values, labels):
    if not values:
        return ""

    # A one-gameweek series is rendered as two points so the line is visible.
    # Keep its labels aligned with those duplicated points for the SVG tooltips.
    labels = list(labels)
    if len(values) == 1:
        values = [values[0], values[0]]
        labels = [labels[0], labels[0]] if labels else ["", ""]
    elif len(labels) < len(values):
        labels.extend([""] * (len(values) - len(labels)))

    width = 560
    height = 160
    pad_x = 40
    pad_y = 22
    low = 1
    high = 20

    points = []
    fill_points = []
    for index, value in enumerate(values):
        value = clamp(to_int(value, low), low, high)
        x = pad_x + index * ((width - pad_x * 2) / max(1, len(values) - 1))
        y = pad_y + ((value - low) / (high - low)) * (height - pad_y * 2)
        points.append(f"{x:.1f},{y:.1f}")
        fill_points.append((x, y))

    fill_path = (
        f"M {fill_points[0][0]:.1f},{height - pad_y:.1f} "
        + " ".join(f"L {x:.1f},{y:.1f}" for x, y in fill_points)
        + f" L {fill_points[-1][0]:.1f},{height - pad_y:.1f} Z"
    )
    circles = "".join(
        f"""
        <g>
            <circle cx='{x:.1f}' cy='{y:.1f}' r='3.5' fill='#00ff87' />
            <circle cx='{x:.1f}' cy='{y:.1f}' r='8' fill='transparent'>
                <title>{esc(labels[i])}: {to_int(values[i], 0)}</title>
            </circle>
        </g>
        """
        for i, (x, y) in enumerate(fill_points)
    )
    y_label_values = list(range(low, high + 1, 3))
    y_labels = "".join(
        f"<text x='{pad_x - 6}' y='{pad_y + ((value - low) / (high - low)) * (height - pad_y * 2) + 3:.1f}' "
        f"fill='rgba(255,255,255,0.65)' font-size='9' text-anchor='end'>{value}</text>"
        for value in y_label_values
    )
    return f"""
    <svg viewBox="0 0 {width} {height}" width="100%" height="160" aria-hidden="true">
        <line x1="{pad_x}" y1="{height - pad_y}" x2="{width - pad_x}" y2="{height - pad_y}" stroke="rgba(255,255,255,0.18)" />
        <line x1="{pad_x}" y1="{pad_y}" x2="{pad_x}" y2="{height - pad_y}" stroke="rgba(255,255,255,0.12)" />
        <text x="12" y="{height / 2:.1f}" fill="rgba(255,255,255,0.65)" font-size="10" text-anchor="middle" transform="rotate(-90 12 {height / 2:.1f})">Position</text>
        {y_labels}
        <path d="{fill_path}" fill="rgba(0,255,135,0.12)" />
        <polyline points="{' '.join(points)}" fill="none" stroke="#00ff87" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
        {circles}
    </svg>
    """


def projected_trend_html(team_id):
    return ""


def standings_positions_by_event(event_id):
    table = {
        team_id: {
            "points": 0,
            "gf": 0,
            "ga": 0,
            "gd": 0,
            "name": team_name(team_id),
        }
        for team_id in team_ids
    }
    for fixture in fixtures:
        if not fixture.get("finished"):
            continue
        fixture_event = to_int(fixture.get("event"), 0)
        if not fixture_event or fixture_event > event_id:
            continue
        home_id = fixture.get("team_h")
        away_id = fixture.get("team_a")
        if not home_id or not away_id:
            continue

        home_gf = to_int(fixture.get("team_h_score"), 0)
        away_gf = to_int(fixture.get("team_a_score"), 0)
        home_row = table[home_id]
        away_row = table[away_id]
        home_row["gf"] += home_gf
        home_row["ga"] += away_gf
        away_row["gf"] += away_gf
        away_row["ga"] += home_gf

        if home_gf > away_gf:
            home_row["points"] += 3
        elif home_gf < away_gf:
            away_row["points"] += 3
        else:
            home_row["points"] += 1
            away_row["points"] += 1

    for row in table.values():
        row["gd"] = row["gf"] - row["ga"]

    ordered = sorted(
        table.items(),
        key=lambda item: (
            item[1]["points"],
            item[1]["gd"],
            item[1]["gf"],
            item[1]["name"],
        ),
        reverse=True,
    )
    return {team_id: idx + 1 for idx, (team_id, _) in enumerate(ordered)}


def positions_trend_html(team_id):
    finished_events = sorted({to_int(f.get("event"), 0) for f in fixtures if f.get("finished")})
    finished_events = [event_id for event_id in finished_events if event_id]
    if not finished_events:
        return "<div class='empty-note'>Table positions are not available yet.</div>"

    labels = [f"GW{event_id}" for event_id in finished_events]
    positions = [standings_positions_by_event(event_id).get(team_id, 20) for event_id in finished_events]
    
    if not labels:
        return "<div class='empty-note'>No data for chart labels.</div>"

    target_ticks = 7
    tick_step = max(1, len(labels) // max(1, target_ticks - 1))
    visible_indexes = set(range(0, len(labels), tick_step))
    visible_indexes.add(len(labels) - 1)
    visible_labels = [labels[idx] for idx in sorted(visible_indexes)]

    label_html = "".join(f"<div class='chart-label'>{esc(label)}</div>" for label in visible_labels)
    return f"""
    <div class="mini-chart">
        {positions_sparkline_svg(positions, labels)}
        <div class="chart-label-row">{label_html}</div>
    </div>
    """


def metric_card(label, value, note=""):
    return f"""
    <div class="metric-card">
        <div class="metric-label">{esc(label)}</div>
        <div class="metric-value">{esc(value)}</div>
        <div class="metric-note">{esc(note)}</div>
    </div>
    """


def snapshot_html(team_id):
    team = team_lookup[team_id]
    stats = TEAM_ANALYTICS[team_id]
    recent = completed_matches(team_id)[-5:]
    recent_points = sum(to_int(match.get("points")) for match in recent)
    next_run = upcoming_matches(team_id, 5)
    avg_fdr = (
        sum(to_int(match.get("difficulty"), 3) for match in next_run) / len(next_run)
        if next_run
        else 0
    )
    fdr_note = f"{run_label(next_run)} next run" if next_run else "Fixture feed pending"

    cards = [
        metric_card("Last 5 form", f"{recent_points} pts", "Result points"),
        metric_card("xG / match", fmt_float(stats["xg_per_match"], 2), "Player xG aggregate"),
        metric_card("xA / match", fmt_float(stats["xa_per_match"], 2), "Chance creation"),
        metric_card("Fixture run", fmt_float(avg_fdr, 1) if next_run else "N/A", fdr_note),
    ]

    return f"""
    <div class="glass-panel">
        <div class="kicker">TEAM SNAPSHOT</div>
        <div class="panel-title">Form, xG, and table position</div>
        <div class="team-head">
            <img class="team-logo-large" src="{logo_url(team.get("code"))}" alt="{esc(team.get("name"))}">
            <div>
                <div class="team-name-main">{esc(team.get("name"))}</div>
                <div class="team-meta">GW {current_event} | {esc(team.get("short_name"))} | strength {esc(team.get("strength"))}</div>
            </div>
        </div>
        <div class="metric-grid">{''.join(cards)}</div>
        {result_badges_html(team_id)}
        {positions_trend_html(team_id)}
        {fixture_pills_html(team_id)}
    </div>
    """


def comparison_metric_rows(team_a_id, team_b_id):
    stats_a = TEAM_ANALYTICS[team_a_id]
    stats_b = TEAM_ANALYTICS[team_b_id]
    rows = [
        (
            "Chance creation",
            stats_a["chance_score"],
            stats_b["chance_score"],
            "",
        ),
        (
            "Clean sheet odds",
            clean_sheet_probability(team_a_id, team_b_id, True) * 100,
            clean_sheet_probability(team_b_id, team_a_id, False) * 100,
            "%",
        ),
        (
            "Set-piece threat",
            stats_a["set_piece_score"],
            stats_b["set_piece_score"],
            "",
        ),
        (
            "Attack strength",
            (
                strength_value(team_a_id, "strength_attack_home")
                + strength_value(team_a_id, "strength_attack_away")
            )
            / 2,
            (
                strength_value(team_b_id, "strength_attack_home")
                + strength_value(team_b_id, "strength_attack_away")
            )
            / 2,
            "",
        ),
        (
            "Defence strength",
            (
                strength_value(team_a_id, "strength_defence_home")
                + strength_value(team_a_id, "strength_defence_away")
            )
            / 2,
            (
                strength_value(team_b_id, "strength_defence_home")
                + strength_value(team_b_id, "strength_defence_away")
            )
            / 2,
            "",
        ),
    ]

    html_rows = []
    for label, value_a, value_b, suffix in rows:
        high = max(value_a, value_b, 1)
        width_a = clamp(value_a / high * 100, 3, 100)
        width_b = clamp(value_b / high * 100, 3, 100)
        value_a_label = f"{value_a:.0f}{suffix}"
        value_b_label = f"{value_b:.0f}{suffix}"
        html_rows.append(
            f"""
            <div class="comparison-row">
                <div class="comparison-value">{esc(value_a_label)}</div>
                <div class="bar-track"><div class="bar-fill" style="width:{width_a:.0f}%"></div></div>
                <div class="comparison-label">{esc(label)}</div>
                <div class="bar-track"><div class="bar-fill away" style="width:{width_b:.0f}%"></div></div>
                <div class="comparison-value right">{esc(value_b_label)}</div>
            </div>
            """
        )
    return "".join(html_rows)


def h2h_html(team_a_id, team_b_id):
    completed = [
        match
        for match in completed_matches(team_a_id)
        if match.get("opponent_id") == team_b_id
    ]
    upcoming = [
        match
        for match in upcoming_matches(team_a_id)
        if match.get("opponent_id") == team_b_id
    ]

    rows = []
    for match in completed[-2:]:
        venue = "H" if match["is_home"] else "A"
        rows.append(
            f"""
            <tr>
                <td>GW{esc(match.get("event"))}</td>
                <td>{esc(team_short(team_a_id))} {esc(match.get("gf"))} - {esc(match.get("ga"))} {esc(team_short(team_b_id))}</td>
                <td>{venue}</td>
            </tr>
            """
        )
    for match in upcoming[:1]:
        venue = "H" if match["is_home"] else "A"
        rows.append(
            f"""
            <tr>
                <td>GW{esc(match.get("event"))}</td>
                <td>{esc(team_short(team_a_id))} vs {esc(team_short(team_b_id))}</td>
                <td>{venue} | FDR {esc(match.get("difficulty"))}</td>
            </tr>
            """
        )

    if not rows:
        return "<div class='empty-note'>No head-to-head fixtures found in the loaded fixture feed.</div>"

    return f"""
    <table class="small-table">
        <thead><tr><th>When</th><th>Match-up</th><th>Context</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
    """


def top_set_piece_text(team_id):
    players = TEAM_ANALYTICS[team_id]["top_set_piece"]
    if not players:
        return "No primary takers listed"
    return ", ".join(player.get("web_name") or player.get("second_name") for player in players)


def comparison_html(team_a_id, team_b_id):
    return f"""
    <div class="glass-panel">
        <div class="kicker">TEAM COMPARISON</div>
        <div class="panel-title">Head-to-head stats and strengths</div>
        <div class="team-meta">{esc(team_name(team_a_id))} set pieces: {esc(top_set_piece_text(team_a_id))}</div>
        <div class="team-meta">{esc(team_name(team_b_id))} set pieces: {esc(top_set_piece_text(team_b_id))}</div>
        {comparison_metric_rows(team_a_id, team_b_id)}
        {h2h_html(team_a_id, team_b_id)}
    </div>
    """


def prediction_inputs_html(team_id):
    next_match = upcoming_matches(team_id, 1)
    next_match = next_match[0] if next_match else None
    stats = TEAM_ANALYTICS[team_id]
    home_ppg, away_ppg = split_summary(team_id)

    if next_match:
        opponent_id = next_match["opponent_id"]
        opponent_strength = strength_value(
            opponent_id,
            "strength_overall_away" if next_match["is_home"] else "strength_overall_home",
        )
        venue = "Home" if next_match["is_home"] else "Away"
        rest = days_rest(team_id, next_match)
        rest_label = f"{rest} days" if rest is not None else "N/A"
        opponent_label = team_name(opponent_id)
        projected = project_goals(team_id, opponent_id, next_match["is_home"])
        cs_prob = clean_sheet_probability(team_id, opponent_id, next_match["is_home"])
        fdr = next_match["difficulty"]
    else:
        opponent_strength = 0
        venue = "N/A"
        rest_label = "N/A"
        opponent_label = "No upcoming fixture"
        projected = stats["xg_per_match"]
        cs_prob = stats["clean_sheet_rate"]
        fdr = "N/A"

    rows = [
        ("Opponent", opponent_label),
        ("Opponent strength", f"{opponent_strength:.0f}" if opponent_strength else "N/A"),
        ("Days of rest", rest_label),
        ("Venue split", f"H {home_ppg:.2f} PPG | A {away_ppg:.2f} PPG"),
        ("Recent minutes", fmt_pct(stats["minute_reliability"])),
        ("Rolling form", f"{sum(to_int(m.get('points')) for m in completed_matches(team_id)[-5:])} pts"),
        ("Projected goals", fmt_float(projected, 2)),
        ("Clean sheet odds", fmt_pct(cs_prob)),
        ("Match FDR", fdr),
        ("Squad form", fmt_float(stats["squad_form"], 1)),
    ]
    row_html = "".join(
        f"""
        <div class="data-row">
            <div class="data-label">{esc(label)}</div>
            <div class="data-value">{esc(value)}</div>
        </div>
        """
        for label, value in rows
    )
    return f"""
    <div class="glass-panel">
        <div class="kicker">PREDICTION INPUTS</div>
        <div class="panel-title">Feature set preview</div>
        <div class="data-grid">{row_html}</div>
    </div>
    """


def fixture_option_label(match):
    venue = "H" if match["is_home"] else "A"
    return (
        f"GW{match.get('event')} {team_short(match.get('opponent_id'))} "
        f"({venue}) | Fixture difficulty: {match.get('difficulty')}"
    )


def forecast_html(team_id, opponent_id, is_home, source_match=None):
    projected_for = project_goals(team_id, opponent_id, is_home)
    projected_against = project_goals(opponent_id, team_id, not is_home)
    cs_prob = clean_sheet_probability(team_id, opponent_id, is_home)
    fdr = (
        source_match.get("difficulty")
        if source_match
        else derived_fdr(team_id, opponent_id, is_home)
    )
    stats = TEAM_ANALYTICS[team_id]
    rest = days_rest(team_id, source_match) if source_match else None
    rest_label = f"{rest} days" if rest is not None else "N/A"
    opponent_strength = strength_value(
        opponent_id,
        "strength_overall_away" if is_home else "strength_overall_home",
    )
    venue = "Home" if is_home else "Away"

    cards = [
        metric_card("Projected goals", fmt_float(projected_for, 2), "Baseline forecast"),
        metric_card("Projected xGA", fmt_float(projected_against, 2), "Opponent forecast"),
        metric_card("Clean sheet", fmt_pct(cs_prob), "Strength adjusted"),
        metric_card("Difficulty", fdr, run_label([{"difficulty": fdr}])),
    ]
    payload_rows = [
        ("team_id", team_id),
        ("opponent_id", opponent_id),
        ("venue", venue.lower()),
        ("opponent_strength", f"{opponent_strength:.0f}"),
        ("days_rest", rest_label),
        ("team_xg_per_match", fmt_float(stats["xg_per_match"], 3)),
        ("team_xa_per_match", fmt_float(stats["xa_per_match"], 3)),
        ("chance_score", fmt_float(stats["chance_score"], 1)),
        ("set_piece_score", fmt_float(stats["set_piece_score"], 1)),
        ("minute_reliability", fmt_float(stats["minute_reliability"], 3)),
    ]
    payload_html = "".join(
        f"<tr><td>{esc(key)}</td><td>{esc(value)}</td></tr>"
        for key, value in payload_rows
    )
    return f"""
    <div class="glass-panel">
        <div class="kicker">MODEL READY</div>
        <div class="panel-title">Team forecast sandbox</div>
        <div class="team-meta">{esc(team_name(team_id))} vs {esc(team_name(opponent_id))} | {venue}</div>
        <div class="metric-grid">{''.join(cards)}</div>
        <table class="small-table">
            <thead><tr><th>Feature</th><th>Value</th></tr></thead>
            <tbody>{payload_html}</tbody>
        </table>
    </div>
    """


st.markdown("### Teams")

preferred_names = ["Aston Villa", "Arsenal"]
alphabetical_names = [team.get("name") for team in teams]
name_options = [name for name in preferred_names if name in alphabetical_names]
name_options.extend(name for name in alphabetical_names if name not in preferred_names)

# Apply the requested default once, including already-open sessions. Subsequent
# selections remain under the user's control.
if not st.session_state.get("teams_villa_default_applied"):
    default_name = name_options[0]
    for key in ("teams_snapshot_select", "teams_compare_a", "teams_forecast_team"):
        st.session_state[key] = default_name
    st.session_state.pop("teams_compare_b", None)
    st.session_state["teams_villa_default_applied"] = True

left, right = st.columns(2, gap="medium")

with left:
    selected_name = st.selectbox("Team snapshot", name_options, key="teams_snapshot_select")
    selected_team_id = team_name_to_id[selected_name]
    st.markdown(clean_html(snapshot_html(selected_team_id)), unsafe_allow_html=True)

with right:
    st.markdown("**Team comparisons**")
    compare_left, compare_right = st.columns(2)
    with compare_left:
        compare_a_name = st.selectbox(
            "Compare team A",
            name_options,
            index=name_options.index(selected_name),
            key="teams_compare_a",
        )
    with compare_right:
        default_b_index = 1 if name_options.index(selected_name) != 1 else 0
        compare_b_name = st.selectbox(
            "Compare team B",
            name_options,
            index=default_b_index,
            key="teams_compare_b",
        )
    compare_a_id = team_name_to_id[compare_a_name]
    compare_b_id = team_name_to_id[compare_b_name]
    st.markdown(clean_html(comparison_html(compare_a_id, compare_b_id)), unsafe_allow_html=True)

# Continue each lower panel in its existing column. A separate `st.columns` row
# would align both panels below the taller snapshot, leaving a large gap above
# the Forecast panel.
squad_panel, form_panel = team_detail_panels(
    elements, fixtures, selected_team_id, team_lookup,
    {position["id"]: position for position in bootstrap_data.get("element_types", [])},
)

with left:
    st.markdown("<div class='column-section-gap'></div>", unsafe_allow_html=True)
    st.markdown(clean_html(prediction_inputs_html(selected_team_id)), unsafe_allow_html=True)
    st.markdown("<div class='column-section-gap'></div>", unsafe_allow_html=True)
    st.markdown(clean_html(squad_panel), unsafe_allow_html=True)

with right:
    st.markdown("<div class='column-section-gap'></div>", unsafe_allow_html=True)
    st.markdown("**Forecast**")
    forecast_team_name = st.selectbox(
        "Forecast team",
        name_options,
        index=name_options.index(selected_name),
        key="teams_forecast_team",
    )
    forecast_team_id = team_name_to_id[forecast_team_name]
    forecast_fixtures = upcoming_matches(forecast_team_id, 5)

    source_match = None
    if forecast_fixtures:
        fixture_labels = [fixture_option_label(match) for match in forecast_fixtures]
        fixture_labels.append("Manual opponent")
        fixture_choice = st.selectbox(
            "Forecast fixture",
            fixture_labels,
            key="teams_forecast_fixture",
        )
        if fixture_choice != "Manual opponent":
            source_match = forecast_fixtures[fixture_labels.index(fixture_choice)]

    if source_match:
        forecast_opponent_id = source_match["opponent_id"]
        forecast_is_home = source_match["is_home"]
    else:
        opponent_options = [
            team.get("name")
            for team in teams
            if team.get("id") != forecast_team_id
        ]
        forecast_opponent_name = st.selectbox(
            "Forecast opponent",
            opponent_options,
            key="teams_forecast_opponent",
        )
        forecast_opponent_id = team_name_to_id[forecast_opponent_name]
        forecast_is_home = (
            st.radio(
                "Venue",
                ["Home", "Away"],
                horizontal=True,
                key="teams_forecast_venue",
            )
            == "Home"
        )

    st.markdown(
        clean_html(
            forecast_html(
                forecast_team_id,
                forecast_opponent_id,
                forecast_is_home,
                source_match,
            )
        ),
        unsafe_allow_html=True,
    )
    st.markdown("<div class='column-section-gap'></div>", unsafe_allow_html=True)
    st.markdown(clean_html(form_panel), unsafe_allow_html=True)

st.html(TEAM_PANEL_ALIGNMENT_SCRIPT, unsafe_allow_javascript=True)
