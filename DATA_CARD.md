# Data Card — MatchMind Synthetic Football Events (generator v3)

## What it is
Fully **synthetic** football (soccer) event streams produced by `matchmind/generator.py`. Each match is a sequence of
`kickoff`, `pass`, `carry`, `tackle`, `foul`, `free_kick`, `corner`, `card`, `possession_change`, `shot`, `full_time` events with pitch coordinates (105×68 m),
timestamps, outcomes, xG on shots, pressure flags, carry speed/distance and a late-game fatigue value.

**No real data is used.** There is no scraped, licensed, tracking or broadcast data, and no real players, clubs, competitions or footage.
Player names are random pairs of invented first/last names; team codes (`NOR`, `SOU`) are fictional.
It is not Premier League data and must not be presented as such.

## How to generate
```bash
python -m matchmind.dataset --out data/ --seeds 0-199 --random-styles
```
Output: `events.csv` (flat, one row per event), `events.jsonl` (full event objects), `matches.json` (per-match meta:
seed, styles, formations, rosters, final score + summary). Same seeds and flags give byte-identical files.

## Generative model (simple, by design)
- Possession-chain random walk: each action is drawn with fixed probabilities and team-style adjustments.
- **Team style** (0..1): `possession` lowers pass failure; `pressing` raises opponent pressure, duel rate and tackle win rate;
  `directness` lengthens and widens forward pass distance (riskier).
- **Formations**: `4-3-3`, `4-4-2`, `4-2-3-1`, `3-5-2`. These set roster positions; attackers (ST/LW/RW/AM) shoot more.
  There is **no** spatial positional play.
- **Fatigue**: 0 until 60', linear to 1 at 90'. Late game gives more pass errors, less pressing, more and slightly better shots, and lower sprint speeds.
- **Set pieces**: fouls give free kicks. A foul in the central box area can be a penalty (xG 0.76, the best-rated outfielder takes it). A foul in the attacking third can lead to a direct free-kick shot. Saved or blocked shots and over-hit passes can win corners, and some corners produce a header (low xG). Each shot carries `meta.set_piece`.
- **Cards**: fouls can lead to a yellow, a second yellow or a rare straight red. A sent-off player takes no further part, and the team with the extra player passes better and shoots slightly more.
- **Score state**: the trailing team plays more directly and shoots slightly more, increasingly so late in the game. The leading team defends slightly more.
- **Shot locations**: shooters cut inside (no byline shots); x ≤ 100.5 m, y within 8–60 m.
- **xG**: a logistic distance/angle model × a calibration factor. The model is not fit to real shots.

## Calibration (300 seeds, random styles)
| metric | synthetic | real top-flight reference (approx.) |
|---|---|---|
| goals / match | 2.57 (open play 1.98, set pieces ~0.58) | ~2.7–2.9 |
| matches with 0–4 goals | 87% | ~85–90% |
| shots / match | 32 (26 open play) | ~25 |
| corners / match | 10.1 | ~10 |
| penalties / match | 0.34 | ~0.25–0.3 |
| fouls / match | 16.7 | ~20–22 |
| yellow / red cards per match | 2.6 / 0.14 | ~3.5–4 / ~0.1 |
| tackles (non-foul duels) / match | 19.6 | ~30–35 |
| passes / match | ~808 | ~850–950 |

Numbers were tuned so aggregates *look* plausible. The match-to-match variance and the correlations between
events were not validated against real data. Shot volume runs a little high.

## Known limitations / biases
- Coordinates are always in the attacking frame of the team on the ball. There is no off-ball or tracking data and no subs, offsides or injuries. Goal kicks after shots are approximated.
- There is no home advantage, no player-level finishing skill beyond position, and no rule-accurate set-piece geometry (positions are approximate).
- Formations change only roster composition, not shape.

## Intended use
Demos, testing and teaching for the MatchMind explainability pipeline (hackathon prototype). It is **not** for betting,
scouting real players, or any claim about real football performance.

## License
MIT, same as the repository. Generated data is free to reuse.
