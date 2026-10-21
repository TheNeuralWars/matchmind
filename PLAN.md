# PLAN — MatchMind (Inside the Game: Developer Hackathon)

**Deadline:** Oct 27 2026 23:59 PT = **Oct 28 08:59 Rome**. Submit on Innovation Studio (hackathons/34887): pitch, <2 min video (YouTube/Vimeo, no copyrighted music/PL trademarks), PUBLIC GitHub URL, working test link.
**Rules source:** github.com/microsoft/insidethegamehackathon (OFFICIAL RULES.md §4.1–4.4, §6).
**Judging (20% each):** Tech implementation (incl. *synthetic data creation* + hero tech: Foundry, Agent Framework, Azure MCP, Copilot agent mode, Fabric, GitHub CLI) · Agentic design · Real-world impact · UX & video · Category fit.
**Category targets:** Grand Prize + **Best Multi-Agent System** (primary) — fallback Best Use of Foundry.

## Angle
AI scout + match narrator. Five-stage pipeline the rules ask for, verbatim: Ingest → Interpret → Explain → Render → Personalize. GoalWorld/GoalChain tie-in: the same engine powers the manager game's sim matches ("your NFT squad's match, narrated for you"). Keep it a **new** codebase (rule 4.3) — only ideas, not code, from goalchain. Generator + agents shared with the Nebius×NVIDIA build (Oct 29): swap llm.py backend.

## Architecture
- `generator.py` synthetic engine (seeded; xG model; pressure; carries with speed/distance; fictional names). Extend: formations, fatigue, team style params, export JSONL/Parquet dataset + data card.
- `state.py` incremental stats: score, xG, possession, pass acc, progressive passes, momentum, control-vs-chaos.
- `agents.py` Analyst / Explainer / Narrator / Personalizer / Renderer; `pipeline.py` Orchestrator with failure fallback.
- `server.py` SSE stream + `web/` overlay UI. Cue JSON = timed, machine-readable overlays.
- Azure ($0 only): Container Apps consumption (scale to 0, free grant), Foundry/Azure OpenAI via free credits only (Azure free account $200 / Students $100 — **Nico must confirm a credit-funded subscription and set a $0 budget alert; never attach paid usage**). Template fallback keeps demo working with no model. Optional: Cosmos DB free tier, Functions free grant, Azure AI Translator F0 (2M chars/mo free) for languages.

## Demo script (≤1:55)
0:00 hook: "Same match, two fans." Split screen analyst vs casual. · 0:15 synthetic generator (seed, event JSON). · 0:35 live stream: goal → explainer *why* + evidence. · 0:55 switch persona/club/language (EN→ES/IT) live. · 1:15 overlay cue JSON → lower-third. · 1:30 architecture (agents + Azure Container Apps + Foundry) · 1:45 GoalWorld vision + repo URL.

## Schedule (Rome)
- **Wed 21:** scaffold MVP ✅, tests ✅, PLAN ✅. Nico: `gh auth login`, Azure login/credits check.
- **Thu 22:** generator v2 (formations, fatigue, styles, dataset export + data card); focus-player mode; i18n via Foundry/Translator.
- **Fri 23:** Foundry narrator live; Microsoft Agent Framework (Python) wrapping agents; MCP tool exposing match state.
- **Sat 24:** deploy Container Apps; GitHub Actions CI/CD; UI polish (pitch map, momentum chart).
- **Sun 25:** recap generator (post-match article + social clip text); eval tests; README diagrams.
- **Mon 26:** record video, upload YouTube (unlisted→public), write pitch.
- **Tue 27:** buffer, final fixes, **submit by 20:00 Rome** (well before 08:59 Oct 28).

## Progress
- **Wed 21 (done):** Generator v2 calibration (`GENERATOR_VERSION=2`): ~27 shots, ~2.6 xG, ~2.7 goals/match over 500 seeds; ~80% of matches 0–4 goals; seed 7 now 0-1 (was 5-3). Deterministic per seed. ✅
- **Wed 21 (done):** Native ES/IT offline templates (`matchmind/i18n.py`) for Explainer, Narrator (analyst + casual registers) and recap; Foundry prompt asks for natural Spanish/Italian commentary. 15 stdlib tests pass. ✅
- **Next:** formations/fatigue/team style params, JSONL dataset export + data card, UI language switch check, Foundry narrator live.
