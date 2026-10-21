# Demo video (< 2:00): shot list + narration

Target **1:55**, 1280×720 or 1920×1080, English voice-over with ES/IT on screen.
Upload to YouTube unlisted, then make it public before submitting.
**Rules:** no copyrighted music (use silence or a CC0/self-made track), and no Premier League marks, crests or footage. Everything shown is synthetic.
Follows the *Demo script* in [PLAN.md](../PLAN.md).

## Draft v1 (Oct 21)
`media/matchmind_demo_v1.mp4` runs 1:44, 1920×1080, H.264/AAC, 6.8 MB. It has no music and only synthetic content. `python3 scripts/assemble_video.py` rebuilds it from:
- **Clips:** `scripts/record_demo.sh 60` (1080p, no cursor, full match in ~55 s at speed 98, so the penalty at 65' is around 40 s in each clip).
- **VO:** `media/vo/s1..s7.wav`, made with local **Piper TTS** (`en_GB-alan-medium`, free/offline) from `media/vo/script.json`, a tightened version of the narration below. The ElevenLabs attempt was rate-limited (429) twice. Nothing was generated or charged; the flow is ready to re-run in the ElevenLabs UI with the "Daniel – Steady Broadcaster" premade voice, ~1,341 credits.
- **Cards:** ffmpeg drawtext. Stills come from `docs/`.

## Assets
| file | what | how to (re)make |
|---|---|---|
| `media/split-analyst-en_casual-it.mp4` | 26 s, split view, seed 8, analyst EN vs casual IT, full match | `scripts/record_demo.sh` |
| `media/analyst-es.mp4` | 26 s, analyst in Spanish | same |
| `media/casual-it-NOR.mp4` | 26 s, casual NOR fan in Italian (penalty, goals) | same |
| `docs/ui-split-en-it.png`, `docs/ui-analyst-es.png`, `docs/ui-casual-it.png` | stills incl. post-match article + social card | headless Chrome deep link (README) |
| `docs/cue-json.png` | cue JSON → lower-third | — |
| `docs/cli.png` | CLI narrated run + recap | — |
| `docs/architecture.png` | architecture diagram | `docs/architecture.mmd` |
| *to record* | terminal: `python -m matchmind.dataset …` + `head events.jsonl`; MCP `tools/call` one-liner | screen-record a terminal |

`media/` is gitignored. Re-run `scripts/record_demo.sh [seconds]` (Xvfb + Chrome kiosk + ffmpeg) to regenerate.
Demo match = **seed 8**: NOR lead 2-0 (41', 65' penalty), then SOU come back to win 3-2 (73', 85', 88').
The clips play the full 90' in ~23 s, so trim, or re-record slower (e.g. `scripts/record_demo.sh 60`) for the live-goal beat.

## Shot list + narration
| time | on screen | narration (VO) |
|---|---|---|
| 0:00–0:15 | `split-analyst-en_casual-it.mp4` from kick-off. Title overlay: "Same match. Two fans." | "Same match, two fans. On the left, an analyst. On the right, a casual supporter watching in Italian. MatchMind gives each of them the match they actually want." |
| 0:15–0:35 | Terminal: `python -m matchmind.dataset --seeds 0-199 --random-styles`, `head -3 data/events.jsonl`; flash DATA_CARD calibration table | "Everything here is synthetic. Our seeded engine generates realistic football: team styles, formations, fatigue, set pieces, cards, subs and home advantage. It averages about 25 shots and 2.6 goals a game, and the data card says honestly what is and isn't real." |
| 0:35–0:55 | `analyst-es.mp4` around 65'–73': penalty awarded → goal cue; zoom on the cue text + shot map dot | "Live, five agents work in a pipeline. They ingest each event, interpret the match state, and an Analyst spots the key moments. The Explainer says *why* it matters, with evidence: a 0.76 xG penalty, and momentum swinging to the away side." |
| 0:55–1:15 | `casual-it-NOR.mp4`: "RIGORE per il NOR!", "GOOOL!"; cut to split view's end, Spanish/Italian recap + social card | "Switch the persona, the club or the language, and the same moment is retold. No jargon for the casual fan, and natural Spanish and Italian rather than literal translation. At full time it writes the match report and a social post." |
| 1:15–1:30 | `docs/cue-json.png` (JSON left, lower-third right) | "Every insight is also a timed, machine-readable overlay cue that a broadcast graphics engine can render directly." |
| 1:30–1:45 | `docs/architecture.png`; quick terminal MCP call `tools/call get_score` | "Under the hood, an orchestrator recovers from agent failures. The same match-state tools are exposed over MCP and to Microsoft Agent Framework, and Azure AI Foundry writes the narration when connected. It runs at zero cost on Azure Container Apps." |
| 1:45–1:55 | Repo URL `github.com/TheNeuralWars/matchmind` + "Built for Inside the Game" + GoalWorld note | "The same engine will narrate matches in GoalWorld, our manager game. MatchMind: every fan, their own match. The code's on GitHub." |

**Claims to keep honest:** say "Foundry when connected" until the live Azure test is done, and "runs on Container Apps" only once it's deployed (otherwise "deploys to").
