import streamlit as st # type: ignore
import streamlit.components.v1 as components # type: ignore
import json
import urllib.request
import ssl
import certifi
from nav import render_top_nav
from player_images import photo_url

st.set_page_config(page_title="FPL Points", layout="wide")

is_guest = st.session_state.get("guest", False)
if "manager_id" not in st.session_state and not is_guest:
    st.warning("No manager ID found. Go back to Home and connect your team.")
    if st.button("Go to Dashboard"):
        st.switch_page("live_dashboard.py")
    st.stop()

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #37003c, #2b1e5b, #00cc6a) !important;
    min-height: 100vh;
}
.stMainBlockContainer {
    padding-top: 2.5rem !important;
    max-width: none !important;
    width: 100% !important;
    margin-left: auto !important;
    margin-right: auto !important;
}
div[data-testid="stHorizontalBlock"] {
    justify-content: center !important;
}
div[data-testid="stButton"] > button {
    background: rgba(255,255,255,0.12) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    border-radius: 12px !important;
    padding: 12px 40px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    width: 100% !important;
}
div[data-testid="stButton"] > button:hover {
    background: rgba(255,255,255,0.22) !important;
    color: white !important;
}
iframe { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

render_top_nav()

def build_player_map(bootstrap):
    team_codes = {t.get("id"): t.get("code", 0) for t in bootstrap.get("teams", [])}
    return {
        p.get("id"): {
            "name": f"{p.get('first_name', '')} {p.get('second_name', '')}".strip() or p.get("web_name") or "Unknown",
            "web_name": p.get("web_name"),
            "team_id": p.get("team"),
            "team_code": team_codes.get(p.get("team"), 0),
            "position": p.get("element_type"),
            "price": (p.get("now_cost", 0) or 0) / 10,
            "photo": photo_url(p),
            "photo_fallback": photo_url(p, legacy=True),
        }
        for p in bootstrap.get("elements", [])
        if p.get("id") is not None
    }

@st.cache_data(ttl=60)
def fetch_live_points(gw):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = f"https://fantasy.premierleague.com/api/event/{gw}/live/"
    with urllib.request.urlopen(url, context=ctx) as r:
        data = json.loads(r.read())
    return {e["id"]: e["stats"]["total_points"] for e in data["elements"]}

@st.cache_data(ttl=3600)
def fetch_fixtures(gw):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = f"https://fantasy.premierleague.com/api/fixtures/?event={gw}"
    with urllib.request.urlopen(url, context=ctx) as r:
        fixtures = json.loads(r.read())
    result = {}
    for f in fixtures:
        h, a = f["team_h"], f["team_a"]
        for team_id, opp_id, venue in [(h, a, "H"), (a, h, "A")]:
            entry = {"opp": opp_id, "venue": venue}
            if team_id in result:
                existing = result[team_id]
                if isinstance(existing, list):
                    existing.append(entry)
                else:
                    result[team_id] = [existing, entry]
            else:
                result[team_id] = entry
    return result

@st.cache_data(ttl=3600)
def fetch_teams(gw):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    with urllib.request.urlopen(url, context=ctx) as r:
        data = json.loads(r.read())
    return {t["id"]: t["short_name"] for t in data["teams"]}

@st.cache_data(ttl=60)
def fetch_gw_stats(gw):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    with urllib.request.urlopen(url, context=ctx) as r:
        bootstrap = json.loads(r.read())
    for event in bootstrap.get("events", []):
        if event["id"] == gw:
            avg = event.get("average_entry_score") or 0
            highest = event.get("highest_score") or event.get("top_element_info", {}).get("points") or 0
            return round(avg), highest
    return 0, 0

@st.cache_data(ttl=3600)
def fetch_bootstrap_static():
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    with urllib.request.urlopen(url, context=ctx) as r:
        return json.loads(r.read())

def current_gw_from_events(events):
    if not events:
        return 1
    current = next((e.get("id") for e in events if e.get("is_current")), None)
    if current:
        return current
    return max((e.get("id") or 1 for e in events), default=1)

bootstrap_static = fetch_bootstrap_static()

if is_guest:
    gw = current_gw_from_events(bootstrap_static.get("events", []))
    manager_id = None
    players = build_player_map(bootstrap_static)
    picks_data = {}
    picks = []
    history = {}
else:
    manager_id = st.session_state.manager_id
    gw = st.session_state.gw
    picks_data = st.session_state.picks
    picks = sorted(picks_data["picks"], key=lambda x: x["position"])
    players = st.session_state.players
    history = st.session_state.history

if is_guest:
    live_pts = {}
    avg_points = "Guest mode"
    highest_points = "Guest mode"
    fixtures = fetch_fixtures(gw)
    team_names = fetch_teams(gw)
    starters = []
    subs = []
    total_gw_points = "Guest mode"
else:
    live_pts = fetch_live_points(gw)
    avg_points, highest_points = fetch_gw_stats(gw)
    fixtures = fetch_fixtures(gw)
    team_names = fetch_teams(gw)
    starters = picks[:11]
    subs = picks[11:]
    total_gw_points = sum(
        live_pts.get(pick["element"], 0) * pick.get("multiplier", 1)
        for pick in starters
    )

avg_display = avg_points if is_guest else int(avg_points)
highest_display = highest_points if is_guest else int(highest_points)
gw_label = "Guest mode" if is_guest else f"Gameweek {gw}"

chips_data = []
active_chip = picks_data.get("active_chip")
if not active_chip:
    active_chip = next(
        (chip.get("name") for chip in history.get("chips", []) if chip.get("event") == gw),
        None,
    )
pitch_chip_class = " pitch-chip-active" if active_chip in {"wildcard", "freehit"} else ""
bench_chip_class = " bench-boost-active" if active_chip == "bboost" else ""
triple_captain_active = active_chip == "3xc"

chip_plays = {}
for chip_entry in history.get("chips", []) if history else []:
    chip_name = chip_entry["name"]
    chip_gw = chip_entry["event"]
    if chip_name not in chip_plays:
        chip_plays[chip_name] = []
    chip_plays[chip_name].append(chip_gw)

all_chips = [
    {"name": "bboost", "display": "Bench Boost"},
    {"name": "freehit", "display": "Free Hit"},
    {"name": "3xc",    "display": "Triple Captain"},
    {"name": "wildcard","display": "Wildcard"},
]

for chip in all_chips:
    chip_name    = chip["name"]
    display_name = chip["display"]
    gws_used     = sorted(chip_plays.get(chip_name, []))

    first_half  = [g for g in gws_used if g < 19]
    second_half = [g for g in gws_used if g >= 19]

    if chip_name == active_chip and gw < 19:
        first_text = "Playing this GameWeek"
    elif first_half:
        first_text = "Playing this GameWeek" if first_half[0] == gw else f"Played in GW {first_half[0]}"
    else:
        first_text = "Available"

    if chip_name == active_chip and gw >= 19:
        second_text = "Playing this GameWeek"
    elif second_half:
        second_text = "Playing this GameWeek" if second_half[0] == gw else f"Played in GW {second_half[0]}"
    else:
        second_text = "Available"

    status_text = f"First Half: <br>{first_text}<br>Second Half: <br>{second_text}"

    if gw < 19:
        if chip_name == active_chip or (first_half and gw in first_half):
            card_status = "active"
        elif first_half:
            card_status = "used"
        else:
            card_status = "available"
    else:
        if chip_name == active_chip or (second_half and gw in second_half):
            card_status = "active"
        elif second_half:
            card_status = "used"
        else:
            card_status = "available"

    chips_data.append({"name": display_name, "status": card_status, "status_text": status_text})

@st.cache_data(ttl=3600)
def fetch_entry_event_entry_history(entry_id, event_id):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = f"https://fantasy.premierleague.com/api/entry/{entry_id}/event/{event_id}/picks/"
    with urllib.request.urlopen(url, context=ctx) as r:
        data = json.loads(r.read())
    return data.get("entry_history", {}) or {}

avg_by_event = {
    e.get("id"): (e.get("average_entry_score") or 0)
    for e in bootstrap_static.get("events", [])
    if e.get("id") is not None
}

gw_labels = list(range(1, gw + 1)) if gw else []
pts_series = []
rank_series = []
if is_guest or not manager_id:
    pts_series = [None for _ in gw_labels]
    rank_series = [None for _ in gw_labels]
else:
    for event_id in gw_labels:
        try:
            eh = fetch_entry_event_entry_history(manager_id, event_id)
            pts_series.append(eh.get("points", eh.get("total_points", 0)) or 0)
            rank_series.append(eh.get("overall_rank", eh.get("rank", 0)) or 0)
        except Exception:
            pts_series.append(0)
            rank_series.append(0)

avg_series = [avg_by_event.get(event_id, 0) for event_id in gw_labels]

gw_labels_json  = json.dumps(gw_labels)
pts_series_json = json.dumps(pts_series)
avg_series_json = json.dumps(avg_series)
rank_series_json = json.dumps(rank_series)

rows = {1: [], 2: [], 3: [], 4: []}
if is_guest:
    rows[1] = [{"position": 1}]
    rows[2] = [{"position": 2} for _ in range(4)]
    rows[3] = [{"position": 3} for _ in range(4)]
    rows[4] = [{"position": 4} for _ in range(2)]
    subs = [{"position": 1}, {"position": 2}, {"position": 3}, {"position": 4}]
else:
    for pick in starters:
        pos = players[pick["element"]]["position"]
        rows[pos].append(pick)

def get_fixture_str(team_id):
    fix = fixtures.get(team_id)
    if not fix:
        return "—"
    if isinstance(fix, list):
        parts = []
        for f in fix:
            opp = team_names.get(f["opp"], "?")
            parts.append(f"{opp} ({f['venue']})")
        return " · ".join(parts)
    opp = team_names.get(fix["opp"], "?")
    return f"{opp} ({fix['venue']})"

POS_SHORT = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

FALLBACK_JERSEY = (
    "data:image/png;base64,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"
)

def player_card(pick, is_sub=False):
    pid = pick.get("element") if pick else None
    p = players.get(pid, {})
    name = p.get("web_name") or (p.get("name", "").split()[-1] if p.get("name") else "Guest mode")
    photo = p.get("photo") or FALLBACK_JERSEY
    photo_fallback = p.get("photo_fallback") or ""
    team_id = p.get("team_id")
    raw_pts = live_pts.get(pid, 0) if pid is not None else 0
    pts = raw_pts if is_sub else raw_pts * pick.get("multiplier", 1)
    fixture   = get_fixture_str(team_id)
    sub_class = " sub" if is_sub else ""
    cap_class = " captain-pick" if (not is_sub and pick.get("is_captain")) else ""
    triple_cap_class = (
        " triple-captain-pick"
        if (triple_captain_active and not is_sub and pick.get("is_captain"))
        else ""
    )
    pos_html  = ""
    if is_sub:
        lbl = POS_SHORT.get(p.get("position") or pick.get("position"), "")
        if lbl:
            pos_html = f'<div class="bench-pos">{lbl}</div>'

    if pick.get("is_captain"):
        badge = '<span class="badge captain">C</span>'
    elif pick.get("is_vice_captain"):
        badge = '<span class="badge vice">V</span>'
    else:
        badge = ""

    return f"""
    <div class="player-card{sub_class}{cap_class}{triple_cap_class}">
        {pos_html}
        {badge}
        <img class="player-img" src="{photo}" data-fallback="{photo_fallback}" onerror="if(this.dataset.fallback){{this.src=this.dataset.fallback;this.dataset.fallback='';}}else{{this.onerror=null;this.src='{FALLBACK_JERSEY}';}}">
        <div class="player-label">
            <div class="player-name">{name}</div>
            <div class="player-pts">{pts}</div>
            {"<div class='fixture-str'>" + fixture + "</div>" if fixture else ""}
        </div>
    </div>"""

pitch_rows = ""
for pos in [1, 2, 3, 4]:
    cards = "".join(player_card(p) for p in rows[pos])
    pitch_rows += f'<div class="pitch-row">{cards}</div>'

bench_cards = "".join(player_card(p, is_sub=True) for p in subs)

tick_step = max(1, len(gw_labels) // 10)

components.html(f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: transparent; font-family: sans-serif; padding: 16px; }}

.header-container {{ text-align: center; color: white; margin-bottom: 16px; }}
.gw-label {{ font-size: 18px; opacity: 0.9; }}

.points-row {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 40px;
    margin-bottom: 5px;
}}

