import json, threading, unittest, urllib.request
from http.server import ThreadingHTTPServer
from matchmind.server import H

class Server(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), H); cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
    @classmethod
    def tearDownClass(cls): cls.srv.shutdown(); cls.srv.server_close()
    def get(self, path): return urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=30).read().decode()
    def events(self, lang):
        body = self.get(f"/stream?seed=7&persona=casual&club=NOR&lang={lang}&speed=1000000")
        out = []
        for block in body.strip().split("\n\n"):
            ev, data = block.split("\n", 1)
            out.append((ev[7:], json.loads(data[6:])))
        return out
    def test_health_and_ui(self):
        self.assertEqual(json.loads(self.get("/health")), {"ok": True})
        html = self.get("/")
        for l in ("en", "es", "it"): self.assertIn(f"<option>{l}</option>", html)
    def test_language_switch(self):
        recaps = {"es": "Final del partido", "it": "Triplice fischio", "en": "Full time"}
        texts = {}
        for lang, word in recaps.items():
            ev = self.events(lang)
            cues = [d for e, d in ev if e == "cue"]
            self.assertTrue(cues and all(c["lang"] == lang for c in cues))
            self.assertIn(word, [d for e, d in ev if e == "recap"][0]["text"])
            texts[lang] = cues[0]["text"]
        self.assertEqual(len(set(texts.values())), 3)

if __name__ == "__main__": unittest.main()
