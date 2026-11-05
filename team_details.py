"""Squad and observed match-form panels for the selected Premier League team."""

from home_insights import escape, number


def squad_for_team(elements, team_id):
    return sorted(
        (player for player in elements
         if player.get("team") == team_id and not player.get("removed")
         and player.get("can_select") is not False),
        key=lambda player: (
            number(player.get("element_type"), 5),
            -number(player.get("minutes")),
            player.get("web_name") or player.get("second_name") or "",
        ),
    )


def team_match_form(fixtures, team_id):
    matches = []
    for fixture in fixtures:
        if not fixture.get("finished") or team_id not in (fixture.get("team_h"), fixture.get("team_a")):
            continue
        home_score, away_score = fixture.get("team_h_score"), fixture.get("team_a_score")
        if home_score is None or away_score is None:
            continue
        home = fixture.get("team_h") == team_id
        goals_for, goals_against = (home_score, away_score) if home else (away_score, home_score)
        result = "W" if goals_for > goals_against else "L" if goals_for < goals_against else "D"
        matches.append({
            "id": fixture.get("id"), "event": fixture.get("event"),
            "kickoff": fixture.get("kickoff_time") or "",
            "opponent": fixture.get("team_a") if home else fixture.get("team_h"),
            "home": home, "gf": goals_for, "ga": goals_against,
            "result": result, "points": {"W": 3, "D": 1, "L": 0}[result],
        })
    matches.sort(key=lambda match: (match["kickoff"], number(match["event"]), number(match["id"])))
    recent = matches[-5:]
    splits = {}
    for label, home in (("Home PPG", True), ("Away PPG", False)):
        subset = [match for match in matches if match["home"] == home]
        splits[label] = sum(match["points"] for match in subset) / len(subset) if subset else None
    return {
        "matches": matches, "recent": matches[-10:],
        "last_five_points": sum(match["points"] for match in recent),
        "last_five_gf": sum(match["gf"] for match in recent),
        "last_five_ga": sum(match["ga"] for match in recent),
        "win_rate": sum(match["result"] == "W" for match in matches) / len(matches) if matches else None,
        **splits,
    }


def form_chart_svg(matches, teams):
    if not matches:
        return '<div class="empty-note">No completed league matches yet.</div>'
    width, height, pad_x, pad_y = 600, 220, 32, 30
    plot_width, plot_height = width - pad_x * 2, height - pad_y * 2
    bar_width = min(38, plot_width / max(len(matches), 1) * 0.55)
    marks = []
    for index, match in enumerate(matches):
        x = pad_x + (index + 0.5) * plot_width / len(matches)
        bar_height = match["points"] / 3 * plot_height
        y = height - pad_y - bar_height
        colour = {"W": "#00ff87", "D": "#ffb500", "L": "#ff4f6d"}[match["result"]]
        opponent = teams.get(match["opponent"], {}).get("short_name", "TBC")
        venue = "H" if match["home"] else "A"
        title = f'GW{match["event"]} · {opponent} ({venue}) · {match["gf"]}–{match["ga"]}'
        marks.append(
            f'<rect x="{x - bar_width / 2:.1f}" y="{min(y, height - pad_y - 4):.1f}" '
            f'width="{bar_width:.1f}" height="{max(bar_height, 4):.1f}" rx="4" fill="{colour}">'
            f'<title>{escape(title)}</title></rect>'
            f'<text x="{x:.1f}" y="{height - 9}" fill="rgba(255,255,255,0.7)" '
            f'font-size="10" text-anchor="middle">GW{escape(match["event"])}</text>'
        )
    grid = "".join(
        f'<line x1="{pad_x}" y1="{height-pad_y-value/3*plot_height:.1f}" x2="{width-pad_x}" '
        f'y2="{height-pad_y-value/3*plot_height:.1f}" stroke="rgba(255,255,255,0.12)"/>'
        f'<text x="{pad_x-10}" y="{height-pad_y-value/3*plot_height+4:.1f}" '
        f'fill="rgba(255,255,255,0.65)" font-size="11" text-anchor="end">{value}</text>'
        for value in (0, 1, 3)
    )
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="220" role="img" '
        f'aria-label="League points earned in the last {len(matches)} completed matches">'
        f'<title>Points per match: win 3, draw 1, loss 0</title>{grid}{"".join(marks)}</svg>'
    )