.total-points {{ font-size: 70px; font-weight: 600; color: #00ff87; line-height: 1; }}

.side-points {{
    display: flex;
    flex-direction: column;
    align-items: center;
}}

.side-label {{
    font-size: 12px;
    opacity: 0.7;
    margin-bottom: 4px;
}}

.side-value {{
    font-size: 32px;
    font-weight: 600;
    color: rgba(255,255,255,0.8);
    line-height: 1;
}}

.main-container {{
    display: flex;
    gap: 20px;
    max-width: none;
    width: 100%;
    margin: 0 auto;
}}

.pitch-container {{ flex: 0 0 60%; }}
.right-column {{ flex: 0 0 38%; display: flex; flex-direction: column; gap: 16px; min-width: 0; }}
.chips-container {{ flex: 0 0 auto; }}
.graphs-container {{ flex: 0 0 auto; min-width: 0; }}

.big-glassbox {{
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 16px 16px 28px 16px;
    border: 1px solid rgba(255,255,255,0.15);
    overflow: visible;
    position: relative;
}}

/* ── Graph icon button ──────────────────────────── */
.graph-nav-btn {{
    position: absolute;
    top: 14px;
    right: -14px;
    width: 32px;
    height: 32px;
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s;
    padding: 0;
}}
.graph-nav-btn:hover {{ background: rgba(255,255,255,0.2); }}
.graph-nav-btn svg {{ width: 16px; height: 16px; }}

.chart-stack {{
    display: flex;
    flex-direction: column;
    gap: 35px;
    align-items: center;
}}

.chart-block {{
    height: 180px;
    display: flex;
    flex-direction: column;
    width: 100%;
}}

.chart-block canvas {{
    width: 100% !important;
    height: 100% !important;
}}

.chart-subtitle {{
    color: rgba(255,255,255,0.75);
    font-size: 12px;
    font-weight: 700;
    text-align: center;
    margin-bottom: -5px;
}}

.pitch {{
    flex: 1 1 auto;
    min-width: 0;
    width: 100%;
    background:
        repeating-linear-gradient(to bottom, rgba(0,0,0,0.06) 0px, rgba(0,0,0,0.06) 32px, transparent 32px, transparent 64px),
        linear-gradient(to bottom, #2ecc71, #27ae60);
    border-radius: 10px;
    padding: 14px 12px;
    border: 2px solid rgba(255,255,255,0.25);
    display: flex;
    flex-direction: column;
    gap: 12px;
    box-shadow: 0 16px 32px rgba(0,0,0,0.5);
    position: relative;
}}

.pitch.pitch-chip-active {{
    border-color: #f2c80c;
    box-shadow:
        inset 0 0 0 2px rgba(255, 239, 147, 0.78),
        0 0 22px rgba(242, 200, 12, 0.48),
        0 16px 32px rgba(0,0,0,0.5);
}}

.squad-layout {{
    display: flex;
    gap: 10px;
    align-items: stretch;
    width: 100%;
    flex: 1 1 auto;
    min-width: 0;
}}

.bench-side {{
    flex: 0 0 128px;
    width: 128px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 10px 8px;
    background: rgba(0,0,0,0.12);
    border-radius: 12px;
}}

.bench-side.bench-boost-active {{
    box-shadow:
        inset 0 0 0 2px #f2c80c,
        0 0 18px rgba(242, 200, 12, 0.42);
}}
.bench-side.bench-boost-active .bench-label {{ color: #ffe66d; }}

.pitch-markings {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }}
.pitch-row {{ display: flex; justify-content: center; gap: 16px; }}

.player-card {{
    position: relative;
    text-align: center;
    width: 102px;
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(10px);
    border-radius: 10px;
    padding: 18px 10px 10px 10px;
    border: 1px solid rgba(255,255,255,0.15);
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}}

.player-card.captain-pick {{
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(10px);
    border: 2px solid #f2c80c;
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}}

.player-card.triple-captain-pick {{
    box-shadow:
        0 0 10px rgba(255, 80, 155, 0.55),
        0 0 18px rgba(0, 229, 255, 0.42),
        0 4px 12px rgba(0,0,0,0.25);
}}
.player-card.triple-captain-pick::after {{
    content: "";
    position: absolute;
    inset: 4px;
    padding: 2px;
    border-radius: 6px;
    background: conic-gradient(
        from 90deg,
        #ff4d6d,
        #ffb703,
        #00e5ff,
        #9b5de5,
        #ff4d6d
    );
    -webkit-mask:
        linear-gradient(#000 0 0) content-box,
        linear-gradient(#000 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    filter: drop-shadow(0 0 3px rgba(255,255,255,0.75));
    pointer-events: none;
    z-index: 1;
    animation: triple-captain-glow 1.5s ease-in-out infinite alternate;
}}
.player-card.triple-captain-pick > * {{ position: relative; z-index: 2; }}

@keyframes triple-captain-glow {{
    from {{ opacity: 0.7; filter: drop-shadow(0 0 2px rgba(255,255,255,0.6)); }}
    to {{ opacity: 1; filter: drop-shadow(0 0 6px rgba(255,255,255,0.95)); }}
}}

@media (prefers-reduced-motion: reduce) {{
    .player-card.triple-captain-pick::after {{ animation: none; }}
}}

.player-img {{ width: 76px; height: 97px; object-fit: contain; filter: drop-shadow(0 3px 5px rgba(0,0,0,0.5)); mix-blend-mode: multiply; }}
.player-label {{ margin-top: 2px; }}

.player-name {{
    background: rgba(55, 0, 60, 0.92);
    color: white;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 5px;
    border-radius: 3px 3px 0 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    border: 1px solid rgba(255,255,255,0.15);
    border-bottom: none;
}}

.player-pts {{
    background: rgba(255,255,255,0.12);
    backdrop-filter: blur(8px);
    color: #fefefe;
    font-size: 12px;
    font-weight: 800;
    padding: 2px 5px;
    border-radius: 0 0 3px 3px;
    border: 1px solid rgba(255,255,255,0.15);
    border-top: none;
}}

.fixture-str {{ color: rgba(255,255,255,0.55); font-size: 7px; margin-top: 5px; }}

.badge {{
    position: absolute;
    top: 3px; left: 3px;
    width: 14px; height: 14px;
    border-radius: 50%;
    font-size: 8px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2;
}}
.badge.captain {{ background: #f2c80c; color: #000; }}
.badge.vice {{ background: rgba(255,255,255,0.85); color: #37003c; }}

.bench-label {{
    color: rgba(255,255,255,0.6);
    font-size: 9px;
    text-align: center;
    margin-bottom: 18px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}}
.bench {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    width: 100%;
}}
.sub {{
    opacity: 0.8;
    width: 108px;
    padding-top: 15px;
    padding-bottom: 15px;
}}
.sub .player-img {{ width: 56px; height: 71px; }}
.sub .player-name {{ font-size: 10px; }}
.sub .player-pts {{ font-size: 11px; }}

.bench-pos {{
    width: 100%;
    text-align: center;
    color: #00ff87;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.6px;
    margin-bottom: 12px;
}}

.chips-title {{ color: white; font-size: 18px; font-weight: 700; margin-bottom: 12px; text-align: center; }}

.chips-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}}

.chip-card {{
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 14px 18px;
    border: 1px solid rgba(255,255,255,0.15);
    min-height: 100px;
}}

.chip-card.used {{ background: rgba(246, 70, 70, 0.25); border-color: rgba(225, 6, 6, 0.932); }}
.chip-card.active {{ background: rgba(242,200,12,0.25); border-color: rgba(242,200,12,0.5); }}
.chip-card.available {{ background: rgba(0,255,135,0.15); border-color: rgba(0,255,135,0.3); }}

.chip-name {{ color: white; font-size: 15px; font-weight: 700; margin-bottom: 6px; }}
.chip-status {{ color: rgba(255,255,255,0.7); font-size: 11px; line-height: 1.5; }}

.chip-card.used .chip-status {{ color: rgba(225, 6, 6, 0.932); }}
.chip-card.active .chip-status {{ color: #f2c80c; }}
.chip-card.available .chip-status {{ color: #00ff87; }}

/* graphs section title row */
.graphs-title-row {{
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    margin-bottom: 16px;
}}
.graphs-section-title {{
    color: white;
    font-size: 18px;
    font-weight: 700;
    text-align: center;
}}
</style>
</head>
<body>
<div class="header-container">
    <div class="gw-label">Your Team</div>
    <div class="gw-label">{gw_label}</div>
    <div class="points-row">
        <div class="side-points">
            <div class="side-label">Average</div>
            <div class="side-value">{avg_display}</div>
        </div>
        <div class="total-points">{total_gw_points}</div>
        <div class="side-points">
            <div class="side-label">Highest</div>
            <div class="side-value">{highest_display}</div>
        </div>
    </div>
</div>

<div class="main-container">
    <div class="pitch-container">
        <div class="big-glassbox">
            <div class="squad-layout">
                <div class="bench-side{bench_chip_class}">
                    <div class="bench-label">Bench</div>
                    <div class="bench">{bench_cards}</div>
                </div>
                <div class="pitch{pitch_chip_class}">
                    <svg class="pitch-markings" viewBox="0 0 100 108" preserveAspectRatio="xMidYMid meet">
                        <line x1="0" y1="-2" x2="100" y2="-2" stroke="rgba(255,255,255,0.4)" stroke-width="0.35"/>
                        <line x1="30" y1="14" x2="70" y2="14" stroke="rgba(255,255,255,0.4)" stroke-width="0.35"/>
                        <line x1="30" y1="-2" x2="30" y2="14" stroke="rgba(255,255,255,0.4)" stroke-width="0.35"/>
                        <line x1="70" y1="-2" x2="70" y2="14" stroke="rgba(255,255,255,0.4)" stroke-width="0.35"/>
                        <path d="M 18 133 A 32 32 0 0 1 82 133" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="0.35"/>
                    </svg>
                    {pitch_rows}
                </div>
            </div>
        </div>
    </div>

    <div class="right-column">
        <div class="chips-container">
            <div class="big-glassbox">
                <div class="chips-title">Chips</div>
                <div class="chips-grid">
                {''.join(f'''
                <div class="chip-card {chip['status']}">
                    <div class="chip-name">{chip['name']}</div>
                    <div class="chip-status">{chip['status_text']}</div>
                </div>''' for chip in chips_data)}
                </div>
            </div>
        </div>

        <div class="graphs-container">
            <div class="big-glassbox">
                <div class="graphs-title-row">
                    <span class="graphs-section-title">Season Stats</span>
                </div>

                <div class="chart-stack">
                    <div class="chart-block">
                        <div class="chart-subtitle">Points &amp; Avg vs GW</div>
                        <canvas id="pointsChart"></canvas>
                    </div>
                    <div class="chart-block">
                        <div class="chart-subtitle">Worldwide Rank vs GW</div>
                        <canvas id="rankChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
const gwLabels   = {gw_labels_json};
const pts        = {pts_series_json};
const avgPts     = {avg_series_json};
const ranks      = {rank_series_json};
const tickStep   = {tick_step};

// ── shared axis options ───────────────────────────────────────────────────
const xAxisOpts = {{
    ticks: {{
        color: 'rgba(255,255,255,0.7)',
        maxRotation: 0,
        minRotation: 0,
        autoSkip: true,
        maxTicksLimit: 10,
        callback: function(val, idx) {{
            return gwLabels[idx];
        }}
    }},
    grid: {{ color: 'rgba(255,255,255,0.08)' }}
}};

new Chart(document.getElementById('pointsChart').getContext('2d'), {{
    type: 'line',
    data: {{
        labels: gwLabels,
        datasets: [
            {{
                label: 'My Pts',
                data: pts,
                borderColor: '#00ff87',
                backgroundColor: 'rgba(0,255,135,0.15)',
                tension: 0.3,
                fill: false,
                pointRadius: 3
            }},
            {{
                label: 'GW Avg',
                data: avgPts,
                borderColor: '#ffb500',
                backgroundColor: 'rgba(255,181,0,0.15)',
                tension: 0.3,
                fill: false,
                pointRadius: 3
            }}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
            legend: {{ labels: {{ color: 'rgba(255,255,255,0.9)', boxWidth: 12, font: {{ size: 11 }} }} }}
        }},
        scales: {{
            x: xAxisOpts,
            y: {{
                ticks: {{ color: 'rgba(255,255,255,0.7)' }},
                grid: {{ color: 'rgba(255,255,255,0.08)' }}
            }}
        }}
    }}
}});

new Chart(document.getElementById('rankChart').getContext('2d'), {{
    type: 'line',
    data: {{
        labels: gwLabels,
        datasets: [{{
            label: 'World Rank',
            data: ranks,
            borderColor: '#00ff87',
            backgroundColor: 'rgba(0,255,135,0.15)',
            tension: 0.3,
            fill: false,
            pointRadius: 3
        }}]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
            legend: {{ labels: {{ color: 'rgba(255,255,255,0.9)', boxWidth: 12, font: {{ size: 11 }} }} }}
        }},
        scales: {{
            x: xAxisOpts,
            y: {{
                min: 1,
                reverse: false,
                ticks: {{ color: 'rgba(255,255,255,0.7)' }},
                grid: {{ color: 'rgba(255,255,255,0.08)' }}
            }}
        }}
    }}
}});

</script>
</body>
</html>
""", height=1000, scrolling=False)

_, col1, spacer, col2, _ = st.columns([2.3, 3, 2.5, 3, 0.8])

with col1:
    if st.button("← Back", use_container_width=True):
        st.switch_page("pages/home.py")
with col2:
    if st.button("Graphs →", use_container_width=True):
        st.switch_page("pages/graphs.py")
