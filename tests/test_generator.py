import unittest, statistics
from matchmind.generator import generate_match, GENERATOR_VERSION, fatigue

def goals(ev): return sum(1 for e in ev if e["type"] == "shot" and e["outcome"] == "goal")

class GeneratorV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.runs = [generate_match(s) for s in range(120)]
    def test_version_and_determinism(self):
        m, ev = generate_match(42)
        self.assertEqual(m["generator_version"], GENERATOR_VERSION)
        self.assertEqual(ev, generate_match(42)[1])
        self.assertNotEqual(ev, generate_match(43)[1])
    def test_realistic_goal_totals(self):
        g = [goals(ev) for _, ev in self.runs]
        self.assertTrue(2.0 <= statistics.mean(g) <= 3.4, statistics.mean(g))
        self.assertGreaterEqual(sum(1 for x in g if x <= 4) / len(g), 0.75)
        self.assertLessEqual(max(g), 9)
    def test_realistic_shot_volume_and_xg(self):
        shots = [[e for e in ev if e["type"] == "shot"] for _, ev in self.runs]
        self.assertTrue(18 <= statistics.mean(len(s) for s in shots) <= 34)
        self.assertTrue(1.8 <= statistics.mean(sum(e["xg"] for e in s) for s in shots) <= 3.6)
    def test_sample_match_not_high_scoring(self):
        self.assertLessEqual(goals(generate_match(7)[1]), 4)

if __name__ == "__main__": unittest.main()

def pass_acc(ev, team):
    ps = [e for e in ev if e["type"] == "pass" and e["team"] == team]
    return sum(e["outcome"] == "success" for e in ps) / len(ps)

class StylesFormationsFatigue(unittest.TestCase):
    SEEDS = range(40)
    def test_possession_style_raises_pass_accuracy(self):
        lo = statistics.mean(pass_acc(generate_match(s, home_style={"possession": 0.1})[1], "NOR") for s in self.SEEDS)
        hi = statistics.mean(pass_acc(generate_match(s, home_style={"possession": 0.9})[1], "NOR") for s in self.SEEDS)
        self.assertGreater(hi, lo + 0.03)
    def test_directness_lengthens_passes(self):
        def fwd(st): return statistics.mean(e["end_x"] - e["x"] for s in self.SEEDS for e in generate_match(s, home_style=st)[1] if e["type"] == "pass" and e["team"] == "NOR" and e["x"] < 60)
        self.assertGreater(fwd({"directness": 0.9}), fwd({"directness": 0.1}) + 3)
    def test_pressing_wins_more_tackles(self):
        def won(st): return sum(e["outcome"] == "won" for s in self.SEEDS for e in generate_match(s, away_style=st)[1] if e["type"] == "tackle" and e["team"] == "SOU")
        self.assertGreater(won({"pressing": 0.9}), won({"pressing": 0.1}) * 1.2)
    def test_formations(self):
        m, ev = generate_match(5, home_style={"formation": "3-5-2"}, away_style={"formation": "4-4-2"})
        self.assertEqual(m["formations"], {"NOR": "3-5-2", "SOU": "4-4-2"})
        self.assertEqual(sum(p["pos"] == "CB" for p in m["players"].values() if p["team"] == "NOR"), 3)
        with self.assertRaises(ValueError): generate_match(1, home_style={"formation": "2-2-6"})
    def test_fatigue_curve_and_late_game_effects(self):
        self.assertEqual(fatigue(30 * 60), 0.0); self.assertAlmostEqual(fatigue(90 * 60), 1.0)
        early = late = early_fail = late_fail = early_n = late_n = 0
        for s in self.SEEDS:
            for e in generate_match(s)[1]:
                if e["type"] == "pass":
                    if 15 <= e["minute"] < 45: early_n += 1; early_fail += e["outcome"] == "fail"
                    elif e["minute"] >= 75: late_n += 1; late_fail += e["outcome"] == "fail"
                if e["type"] == "shot" and e["meta"]["fatigue"] > 0.5: self.assertGreater(e["minute"], 74)
        self.assertGreater(late_fail / late_n, early_fail / early_n + 0.02)
    def test_styles_deterministic(self):
        kw = dict(home_style={"pressing": 0.8, "formation": "4-2-3-1"})
        self.assertEqual(generate_match(9, **kw), generate_match(9, **kw))

class SetPiecesCardsScoreState(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from matchmind.dataset import random_style
        cls.runs = [generate_match(s, home_style=random_style(s, "h"), away_style=random_style(s, "a")) for s in range(150)]
    def per_match(self, pred): return sum(1 for _, ev in self.runs for e in ev if pred(e)) / len(self.runs)
    def test_calibrated_with_set_pieces(self):
        self.assertTrue(2.4 <= self.per_match(lambda e: e["type"] == "shot" and e["outcome"] == "goal") <= 2.9)
    def test_set_piece_volumes(self):
        self.assertTrue(7 <= self.per_match(lambda e: e["type"] == "corner") <= 13)
        self.assertTrue(0.15 <= self.per_match(lambda e: e.get("meta", {}).get("set_piece") == "penalty") <= 0.45)
        self.assertGreater(self.per_match(lambda e: e.get("meta", {}).get("set_piece") == "free_kick"), 0.5)
        sp = self.per_match(lambda e: e["type"] == "shot" and e["outcome"] == "goal" and e["meta"]["set_piece"] != "open_play")
        self.assertTrue(0.3 <= sp <= 1.0, sp)
    def test_cards_and_duels(self):
        self.assertTrue(2 <= self.per_match(lambda e: e["type"] == "card" and e["outcome"] == "yellow") <= 4.5)
        self.assertTrue(0.04 <= self.per_match(lambda e: e["type"] == "card" and e["outcome"] == "red") <= 0.25)
        self.assertTrue(25 <= self.per_match(lambda e: e["type"] in ("tackle", "foul")) <= 50)   # was ~99
        self.assertTrue(12 <= self.per_match(lambda e: e["type"] == "foul") <= 25)
    def test_sent_off_player_takes_no_further_part(self):
        for _, ev in self.runs:
            reds = {e["player"]: e["seq"] for e in ev if e["type"] == "card" and e["outcome"] == "red"}
            for e in ev:
                if e["player"] in reds and e["type"] != "full_time": self.assertLessEqual(e["seq"], reds[e["player"]])
    def test_trailing_team_attacks_more(self):
        """Shots per minute of game time: trailing team vs leading team (score-state reaction)."""
        trail = lead = 0
        for _, ev in self.runs:
            sc = {}
            for e in ev:
                if e["type"] == "shot":
                    me, other = sc.get(e["team"], 0), sum(v for k, v in sc.items() if k != e["team"])
                    trail += me < other; lead += me > other
                    if e["outcome"] == "goal": sc[e["team"]] = me + 1
        self.assertGreater(trail, lead)
    def test_full_time_score_matches(self):
        for _, ev in self.runs:
            g = {}
            for e in ev:
                if e["type"] == "shot" and e["outcome"] == "goal": g[e["team"]] = g.get(e["team"], 0) + 1
            self.assertEqual({k: v for k, v in ev[-1]["meta"]["score"].items() if v}, g)
    def test_shot_locations_plausible(self):
        for _, ev in self.runs:
            for e in ev:
                if e["type"] == "shot":
                    self.assertLessEqual(e["x"], 100.5); self.assertTrue(8 <= e["y"] <= 60)
