import shutil
import subprocess
import unittest

from team_details import TEAM_PANEL_ALIGNMENT_SCRIPT, squad_for_team, team_detail_panels, team_match_form


def match(match_id, home, away, goals_home, goals_away, **changes):
    return {
        "id": match_id, "team_h": home, "team_a": away,
        "team_h_score": goals_home, "team_a_score": goals_away,
        "event": match_id, "finished": True,
        "kickoff_time": f"2026-09-{match_id:02d}T15:00:00Z", **changes,
    }


class TeamDetailsTests(unittest.TestCase):
    def test_squad_contains_only_selected_current_team_players(self):
        players = [
            {"id": 1, "team": 1, "element_type": 3, "minutes": 900},
            {"id": 2, "team": 1, "element_type": 1, "minutes": 500},
            {"id": 3, "team": 1, "element_type": 1, "minutes": 100},
            {"id": 4, "team": 2}, {"id": 5, "team": 1, "removed": True},
            {"id": 6, "team": 1, "can_select": False},
        ]
        self.assertEqual([p["id"] for p in squad_for_team(players, 1)], [2, 3, 1])

    def test_match_results_use_selected_teams_perspective(self):
        form = team_match_form([
            match(1, 1, 2, 2, 0), match(2, 3, 1, 3, 1), match(3, 1, 4, 1, 1),
        ], 1)
        self.assertEqual([row["result"] for row in form["matches"]], ["W", "L", "D"])
        self.assertEqual(form["last_five_points"], 4)
        self.assertEqual(form["last_five_gf"], 4)
        self.assertEqual(form["last_five_ga"], 4)
        self.assertEqual(form["Home PPG"], 2)
        self.assertEqual(form["Away PPG"], 0)
        self.assertAlmostEqual(form["win_rate"], 1 / 3)

    def test_live_and_incomplete_matches_are_not_counted_as_final_results(self):
        form = team_match_form([
            match(1, 1, 2, 2, 0, finished=False),
            match(2, 1, 3, None, None), match(3, 4, 5, 2, 0),
        ], 1)
        self.assertEqual(form["matches"], [])
        self.assertIsNone(form["Home PPG"])
        self.assertIsNone(form["win_rate"])

    def test_recent_form_uses_latest_five_and_chart_latest_ten(self):
        fixtures = [match(i, 1, 2, 2, 0) for i in range(1, 13)]
        form = team_match_form(list(reversed(fixtures)), 1)
        self.assertEqual(form["last_five_points"], 15)
        self.assertEqual([row["event"] for row in form["recent"]], list(range(3, 13)))

    def test_empty_team_and_season_render_usable_states(self):
        markup = "".join(team_detail_panels([], [], 1, {1: {"name": "Example"}}, {}))
        self.assertIn("No squad data available", markup)
        self.assertIn("No completed league matches", markup)
        self.assertIn("Example", markup)

    def test_player_news_and_club_names_are_escaped(self):
        players = [{"team": 1, "web_name": "<script>player</script>", "status": "i", "news": 'Injury " onclick="alert(1)'}]
        markup = "".join(team_detail_panels(players, [], 1, {1: {"name": "<script>club</script>"}}, {}))
        self.assertNotIn("<script>", markup)
        self.assertIn("&lt;script&gt;", markup)
        self.assertNotIn('" onclick="alert(1)', markup)

    @unittest.skipUnless(shutil.which("node"), "Node is needed for the layout logic check")
    def test_panels_keep_their_own_starts_and_align_bottoms(self):
        script = TEAM_PANEL_ALIGNMENT_SCRIPT.removeprefix("\n<script>").removesuffix("</script>\n")
        harness = """
const assert = require('node:assert/strict');
const makePanel = (left, right, top, naturalHeight) => ({
    left, right, top, naturalHeight, style: {},
    getBoundingClientRect() {return {left:this.left, right:this.right, top:this.top,
        bottom:this.top + Math.max(this.naturalHeight, parseFloat(this.style.minHeight) || 0)};},
});
const squad = makePanel(32, 480, 500, 700);
const form = makePanel(512, 960, 750, 600);
let nextFrame;
let onResize;
global.window = {
    document: {body: {}, querySelector(selector) {return selector === '[data-team-squad]' ? squad : form;}},
    requestAnimationFrame(fn) {nextFrame = fn; return 1;}, cancelAnimationFrame() {},
    addEventListener() {}, removeEventListener() {},
    ResizeObserver: class {constructor(fn) {onResize = fn;} observe() {} disconnect() {}},
    MutationObserver: class {observe() {} disconnect() {}},
};
__SCRIPT__
assert.equal(squad.top, 500);
assert.equal(form.top, 750);
assert.equal(squad.getBoundingClientRect().bottom, 1350);
assert.equal(form.getBoundingClientRect().bottom, 1350);
squad.naturalHeight = 1000;
onResize(); nextFrame();
assert.equal(squad.getBoundingClientRect().bottom, 1500);
assert.equal(form.getBoundingClientRect().bottom, 1500);
// A team with fewer squad members must not retain the previous extra height.
squad.naturalHeight = 500;
onResize(); nextFrame();
assert.equal(squad.getBoundingClientRect().bottom, 1350);
assert.equal(form.getBoundingClientRect().bottom, 1350);
// On narrow screens the panels stack at their natural heights.
form.left = 32;
onResize(); nextFrame();
assert.equal(squad.style.minHeight, '0px');
assert.equal(form.style.minHeight, '0px');
window.__fplTeamPanelAlignmentCleanup();
""".replace("__SCRIPT__", script)
        result = subprocess.run([shutil.which("node"), "-e", harness], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
