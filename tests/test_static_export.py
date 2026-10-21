import json, os, tempfile, unittest
from matchmind.static_export import export

class StaticExport(unittest.TestCase):
    def test_export_replays_match_pipeline(self):
        with tempfile.TemporaryDirectory() as d:
            res = export(d, [8])
            self.assertEqual(res[0]["files"], 19)
            html = open(os.path.join(d, "index.html")).read()
            self.assertIn("window.MATCHMIND_STATIC", html); self.assertIn("class Replay", html)
            with open(os.path.join(d, "replay/8/base.json")) as f: base = json.load(f)
            shots = [x for x in base if x[1] == "shot"]
            final = [x for x in base if x[1] == "state"][-1][2]["score"]
            self.assertEqual(sum(s[2]["outcome"] == "goal" for s in shots), sum(final.values()))
            self.assertEqual(final, res[0]["score"])
            self.assertEqual([x[0] for x in base], sorted(x[0] for x in base))
            with open(os.path.join(d, "replay/8/casual-it-NOR.json")) as f: p = json.load(f)
            self.assertEqual(p[-1][1], "recap"); self.assertIn("Marcatori", p[-1][2]["article"])
            self.assertTrue(all(c[2]["lang"] == "it" for c in p if c[1] == "cue"))
            with open(os.path.join(d, "replay/8/analyst-en-none.json")) as f: a = json.load(f)
            self.assertGreater(len(a), len(p))

if __name__ == "__main__": unittest.main()
