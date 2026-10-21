"""Orchestrator: Ingest -> Interpret -> Explain -> Render -> Personalize, with agent handoffs and failure recovery."""
from .state import MatchState
from .agents import AnalystAgent, ExplainerAgent, NarratorAgent, PersonalizerAgent, RendererAgent

class Orchestrator:
    def __init__(self, meta, profiles):
        self.meta, self.profiles = meta, profiles
        self.state = MatchState(meta)
        self.analyst, self.explainer, self.narrator = AnalystAgent(), ExplainerAgent(), NarratorAgent()
        self.personalizer, self.renderer = PersonalizerAgent(), RendererAgent()
        self.prev = None; self.log = []
    def step(self, e):
        self.state.ingest(e)                                   # ingest + interpret
        st = self.state.snapshot()
        out = {pid: [] for pid in self.profiles}
        for kind, base in self.analyst.detect(e, st, self.prev):
            ins = self.explainer.explain(kind, e, st, self.meta)  # explain
            for pid, prof in self.profiles.items():               # personalize
                sc = self.personalizer.score(ins, base, prof, self.meta)
                if sc < self.personalizer.threshold(prof): continue
                try:
                    text, src = self.narrator.narrate(ins, prof.get("persona", "casual"), prof.get("lang", "en"))
                except Exception as ex:                              # recovery: fall back to raw explanation
                    text, src = ins["why"], f"fallback:{type(ex).__name__}"
                cue = self.renderer.overlay(e, ins, text, st, prof)  # render
                cue.update(score_rank=sc, source=src, evidence=ins["evidence"])
                out[pid].append(cue)
        self.prev = st
        return st, out

def recap(orch):
    st = orch.state.snapshot(); h, a = orch.meta["home"], orch.meta["away"]
    top = max(orch.state.player.items(), key=lambda kv: kv[1]["xg"] + 2 * kv[1]["goals"], default=(None, {}))
    star = orch.meta["players"][top[0]]["name"] if top[0] else "n/a"
    return (f"Full time: {h} {st['score'][h]}-{st['score'][a]} {a}. xG {st['teams'][h]['xg']}-{st['teams'][a]['xg']}, "
            f"possession {st['possession'][h]}%-{st['possession'][a]}%. Standout: {star}.")
