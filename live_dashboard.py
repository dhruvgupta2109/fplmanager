import streamlit as st # type: ignore
import json
import urllib.request
import ssl
import certifi
from player_images import photo_url

st.set_page_config(
    page_title="FPL Manager",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def fetch(url):
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, context=ctx) as r:
        return json.loads(r.read())

def load_bootstrap():
    return fetch("https://fantasy.premierleague.com/api/bootstrap-static/")

def get_current_gw(bootstrap):
    for e in bootstrap["events"]:
        if e["is_current"]:
            return e["id"]
    return None

def build_player_map(bootstrap):
    team_codes = {t["id"]: t["code"] for t in bootstrap["teams"]}
    return {
        p["id"]: {
            "name": f"{p['first_name']} {p['second_name']}",
            "web_name": p["web_name"],
            "team_id": p["team"],
            "team_code": team_codes.get(p["team"], 0),
            "position": p["element_type"],
            "price": p["now_cost"] / 10,
            "photo": photo_url(p),
            "photo_fallback": photo_url(p, legacy=True),
        }
        for p in bootstrap["elements"]
    }

st.markdown("""
<style>
:root {
    --ink: #16051d;
    --plum: #37003c;
    --violet: #5b2b82;
    --green: #00ff87;
    --green-deep: #00c96b;
    --paper: #ebe4f0;
    --muted: #756b7b;
}

.stApp {
    background:
        radial-gradient(circle at 14% 18%, rgba(178, 76, 255, 0.32), transparent 28rem),
        radial-gradient(circle at 88% 82%, rgba(0, 255, 135, 0.24), transparent 30rem),
        linear-gradient(135deg, #220028 0%, #30134d 48%, #073f38 100%);
    min-height: 100vh;
    color: var(--ink);
}

.stApp::before,
.stApp::after {
    content: "";
    position: fixed;
    pointer-events: none;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 999px;
    transform: rotate(-18deg);
}

.stApp::before {
    width: 32rem;
    height: 11rem;
    top: 5rem;
    right: -10rem;
}

.stApp::after {
    width: 28rem;
    height: 9rem;
    bottom: -2rem;
    left: -9rem;
}

header[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"],
[data-testid="collapsedControl"] {
    display: none;
}

.stMainBlockContainer {
    max-width: 1240px !important;
    padding: clamp(2.5rem, 7vh, 6rem) 2rem 2.5rem !important;
}

.st-key-login_shell {
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.20);
    border-radius: 28px;
    background: rgba(255,255,255,0.96);
    box-shadow: 0 30px 80px rgba(9, 0, 20, 0.42);
}

.st-key-login_shell > div[data-testid="stVerticalBlock"] {
    gap: 0 !important;
}

.st-key-login_shell div[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
    align-items: stretch !important;
}

.st-key-login_shell div[data-testid="column"] {
    padding: 0 !important;
}

.st-key-login_shell div[data-testid="column"]:has(.login-hero),
.st-key-login_shell div[data-testid="column"]:has(.login-hero) > div[data-testid="stVerticalBlock"],
.st-key-login_shell div[data-testid="column"]:has(.login-hero) div[data-testid="stElementContainer"],
.st-key-login_shell div[data-testid="column"]:has(.login-hero) div[data-testid="stMarkdownContainer"] {
    height: 100%;
}

.login-hero {
    position: relative;
    display: flex;
    height: 100%;
    min-height: 700px;
    box-sizing: border-box;
    flex-direction: column;
    justify-content: space-between;
    overflow: hidden;
    padding: clamp(2.2rem, 4vw, 4rem);
    background:
        radial-gradient(circle at 95% 5%, rgba(0,255,135,0.24), transparent 15rem),
        linear-gradient(150deg, #25002b 0%, #42004a 62%, #591153 100%);
    color: white;
}

.login-hero::after {
    content: "";
    position: absolute;
    width: 19rem;
    height: 19rem;
    right: -10rem;
    bottom: -9rem;
    border: 4rem solid rgba(255,255,255,0.045);
    border-radius: 50%;
}

.login-hero h1 {
    max-width: none;
    margin: 0;
    color: white;
    font-size: clamp(2.55rem, 4.2vw, 4.6rem);
    font-weight: 900;
    letter-spacing: -0.055em;
    line-height: 0.98;
}

.login-hero h1 span {
    color: var(--green);
}

.headline-nowrap {
    display: inline-block;
    white-space: nowrap !important;
    word-break: keep-all !important;
    overflow-wrap: normal !important;
}

.hero-copy {
    max-width: 31rem;
    margin: 1.35rem 0 0;
    color: rgba(255,255,255,0.72);
    font-size: 1.03rem;
    line-height: 1.65;
}

.hero-copy + .hero-copy {
    margin-top: 0.8rem;
}

.feature-row {
    position: relative;
    z-index: 1;
    display: flex;
    flex-wrap: wrap;
    gap: 0.7rem;
    margin-top: 2.8rem;
}

.feature-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.48rem;
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 999px;
    padding: 0.56rem 0.78rem;
    background: rgba(255,255,255,0.08);
    color: rgba(255,255,255,0.86);
    font-size: 0.76rem;
    font-weight: 700;
}

.feature-pill::before {
    content: "";
    width: 0.42rem;
    height: 0.42rem;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 0 4px rgba(0,255,135,0.10);
}

.form-intro {
    margin-bottom: 1.55rem;
}

.form-intro h2 {
    margin: 0 0 0.55rem;
    color: #ffffff;
    font-size: clamp(1.7rem, 2.4vw, 2.15rem);
    font-weight: 850;
    letter-spacing: -0.035em;
}

.form-intro p {
    margin: 0;
    color: rgba(255,255,255,0.62);
    font-size: 0.94rem;
    line-height: 1.55;
}

.st-key-login_form_panel {
    display: flex;
    min-height: 700px;
    box-sizing: border-box;
    justify-content: center;
    padding: clamp(2.2rem, 4vw, 4rem) clamp(2rem, 4vw, 3.6rem);
    background:
        radial-gradient(circle at 100% 0%, rgba(119,45,130,0.24), transparent 20rem),
        linear-gradient(155deg, #251a31 0%, #17151f 100%);
}

.st-key-login_form_panel > div[data-testid="stVerticalBlock"] {
    justify-content: center;
    gap: 0.8rem !important;
}

.st-key-connect_form {
    border: 0 !important;
}

.st-key-connect_form > div {
    padding: 0 !important;
}

.st-key-connect_form div[data-testid="stVerticalBlock"] {
    gap: 0.65rem !important;
}

.st-key-manager_id_input label p {
    color: rgba(255,255,255,0.88) !important;
    font-size: 0.83rem !important;
    font-weight: 800 !important;
}

.st-key-manager_id_input [data-baseweb="input"] {
    min-height: 3.3rem;
    border: 1px solid rgba(255,255,255,0.16) !important;
    border-radius: 13px !important;
    background: rgba(7,5,12,0.52) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
    transition: border-color 160ms ease, box-shadow 160ms ease;
}

.st-key-manager_id_input [data-baseweb="input"]:focus-within {
    border-color: rgba(0,255,135,0.65) !important;
    box-shadow: 0 0 0 4px rgba(0,255,135,0.10) !important;
}

.st-key-manager_id_input input {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    caret-color: var(--green);
    font-size: 0.94rem !important;
}

.st-key-manager_id_input input::placeholder {
    color: rgba(255,255,255,0.58) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.58) !important;
    opacity: 1 !important;
}

.st-key-connect_button button {
    min-height: 3.3rem;
    margin-top: 0.25rem;
    border: 0 !important;
    border-radius: 13px !important;
    background: linear-gradient(135deg, var(--green), #36f29a) !important;
    color: #16051d !important;
    font-size: 0.92rem !important;
    font-weight: 850 !important;
    box-shadow: 0 10px 24px rgba(0,201,107,0.22) !important;
    transition: transform 160ms ease, box-shadow 160ms ease, filter 160ms ease;
}

.st-key-connect_button button:hover {
    border: 0 !important;
    color: #16051d !important;
    filter: brightness(1.02);
    transform: translateY(-2px);
    box-shadow: 0 14px 28px rgba(0,201,107,0.28) !important;
}

.st-key-connect_button button:active,
.st-key-guest_login button:active {
    transform: translateY(0);
}

.choice-divider {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 0.1rem 0;
    color: rgba(255,255,255,0.42);
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.choice-divider::before,
.choice-divider::after {
    content: "";
    flex: 1;
    height: 1px;
    background: rgba(255,255,255,0.12);
}

.st-key-guest_login button {
    min-height: 3.15rem;
    border: 1px solid rgba(255,255,255,0.18) !important;
    border-radius: 13px !important;
    background: transparent !important;
    color: rgba(255,255,255,0.82) !important;
    font-size: 0.88rem !important;
    font-weight: 800 !important;
    box-shadow: none !important;
    transition: transform 160ms ease, background 160ms ease, border-color 160ms ease;
}

.st-key-guest_login button:hover {
    border-color: rgba(255,255,255,0.32) !important;
    background: rgba(255,255,255,0.08) !important;
    color: #ffffff !important;
    transform: translateY(-1px);
}

.st-key-login_form_panel div[data-testid="stExpander"] {
    border: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
}

.st-key-login_form_panel div[data-testid="stExpander"] details {
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 11px !important;
    background: rgba(255,255,255,0.055) !important;
}

.st-key-login_form_panel div[data-testid="stExpander"] summary {
    color: rgba(255,255,255,0.70) !important;
    font-size: 0.79rem !important;
    font-weight: 750 !important;
}

.st-key-login_form_panel div[data-testid="stExpander"] summary p {
    color: inherit !important;
}

.st-key-login_form_panel div[data-testid="stExpander"] summary:hover {
    color: #ffffff !important;
}

.st-key-login_form_panel [data-testid="stExpanderDetails"] {
    color: rgba(255,255,255,0.64) !important;
    font-size: 0.78rem !important;
    line-height: 1.5;
}

.st-key-login_form_panel [data-testid="stExpanderDetails"] p,
.st-key-login_form_panel [data-testid="stExpanderDetails"] li {
    color: rgba(255,255,255,0.64) !important;
}

.st-key-login_form_panel [data-testid="stExpanderDetails"] code {
    color: var(--green) !important;
    background: rgba(0,255,135,0.08) !important;
}

.stAlert {
    border-radius: 12px !important;
}

@media (max-width: 760px) {
    .stMainBlockContainer {
        padding: 1.5rem 1rem 2rem !important;
    }

    .st-key-login_shell div[data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
    }

    .st-key-login_shell div[data-testid="column"] {
        width: 100% !important;
    }

    .login-hero,
    .st-key-login_form_panel {
        min-height: auto;
    }

    .login-hero {
        padding: 2.2rem 1.7rem;
    }

    .login-hero h1 {
        max-width: 10ch;
        font-size: 2.75rem;
    }

    .hero-copy {
        font-size: 0.92rem;
    }

    .feature-row {
        margin-top: 2rem;
    }

    .st-key-login_form_panel {
        padding: 2.25rem 1.6rem;
    }
}

@media (max-width: 420px) {
    .feature-pill:last-child {
        display: none;
    }

    .login-hero h1 {
        font-size: 2.45rem;
    }
}
</style>
""", unsafe_allow_html=True)

