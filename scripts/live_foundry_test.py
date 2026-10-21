"""Live narration check against Azure OpenAI/Foundry through NarratorAgent (reads .env). Writes docs/live/foundry_narration.json (no secrets)."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for l in open(os.path.join(os.path.dirname(__file__), "..", ".env")):
    if "=" in l and not l.startswith("#"): k, v = l.strip().split("=", 1); os.environ.setdefault(k, v)
from matchmind.agents import NarratorAgent
from matchmind import tools as T
moms = [m for m in T.get_key_moments(8, None, limit=80)["moments"] if m["kind"] in ("goal", "penalty", "big_chance")]
rows, n = [], NarratorAgent()
for m in moms[:3]:
    for lang in ("en", "es", "it"):
        for persona in ("analyst", "casual"):
            t0 = time.time(); txt, src = n.narrate({"why": m["why"]}, persona, lang)
            rows.append({"moment": m.get("id"), "lang": lang, "persona": persona, "source": src, "ms": int((time.time()-t0)*1000), "text": txt})
out = {"deployment": os.environ.get("AZURE_OPENAI_DEPLOYMENT"), "model": "gpt-4.1-mini (2025-04-14)", "region": "swedencentral",
       "foundry_lines": sum(r["source"] == "foundry" for r in rows), "total": len(rows), "rows": rows}
json.dump(out, open("docs/live/foundry_narration.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: out[k] for k in ("foundry_lines", "total")})); [print(r["lang"], r["persona"], r["source"], r["ms"], "|", r["text"]) for r in rows]
