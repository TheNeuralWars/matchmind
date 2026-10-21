# MatchMind: Inside the Game submission

**Links**
- Repo (public): https://github.com/TheNeuralWars/matchmind
- **Test link (free, no login):** https://theneuralwars.github.io/matchmind/ is a static replay of the real pipeline, rebuilt by GitHub Actions on every push. Try `?autostart=1&view=split&seed=8&lang=en&lang2=it`.
- Demo video (< 2 min): *YouTube URL to add after upload*
- Categories: **Grand Prize** + **Best Multi-Agent System** (primary). Fallback: Best Use of Microsoft Foundry.

## Elevator pitch
Football coverage serves one audience at a time. MatchMind takes a stream of **synthetic, football-realistic match events** and turns it into **explainable, personalised, broadcast-ready match intelligence**. The same match becomes two genuinely different experiences: a data-rich analyst view and a warm, jargon-free fan view. Each works in English, Spanish or Italian, with a favourite club or a focus player. Every insight says *why* it matters, carries auditable evidence, and is emitted as a timed overlay cue a graphics engine can render.

## What we built (maps to §4.1)
| challenge requirement | MatchMind |
|---|---|
| (a) **Ingest** synthetic events live | Seeded generator → event stream (passes, carries, shots with xG, tackles, fouls, possession changes, pressure flags, corners, free kicks, penalties, cards, subs, metadata). Delivered over SSE in real time. |
| (b) **Interpret** | Incremental `MatchState`: score, xG, possession, pass accuracy, progressive passes, momentum (−1..1), control-vs-chaos index, per-player distance and top speed. |
| (c) **Explain** | Analyst agent detects key moments (goals, big chances, penalties awarded, red cards, speed bursts, line-breaking passes, momentum swings, chaos spikes), with thresholds and cooldowns. The Explainer agent says *why* and attaches evidence. |
| (d) **Render** | Renderer agent emits timed, machine-readable cue JSON (template, anchor, duration, data, evidence, source). The web UI draws a live SVG shot map and momentum chart. |
| (e) **Personalize** | Personalizer agent: persona (analyst/casual), favourite club, focus player, language. A split screen shows two fans side by side. |
| (ii) Real-time intelligence | Player tagging in every cue, speed/distance indicators when thresholds are hit, pass distance/accuracy, xG. |
| (iii) Narrative | Live commentary lines + automated post-match article and social post (EN/ES/IT), built only from event facts. |
| (iv) Explainability | Control-vs-chaos, momentum swings and pressure, each with evidence fields. |
| (v) Data innovation | Generator v4: team styles (possession/pressing/directness), 4 formations, fatigue, set pieces, cards, subs, score-state reaction, home advantage. Calibrated (2.6 goals, 25 shots, 20 fouls, 10 corners per match), with an exportable CSV/JSONL dataset and an honest [DATA_CARD](../DATA_CARD.md). |
| (vi) Multi-language | Natively written EN/ES/IT templates (not literal translation). The Foundry narrator is prompted for natural commentary in each language. |

## Microsoft / GitHub technologies
| technology | how | status |
|---|---|---|
| **Microsoft Agent Framework** | `matchmind/agent_framework_adapter.py` exposes the match-state tools as Agent Framework function tools and builds an Azure OpenAI-backed agent. | Code + tests with an injected client; **live run pending Azure access** |
| **MCP** | `matchmind/mcp_server.py`: a stdlib MCP server (JSON-RPC over stdio) with `get_score`, `get_momentum`, `get_key_moments`, `explain_moment`. | **Live**, tested via subprocess + CI smoke test |
| **Microsoft Foundry / Azure OpenAI** | Narrator agent calls a Foundry deployment when env vars are set. Template fallback otherwise. | Code path ready; **not yet run live** (no Azure credits connected yet) |
| **Azure Container Apps** | `Dockerfile` + `infra/deploy-containerapp.sh` (scale-to-zero). | Ready; **not deployed yet** |
| **GitHub Actions / Pages / CLI / Copilot-style agentic dev** | CI on Python 3.9 + 3.12 (unit tests + MCP smoke). Pages deploys the static replay. The repo is managed with `gh`. | **Live** |

## Agentic design (Best Multi-Agent System)
Specialised agents have distinct roles: **Analyst** → **Explainer** → **Personalizer** → **Narrator** → **Renderer**. They coordinate through a shared `MatchState` and explicit handoffs in the **Orchestrator**.
- **Failure recovery:** if the Narrator (model) fails, the Orchestrator falls back to a localised template, then to a generic localised line. The match never stops, and the cue records `source: fallback:<Error>`. This is covered by tests.
- **Per-fan routing:** one detection pass fans out to many profiles. Each profile gets its own ranking, filtering, register and language, which a single agent could not do as cheaply or transparently.
- **The same tools serve three surfaces:** pipeline, MCP clients and Agent Framework agents.

## Real-world impact
Broadcasters and streamers can produce one feed and serve many audiences and markets. Overlay cues plug into a graphics engine, and recaps and social posts are produced automatically. Every claim traces back to events, which is what an editorial team needs before trusting automation.

## Quality
- 53 stdlib unit tests and no runtime dependencies.
- Deterministic per seed.
- Docs: [ARCHITECTURE](ARCHITECTURE.md), [DATA_CARD](../DATA_CARD.md), [VIDEO](VIDEO.md).

## Honest status (as of Oct 21, 2026)
- **Works now, $0:** generator, full pipeline, EN/ES/IT, split UI, recap, MCP server, dataset export, CI, and the GitHub Pages replay.
- **Pending Azure access:** live Foundry narration, a live Agent Framework run, and the Container Apps deploy. The Pages build is a static replay of template narration, not a live model.
- **Not done:** auto-eventing from video, ball/shot speed metrics, and pass difficulty rating (pass distance and accuracy exist).

## Testing instructions for judges
1. Open the test link. Pick a seed, view (single/split), persona, club and language, then **Kick off**.
2. Locally (Python ≥ 3.9, nothing to install): `git clone … && cd matchmind && python -m unittest && python -m matchmind.server`, then open http://localhost:8000.
3. MCP: `printf '{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n' | python -m matchmind.mcp_server`.
