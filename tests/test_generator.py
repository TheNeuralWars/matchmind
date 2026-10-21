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
        def fwd(st): return statistics.mean(e["end_x"] - e["x"] for s in self.SEEDS for e in generate_match(s, home_style=st)[1] if e["type"] == "pass" and e["team"] == "NOR")
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
