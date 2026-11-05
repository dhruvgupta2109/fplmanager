import unittest

from home_insights import (
    differential_watch, differential_watch_html, squad_alerts, squad_alerts_html,
)


def player(player_id=1, **changes):
    return {
        "id": player_id, "web_name": f"Player {player_id}", "team": 1,
        "element_type": 3, "status": "a", "minutes": 450, "form": "5.0",
        "now_cost": 65, "selected_by_percent": "4.5", "total_points": 40,
        **changes,
    }


class SquadAlertsTests(unittest.TestCase):
    def test_flags_only_owned_players_and_includes_bench(self):
        players = [player(1), player(2, status="i"), player(3, status="s")]
        picks = [{"element": 1, "position": 1}, {"element": 2, "position": 12}]
        alerts = squad_alerts(players, picks)
        self.assertEqual([row["player"]["id"] for row in alerts], [2])
        self.assertIn("Bench", squad_alerts_html(alerts, {}, {}))

    def test_available_player_with_reduced_chance_is_flagged(self):
        alerts = squad_alerts([player(chance_of_playing_next_round=75)], [{"element": 1}])
        self.assertEqual(alerts[0]["label"], "Doubtful")
        self.assertIn("75% chance next GW", squad_alerts_html(alerts, {}, {}))

    def test_healthy_players_with_old_news_are_not_flagged(self):
        for chance in (None, 100):
            with self.subTest(chance=chance):
                players = [player(news="Recovered from injury", chance_of_playing_next_round=chance)]
                self.assertEqual(squad_alerts(players, [{"element": 1}]), [])

    def test_severe_alerts_first_and_unknown_chance_is_not_zero(self):
        players = [player(1, status="d"), player(2, status="s", chance_of_playing_next_round=0)]
        alerts = squad_alerts(players, [{"element": 1}, {"element": 2}])
        self.assertEqual([row["label"] for row in alerts], ["Suspended", "Doubtful"])
        markup = squad_alerts_html(alerts, {}, {})
        self.assertIn("Chance of playing not provided", markup)

    def test_missing_player_or_squad_does_not_claim_all_clear(self):
        alerts = squad_alerts([], [{"element": 99}])
        self.assertEqual(alerts[0]["label"], "Status unavailable")
        self.assertNotIn("No availability flags", squad_alerts_html(alerts, {}, {}))
        self.assertIn("Connect your team", squad_alerts_html([], {}, {}, is_guest=True))
        self.assertIn("Reconnect your team", squad_alerts_html([], {}, {}, has_squad=False))
        self.assertIn("No availability flags", squad_alerts_html([], {}, {}))

    def test_removed_player_and_captain_are_identified(self):
        alerts = squad_alerts([player(removed=True)], [{"element": 1, "is_captain": True}])
        self.assertEqual(alerts[0]["label"], "Unavailable")
        self.assertIn("Captain", squad_alerts_html(alerts, {}, {}))


class DifferentialWatchTests(unittest.TestCase):
    def test_excludes_popular_injured_and_insufficient_minutes(self):
        players = [
            player(1, selected_by_percent="9.9", minutes=180),
            player(2, selected_by_percent="10.0"),
            player(3, status="i"), player(4, minutes=179),
            player(5, form="0.0"), player(6, removed=True),
            player(7, can_select=False), player(8, chance_of_playing_next_round=75),
            player(9, selected_by_percent=None), player(10, form="NaN"),
        ]
        self.assertEqual([row["player"]["id"] for row in differential_watch(players, [])], [1])

    def test_orders_by_form_and_excludes_owned_players(self):
        players = [player(1, form="9"), player(2, form="4"), player(3, form="7")]
        rows = differential_watch(players, [], [{"element": 1}])
        self.assertEqual([row["player"]["id"] for row in rows], [3, 2])
        self.assertEqual(len(differential_watch([player(i) for i in range(10)], [])), 5)

    def test_next_fixture_skips_completed_and_started_matches(self):
        fixtures = [
            {"id": 1, "team_h": 1, "team_a": 2, "event": 8, "finished": True},
            {"id": 2, "team_h": 1, "team_a": 3, "event": 9, "started": True},
            {"id": 4, "team_h": 1, "team_a": 4, "event": 10, "kickoff_time": "2026-11-09"},
            {"id": 3, "team_h": 5, "team_a": 1, "event": 10, "kickoff_time": "2026-11-07", "team_a_difficulty": 4},
        ]
        gameweeks = differential_watch([player()], fixtures)[0]["gameweeks"]
        self.assertEqual([week["event"] for week in gameweeks], [10, 11, 12])
        self.assertEqual(gameweeks[0]["fixtures"], [
            {"opponent": 5, "venue": "A", "difficulty": 4},
            {"opponent": 4, "venue": "H", "difficulty": None},
        ])

    def test_three_gameweeks_include_blanks_and_double_fixtures(self):
        fixtures = [
            {"team_h": 1, "team_a": 2, "event": 10},
            {"team_h": 1, "team_a": 3, "event": 12},
            {"team_h": 4, "team_a": 1, "event": 12},
            {"team_h": 1, "team_a": 5, "event": 13},
        ]
        rows = differential_watch([player()], fixtures, start_gameweek=10)
        gameweeks = rows[0]["gameweeks"]
        self.assertEqual([week["event"] for week in gameweeks], [10, 11, 12])
        self.assertEqual([len(week["fixtures"]) for week in gameweeks], [1, 0, 2])
        teams = {i: {"short_name": f"Club{i}"} for i in range(1, 6)}
        markup = differential_watch_html(rows, teams, {})
        self.assertIn("No fixture", markup)
        self.assertIn("Club3 (H)", markup)
        self.assertIn("Club4 (A)", markup)
        self.assertNotIn("Club5", markup)

    def test_shared_gameweek_window_does_not_skip_teams_blank_week(self):
        fixtures = [{"team_h": 1, "team_a": 2, "event": 11}]
        rows = differential_watch([player()], fixtures, start_gameweek=10)
        self.assertEqual(rows[0]["gameweeks"][0], {"event": 10, "fixtures": []})

    def test_end_of_season_does_not_invent_extra_gameweeks(self):
        rows = differential_watch([player()], [], start_gameweek=38)
        self.assertEqual(rows[0]["gameweeks"], [{"event": 38, "fixtures": []}])

    def test_empty_and_unknown_fixture_states(self):
        self.assertIn("No available players", differential_watch_html([], {}, {}))
        markup = differential_watch_html(differential_watch([player()], []), {}, {})
        self.assertIn("No upcoming fixture", markup)
        self.assertIn("£6.5m", markup)

    def test_player_and_news_text_is_escaped(self):
        unsafe = player(web_name='<script>alert("name")</script>', status="i", news="<img src=x onerror=alert(1)>")
        markup = squad_alerts_html(squad_alerts([unsafe], [{"element": 1}]), {}, {})
        self.assertNotIn("<script>", markup)
        self.assertNotIn("<img src=x", markup)
        unsafe["status"] = "a"
        markup = differential_watch_html(differential_watch([unsafe], []), {}, {})
        self.assertNotIn("<script>", markup)


if __name__ == "__main__":
    unittest.main()
