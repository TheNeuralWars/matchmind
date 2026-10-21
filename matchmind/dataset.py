"""Export synthetic matches as a dataset: events.csv, events.jsonl, matches.json (+ summary). Stdlib only.

python -m matchmind.dataset --out data/ --seeds 0-49 [--random-styles]
"""
import argparse, csv, json, os, random, statistics
from .generator import generate_match, FORMATIONS, GENERATOR_VERSION

CSV_FIELDS = ["match_id", "seq", "t", "minute", "type", "team", "player", "x", "y", "end_x", "end_y",
              "outcome", "xg", "pressure", "top_speed_kmh", "distance_m", "fatigue", "cause", "set_piece", "kind", "reason"]

def random_style(seed, side):
    r = random.Random(f"style-{seed}-{side}")
    return {"possession": round(r.random(), 2), "pressing": round(r.random(), 2), "directness": round(r.random(), 2),
            "formation": r.choice(sorted(FORMATIONS))}

def parse_seeds(spec):
    out = []
    for part in str(spec).split(","):
        a, _, b = part.partition("-")
        out += list(range(int(a), int(b) + 1)) if b else [int(a)]
    return out

def flat(match_id, e):
    m = e.get("meta", {})
    row = {k: e.get(k) for k in CSV_FIELDS}
    row.update(match_id=match_id, top_speed_kmh=m.get("top_speed_kmh"), distance_m=m.get("distance_m"),
               fatigue=m.get("fatigue"), cause=m.get("cause"),
               set_piece=m.get("set_piece"), kind=m.get("kind"), reason=m.get("reason"))
    return row

def export(out_dir, seeds, random_styles=False):
    os.makedirs(out_dir, exist_ok=True)
    matches, goals = [], []
    with open(os.path.join(out_dir, "events.csv"), "w", newline="") as fc, open(os.path.join(out_dir, "events.jsonl"), "w") as fj:
        w = csv.DictWriter(fc, fieldnames=CSV_FIELDS); w.writeheader()
        for s in seeds:
            hs, as_ = (random_style(s, "h"), random_style(s, "a")) if random_styles else (None, None)
            meta, ev = generate_match(s, home_style=hs, away_style=as_)
            score = {meta["home"]: 0, meta["away"]: 0}
            for e in ev:
                if e["type"] == "shot" and e["outcome"] == "goal": score[e["team"]] += 1
                fj.write(json.dumps({"match_id": meta["match_id"], **e}) + "\n"); w.writerow(flat(meta["match_id"], e))
            goals.append(sum(score.values()))
            matches.append({k: meta[k] for k in ("match_id", "seed", "home", "away", "generator_version", "styles", "formations", "players")}
                           | {"score": score, "n_events": len(ev)})
    summary = {"generator_version": GENERATOR_VERSION, "n_matches": len(matches), "n_events": sum(m["n_events"] for m in matches),
               "goals_per_match_mean": round(statistics.mean(goals), 2) if goals else 0,
               "share_0_to_4_goals": round(sum(g <= 4 for g in goals) / max(1, len(goals)), 2)}
    with open(os.path.join(out_dir, "matches.json"), "w") as f:
        json.dump({"summary": summary, "matches": matches}, f, indent=1)
    return summary

def main(argv=None):
    ap = argparse.ArgumentParser(description="Export MatchMind synthetic dataset")
    ap.add_argument("--out", default="data"); ap.add_argument("--seeds", default="0-49")
    ap.add_argument("--random-styles", action="store_true")
    a = ap.parse_args(argv)
    print(json.dumps(export(a.out, parse_seeds(a.seeds), a.random_styles)))

if __name__ == "__main__": main()
