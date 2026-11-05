import shutil
import subprocess
import unittest

from home_leaderboards import (
    LEADERBOARD_LAYOUT_SCRIPT, player_leaderboards, player_leaderboards_html,
)


def player(player_id, **changes):
    return {"id": player_id, "web_name": f"Player {player_id}", "element_type": 3, **changes}


class PlayerLeaderboardTests(unittest.TestCase):
    def test_ranks_season_returns_and_preserves_ties(self):
        boards = player_leaderboards([
            player(1, goals_scored=5), player(2, goals_scored=9),
            player(3, goals_scored=5), player(4, goals_scored=2),
        ])
        self.assertEqual([row["player"]["id"] for row in boards[0]["rows"]], [2, 1, 3, 4])
        self.assertEqual([row["rank"] for row in boards[0]["rows"]], [1, 2, 2, 4])

    def test_clean_sheet_board_is_explicitly_goalkeepers_only(self):
        board = player_leaderboards([
            player(1, element_type=1, clean_sheets=6),
            player(2, element_type=2, clean_sheets=8),
            player(3, element_type=3, clean_sheets=9),
        ])[2]
        self.assertEqual(board["subtitle"], "Goalkeepers")
        self.assertEqual([row["player"]["id"] for row in board["rows"]], [1])

    def test_injury_does_not_remove_past_achievements(self):
        boards = player_leaderboards([player(1, assists=7, status="i")])
        self.assertEqual(boards[1]["rows"][0]["value"], 7)

    def test_limits_lists_and_excludes_zero_or_missing_totals(self):
        players = [player(i, goals_scored=i) for i in range(20)]
        players += [player(100, goals_scored=None), player(101, goals_scored="NaN")]
        boards = player_leaderboards(players)
        self.assertEqual(len(boards[0]["rows"]), 10)
        self.assertEqual(boards[1]["rows"], [])
        self.assertIn("No season returns yet", player_leaderboards_html(boards, {}, {}))

    def test_names_are_escaped(self):
        boards = player_leaderboards([player(1, web_name="<script>alert(1)</script>", assists=1)])
        markup = player_leaderboards_html(boards, {}, {})
        self.assertNotIn("<script>", markup)
        self.assertIn("&lt;script&gt;", markup)

    @unittest.skipUnless(shutil.which("node"), "Node is needed for the browser-layout logic check")
    def test_panel_stays_inside_gap_when_layout_changes(self):
        script = LEADERBOARD_LAYOUT_SCRIPT.removeprefix("\n<script>").removesuffix("</script>\n")
        harness = """
const assert = require('node:assert/strict');
let leftRect = {right: 480, bottom: 1800};
let slotRect = {left: 512, top: 1200};
const slot = {style: {}, setAttribute(key, value) {this[key] = value;}, getBoundingClientRect() {return slotRect;}};
const left = {getBoundingClientRect() {return leftRect;}};
const resizeObservers = [];
const mutationObservers = [];
let nextFrame = null;
const host = {
    document: {
        body: {},
        // Streamlit's real Markdown renderer changes the heading's original ID.
        getElementById(id) {return id === 'home-leaderboard-slot' ? slot : null;},
        querySelector(selector) {return selector === '[data-home-differentials]' ? left : {};},
    },
    requestAnimationFrame(fn) {nextFrame = fn; return 1;},
    cancelAnimationFrame() {nextFrame = null;},
    addEventListener() {}, removeEventListener() {},
    ResizeObserver: class {constructor(fn) {this.fn = fn; resizeObservers.push(this);} observe() {} disconnect() {}},
    MutationObserver: class {constructor(fn) {this.fn = fn; mutationObservers.push(this);} observe() {} disconnect() {}},
};
// st.html executes directly in the app, even when an outer site embeds it.
host.parent = {get document() {throw new Error('Must not access an outer iframe');}};
global.window = host;
function flush() {const callback = nextFrame; nextFrame = null; if (callback) callback();}
__LAYOUT_SCRIPT__
flush();
assert.equal(slot.style.height, '600px');
assert.equal(slot.style.visibility, 'visible');
assert.equal(slotRect.top + parseFloat(slot.style.height), leftRect.bottom);
leftRect.bottom = 1510.8;
resizeObservers[0].fn(); flush();
assert.equal(slot.style.height, '310px');
assert.ok(slotRect.top + parseFloat(slot.style.height) <= leftRect.bottom);
// Stacked/mobile columns have no gap beside the left column.
slotRect.left = 32;
resizeObservers[0].fn(); flush();
assert.equal(slot.style.height, '0px');
assert.equal(slot['aria-hidden'], 'true');
// A short left column must not be made taller by these leaderboards.
slotRect.left = 512;
leftRect.bottom = 1100;
mutationObservers[0].fn(); flush();
assert.equal(slot.style.height, '0px');
// Reflow back to a large enough gap restores the panel.
leftRect.bottom = 1700;
resizeObservers[0].fn(); flush();
assert.equal(slot.style.height, '500px');
assert.equal(slot['aria-hidden'], 'false');
host.__fplLeaderboardLayoutCleanup();
assert.equal(host.__fplLeaderboardLayoutCleanup, undefined);
""".replace("__LAYOUT_SCRIPT__", script)
        result = subprocess.run([shutil.which("node"), "-e", harness], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
