"""Squad availability and low-ownership form picks for the home dashboard."""

import html
import math


def number(value, default=0.0):
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default


def squad_alerts(elements, picks):
    players = {player["id"]: player for player in elements}
    labels = {
        "i": "Injured", "s": "Suspended", "d": "Doubtful",
        "u": "Unavailable", "n": "Unavailable",
    }
    alerts = []
    seen = set()
    for pick in picks:
        player_id = pick.get("element")
        if player_id in seen:
            continue
        seen.add(player_id)
        player = players.get(player_id)
        if player is None:
            alerts.append({
                "player": {"web_name": f"Player {player_id}"}, "pick": pick,
                "label": "Status unavailable", "chance": None, "severity": "unknown",
            })
            continue
        chance = number(player.get("chance_of_playing_next_round"), None)
        status = player.get("status")
        unavailable = player.get("removed") or player.get("can_select") is False
        if status == "a" and not unavailable and (chance is None or chance >= 100):
            continue
        label = "Unavailable" if unavailable else labels.get(status, "Status unavailable")
        if status == "a" and chance is not None and chance < 100:
            label = "Doubtful"
        severity = "danger" if unavailable or status in ("i", "s", "u", "n") or chance == 0 else "warning"
        alerts.append({
            "player": player, "pick": pick, "label": label,
            "chance": chance, "severity": severity,
        })
    alerts.sort(key=lambda row: (
        {"danger": 0, "warning": 1, "unknown": 2}[row["severity"]],
        row["chance"] if row["chance"] is not None else 101,
        number(row["pick"].get("position"), 16),
    ))
    return alerts


def differential_watch(elements, fixtures, picks=(), limit=5, *, start_gameweek=None):
    owned = {pick.get("element") for pick in picks}
    candidates = []
    for player in elements:
        ownership = number(player.get("selected_by_percent"), None)
        chance = number(player.get("chance_of_playing_next_round"), None)
        if (
            player.get("id") in owned
            or player.get("status") != "a"
            or player.get("removed")
            or player.get("can_select") is False
            or (chance is not None and chance < 100)
            or ownership is None or not 0 <= ownership < 10
            or number(player.get("minutes")) < 180
            or number(player.get("form")) <= 0
        ):
            continue
        candidates.append(player)
    candidates.sort(key=lambda player: (
        -number(player.get("form")),
        -number(player.get("total_points")),
        number(player.get("selected_by_percent")),
        player.get("web_name") or "",
    ))

    upcoming = sorted(
        (fixture for fixture in fixtures if not fixture.get("finished") and not fixture.get("started")),
        key=lambda fixture: (
            number(fixture.get("event"), 1000),
            fixture.get("kickoff_time") or "9999",
            number(fixture.get("id")),
        ),
    )
    if start_gameweek is None:
        start_gameweek = next((fixture["event"] for fixture in upcoming if fixture.get("event")), None)
    gameweeks = range(start_gameweek, min(start_gameweek + 3, 39)) if start_gameweek else ()
    fixtures_by_team = {}
    for fixture in upcoming:
        event = fixture.get("event")
        if event not in gameweeks:
            continue
        for side, opponent in (("h", "a"), ("a", "h")):
            fixtures_by_team.setdefault((fixture.get(f"team_{side}"), event), []).append({
                "opponent": fixture.get(f"team_{opponent}"),
                "venue": "H" if side == "h" else "A",
                "difficulty": fixture.get(f"team_{side}_difficulty"),
            })
    return [{
        "player": player,
        "gameweeks": [{
            "event": event,
            "fixtures": fixtures_by_team.get((player.get("team"), event), []),
        } for event in gameweeks],
    } for player in candidates[:limit]]


