"""Season leaderboards and sizing for the remaining home-dashboard space."""

from home_insights import escape, number, player_identity


def player_leaderboards(elements, limit=10):
    boards = []
    for title, field, goalkeepers_only in (
        ("Goals", "goals_scored", False),
        ("Assists", "assists", False),
        ("Clean sheets", "clean_sheets", True),
    ):
        players = [player for player in elements
                   if number(player.get(field)) > 0
                   and player.get("element_type") in (1, 2, 3, 4)
                   and (not goalkeepers_only or player.get("element_type") == 1)]
        players.sort(key=lambda player: (
            -number(player.get(field)),
            player.get("web_name") or player.get("second_name") or "",
            number(player.get("id")),
        ))
        rows = []
        previous_value, rank = None, 0
        for index, player in enumerate(players[:limit], 1):
            value = int(number(player.get(field)))
            if value != previous_value:
                rank = index
            rows.append({"player": player, "value": value, "rank": rank})
            previous_value = value
        boards.append({
            "title": title,
            "subtitle": "Goalkeepers" if goalkeepers_only else "All players",
            "rows": rows,
        })
    return boards


def player_leaderboards_html(boards, teams, positions, *, gameweek=None):
    columns = []
    for board in boards:
        items = []
        for row in board["rows"]:
            items.append(
                '<li class="leaderboard-item">'
                f'<span class="trend-num">{row["rank"]}.</span>'
                f'{player_identity(row["player"], teams, positions)}'
                f'<span class="leaderboard-value">{row["value"]}</span></li>'
            )
        body = '<ol class="leaderboard-list">' + "".join(items) + '</ol>' if items else (
            '<div class="insight-empty">No season returns yet.</div>'
        )
        columns.append(
            '<section class="leaderboard-column">'
            f'<h4 class="leaderboard-column-title">{escape(board["title"])}</h4>'
            f'<p class="leaderboard-column-subtitle">{escape(board["subtitle"])}</p>'
            f'{body}</section>'
        )
    return (
        '<div id="home-leaderboard-slot">'
        '<section class="glass-box player-leaderboards" aria-labelledby="player-leaderboards-title">'
        '<div class="leaderboards-header">'
        '<h3 id="player-leaderboards-title">Player leaderboards</h3>'
        f'<p>Updated till Gameweek {escape(gameweek) if gameweek is not None else "—"}</p></div>'
        f'<div class="leaderboard-columns">{"".join(columns)}</div>'
        '</section></div>'
    )


# The left column changes height with squad alerts and responsive text wrapping.
# Measure its existing bottom edge rather than assigning another tall fixed card.
LEADERBOARD_LAYOUT_SCRIPT = """
<script>
(() => {
    const host = window;
    const doc = host.document;
    const cleanupKey = "__fplLeaderboardLayoutCleanup";
    if (host[cleanupKey]) host[cleanupKey]();
    let frame = 0;
    let watched = [];
    const schedule = () => {
        if (!frame) frame = host.requestAnimationFrame(fit);
    };
    const resizeObserver = new host.ResizeObserver(schedule);
    function fit() {
        frame = 0;
        const slot = doc.getElementById("home-leaderboard-slot");
        // Streamlit replaces heading IDs with generated anchors. Target the
        // section's data attribute, which is preserved by Markdown rendering.
        const left = doc.querySelector("[data-home-differentials]");
        const standings = doc.querySelector(".standings-wrap");
        if (!slot || !left || !standings) return;
        const targets = [left, standings, doc.querySelector(".stMainBlockContainer")].filter(Boolean);
        if (targets.some((target, index) => target !== watched[index]) || targets.length !== watched.length) {
            resizeObserver.disconnect();
            targets.forEach(target => resizeObserver.observe(target));
            watched = targets;
        }
        const leftRect = left.getBoundingClientRect();
        const slotRect = slot.getBoundingClientRect();
        const sideBySide = slotRect.left >= leftRect.right - 1;
        const remaining = Math.max(0, Math.floor(leftRect.bottom - slotRect.top));
        const height = sideBySide && remaining >= 140 ? remaining : 0;
        const heightStyle = `${height}px`;
        if (slot.style.height !== heightStyle) slot.style.height = heightStyle;
        slot.style.visibility = height ? "visible" : "hidden";
        slot.setAttribute("aria-hidden", height ? "false" : "true");
    }
    const mutationObserver = new host.MutationObserver(schedule);
    mutationObserver.observe(doc.body, {childList: true, subtree: true});
    host.addEventListener("resize", schedule);
    const cleanup = () => {
        if (frame) host.cancelAnimationFrame(frame);
        resizeObserver.disconnect();
        mutationObserver.disconnect();
        host.removeEventListener("resize", schedule);
        if (host[cleanupKey] === cleanup) delete host[cleanupKey];
    };
    host[cleanupKey] = cleanup;
    window.addEventListener("pagehide", cleanup, {once: true});
    fit();
})();
</script>
"""
