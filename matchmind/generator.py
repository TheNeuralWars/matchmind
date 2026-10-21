"""Seeded synthetic football event generator. No real players, clubs or match data are used."""
import math, random
from dataclasses import dataclass, asdict, field

FIRST = ["Aren", "Bo", "Caio", "Dario", "Eli", "Femi", "Gus", "Hiro", "Iker", "Jules", "Kofi", "Luca", "Milo", "Nico", "Oren", "Pax", "Rui", "Sami", "Teo", "Udo", "Vik", "Wes"]
LAST = ["Arkwright", "Belmonte", "Castell", "Drago", "Esposa", "Ferro", "Galant", "Hale", "Iriarte", "Juno", "Kestrel", "Lorne", "Marlow", "Novak", "Orsini", "Pell", "Quist", "Rook", "Sable", "Tarn", "Vale", "Wren"]
POS = ["GK", "RB", "CB", "CB", "LB", "DM", "CM", "CM", "RW", "ST", "LW"]
FORMATIONS = {
    "4-3-3": POS,
    "4-4-2": ["GK", "RB", "CB", "CB", "LB", "RM", "CM", "CM", "LM", "ST", "ST"],
    "4-2-3-1": ["GK", "RB", "CB", "CB", "LB", "DM", "DM", "RW", "AM", "LW", "ST"],
    "3-5-2": ["GK", "CB", "CB", "CB", "RWB", "CM", "DM", "CM", "LWB", "ST", "ST"],
}
ATTACKERS = ("ST", "LW", "RW", "AM")
DEFAULT_STYLE = {"possession": 0.5, "pressing": 0.5, "directness": 0.5, "formation": "4-3-3"}

def style_of(st):
    """Team style, each 0..1: possession (keeps the ball, safer passes), pressing (forces errors, more duels), directness (longer, riskier forward passes)."""
    out = dict(DEFAULT_STYLE, **(st or {}))
    for k in ("possession", "pressing", "directness"): out[k] = max(0.0, min(1.0, float(out[k])))
    if out["formation"] not in FORMATIONS: raise ValueError(f"unknown formation {out['formation']}")
    return out

def fatigue(t, minutes=90):
    """0 until 60', rising linearly to ~1 at full time: late games get sloppier and more open."""
    return max(0.0, min(1.0, (t / 60 - 60) / max(1, minutes - 60)))

@dataclass
class Player:
    id: str; name: str; team: str; pos: str; rating: int; pace: int

@dataclass
class Event:
    seq: int; t: float; minute: int; type: str; team: str; player: str
    x: float; y: float; end_x: float = None; end_y: float = None
    outcome: str = "success"; xg: float = None; pressure: bool = False; meta: dict = field(default_factory=dict)
    def to_dict(self): return {k: v for k, v in asdict(self).items() if v is not None}

def make_team(code, rng, formation="4-3-3"):
    return [Player(f"{code}{i+1}", f"{rng.choice(FIRST)} {rng.choice(LAST)}", code, p, rng.randint(62, 90), rng.randint(55, 95)) for i, p in enumerate(FORMATIONS[formation])]

def xg_for(x, y):
    """Simple distance/angle xG on a 105x68 pitch, attacking towards x=105."""
    dx, dy = 105 - x, abs(34 - y)
    dist = math.hypot(dx, dy)
    angle = math.atan2(7.32 * dx, dx * dx + dy * dy - (7.32 / 2) ** 2) if dist > 0 else 1.5
    return round(max(0.01, min(0.95, 1 / (1 + math.exp(-(-1.2 + 1.4 * abs(angle) - 0.09 * dist))))), 3)

GENERATOR_VERSION = 2
SHOT_BASE, SHOT_FWD_BONUS = 0.075, 0.025   # v2: ~24 shots/match (EPL avg ~25)
FINISH_CAL = 0.72                           # v2: calibrates finishing so goals ~2.7/match (EPL avg ~2.8)

