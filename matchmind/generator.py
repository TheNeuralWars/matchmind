"""Seeded synthetic football event generator. No real players, clubs or match data are used."""
import math, random
from dataclasses import dataclass, asdict, field

FIRST = ["Aren", "Bo", "Caio", "Dario", "Eli", "Femi", "Gus", "Hiro", "Iker", "Jules", "Kofi", "Luca", "Milo", "Nico", "Oren", "Pax", "Rui", "Sami", "Teo", "Udo", "Vik", "Wes"]
LAST = ["Arkwright", "Belmonte", "Castell", "Drago", "Esposa", "Ferro", "Galant", "Hale", "Iriarte", "Juno", "Kestrel", "Lorne", "Marlow", "Novak", "Orsini", "Pell", "Quist", "Rook", "Sable", "Tarn", "Vale", "Wren"]
POS = ["GK", "RB", "CB", "CB", "LB", "DM", "CM", "CM", "RW", "ST", "LW"]

@dataclass
class Player:
    id: str; name: str; team: str; pos: str; rating: int; pace: int

@dataclass
class Event:
    seq: int; t: float; minute: int; type: str; team: str; player: str
    x: float; y: float; end_x: float = None; end_y: float = None
    outcome: str = "success"; xg: float = None; pressure: bool = False; meta: dict = field(default_factory=dict)
    def to_dict(self): return {k: v for k, v in asdict(self).items() if v is not None}

def make_team(code, rng):
    return [Player(f"{code}{i+1}", f"{rng.choice(FIRST)} {rng.choice(LAST)}", code, p, rng.randint(62, 90), rng.randint(55, 95)) for i, p in enumerate(POS)]

def xg_for(x, y):
    """Simple distance/angle xG on a 105x68 pitch, attacking towards x=105."""
    dx, dy = 105 - x, abs(34 - y)
    dist = math.hypot(dx, dy)
    angle = math.atan2(7.32 * dx, dx * dx + dy * dy - (7.32 / 2) ** 2) if dist > 0 else 1.5
    return round(max(0.01, min(0.95, 1 / (1 + math.exp(-(-1.2 + 1.4 * abs(angle) - 0.09 * dist))))), 3)

GENERATOR_VERSION = 2
SHOT_BASE, SHOT_FWD_BONUS = 0.075, 0.025   # v2: ~24 shots/match (EPL avg ~25)
FINISH_CAL = 0.80                           # v2: calibrates finishing so goals ~2.7/match (EPL avg ~2.8)

def generate_match(seed=7, home="NOR", away="SOU", minutes=90, home_style=0.55):
    """Yield a deterministic event stream. home_style ~ share of possession tendency for the home team."""
    rng = random.Random(seed)
    squads = {home: make_team(home, rng), away: make_team(away, rng)}
    meta = {"match_id": f"SYN-{seed}", "home": home, "away": away, "seed": seed, "generator_version": GENERATOR_VERSION,
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
        p = rng.choice(side[1:])
        pressure = rng.random() < 0.3
        r = rng.random()
        if x > 80 and r < SHOT_BASE + (SHOT_FWD_BONUS if p.pos in ("ST", "LW", "RW") else 0):
            sx, sy = x + rng.uniform(0, 8), y
            xg = round(max(0.01, xg_for(min(sx, 104), sy) * FINISH_CAL), 3)
            goal = rng.random() < xg
            add(type="shot", team=team, player=p.id, x=round(min(sx, 104), 1), y=round(sy, 1), outcome="goal" if goal else rng.choice(["saved", "off_target", "blocked"]), xg=xg, pressure=pressure)
            team, x, y = opp, 52.5 if goal else 10, 34
            if goal: add(type="kickoff", team=team, player=squads[team][9].id, x=52.5, y=34)
            continue
        if r < 0.80:
            ex = max(1, min(104, x + rng.gauss(7 if team == home else 7, 12)))
            ey = max(1, min(67, y + rng.gauss(0, 12)))
            fail_p = 0.12 + (0.12 if pressure else 0) + max(0, (ex - x)) / 300 - (p.rating - 75) / 300
            ok = rng.random() > fail_p
            add(type="pass", team=team, player=p.id, x=round(x, 1), y=round(y, 1), end_x=round(ex, 1), end_y=round(ey, 1), outcome="success" if ok else "fail", pressure=pressure)
            if ok: x, y = ex, ey
            else:
                team, x, y = opp, 105 - ex, 68 - ey
                add(type="possession_change", team=team, player=rng.choice(squads[team][1:]).id, x=round(x, 1), y=round(y, 1), meta={"cause": "interception"})
        elif r < 0.92:
            d = rng.choice(squads[opp][1:8])
            won = rng.random() < 0.5
            add(type="tackle", team=opp, player=d.id, x=round(105 - x, 1), y=round(68 - y, 1), outcome="won" if won else "lost", pressure=True)
            if won: team, x, y = opp, 105 - x, 68 - y
        else:
            dist = rng.uniform(12, 35); speed = round(20 + p.pace / 6 + rng.uniform(-2, 3), 1)
            add(type="carry", team=team, player=p.id, x=round(x, 1), y=round(y, 1), end_x=round(min(104, x + dist), 1), end_y=round(y, 1), meta={"top_speed_kmh": speed, "distance_m": round(dist, 1)})
            x = min(104, x + dist)
        # orient: home attacks to 105; for simplicity coordinates are always in attacking frame of team in possession
    add(type="full_time", team=home, player=squads[home][0].id, x=52.5, y=34)
    return meta, [e.to_dict() for e in events]
