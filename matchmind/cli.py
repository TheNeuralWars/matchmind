import argparse, json
from .generator import generate_match, DEMO_SEED
from .pipeline import Orchestrator, recap
from .recap import post_match

DEFAULT_PROFILES = {"analyst": {"persona": "analyst", "lang": "en"}, "casual_fan": {"persona": "casual", "club": "NOR", "lang": "en"}}

def main(argv=None):
    ap = argparse.ArgumentParser(description="MatchMind synthetic match insights")
    ap.add_argument("--seed", type=int, default=DEMO_SEED); ap.add_argument("--profile", default="casual_fan")
    ap.add_argument("--lang", default="en", choices=["en", "es", "it"])
    ap.add_argument("--dump-events", help="write synthetic events JSONL here")
    a = ap.parse_args(argv)
    meta, events = generate_match(a.seed)
    if a.dump_events:
        with open(a.dump_events, "w") as f:
            for e in events: f.write(json.dumps(e) + "\n")
    o = Orchestrator(meta, DEFAULT_PROFILES)
    for e in events:
        _, out = o.step(e)
        for cue in out.get(a.profile, []): print(f"{cue['minute']:>2}'  {cue['text']}")
    print(recap(o))
    pm = post_match(meta, events, a.lang)
    print("\n" + pm["article"] + "\n\n" + pm["social"])

if __name__ == "__main__": main()
