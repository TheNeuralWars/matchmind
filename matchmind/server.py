"""Tiny stdlib HTTP server: GET / (overlay demo UI), GET /stream?seed=&persona=&club=&lang=&speed= (SSE: meta/state/shot/cue/recap), GET /health."""
import json, os, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from .generator import generate_match, DEMO_SEED
from .pipeline import Orchestrator, recap
from .recap import post_match

WEB = os.path.join(os.path.dirname(__file__), "..", "web", "index.html")

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        u = urlparse(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path == "/health":
            return self._send(200, "application/json", b'{"ok":true}')
        if u.path == "/":
            with open(WEB, "rb") as f: return self._send(200, "text/html", f.read())
        if u.path == "/stream":
            meta, events = generate_match(int(q.get("seed", DEMO_SEED)))
            prof = {"persona": q.get("persona", "casual"), "club": q.get("club") or None, "lang": q.get("lang", "en"), "player_id": q.get("player") or None}
            o = Orchestrator(meta, {"me": prof}); speed = float(q.get("speed", 60))
            self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.send_header("Cache-Control", "no-cache"); self.end_headers()
            try:
                self._sse("meta", {"home": meta["home"], "away": meta["away"], "players": meta["players"]})
                last_t = 0
                for e in events:
                    time.sleep(max(0, (e["t"] - last_t) / speed)); last_t = e["t"]
                    st, out = o.step(e)
                    self._sse("state", st)
                    if e["type"] == "shot":
                        self._sse("shot", {k: e.get(k) for k in ("t", "minute", "team", "player", "x", "y", "xg", "outcome")} | {"set_piece": e["meta"].get("set_piece")})
                    for cue in out["me"]: self._sse("cue", cue)
                pm = post_match(meta, events, prof["lang"])
                self._sse("recap", {"text": recap(o, prof["lang"]), "article": pm["article"], "social": pm["social"]})
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        self._send(404, "text/plain", b"not found")
    def _sse(self, ev, data):
        self.wfile.write(f"event: {ev}\ndata: {json.dumps(data)}\n\n".encode()); self.wfile.flush()
    def _send(self, code, ct, body):
        self.send_response(code); self.send_header("Content-Type", ct); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass

def main():
    port = int(os.getenv("PORT", 8000)); print(f"MatchMind on :{port}")
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()

if __name__ == "__main__": main()