def team_detail_panels(elements, fixtures, team_id, teams, positions):
    team = teams.get(team_id, {})
    team_name = team.get("name", "Selected team")
    players = squad_for_team(elements, team_id)
    rows = []
    labels = {"a": "Available", "d": "Doubtful", "i": "Injured", "s": "Suspended", "u": "Unavailable", "n": "Unavailable"}
    for player in players:
        status = player.get("status")
        chance = number(player.get("chance_of_playing_next_round"), None)
        flagged = status != "a" or (chance is not None and chance < 100)
        label = labels.get(status, "Unknown")
        if status == "a" and flagged:
            label = "Doubtful"
        if flagged and chance is not None:
            label += f" · {chance:.0f}%"
        status_class = "flagged" if flagged else "available"
        position = positions.get(player.get("element_type"), {}).get("singular_name_short", "—")
        name = player.get("web_name") or player.get("second_name") or "Unknown"
        price = number(player.get("now_cost"), None)
        price_text = f"£{price / 10:.1f}m" if price is not None else "—"
        rows.append(
            '<tr>'
            f'<td class="squad-player">{escape(name)}</td><td>{escape(position)}</td>'
            f'<td>{price_text}</td><td>{int(number(player.get("minutes"))):,}</td>'
            f'<td class="squad-points">{int(number(player.get("total_points")))}</td>'
            f'<td>{number(player.get("form")):.1f}</td>'
            f'<td><span class="squad-status {status_class}" title="{escape(player.get("news") or label)}">{escape(label)}</span></td>'
            '</tr>'
        )
    squad_table = (
        '<div class="team-squad-scroll"><table class="small-table team-squad-table">'
        '<thead><tr><th scope="col">Player</th><th scope="col">Pos</th><th scope="col">Price</th>'
        '<th scope="col">Minutes</th><th scope="col">Points</th><th scope="col">Form</th>'
        '<th scope="col">Availability</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>' if rows else
        '<div class="empty-note">No squad data available for this team.</div>'
    )

    form = team_match_form(fixtures, team_id)
    metrics = [
        ("Last 5 points", str(form["last_five_points"]) if form["matches"] else "—"),
        ("Last 5 goals for", str(form["last_five_gf"]) if form["matches"] else "—"),
        ("Last 5 goals against", str(form["last_five_ga"]) if form["matches"] else "—"),
        ("Win rate", f'{form["win_rate"]:.0%}' if form["win_rate"] is not None else "—"),
        ("Home PPG", f'{form["Home PPG"]:.2f}' if form["Home PPG"] is not None else "—"),
        ("Away PPG", f'{form["Away PPG"]:.2f}' if form["Away PPG"] is not None else "—"),
    ]
    metrics_html = "".join(
        f'<div class="metric-card"><div class="metric-label">{escape(label)}</div>'
        f'<div class="metric-value">{escape(value)}</div></div>' for label, value in metrics
    )
    results = []
    for match in reversed(form["recent"]):
        opponent = teams.get(match["opponent"], {})
        venue = "H" if match["home"] else "A"
        result_class = {"W": "result-win", "D": "result-draw", "L": "result-loss"}[match["result"]]
        results.append(
            '<li class="team-form-result">'
            f'<span class="team-form-gameweek">GW{escape(match["event"])}</span>'
            f'<span class="team-form-opponent">{escape(opponent.get("name") or "Unknown")} ({venue})</span>'
            f'<span class="team-form-score">{match["gf"]} – {match["ga"]}</span>'
            f'<span class="result-badge {result_class}">{match["result"]}</span></li>'
        )
    results_html = f'<ol class="team-form-results">{"".join(results)}</ol>' if results else ""
    squad_panel = (
        '<section class="glass-panel team-squad-panel" data-team-squad="true" aria-label="Squad overview">'
        '<div class="kicker">SQUAD OVERVIEW</div><div class="panel-title">Players, value and availability</div>'
        f'<div class="team-meta">{escape(team_name)} · {len(players)} players · Ordered by position and minutes</div>'
        f'{squad_table}</section>'
    )
    form_panel = (
        '<section class="glass-panel team-form-panel" data-team-form="true" aria-label="Team form trends">'
        '<div><div class="kicker">TEAM FORM TRENDS</div><div class="panel-title">Results and points over time</div>'
        f'<div class="team-meta">{escape(team_name)} · Completed league matches</div></div>'
        f'<div class="team-form-metrics">{metrics_html}</div>'
        '<div class="mini-chart team-form-chart"><div class="team-meta">Points per match · Last 10</div>'
        f'{form_chart_svg(form["recent"], teams)}</div>'
        '<div class="team-form-history"><div class="panel-title">Recent results</div>'
        f'{results_html}</div></section>'
    )
    return squad_panel, form_panel


TEAM_PANEL_ALIGNMENT_SCRIPT = """
<script>
(() => {
    const host = window;
    const doc = host.document;
    const key = "__fplTeamPanelAlignmentCleanup";
    if (host[key]) host[key]();
    let frame = 0;
    let watched = [];
    const schedule = () => {
        if (!frame) frame = host.requestAnimationFrame(align);
    };
    const resizeObserver = new host.ResizeObserver(schedule);
    function align() {
        frame = 0;
        const squad = doc.querySelector("[data-team-squad]");
        const form = doc.querySelector("[data-team-form]");
        if (!squad || !form) return;
        const targets = [squad, form];
        if (targets.some((target, index) => target !== watched[index])) {
            resizeObserver.disconnect();
            targets.forEach(target => resizeObserver.observe(target));
            watched = targets;
        }
        // Start at each panel's content height. Neither waits for the opposite
        // column, so there is no empty area above Squad overview.
        targets.forEach(target => target.style.minHeight = "0px");
        const left = squad.getBoundingClientRect();
        const right = form.getBoundingClientRect();
        if (right.left < left.right - 1) return;
        const bottom = Math.max(left.bottom, right.bottom);
        squad.style.minHeight = `${Math.ceil(bottom - left.top)}px`;
        form.style.minHeight = `${Math.ceil(bottom - right.top)}px`;
    }
    const mutationObserver = new host.MutationObserver(schedule);
    mutationObserver.observe(doc.body, {childList: true, subtree: true});
    host.addEventListener("resize", schedule);
    const cleanup = () => {
        if (frame) host.cancelAnimationFrame(frame);
        resizeObserver.disconnect();
        mutationObserver.disconnect();
        host.removeEventListener("resize", schedule);
        if (host[key] === cleanup) delete host[key];
    };
    host[key] = cleanup;
    host.addEventListener("pagehide", cleanup, {once: true});
    align();
})();
</script>
"""
