"""Specialised agents sharing MatchState. Each agent has one role; the Orchestrator hands off between them."""
from .llm import chat

class AnalystAgent:
    """Detects key moments (with thresholds) from the event + state."""
    SPEED_KMH = 33.0
    COOLDOWN_S = {"momentum_swing": 300, "chaos_spike": 420, "speed_burst": 180}
    def __init__(self): self._last = {}
    def _ok(self, kind, t):
        if t - self._last.get(kind, -1e9) < self.COOLDOWN_S.get(kind, 0): return False
        self._last[kind] = t; return True
    def detect(self, e, st, prev):
        return [(k, b) for k, b in self._detect(e, st, prev) if self._ok(k, e["t"])]
    def _detect(self, e, st, prev):
        out = []
        k = e["type"]
        if k == "shot" and e["outcome"] == "goal": out.append(("goal", 1.0))
        elif k == "shot" and e["xg"] >= 0.25: out.append(("big_chance", 0.8))
        elif k == "shot": out.append(("shot", 0.4))
        if k == "carry" and e["meta"]["top_speed_kmh"] >= self.SPEED_KMH: out.append(("speed_burst", 0.6))
        if k == "pass" and e["outcome"] == "success" and e["end_x"] - e["x"] >= 30: out.append(("line_breaking_pass", 0.5))
        if prev is not None and (prev["momentum"] > 0) != (st["momentum"] > 0) and abs(st["momentum"] - prev["momentum"]) >= 0.3: out.append(("momentum_swing", 0.7))
        if prev is not None and prev["chaos"] < 0.5 <= st["chaos"]: out.append(("chaos_spike", 0.6))
        return out

class ExplainerAgent:
    """Turns a moment into WHY it matters, with evidence fields judges/analysts can audit."""
    def explain(self, kind, e, st, meta):
        name = meta["players"][e["player"]]["name"]; tm = e["team"]; opp = meta["away"] if tm == meta["home"] else meta["home"]
        ev = {"minute": e["minute"], "team": tm, "player": name, "momentum": st["momentum"], "chaos": st["chaos"]}
        if kind == "goal":
            why = f"{name} converts a {e['xg']:.2f} xG chance" + (" — well above expectation" if e["xg"] < 0.15 else "") + f"; {tm} total xG now {st['teams'][tm]['xg']}."
        elif kind == "big_chance":
            why = f"{name} had a {e['xg']:.2f} xG look ({e['outcome']}). {tm} are creating quality, not just volume."
        elif kind == "shot":
            why = f"Low-value attempt ({e['xg']:.2f} xG) from {name}; pressure={'yes' if e.get('pressure') else 'no'}."
        elif kind == "speed_burst":
            why = f"{name} hits {e['meta']['top_speed_kmh']} km/h over {e['meta']['distance_m']} m, stretching {opp}'s line."
        elif kind == "line_breaking_pass":
            why = f"{name} breaks lines with a {e['end_x'] - e['x']:.0f} m progressive pass, bypassing {opp}'s press."
        elif kind == "momentum_swing":
            lead = meta["home"] if st["momentum"] > 0 else meta["away"]
            why = f"Momentum flips to {lead} ({st['momentum']:+.2f}) — territory and duel wins over the last ~40 actions."
        else:
            why = f"Game turns chaotic (chaos index {st['chaos']}): turnovers and pressured actions dominate; control is up for grabs."
        return {"kind": kind, "why": why, "evidence": ev}

TEMPL = {
    "en": "{why}", "es": "[ES] {why}", "it": "[IT] {why}",
}
class NarratorAgent:
    """Writes commentary lines; uses Azure AI Foundry model when configured, else deterministic template."""
    def narrate(self, insight, persona, lang="en"):
        style = "data-rich, precise, cite numbers" if persona == "analyst" else "short, warm, exciting, no jargon"
        txt = chat(f"You are a football match narrator. Style: {style}. Language: {lang}. One sentence, max 30 words. Only use facts provided.", insight["why"])
        if txt: return txt, "foundry"
        base = insight["why"]
        if persona == "casual":
            base = {"goal": "GOAL! ", "big_chance": "So close! ", "speed_burst": "Rapid! ", "momentum_swing": "The tide is turning! ", "chaos_spike": "It's getting wild! "}.get(insight["kind"], "") + base.split(";")[0].split(" — ")[0]
        return TEMPL.get(lang, "{why}").format(why=base), "template"

class PersonalizerAgent:
    """Filters/re-ranks insights per fan profile: persona, favourite club, focus player, language."""
    def score(self, insight, base, profile, meta):
        s = base
        if profile.get("club") and insight["evidence"]["team"] == profile["club"]: s += 0.3
        fp = profile.get("player_id")
        if fp and meta["players"].get(fp, {}).get("name") == insight["evidence"]["player"]: s += 0.6
        if profile.get("persona") == "casual" and insight["kind"] in ("shot", "line_breaking_pass", "chaos_spike"): s -= 0.3
        return round(s, 2)
    def threshold(self, profile):
        return 0.55 if profile.get("persona") == "casual" else 0.35

class RendererAgent:
    """Produces timed, machine-readable overlay cues for a broadcast graphics engine."""
    def overlay(self, e, insight, text, st, profile):
        return {"t": e["t"], "minute": e["minute"], "duration_s": 6 if insight["kind"] in ("goal", "momentum_swing") else 4,
                "template": f"lower_third.{insight['kind']}", "anchor": "bottom_left", "text": text,
                "data": {"score": st["score"], "momentum": st["momentum"], "possession": st["possession"]}, "lang": profile.get("lang", "en")}
