import unittest, statistics
from matchmind.generator import generate_match, GENERATOR_VERSION

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
