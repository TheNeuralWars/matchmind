import unittest
from matchmind.generator import generate_match
from matchmind.pipeline import Orchestrator, recap
from matchmind.i18n import WHY, CASUAL, LANGS, render

KINDS = ["goal", "big_chance", "shot", "speed_burst", "line_breaking_pass", "momentum_swing", "chaos_spike"]
P = dict(name="Luca Ferro", team="NOR", opp="SOU", lead="NOR", momentum=0.42, chaos=0.55, xg=0.08, outcome="saved",
         pressure=True, team_xg=1.3, speed=34.1, dist=22.0, metres=31.0)

class I18n(unittest.TestCase):
    def test_all_kinds_all_langs(self):
        for lang in LANGS:
            for k in KINDS:
                for persona in ("analyst", "casual"):
                    t = render(k, P, lang, persona)
                    self.assertTrue(t and "{" not in t and "[ES]" not in t and "[IT]" not in t, (lang, k, t))
    def test_languages_really_differ(self):
        for k in KINDS:
            self.assertEqual(len({render(k, P, l) for l in LANGS}), 3, k)
            self.assertEqual(len({render(k, P, l, "casual") for l in LANGS}), 3, k)
    def test_localised_vocab(self):
        self.assertIn("parada", render("big_chance", P, "es"))
        self.assertIn("parata", render("big_chance", P, "it"))
        self.assertIn("¡GOOOL!", render("goal", P, "es", "casual"))
        self.assertIn("muy por encima", render("goal", P, "es"))
        self.assertIn("sì", render("shot", P, "it"))
    def test_casual_has_no_jargon(self):
        for lang in LANGS:
            for k in KINDS: self.assertNotIn("xG", render(k, P, lang, "casual"))
    def test_unknown_lang_falls_back_to_en(self):
        self.assertEqual(render("goal", P, "de"), render("goal", P, "en"))
    def test_pipeline_end_to_end(self):
        meta, ev = generate_match(7)
        profs = {l: {"persona": "casual", "club": "NOR", "lang": l} for l in LANGS}
        profs.update({f"a_{l}": {"persona": "analyst", "lang": l} for l in LANGS})
        o = Orchestrator(meta, profs); cues = {p: [] for p in profs}
        for e in ev:
            for p, c in o.step(e)[1].items(): cues[p] += c
        for p, cs in cues.items():
            self.assertTrue(cs, p)
            self.assertTrue(all(c["lang"] == profs[p]["lang"] and "[" not in c["text"] for c in cs))
        self.assertNotEqual(cues["es"][0]["text"], cues["it"][0]["text"])
        self.assertIn("Final del partido", recap(o, "es")); self.assertIn("Triplice fischio", recap(o, "it"))

if __name__ == "__main__": unittest.main()
