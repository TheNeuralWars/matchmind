import unittest
from matchmind.generator import generate_match, xg_for
from matchmind.pipeline import Orchestrator, recap

P = {"analyst": {"persona": "analyst"}, "casual": {"persona": "casual", "club": "NOR"}}

class T(unittest.TestCase):
    def test_deterministic(self):
        self.assertEqual(generate_match(3)[1], generate_match(3)[1])
    def test_event_schema(self):
        meta, ev = generate_match(1)
        self.assertGreater(len(ev), 500)
        types = {e["type"] for e in ev}
        self.assertTrue({"pass", "shot", "tackle", "possession_change", "carry"} <= types)
        self.assertTrue(all(e["player"] in meta["players"] for e in ev))
        self.assertEqual(ev[-1]["type"], "full_time")
    def test_xg_bounds(self):
        self.assertGreater(xg_for(100, 34), xg_for(75, 10))
    def test_score_matches_goals(self):
        meta, ev = generate_match(11); o = Orchestrator(meta, P)
        for e in ev: o.step(e)
        goals = sum(1 for e in ev if e["type"] == "shot" and e["outcome"] == "goal")
        self.assertEqual(sum(o.state.score.values()), goals)
        self.assertIn("Full time", recap(o))
    def test_personas_differ(self):
        meta, ev = generate_match(7); o = Orchestrator(meta, P); a, c = [], []
        for e in ev:
            _, out = o.step(e); a += out["analyst"]; c += out["casual"]
        self.assertGreater(len(a), len(c))
        self.assertTrue(all({"t", "template", "text", "duration_s"} <= set(x) for x in a))
        self.assertEqual({x["source"] for x in a}, {"template"})

if __name__ == "__main__": unittest.main()
