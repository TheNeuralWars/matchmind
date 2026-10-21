"""Specialised agents sharing MatchState. Each agent has one role; the Orchestrator hands off between them."""
from .llm import chat
from .i18n import render, norm

class AnalystAgent:
    """Detects key moments (with thresholds) from the event + state."""
    SPEED_KMH = 33.0
    COOLDOWN_S = {"momentum_swing": 300, "chaos_spike": 420, "speed_burst": 480}
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
        if k == "free_kick" and e["meta"].get("kind") == "penalty": out.append(("penalty_awarded", 0.9))
        if k == "card" and e["outcome"] == "red": out.append(("red_card", 0.9))
        if k == "carry" and e["meta"]["top_speed_kmh"] >= self.SPEED_KMH: out.append(("speed_burst", 0.6))
        if k == "pass" and e["outcome"] == "success" and e["end_x"] - e["x"] >= 30: out.append(("line_breaking_pass", 0.5))
        if prev is not None and (prev["momentum"] > 0) != (st["momentum"] > 0) and abs(st["momentum"] - prev["momentum"]) >= 0.3: out.append(("momentum_swing", 0.7))
        if prev is not None and prev["chaos"] < 0.5 <= st["chaos"]: out.append(("chaos_spike", 0.6))
        return out

class ExplainerAgent:
    """Turns a moment into WHY it matters, with evidence fields judges/analysts can audit.
    Keeps language-neutral params so Narrator can render natively in EN/ES/IT."""
    def explain(self, kind, e, st, meta, lang="en"):
        name = meta["players"][e["player"]]["name"]; tm = e["team"]; opp = meta["away"] if tm == meta["home"] else meta["home"]
        ev = {"minute": e["minute"], "team": tm, "player": name, "momentum": st["momentum"], "chaos": st["chaos"]}
        p = {"name": name, "team": tm, "opp": opp, "momentum": st["momentum"], "chaos": st["chaos"],
             "lead": meta["home"] if st["momentum"] > 0 else meta["away"]}
        if kind in ("goal", "big_chance", "shot"):
            p.update(xg=e["xg"], outcome=e["outcome"], pressure=bool(e.get("pressure")), team_xg=st["teams"][tm]["xg"])
        elif kind == "speed_burst":
            p.update(speed=e["meta"]["top_speed_kmh"], dist=e["meta"]["distance_m"])
        elif kind == "line_breaking_pass":
            p.update(metres=e["end_x"] - e["x"])
        return {"kind": kind, "why": render(kind, p, lang), "params": p, "evidence": ev}

class NarratorAgent:
    """Writes commentary lines; uses Azure AI Foundry model when configured, else native EN/ES/IT templates."""
    LANG_NAME = {"en": "English", "es": "Spanish (natural Spanish football commentary)", "it": "Italian (natural Italian telecronaca)"}
    def narrate(self, insight, persona, lang="en"):
        lang = norm(lang)
        style = "data-rich, precise, cite numbers" if persona == "analyst" else "short, warm, exciting, no jargon"
        txt = chat(f"You are a football match narrator. Style: {style}. Language: {self.LANG_NAME[lang]}. One sentence, max 30 words. Only use facts provided.", insight["why"])
        if txt: return txt, "foundry"
        if "params" not in insight: return insight["why"], "template"
        return render(insight["kind"], insight["params"], lang, "casual" if persona == "casual" else "analyst"), "template"

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
                "data": {"score": st["score"], "momentum": st["momentum"], "possession": st["possession"]}, "lang": norm(profile.get("lang", "en"))}
