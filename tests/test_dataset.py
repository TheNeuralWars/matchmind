import csv, json, os, tempfile, unittest
from matchmind.dataset import export, parse_seeds, CSV_FIELDS

class Dataset(unittest.TestCase):
    def test_parse_seeds(self): self.assertEqual(parse_seeds("0-2,7"), [0, 1, 2, 7])
    def test_export_consistent_and_deterministic(self):
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            s = export(d1, [1, 2, 3], random_styles=True); export(d2, [1, 2, 3], random_styles=True)
            for f in ("events.csv", "events.jsonl", "matches.json"):
                self.assertEqual(open(os.path.join(d1, f)).read(), open(os.path.join(d2, f)).read(), f)
            rows = list(csv.DictReader(open(os.path.join(d1, "events.csv"))))
            jl = [json.loads(l) for l in open(os.path.join(d1, "events.jsonl"))]
            self.assertEqual(len(rows), len(jl)); self.assertEqual(len(rows), s["n_events"])
            self.assertEqual(list(rows[0].keys()), CSV_FIELDS)
            m = json.load(open(os.path.join(d1, "matches.json")))
            self.assertEqual(m["summary"]["n_matches"], 3)
            for match in m["matches"]:
                g = sum(1 for e in jl if e["match_id"] == match["match_id"] and e["type"] == "shot" and e["outcome"] == "goal")
                self.assertEqual(sum(match["score"].values()), g)
                self.assertIn(match["formations"]["NOR"], ("4-3-3", "4-4-2", "4-2-3-1", "3-5-2"))

if __name__ == "__main__": unittest.main()