def generate_match(seed=7, home="NOR", away="SOU", minutes=90, home_style=None, away_style=None):
    """Return (meta, events), deterministic for (seed, styles). Styles: see style_of()."""
    rng = random.Random(seed)
    styles = {home: style_of(home_style), away: style_of(away_style)}
    squads = {home: make_team(home, rng, styles[home]["formation"]), away: make_team(away, rng, styles[away]["formation"])}
    meta = {"match_id": f"SYN-{seed}", "home": home, "away": away, "seed": seed, "generator_version": GENERATOR_VERSION,
            "styles": styles, "formations": {t: styles[t]["formation"] for t in styles},
            "players": {p.id: asdict(p) for s in squads.values() for p in s}}
    events, seq, t = [], 0, 0.0
    team = home
    def add(**kw):
        nonlocal seq
        seq += 1
        e = Event(seq=seq, t=round(t, 1), minute=int(t // 60), **kw); events.append(e); return e
    add(type="kickoff", team=home, player=squads[home][9].id, x=52.5, y=34)
    x, y = 52.5, 34.0
    while t < minutes * 60:
        t += rng.uniform(2, 9)
        side = squads[team]
        opp = away if team == home else home
        st, ost, fat = styles[team], styles[opp], fatigue(t, minutes)
        p = rng.choice(side[1:])
        pressure = rng.random() < 0.18 + 0.24 * ost["pressing"] - 0.10 * fat
        r = rng.random()
        if x > 80 and r < SHOT_BASE + (SHOT_FWD_BONUS if p.pos in ATTACKERS else 0) + 0.02 * fat:
            sx, sy = x + rng.uniform(0, 8), y
            xg = round(max(0.01, min(0.95, xg_for(min(sx, 104), sy) * FINISH_CAL * (1 + 0.15 * fat))), 3)
            goal = rng.random() < xg
            add(type="shot", team=team, player=p.id, x=round(min(sx, 104), 1), y=round(sy, 1), outcome="goal" if goal else rng.choice(["saved", "off_target", "blocked"]), xg=xg, pressure=pressure, meta={"fatigue": round(fat, 2)})
            team, x, y = opp, 52.5 if goal else 10, 34
            if goal: add(type="kickoff", team=team, player=squads[team][9].id, x=52.5, y=34)
            continue
        if r < 0.80:
            ex = max(1, min(104, x + rng.gauss(3 + 8 * st["directness"], 9 + 6 * st["directness"])))
            ey = max(1, min(67, y + rng.gauss(0, 12)))
            fail_p = (0.15 - 0.08 * st["possession"] + (0.12 if pressure else 0) + max(0, (ex - x)) / 300
                      - (p.rating - 75) / 300 + 0.06 * fat)
            ok = rng.random() > fail_p
            add(type="pass", team=team, player=p.id, x=round(x, 1), y=round(y, 1), end_x=round(ex, 1), end_y=round(ey, 1), outcome="success" if ok else "fail", pressure=pressure)
            if ok: x, y = ex, ey
            else:
                team, x, y = opp, 105 - ex, 68 - ey
                add(type="possession_change", team=team, player=rng.choice(squads[team][1:]).id, x=round(x, 1), y=round(y, 1), meta={"cause": "interception"})
        elif r < 0.86 + 0.08 * ost["pressing"]:
            d = rng.choice(squads[opp][1:8])
            won = rng.random() < 0.42 + 0.16 * ost["pressing"] - 0.08 * fat
            add(type="tackle", team=opp, player=d.id, x=round(105 - x, 1), y=round(68 - y, 1), outcome="won" if won else "lost", pressure=True)
            if won: team, x, y = opp, 105 - x, 68 - y
        else:
            dist = rng.uniform(12, 35); speed = round(20 + p.pace / 6 + rng.uniform(-2, 3) - 2.5 * fat, 1)
            add(type="carry", team=team, player=p.id, x=round(x, 1), y=round(y, 1), end_x=round(min(104, x + dist), 1), end_y=round(y, 1), meta={"top_speed_kmh": speed, "distance_m": round(dist, 1)})
            x = min(104, x + dist)
        # orient: home attacks to 105; for simplicity coordinates are always in attacking frame of team in possession
    add(type="full_time", team=home, player=squads[home][0].id, x=52.5, y=34)
    return meta, [e.to_dict() for e in events]
