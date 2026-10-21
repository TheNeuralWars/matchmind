"""Precompute replays so the web UI runs with no server (GitHub Pages / any static host, $0).

python -m matchmind.static_export --out site --seeds 8,12,6,1,3
Writes site/index.html (the same UI, static mode) + site/replay/<seed>/base.json (meta, per-minute states, shots)
and site/replay/<seed>/<persona>-<lang>-<club>.json (cues + recap). The UI replays them on the same timeline as SSE.
"""
import argparse, json, os, shutil
from .generator import generate_match, DEMO_SEED
from .pipeline import Orchestrator, recap
from .recap import post_match

PERSONAS, LANGS, CLUBS = ("casual", "analyst"), ("en", "es", "it"), ("", "NOR", "SOU")
WEB = os.path.join(os.path.dirname(__file__), "..", "web", "index.html")

def pid(persona, lang, club): return f"{persona}-{lang}-{club or 'none'}"

def export_seed(seed, out):
    meta, events = generate_match(seed)
    profiles = {pid(p, l, c): {"persona": p, "lang": l, "club": c or None} for p in PERSONAS for l in LANGS for c in CLUBS}
    o = Orchestrator(meta, profiles)
    base = [[0, "meta", {"home": meta["home"], "away": meta["away"], "players": meta["players"]}]]
    per = {k: [] for k in profiles}
    last_min, last_score = None, None
    for e in events:
        st, out_cues = o.step(e)
        if st["minute"] != last_min or st["score"] != last_score or e["type"] == "full_time":
            base.append([e["t"], "state", st]); last_min, last_score = st["minute"], dict(st["score"])
        if e["type"] == "shot":
            base.append([e["t"], "shot", {k: e.get(k) for k in ("t", "minute", "team", "player", "x", "y", "xg", "outcome")} | {"set_piece": e["meta"].get("set_piece")}])
        for k, cues in out_cues.items():
            per[k] += [[e["t"], "cue", c] for c in cues]
    end = events[-1]["t"] + 0.1
    d = os.path.join(out, "replay", str(seed)); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "base.json"), "w") as f: json.dump(base, f, separators=(",", ":"), ensure_ascii=False)
    recaps = {l: post_match(meta, events, l) for l in LANGS}
    for k, prof in profiles.items():
        pm = recaps[prof["lang"]]
        rows = per[k] + [[end, "recap", {"text": recap(o, prof["lang"]), "article": pm["article"], "social": pm["social"]}]]
        with open(os.path.join(d, k + ".json"), "w") as f: json.dump(rows, f, separators=(",", ":"), ensure_ascii=False)
    return {"seed": seed, "score": events[-1]["meta"]["score"], "files": len(profiles) + 1}

def export(out, seeds):
    os.makedirs(out, exist_ok=True)
    html = open(WEB, encoding="utf-8").read().replace("<script>", "<script>window.MATCHMIND_STATIC=" + json.dumps({"seeds": seeds}) + ";</script><script>", 1)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f: f.write(html)
    open(os.path.join(out, ".nojekyll"), "w").close()
    return [export_seed(s, out) for s in seeds]

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="site"); ap.add_argument("--seeds", default=f"{DEMO_SEED},12,6,1,3")
    a = ap.parse_args(argv)
    print(json.dumps(export(a.out, [int(s) for s in a.seeds.split(",")])))

if __name__ == "__main__": main()
