"""Match-state tools shared by the MCP server and the Agent Framework adapter. Pure functions, JSON-serialisable outputs."""
from functools import lru_cache
from .generator import generate_match, DEMO_SEED
from .state import MatchState
from .agents import AnalystAgent, ExplainerAgent, NarratorAgent
from .i18n import norm

@lru_cache(maxsize=32)
def _replay(seed):
    """Full deterministic replay: per-event snapshots and every detected key moment."""
    meta, events = generate_match(seed)
    state, analyst, explainer = MatchState(meta), AnalystAgent(), ExplainerAgent()
    snaps, moments, prev = [], [], None
    for e in events:
        state.ingest(e); st = state.snapshot(); snaps.append((e["t"], st))
        for kind, base in analyst.detect(e, st, prev):
            ins = explainer.explain(kind, e, st, meta)
            moments.append({"id": f"{meta['match_id']}-{e['seq']}-{kind}", "t": e["t"], "minute": e["minute"], "kind": kind,
                            "importance": base, "team": e["team"], "why": ins["why"], "evidence": ins["evidence"], "_ins": ins})
        prev = st
    return meta, snaps, moments

def _at(seed, minute):
    meta, snaps, moments = _replay(int(seed))
    if minute is None: return meta, snaps[-1][1], moments
    cut = float(minute) * 60
    st = snaps[0][1]
    for t, s in snaps:
        if t > cut: break
        st = s
    return meta, st, [m for m in moments if m["t"] <= cut]

def _public(m): return {k: v for k, v in m.items() if not k.startswith("_")}

def get_score(seed=DEMO_SEED, minute=None):
    meta, st, _ = _at(seed, minute)
    return {"match_id": meta["match_id"], "minute": st["minute"], "home": meta["home"], "away": meta["away"], "score": st["score"],
            "xg": {t: st["teams"][t]["xg"] for t in st["teams"]}, "possession": st["possession"]}

def get_momentum(seed=DEMO_SEED, minute=None):
    meta, st, _ = _at(seed, minute)
    leader = None if st["momentum"] == 0 else (meta["home"] if st["momentum"] > 0 else meta["away"])
    return {"minute": st["minute"], "momentum": st["momentum"], "leader": leader, "chaos": st["chaos"],
            "note": "momentum in -1..1, positive = home on top over the last ~40 actions; chaos 0 = control, 1 = chaos"}

def get_key_moments(seed=DEMO_SEED, minute=None, kinds=None, min_importance=0.0, limit=20):
    _, _, ms = _at(seed, minute)
    ms = [m for m in ms if m["importance"] >= float(min_importance) and (not kinds or m["kind"] in kinds)]
    return {"count": len(ms), "moments": [_public(m) for m in ms[-int(limit):]]}

def explain_moment(moment_id, lang="en", persona="analyst"):
    seed = int(str(moment_id).split("-")[1])
    for m in _replay(seed)[2]:
        if m["id"] == moment_id:
            text, src = NarratorAgent().narrate(m["_ins"], persona, lang)
            return {"id": moment_id, "kind": m["kind"], "minute": m["minute"], "lang": norm(lang), "persona": persona,
                    "text": text, "source": src, "why_en": m["why"], "evidence": m["evidence"]}
    raise KeyError(f"unknown moment_id {moment_id}")

_SEED = {"type": "integer", "description": "Synthetic match seed (deterministic)", "default": DEMO_SEED}
_MIN = {"type": "number", "description": "Game minute to query state at; omit for full time"}
TOOLS = {
    "get_score": (get_score, "Score, xG and possession of a synthetic match at a given minute.",
                  {"type": "object", "properties": {"seed": _SEED, "minute": _MIN}}),
    "get_momentum": (get_momentum, "Momentum (-1..1, + = home) and control-vs-chaos index at a given minute.",
                     {"type": "object", "properties": {"seed": _SEED, "minute": _MIN}}),
    "get_key_moments": (get_key_moments, "Key moments detected by the Analyst agent (goals, big chances, penalties, red cards, momentum swings...).",
                        {"type": "object", "properties": {"seed": _SEED, "minute": _MIN,
                         "kinds": {"type": "array", "items": {"type": "string"}}, "min_importance": {"type": "number"}, "limit": {"type": "integer"}}}),
    "explain_moment": (explain_moment, "Explain why a key moment matters, in en/es/it, for an analyst or casual-fan persona.",
                       {"type": "object", "required": ["moment_id"], "properties": {"moment_id": {"type": "string"},
                        "lang": {"type": "string", "enum": ["en", "es", "it"]}, "persona": {"type": "string", "enum": ["analyst", "casual"]}}}),
}
