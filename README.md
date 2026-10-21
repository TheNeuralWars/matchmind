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
Requires only **Python 3.9+**. There are no dependencies and no API keys, and everything runs offline at $0.
```bash
git clone https://github.com/TheNeuralWars/matchmind && cd matchmind
python -m unittest -v                                   # 27 tests, stdlib only
python -m matchmind.cli --seed 7 --profile analyst      # narrated match in the terminal
python -m matchmind.server                              # open http://localhost:8000 (pick persona / club / en·es·it)
python -m matchmind.dataset --out data/ --seeds 0-199 --random-styles   # synthetic dataset (CSV + JSONL)
```
Stream endpoint directly: `curl -N "localhost:8000/stream?seed=7&persona=casual&club=NOR&lang=es&speed=600"`
(SSE events: `meta`, `state`, `cue`, `recap`).

### Generator knobs
```python
from matchmind.generator import generate_match
meta, events = generate_match(seed=7,
    home_style={"possession": 0.8, "pressing": 0.7, "directness": 0.3, "formation": "4-3-3"},
    away_style={"possession": 0.3, "directness": 0.9, "formation": "3-5-2"})
```
Styles run 0..1. The formations are `4-3-3`, `4-4-2`, `4-2-3-1` and `3-5-2`. Fatigue builds from 60' and makes the late game sloppier and more open.
Calibrated to ~2.6–2.8 goals per match, with ~90% of matches ending 0–4 goals. See **[DATA_CARD.md](DATA_CARD.md)** for exactly what is (and isn't) realistic.

### Languages
English, Spanish and Italian have hand-written native templates (`matchmind/i18n.py`) in an analyst register and a casual-fan register.
If Azure AI Foundry is configured it writes the lines; if it fails, the output falls back to the localised templates.

Optional Azure AI Foundry narration: set `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`.

## Screenshots (to capture)
- [ ] `docs/ui-casual-en.png` — overlay UI, casual fan, NOR, English
- [ ] `docs/ui-analyst-es.png` — same match, analyst, Spanish (split-screen hook)
- [ ] `docs/ui-casual-it.png` — Italian lower-thirds during a goal
- [ ] `docs/cue-json.png` — raw overlay cue JSON next to the rendered lower-third
- [ ] `docs/cli.png` — CLI narrated run + recap
- [ ] `docs/architecture.png` — Ingest → Interpret → Explain → Render → Personalize diagram

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
