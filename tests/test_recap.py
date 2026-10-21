import unittest
from matchmind.generator import generate_match
from matchmind.recap import post_match, facts, social

class Recap(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.ms = {s: generate_match(s) for s in range(40)}
    def test_facts_consistent_with_events(self):
        for m, ev in self.ms.values():
            f = facts(m, ev)
            self.assertEqual(f["score"], ev[-1]["meta"]["score"])
            self.assertEqual(len(f["goals"]), sum(f["score"].values()))
            if f["winner"]: self.assertGreater(f["score"][f["winner"]], min(f["score"].values()))
            if f["comeback"]: self.assertIsNotNone(f["winner"])
    def test_all_languages_distinct_and_mention_score(self):
        for m, ev in self.ms.values():
            out = {l: post_match(m, ev, l) for l in ("en", "es", "it")}
            sc = ev[-1]["meta"]["score"]; line = f"{sc[m['home']]}-{sc[m['away']]}"
            self.assertEqual(len({o["article"] for o in out.values()}), 3)
            for o in out.values():
                self.assertIn(line, o["social"]); self.assertLessEqual(len(o["social"]), 280)
                self.assertIn("#MatchMind", o["social"]); self.assertNotIn("{", o["article"] + o["social"])
                for g in o["facts"]["goals"]: self.assertIn(g["player"], o["article"])
    def test_localised_vocab_and_story_hooks(self):
        m, ev = self.ms[8]                       # demo match: away comeback with a penalty
        en, es, it = (post_match(m, ev, l) for l in ("en", "es", "it"))
        self.assertTrue(en["facts"]["comeback"])
        self.assertIn("coming from behind", en["article"]); self.assertIn("remontar", es["article"]); self.assertIn("rimonta", it["article"])
        self.assertIn("(pen.)", es["article"]); self.assertIn("(rig.)", it["article"])
        m0, ev0 = self.ms[5]                     # 0-0
        self.assertIn("0-0", post_match(m0, ev0, "it")["article"]); self.assertIn("sin goles", post_match(m0, ev0, "es")["article"])
    def test_social_limit(self):
        m, ev = self.ms[8]; self.assertLessEqual(len(social(facts(m, ev), "es", limit=60)), 60)

if __name__ == "__main__": unittest.main()
