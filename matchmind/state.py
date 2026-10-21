"""Interpret stage: incremental aggregation of events into match state."""
from collections import defaultdict, deque
import math

class MatchState:
    def __init__(self, meta):
        self.meta = meta; self.home, self.away = meta["home"], meta["away"]
        self.score = {self.home: 0, self.away: 0}
        self.stats = {t: defaultdict(float) for t in (self.home, self.away)}
        self.player = defaultdict(lambda: defaultdict(float))
        self.window = deque(maxlen=40)  # recent events for momentum
        self.last = None
    def ingest(self, e):
        s, tm = self.stats[e["team"]], e["team"]; pl = self.player[e["player"]]
        k = e["type"]
        if k == "pass":
            s["passes"] += 1; pl["passes"] += 1
            if e["outcome"] == "success": s["passes_ok"] += 1; pl["passes_ok"] += 1
            d = math.hypot(e["end_x"] - e["x"], e["end_y"] - e["y"]); s["pass_dist"] += d
            if e["end_x"] - e["x"] > 15 and e["outcome"] == "success": s["progressive"] += 1
            if e.get("pressure"): s["passes_under_pressure"] += 1
        elif k == "shot":
            s["shots"] += 1; s["xg"] += e["xg"]; pl["shots"] += 1; pl["xg"] += e["xg"]
            if e["outcome"] == "goal": self.score[tm] += 1; pl["goals"] += 1
        elif k == "tackle":
            s["tackles"] += 1; s["tackles_won"] += e["outcome"] == "won"
        elif k == "possession_change":
            s["recoveries"] += 1
        elif k == "corner": s["corners"] += 1
        elif k == "foul": s["fouls"] += 1
        elif k == "card": s["yellow" if e["outcome"] == "yellow" else "red"] += 1
        elif k == "carry":
            pl["distance_m"] += e["meta"]["distance_m"]; pl["top_speed_kmh"] = max(pl["top_speed_kmh"], e["meta"]["top_speed_kmh"])
        if k in ("pass", "carry", "shot"): s["touches"] += 1
        if k not in ("card", "substitution", "full_time"): self.window.append(e)
        self.last = e
    def possession(self):
        a, b = self.stats[self.home]["touches"], self.stats[self.away]["touches"]
        return {self.home: round(100 * a / max(1, a + b)), self.away: round(100 * b / max(1, a + b))}
    def momentum(self):
        """-1..1, positive = home on top over the recent window (territory + threat + duels)."""
        v = 0.0
        for e in self.window:
            sgn = 1 if e["team"] == self.home else -1
            v += sgn * (0.2 + (e.get("xg") or 0) * 5 + (0.3 if e["type"] == "tackle" and e["outcome"] == "won" else 0) + (e["x"] - 52.5) / 105)
        return round(max(-1, min(1, v / 20)), 2)
    def chaos(self):
        """Share of recent events that are turnovers/duels/pressured: control (0) vs chaos (1)."""
        if not self.window: return 0.0
        c = sum(1 for e in self.window if e["type"] in ("tackle", "possession_change") or e.get("pressure") or e.get("outcome") == "fail")
        return round(c / len(self.window), 2)
    def snapshot(self):
        def team(t):
            s = self.stats[t]
            return {"passes": int(s["passes"]), "pass_acc": round(100 * s["passes_ok"] / max(1, s["passes"])), "shots": int(s["shots"]), "xg": round(s["xg"], 2), "tackles_won": int(s["tackles_won"]), "progressive_passes": int(s["progressive"]),
                    "corners": int(s["corners"]), "fouls": int(s["fouls"]), "yellow": int(s["yellow"]), "red": int(s["red"])}
        return {"minute": self.last["minute"] if self.last else 0, "score": dict(self.score), "possession": self.possession(), "momentum": self.momentum(), "chaos": self.chaos(), "teams": {t: team(t) for t in (self.home, self.away)}}
