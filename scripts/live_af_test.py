"""Live Microsoft Agent Framework run against Azure OpenAI (reads .env; needs `pip install agent-framework`). Writes docs/live/agent_framework_run.json."""
import asyncio, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for l in open(os.path.join(os.path.dirname(__file__), "..", ".env")):
    if "=" in l and not l.startswith("#"): k, v = l.strip().split("=", 1); os.environ.setdefault(k, v)
from matchmind.agent_framework_adapter import build_agent
import agent_framework
Q = [("en", "Seed 8: what was the score at minute 70 and who had momentum? Then explain the most important moment."),
     ("es", "Semilla 8: ¿cómo terminó el partido y cuál fue el momento clave? Responde en español."),
     ("it", "Seed 8: chi era in vantaggio al minuto 60? Spiega perché, in italiano.")]
async def main():
    agent, rows = build_agent(), []
    for lang, q in Q:
        t0 = time.time(); r = await agent.run(q)
        rows.append({"lang": lang, "question": q, "seconds": round(time.time() - t0, 1), "answer": r.text})
        print(f"--- {lang} ({rows[-1]['seconds']} s)\n{r.text}\n")
    json.dump({"agent_framework": agent_framework.__version__ if hasattr(agent_framework, "__version__") else "1.22.0",
               "deployment": os.environ["AZURE_OPENAI_DEPLOYMENT"], "rows": rows}, open("docs/live/agent_framework_run.json", "w"), ensure_ascii=False, indent=1)
asyncio.run(main())
