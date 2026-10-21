# MatchMind ⚽🤖 — Synthetic Match Insights Engine

Entry for **Microsoft × Premier League "Inside the Game: Developer Hackathon"** (2026). Built in public by [@nico](https://goalworld.fun).

MatchMind turns a **synthetic, football-realistic event stream** into **explainable, personalised, broadcast-ready match intelligence**:

```
Ingest → Interpret → Explain → Render → Personalize
events   MatchState   Explainer  Renderer   Personalizer (+ Narrator)
```

- **Synthetic data engine** (`matchmind/generator.py`): seeded, reproducible matches with passes, shots (xG model), tackles, possession changes, pressure, carries (speed/distance) and match metadata. Fictional players and clubs only — no real data or footage.
- **Multi-agent pipeline** (`matchmind/agents.py`, `pipeline.py`): Analyst (key-moment detection with thresholds/cooldowns), Explainer (*why* it matters, with auditable evidence), Narrator (Azure AI Foundry model, deterministic fallback), Personalizer (persona / favourite club / focus player / language), Renderer (timed overlay cues JSON). The Orchestrator recovers from agent failures.
- **Explainability metrics**: momentum (−1..1), control-vs-chaos index, xG, progressive passes, pass accuracy.
- **Live demo UI** (`web/index.html`) via Server-Sent Events; same match, two genuinely different experiences (analyst vs casual fan).

## Quickstart
```bash
python -m unittest -v                 # tests (stdlib only, no deps)
python -m matchmind.cli --seed 7 --profile analyst
python -m matchmind.server            # http://localhost:8000
```
Optional Azure AI Foundry narration: set `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`. Without them everything runs offline at $0.

## Azure
- **Azure Container Apps** (scale-to-zero, Consumption free grant) — `infra/deploy-containerapp.sh`, `Dockerfile`
- **Microsoft Foundry / Azure OpenAI** — narrator + multilingual output (`matchmind/llm.py`)
- Roadmap: Azure Functions event ingestion, Cosmos DB free tier for match state, Microsoft Agent Framework orchestration.

## Overlay cue format
```json
{"t": 1234.5, "minute": 20, "duration_s": 6, "template": "lower_third.goal", "anchor": "bottom_left",
 "text": "...", "data": {"score": {...}, "momentum": 0.4, "possession": {...}}, "lang": "en",
 "score_rank": 1.3, "source": "foundry|template", "evidence": {...}}
```

## License
MIT