def escape(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def player_identity(player, teams, positions):
    team = teams.get(player.get("team"), {})
    name = player.get("web_name") or player.get("second_name") or "Unknown player"
    position = positions.get(player.get("element_type"), {}).get("singular_name_short", "")
    meta = " · ".join(filter(None, (team.get("short_name"), position)))
    code = number(team.get("code"))
    badge = (
        f'<img class="team-logo" src="https://resources.premierleague.com/'
        f'premierleague/badges/50/t{int(code)}.png" alt="" loading="lazy">'
        if code > 0 else ""
    )
    return (
        f'<div class="insight-player">{badge}<div class="insight-player-copy">'
        f'<div class="insight-player-name">{escape(name)}</div>'
        f'<div class="insight-meta">{escape(meta)}</div></div></div>'
    )


def squad_alerts_html(alerts, teams, positions, *, is_guest=False, has_squad=True):
    rows = []
    for alert in alerts:
        player, pick = alert["player"], alert["pick"]
        role = "Captain" if pick.get("is_captain") else "Vice-captain" if pick.get("is_vice_captain") else (
            "Starting XI" if 1 <= number(pick.get("position")) <= 11 else "Bench"
        )
        chance = alert["chance"]
        availability = f"{chance:.0f}% chance next GW" if chance is not None else "Chance of playing not provided"
        news = player.get("news") or "No further update from FPL."
        rows.append(
            '<li class="insight-row">'
            f'<div class="insight-row-head">{player_identity(player, teams, positions)}'
            f'<span class="insight-status {alert["severity"]}">{escape(alert["label"])}</span></div>'
            f'<div class="insight-meta insight-availability">{escape(role)} · {escape(availability)}</div>'
            f'<div class="insight-news">{escape(news)}</div></li>'
        )
    if is_guest:
        body = '<div class="insight-empty">Connect your team to see your squad’s injury and suspension alerts.</div>'
    elif not has_squad:
        body = '<div class="insight-empty">Your squad is unavailable. Reconnect your team to check availability.</div>'
    elif not rows:
        body = '<div class="insight-empty insight-clear">No availability flags in your squad.</div>'
    else:
        body = f'<ul class="insight-list">{"".join(rows)}</ul>'
    count = f'<span class="insight-count">{len(alerts)}</span>' if alerts else ""
    return (
        '<section class="glass-box matches-box home-insight-box" aria-labelledby="squad-alerts-title">'
        f'<h3 class="section-title" id="squad-alerts-title">Squad alerts {count}</h3>'
        '<p class="insight-subtitle">Next gameweek availability · Official FPL updates</p>'
        f'{body}</section>'
    )


def differential_watch_html(rows, teams, positions):
    items = []
    for rank, row in enumerate(rows, 1):
        player = row["player"]
        gameweek_boxes = []
        for gameweek in row["gameweeks"]:
            opponents = []
            fixtures = gameweek["fixtures"]
            for fixture in fixtures:
                opponent = teams.get(fixture["opponent"], {})
                opponent_name = opponent.get("short_name") or opponent.get("name") or "TBC"
                difficulty = int(number(fixture.get("difficulty")))
                difficulty_label = f" · Difficulty {difficulty}/5" if 1 <= difficulty <= 5 else ""
                venue = "Home" if fixture["venue"] == "H" else "Away"
                tooltip = f'{opponent.get("name") or opponent_name} · {venue} · GW{gameweek["event"]}{difficulty_label}'
                opponents.append(
                    f'<span class="insight-opponent difficulty-{difficulty}" title="{escape(tooltip)}">'
                    f'{escape(opponent_name)} ({fixture["venue"]})</span>'
                )
            difficulty_class = f' difficulty-{int(number(fixtures[0].get("difficulty")))}' if len(fixtures) == 1 else ""
            opponent_html = "".join(opponents) or '<span class="insight-meta">No fixture</span>'
            gameweek_boxes.append(
                f'<span class="insight-fixture{difficulty_class}">'
                f'<span class="insight-next-label">GW{gameweek["event"]}</span>{opponent_html}</span>'
            )
        next_html = (
            f'<div class="insight-fixtures">{"".join(gameweek_boxes)}</div>' if gameweek_boxes else
            '<div class="insight-fixtures insight-meta">No upcoming fixture</div>'
        )
        price = number(player.get("now_cost"), None)
        price_text = f"£{price / 10:.1f}m" if price is not None else "—"
        items.append(
            '<li class="insight-row">'
            f'<div class="insight-row-head"><span class="trend-num">{rank}.</span>'
            f'{player_identity(player, teams, positions)}</div>{next_html}'
            '<div class="insight-stats">'
            f'<div><span class="insight-stat-label">Price</span><span class="insight-stat-value">{price_text}</span></div>'
            f'<div><span class="insight-stat-label">Form</span><span class="insight-stat-value">{number(player.get("form")):.1f}</span></div>'
            f'<div><span class="insight-stat-label">Owned</span><span class="insight-stat-value">{number(player.get("selected_by_percent")):.1f}%</span></div>'
            '</div></li>'
        )
    body = f'<ol class="insight-list">{"".join(items)}</ol>' if items else (
        '<div class="insight-empty">No available players meet the form and ownership criteria right now.</div>'
    )
    return (
        '<section class="glass-box matches-box home-insight-box" data-home-differentials="true" aria-labelledby="differential-watch-title">'
        '<h3 class="section-title" id="differential-watch-title">Differential watch</h3>'
        '<p class="insight-subtitle">Under 10% owned · Ranked by form · 180+ minutes</p>'
        f'{body}</section>'
    )
