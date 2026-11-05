import json
import ssl
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import certifi
import streamlit as st  # type: ignore
from nav import render_top_nav
from player_images import player_image


st.set_page_config(page_title="FPL Players", layout="wide")

is_guest = st.session_state.get("guest", False)
if "manager_id" not in st.session_state and not is_guest:
    st.warning("No manager ID found. Go back to Dashboard and connect your team.")
    if st.button("Go to Dashboard"):
        st.switch_page("live_dashboard.py")
    st.stop()


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

h1, h2, h3, p, span, li, label {
    color: white !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.20) !important;
    border-radius: 18px !important;
    box-shadow: 0 14px 34px rgba(0,0,0,0.28) !important;
}

div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.10) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    border-radius: 12px !important;
    padding: 10px !important;
}

div[data-testid="stMetric"] label,
div[data-testid="stMetric"] div {
    color: white !important;
}

div[data-baseweb="select"] > div,
div[role="radiogroup"] label {
    background: rgba(255,255,255,0.12) !important;
    border-color: rgba(255,255,255,0.25) !important;
    color: white !important;
}

div[data-testid="stSlider"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stRadio"] label {
    color: rgba(255,255,255,0.86) !important;
    font-weight: 800 !important;
}
</style>
""",
    unsafe_allow_html=True,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
LOCAL_BOOTSTRAP_PATH = ROOT_DIR / "data" / "raw" / "bootstrap_static.json"
LOCAL_FIXTURES_PATH = ROOT_DIR / "data" / "raw" / "fixtures.json"
BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
FIXTURES_URL = "https://fantasy.premierleague.com/api/fixtures/"
SUMMARY_URL = "https://fantasy.premierleague.com/api/element-summary/{element_id}/"


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


def parse_dt(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_local_json(path, fallback):
    if not path.exists():
        return fallback
    try:
        with path.open() as f:
            return json.load(f)
    except Exception:
        return fallback


def fetch_json(url):
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, context=ctx, timeout=8) as response:
        return json.loads(response.read())


@st.cache_data(ttl=900, show_spinner=False)
def fetch_bootstrap_data():
    try:
        return fetch_json(BOOTSTRAP_URL)
    except Exception:
        return load_local_json(LOCAL_BOOTSTRAP_PATH, {})


@st.cache_data(ttl=900, show_spinner=False)
def fetch_fixtures_data():
    try:
        return fetch_json(FIXTURES_URL)
    except Exception:
        return load_local_json(LOCAL_FIXTURES_PATH, [])


@st.cache_data(ttl=900, show_spinner=False)
def fetch_player_summary(element_id):
    try:
        return fetch_json(SUMMARY_URL.format(element_id=element_id))
    except Exception:
        return {"fixtures": [], "history": [], "history_past": []}


def current_event_from_events(events):
    for flag in ("is_current", "is_next", "is_previous"):
        event = next((e for e in events if e.get(flag)), None)
        if event:
            return to_int(event.get("id"), 1)
    return 1


def full_name(player):
    name = f"{player.get('first_name') or ''} {player.get('second_name') or ''}".strip()
    return name or player.get("web_name") or f"Player {player.get('id')}"


def position_short(player, element_type_map):
    meta = element_type_map.get(player.get("element_type"), {})
    return meta.get("singular_name_short") or meta.get("singular_name") or "UNK"


def display_name(player, team_map, element_type_map):
    team = team_map.get(player.get("team"), {})
    return (
        f"{player.get('web_name') or full_name(player)} - "
        f"{team.get('short_name', 'UNK')} - {position_short(player, element_type_map)}"
    )


def normalize_player_id(player_id, player_by_id):
    if player_id in (None, 0, "0", "None"):
        return 0
    normalized = to_int(player_id, 0)
    return normalized if normalized in player_by_id else 0


def player_option_label(player_id, player_by_id, team_map, element_type_map, none_label=None):
    normalized = normalize_player_id(player_id, player_by_id)
    if normalized == 0:
        return none_label or str(player_id)
    return display_name(player_by_id[normalized], team_map, element_type_map)


def cost(player):
    return to_float(player.get("now_cost")) / 10


def xgi(player):
    return to_float(player.get("expected_goal_involvements"))


def points_per_90(player):
    minutes = to_float(player.get("minutes"))
    if minutes <= 0:
        return 0.0
    return to_float(player.get("total_points")) / minutes * 90


def value_score(player):
    player_cost = cost(player)
    if player_cost <= 0:
        return 0.0
    return to_float(player.get("total_points")) / player_cost


def status_label(player):
    labels = {
        "a": "Available",
        "d": "Doubtful",
        "i": "Injured",
        "n": "Unavailable",
        "s": "Suspended",
        "u": "Unavailable",
    }
    base = labels.get(player.get("status"), "Unknown")
    chance = player.get("chance_of_playing_next_round")
    if chance is not None and player.get("status") != "a":
        return f"{base} ({chance}%)"
    return base


def latest_history_entry(history):
    if not history:
        return None
    return max(
        history,
        key=lambda row: (
            to_int(row.get("round")),
            parse_dt(row.get("kickoff_time")) or datetime.min.replace(tzinfo=timezone.utc),
        ),
    )


def latest_match_label(entry, team_map):
    if not entry:
        return "No current-season match history yet."

    opponent = team_map.get(entry.get("opponent_team"), {})
    side = "H" if entry.get("was_home") else "A"
    return (
        f"Latest: GW{to_int(entry.get('round'))} vs {opponent.get('short_name', 'UNK')} "
        f"({side}) - {to_int(entry.get('total_points'))} pts, "
        f"{to_int(entry.get('minutes'))} min, "
        f"xGI {to_float(entry.get('expected_goal_involvements')):.2f}"
    )


def recent_history(history, count=5):
    return sorted(
        history,
        key=lambda row: (
            to_int(row.get("round")),
            parse_dt(row.get("kickoff_time")) or datetime.min.replace(tzinfo=timezone.utc),
        ),
    )[-count:]


def rolling_xgi(history, count=5):
    return sum(to_float(row.get("expected_goal_involvements")) for row in recent_history(history, count))


def percentile_rank(players, value_getter, value):
    values = sorted(value_getter(player) for player in players)
    if not values:
        return 0
    below = sum(1 for existing_value in values if existing_value <= value)
    return round(below / len(values) * 100)


def next_fixtures_for_team(team_id, fixtures, team_map, count=5):
    upcoming = []
    for fixture in fixtures:
        if fixture.get("finished"):
            continue
        if team_id not in (fixture.get("team_h"), fixture.get("team_a")):
            continue

        is_home = fixture.get("team_h") == team_id
        opponent_id = fixture.get("team_a") if is_home else fixture.get("team_h")
        opponent = team_map.get(opponent_id, {})
        difficulty = fixture.get("team_h_difficulty" if is_home else "team_a_difficulty")
        upcoming.append(
            {
                "event": to_int(fixture.get("event")),
                "kickoff": parse_dt(fixture.get("kickoff_time")),
                "opponent": opponent.get("short_name", "UNK"),
                "venue": "H" if is_home else "A",
                "difficulty": to_int(difficulty, 3),
            }
        )

    upcoming.sort(key=lambda fx: (fx["event"], fx["kickoff"] or datetime.max.replace(tzinfo=timezone.utc)))
    return upcoming[:count]


def fixture_summary(fixtures):
    if not fixtures:
        return "No upcoming fixtures"
    return ", ".join(
        f"GW{fixture['event']} {fixture['opponent']} ({fixture['venue']}, FDR {fixture['difficulty']})"
        for fixture in fixtures
    )


def value_rows(players, team_map, element_type_map):
    rows = []
    for player in players:
        team = team_map.get(player.get("team"), {})
        rows.append(
            {
                "Player": player.get("web_name") or full_name(player),
                "Team": team.get("short_name", "UNK"),
                "Pos": position_short(player, element_type_map),
                "Price": f"£{cost(player):.1f}",
                "Pts": to_int(player.get("total_points")),
                "Form": f"{to_float(player.get('form')):.1f}",
                "Value": f"{value_score(player):.1f}",
            }
        )
    return rows


def comparison_metric_rows(players):
    metric_specs = [
        ("Total points", lambda p: to_float(p.get("total_points")), "{:.0f}"),
        ("Form", lambda p: to_float(p.get("form")), "{:.1f}"),
        ("Minutes", lambda p: to_float(p.get("minutes")), "{:.0f}"),
        ("Starts", lambda p: to_float(p.get("starts")), "{:.0f}"),
        ("Pts/90", points_per_90, "{:.2f}"),
        ("xG", lambda p: to_float(p.get("expected_goals")), "{:.2f}"),
        ("xA", lambda p: to_float(p.get("expected_assists")), "{:.2f}"),
        ("xGI", xgi, "{:.2f}"),
        ("xGI/90", lambda p: to_float(p.get("expected_goal_involvements_per_90")), "{:.2f}"),
        ("Threat", lambda p: to_float(p.get("threat")), "{:.1f}"),
        ("Creativity", lambda p: to_float(p.get("creativity")), "{:.1f}"),
        ("ICT index", lambda p: to_float(p.get("ict_index")), "{:.1f}"),
        ("Ownership", lambda p: to_float(p.get("selected_by_percent")), "{:.1f}%"),
        ("Value", value_score, "{:.1f}"),
    ]

    rows = []
    for label, getter, formatter in metric_specs:
        row = {"Metric": label}
        for player in players:
            row[player.get("web_name") or full_name(player)] = formatter.format(getter(player))
        rows.append(row)
    return rows


def model_rows(players, team_map, element_type_map, fixtures, current_event):
    rows = []
    minutes_denominator = max(1, to_int(current_event, 1)) * 90
    for player in players:
        team = team_map.get(player.get("team"), {})
        future = next_fixtures_for_team(player.get("team"), fixtures, team_map, count=3)
        minutes_share = min(100, to_float(player.get("minutes")) / minutes_denominator * 100)
        rows.append(
            {
                "Player": player.get("web_name") or full_name(player),
                "Team": team.get("short_name", "UNK"),
                "Pos": position_short(player, element_type_map),
                "Form": f"{to_float(player.get('form')):.1f}",
                "xGI/90": f"{to_float(player.get('expected_goal_involvements_per_90')):.2f}",
                "Pts/90": f"{points_per_90(player):.2f}",
                "Min Share": f"{minutes_share:.0f}%",
                "Own": f"{to_float(player.get('selected_by_percent')):.1f}%",
                "Next": fixture_summary(future),
            }
        )
    return rows


def render_recent_form(history):
    rows = []
    for row in recent_history(history):
        rows.append(
            {
                "GW": f"GW{to_int(row.get('round'))}",
                "Points": to_int(row.get("total_points")),
                "Minutes": to_int(row.get("minutes")),
                "xGI": f"{to_float(row.get('expected_goal_involvements')):.2f}",
            }
        )

    if rows:
        st.dataframe(rows, hide_index=True, width='stretch')
    else:
        st.caption("No recent gameweek data available.")


def render_radar(player, peers, history):
    metrics = [
        ("Form", to_float(player.get("form")), lambda p: to_float(p.get("form"))),
        ("Pts/90", points_per_90(player), points_per_90),
        (
            "xGI/90",
            to_float(player.get("expected_goal_involvements_per_90")),
            lambda p: to_float(p.get("expected_goal_involvements_per_90")),
        ),
        ("Minutes", to_float(player.get("minutes")), lambda p: to_float(p.get("minutes"))),
        ("Threat", to_float(player.get("threat")), lambda p: to_float(p.get("threat"))),
        ("Last 5 xGI", rolling_xgi(history), xgi),
    ]

    st.subheader("Player Radar")
    st.caption("Position percentile snapshot")
    for label, value, getter in metrics:
        rank = percentile_rank(peers, getter, value)
        st.progress(rank / 100, text=f"{label}: {rank} percentile")


render_top_nav()

bootstrap_data = fetch_bootstrap_data()
fixtures = fetch_fixtures_data()
teams = bootstrap_data.get("teams", [])
elements = bootstrap_data.get("elements", [])
element_types = bootstrap_data.get("element_types", [])

if not teams or not elements:
    st.error("No player data was found in the FPL bootstrap data.")
    st.stop()

team_map = {team.get("id"): team for team in teams}
element_type_map = {element_type.get("id"): element_type for element_type in element_types}
current_event = st.session_state.get("gw") or current_event_from_events(bootstrap_data.get("events", []))
players = sorted(
    [player for player in elements if not player.get("removed")],
    key=lambda p: (p.get("web_name") or full_name(p)).lower(),
)
player_by_id = {player.get("id"): player for player in players}
player_ids = [player.get("id") for player in players if player.get("id") is not None]
default_profile = max(players, key=lambda p: to_float(p.get("total_points")))

st.title("Players")

selected_profile_id = st.selectbox(
    "Latest player profile",
    player_ids,
    index=player_ids.index(default_profile.get("id")),
    format_func=lambda player_id: player_option_label(player_id, player_by_id, team_map, element_type_map),
)
profile_id = normalize_player_id(selected_profile_id, player_by_id) or default_profile.get("id")
profile = player_by_id[profile_id]
profile_team = team_map.get(profile.get("team"), {})
summary = fetch_player_summary(profile_id)
history = summary.get("history", []) or []
latest_entry = latest_history_entry(history)
recent_xgi = rolling_xgi(history)
news = profile.get("news") or latest_match_label(latest_entry, team_map)

with st.container(border=True):
    profile_left, profile_right = st.columns([1.35, 1], gap="large")

    with profile_left:
        image_col, text_col = st.columns([0.25, 0.75], vertical_alignment="center")
        with image_col:
            st.image(player_image(profile), width=110)
        with text_col:
            st.caption("LATEST PLAYER PROFILE")
            st.header(full_name(profile))
            st.write(
                f"{profile_team.get('name', 'Unknown')} - "
                f"{position_short(profile, element_type_map)} - "
                f"£{cost(profile):.1f} - {status_label(profile)}"
            )
            st.caption(news)

        metric_cols = st.columns(4)
        metric_cols[0].metric("Form", f"{to_float(profile.get('form')):.1f}")
        metric_cols[1].metric("Total Points", f"{to_int(profile.get('total_points'))}")
        metric_cols[2].metric("Pts/90", f"{points_per_90(profile):.2f}")
        metric_cols[3].metric("xGI", f"{xgi(profile):.2f}")

        metric_cols = st.columns(4)
        metric_cols[0].metric("Last 5 xGI", f"{recent_xgi:.2f}")
        metric_cols[1].metric("Minutes", f"{to_int(profile.get('minutes'))}")
        metric_cols[2].metric("Ownership", f"{to_float(profile.get('selected_by_percent')):.1f}%")
        metric_cols[3].metric("Value", f"{value_score(profile):.1f}")

    with profile_right:
        st.subheader("Recent Minutes & Output")
        render_recent_form(history)

st.write("")

radar_col, value_col = st.columns([1.05, 0.95], gap="large")

with radar_col:
    with st.container(border=True):
        peers = [
            player
            for player in players
            if player.get("element_type") == profile.get("element_type")
            and to_float(player.get("minutes")) >= 450
        ]
        render_radar(profile, peers or players, history)

with value_col:
    with st.container(border=True):
        st.subheader("Value Picks")
        st.caption("Price-to-output comparison")

        position_options = ["All"] + [
            element_type.get("singular_name_short") or element_type.get("singular_name")
            for element_type in sorted(element_types, key=lambda e: to_int(e.get("id")))
        ]
        position_filter = st.radio("Position", position_options, horizontal=True)
        max_price = st.slider("Max price", min_value=3.5, max_value=15.0, value=15.0, step=0.1)
        max_minutes = max(3420, max(to_int(player.get("minutes")) for player in players))
        min_minutes = st.slider("Minimum minutes", min_value=0, max_value=max_minutes, value=450, step=90)

        value_players = [
            player
            for player in players
            if cost(player) <= max_price
            and to_float(player.get("minutes")) >= min_minutes
            and (
                position_filter == "All"
                or position_short(player, element_type_map) == position_filter
            )
        ]
        value_players.sort(key=value_score, reverse=True)
        st.dataframe(value_rows(value_players[:8], team_map, element_type_map), hide_index=True, width='stretch')

st.write("")

with st.container(border=True):
    st.subheader("Player Comparison")
    st.caption("Choose up to three players for xG, xA, threat, ownership, and minutes-adjusted output.")

    top_comparison_pool = sorted(players, key=lambda p: to_float(p.get("total_points")), reverse=True)
    comparison_defaults = [profile_id]
    for player in top_comparison_pool:
        player_id = player.get("id")
        if player_id not in comparison_defaults:
            comparison_defaults.append(player_id)
        if len(comparison_defaults) == 3:
            break

    selector_cols = st.columns(3, gap="large")
    select_options = [0] + player_ids
    selected_comparison_ids = []
    raw_comparison_ids = []
    for idx, col in enumerate(selector_cols):
        default_id = comparison_defaults[idx] if idx < len(comparison_defaults) else 0
        with col:
            selected_id = st.selectbox(
                f"Player {idx + 1}",
                select_options,
                index=select_options.index(default_id),
                format_func=lambda player_id: player_option_label(
                    player_id,
                    player_by_id,
                    team_map,
                    element_type_map,
                    none_label="None",
                ),
                key=f"comparison_player_{idx + 1}",
            )
        normalized_selected_id = normalize_player_id(selected_id, player_by_id)
        raw_comparison_ids.append(normalized_selected_id)
        if normalized_selected_id and normalized_selected_id not in selected_comparison_ids:
            selected_comparison_ids.append(normalized_selected_id)

    comparison_players = [player_by_id[player_id] for player_id in selected_comparison_ids]
    if len(selected_comparison_ids) < len([player_id for player_id in raw_comparison_ids if player_id]):
        st.warning("Duplicate comparison selections are shown once.")

    if comparison_players:
        card_cols = st.columns(len(comparison_players), gap="large")
        for col, player in zip(card_cols, comparison_players):
            team = team_map.get(player.get("team"), {})
            with col:
                st.image(player_image(player), width=80)
                st.metric(player.get("web_name") or full_name(player), f"{to_int(player.get('total_points'))} pts")
                st.caption(
                    f"{team.get('short_name', 'UNK')} - "
                    f"{position_short(player, element_type_map)} - "
                    f"£{cost(player):.1f}"
                )

        st.dataframe(comparison_metric_rows(comparison_players), hide_index=True, width='stretch')
    else:
        st.info("Select at least one player to compare.")

st.write("")

with st.container(border=True):
    st.subheader("Model Inputs")
    st.caption("Current features for next 3-5 gameweek scoring experiments.")

    model_players = []
    for player in [profile] + comparison_players:
        if player.get("id") not in [existing.get("id") for existing in model_players]:
            model_players.append(player)

    st.dataframe(
        model_rows(model_players, team_map, element_type_map, fixtures, current_event),
        hide_index=True,
        width='stretch',
    )