def connect_team():
    """Connect to an FPL team after the form is submitted."""
    manager_id = st.session_state.get("manager_id_input", "").strip()
    
    if not manager_id:
        st.warning("Enter your Manager ID to connect.")
        return
    
    if not manager_id.isdigit():
        st.error("Your Manager ID should contain numbers only.")
        return

    try:
        with st.spinner("Connecting to your team…"):
            bootstrap = load_bootstrap()
            gw        = get_current_gw(bootstrap)
            players   = build_player_map(bootstrap)

            entry   = fetch(f"https://fantasy.premierleague.com/api/entry/{manager_id}/")
            history = fetch(f"https://fantasy.premierleague.com/api/entry/{manager_id}/history/")
            picks   = fetch(f"https://fantasy.premierleague.com/api/entry/{manager_id}/event/{gw}/picks/")
    except Exception:
        st.error("We couldn't find that team. Check the ID and try again.")
        return

    st.session_state.guest      = False
    st.session_state.manager_id = manager_id
    st.session_state.entry      = entry
    st.session_state.history    = history
    st.session_state.picks      = picks
    st.session_state.players    = players
    st.session_state.gw         = gw

    st.switch_page("pages/home.py")

with st.container(key="login_shell"):
    hero_col, form_col = st.columns([1.08, 0.92], gap=None)

    with hero_col:
        st.markdown(
            """
            <section class="login-hero">
                <div>
                    <h1>Your team.<br><span class="headline-nowrap">In&nbsp;real&nbsp;time.</span></h1>
                    <br>
                    <p class="hero-copy">
                        Follow every gameweek as it happens, with live scoring for
                        your active eleven, captain and vice captain multipliers,
                        bench returns, and the wider context of average and highest scores.
                    </p>
                    <br>
                    <p class="hero-copy">
                        Go deeper with fixture statistics, player performance profiles,
                        value comparisons, team strength analysis, and upcoming
                        fixture difficulty.
                    </p>
                    <br>
                    <p class="hero-copy">
                        Review how your points and overall rank evolve across the
                        season, then see exactly where you stand in every mini league.
                    </p>
                    <br>
                    <p class="hero-copy">
                        Use the Transfer Lab to assess your current squad, discover
                        standout picks in every position, and explore recommendations
                        shaped by performance and value.
                    </p>
                </div>
                <div class="feature-row" aria-label="Features">
                    <span class="feature-pill">Live points</span>
                    <span class="feature-pill">Squad insights</span>
                    <span class="feature-pill">League ranks</span>
                </div>
            </section>
            """,
            unsafe_allow_html=True,
        )

    with form_col:
        with st.container(key="login_form_panel"):
            st.markdown(
                """
                <div class="form-intro">
                    <h2>Connect your team</h2>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("connect_form", border=False):
                st.text_input(
                    "Manager ID",
                    placeholder="e.g. 1234567",
                    key="manager_id_input",
                    help="This is the number in your FPL team URL.",
                )
                connect_clicked = st.form_submit_button(
                    "Connect my team",
                    use_container_width=True,
                    type="primary",
                    key="connect_button",
                )

            st.markdown('<div class="choice-divider"><span>or</span></div>', unsafe_allow_html=True)
            guest_clicked = st.button(
                "Continue as guest",
                use_container_width=True,
                key="guest_login",
            )

            with st.expander("Where can I find my Manager ID?", expanded=True):
                st.markdown(
                    """
                    Open your team on the FPL website and select **Points**.
                    In a URL like: `fantasy.premierleague.com/entry/1637221/event/26`,
                    your Manager ID is `3807119`.
                    """
                )

if connect_clicked:
    connect_team()

if guest_clicked:
    st.session_state.guest = True
    for key in ("manager_id", "entry", "history", "picks", "players", "gw"):
        st.session_state.pop(key, None)
    st.switch_page("pages/home.py")
