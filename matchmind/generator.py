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

GENERATOR_VERSION = 3
SHOT_BASE, SHOT_FWD_BONUS = 0.062, 0.02   # v3: ~26 open-play shots + set pieces
FINISH_CAL = 0.74                           # v3: open play ~2.1 goals; set pieces add ~0.6

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
    score = {home: 0, away: 0}
    on_pitch = {k: list(v) for k, v in squads.items()}      # outfield + GK still playing
    yellows = {}
    def add(**kw):
        nonlocal seq
        seq += 1
        e = Event(seq=seq, t=round(t, 1), minute=int(t // 60), **kw); events.append(e); return e
    def outfield(tm, n=None): return [q for q in on_pitch[tm] if q.pos != "GK"][:n]
    def shoot(tm, pl, sx, sy, xg, set_piece, pressure=False):
        goal = rng.random() < xg
        add(type="shot", team=tm, player=pl.id, x=round(sx, 1), y=round(sy, 1), outcome="goal" if goal else rng.choice(["saved", "off_target", "blocked"]),
            xg=round(xg, 3), pressure=pressure, meta={"fatigue": round(fatigue(t, minutes), 2), "set_piece": set_piece})
        if goal: score[tm] += 1
        return goal, events[-1].outcome
    def book(tm, pl):
        """Card for a foul. Second yellow or straight red sends the player off."""
        if rng.random() < 0.002 or (rng.random() < 0.05 and yellows.get(pl.id)):
            add(type="card", team=tm, player=pl.id, x=0, y=0, outcome="red", meta={"reason": "second_yellow" if yellows.get(pl.id) else "serious_foul"})
            on_pitch[tm] = [q for q in on_pitch[tm] if q.id != pl.id]
        elif rng.random() < 0.16:
            yellows[pl.id] = 1; add(type="card", team=tm, player=pl.id, x=0, y=0, outcome="yellow")
    def corner(tm, opp_tm):
        """Corner: ~1 in 3 produce a header/shot, low xG."""
        taker = rng.choice(outfield(tm)); cy = rng.choice([0.5, 67.5])
        add(type="corner", team=tm, player=taker.id, x=104.5, y=cy)
        if rng.random() < 0.33:
            hy = rng.uniform(27, 41)
            return shoot(tm, rng.choice(outfield(tm)), rng.uniform(93, 100), hy, max(0.02, xg_for(96, hy) * 0.30), "corner")
        return None
    add(type="kickoff", team=home, player=on_pitch[home][9].id, x=52.5, y=34)
    x, y = 52.5, 34.0
    while t < minutes * 60:
        t += rng.uniform(2, 9)
        opp = away if team == home else home
        st, ost, fat = styles[team], styles[opp], fatigue(t, minutes)
        diff = score[team] - score[opp]
        chase = 0.0 if diff == 0 else (-1 if diff > 0 else 1) * min(1.0, abs(diff) * 0.6) * (0.4 + t / (minutes * 60))  # >0 trailing, <0 protecting a lead
        men = (len(on_pitch[team]) - len(on_pitch[opp])) / 11                  # numerical (dis)advantage
        p = rng.choice(outfield(team))
        pressure = rng.random() < 0.18 + 0.24 * ost["pressing"] - 0.10 * fat
        r = rng.random()
        if x > 80 and r < SHOT_BASE + (SHOT_FWD_BONUS if p.pos in ATTACKERS else 0) + 0.02 * fat + 0.01 * max(0, chase) + 0.02 * men:
            sx = min(100.5, max(78, rng.gauss(91, 5) if x > 95 else x + rng.uniform(-2, 6)))   # no byline shots
            sy = max(8, min(60, 34 + (y - 34) * 0.55 + rng.gauss(0, 4)))                       # shooters cut inside
            goal, out = shoot(team, p, sx, sy, max(0.01, min(0.95, xg_for(sx, sy) * FINISH_CAL * (1 + 0.15 * fat))), "open_play", pressure)
            if not goal and out in ("saved", "blocked") and rng.random() < 0.28:
                res = corner(team, opp)                    # corner may produce a second shot
                goal = bool(res and res[0])
            if goal:
                team = opp; add(type="kickoff", team=team, player=outfield(team)[-1].id, x=52.5, y=34); x, y = 52.5, 34
            else:
                team, x, y = opp, 10, 34
            continue
        if r < 0.85:
            dr = min(1.0, st["directness"] + 0.25 * max(0, chase))
            ex = max(1, min(104, x + rng.gauss(3 + 8 * dr, 9 + 6 * dr)))
            ey = max(1, min(67, y + rng.gauss(0, 12)))
            fail_p = (0.15 - 0.08 * st["possession"] + (0.12 if pressure else 0) + max(0, (ex - x)) / 300
                      - (p.rating - 75) / 300 + 0.06 * fat - 0.05 * men)
            ok = rng.random() > fail_p
            add(type="pass", team=team, player=p.id, x=round(x, 1), y=round(y, 1), end_x=round(ex, 1), end_y=round(ey, 1), outcome="success" if ok else "fail", pressure=pressure)
            if ok: x, y = ex, ey
            elif ex > 95 and rng.random() < 0.15:   # cleared behind for a corner
                res = corner(team, opp)
                if res and res[0]:
                    team = opp; add(type="kickoff", team=team, player=outfield(team)[-1].id, x=52.5, y=34); x, y = 52.5, 34
                else: team, x, y = opp, 10, 34
            else:
                team, x, y = opp, 105 - ex, 68 - ey
                add(type="possession_change", team=team, player=rng.choice(outfield(team)).id, x=round(x, 1), y=round(y, 1), meta={"cause": "interception"})
        elif r < 0.875 + 0.02 * ost["pressing"] + 0.01 * max(0, -chase):
            d = rng.choice(outfield(opp, 7))
            u = rng.random()
            foul_p = 0.40 + 0.10 * fat + 0.08 * ost["pressing"]
            if u < foul_p:                                           # foul -> free kick / penalty
                add(type="foul", team=opp, player=d.id, x=round(105 - x, 1), y=round(68 - y, 1), outcome="committed")
                book(opp, d)
                if x > 88.5 and abs(y - 34) < 20 and rng.random() < 0.12:
                    add(type="free_kick", team=team, player=p.id, x=94, y=34, meta={"kind": "penalty"})
                    goal, _ = shoot(team, max(outfield(team), key=lambda q: q.rating), 94, 34, 0.76, "penalty")
                    team = opp
                    if goal: add(type="kickoff", team=team, player=outfield(team)[-1].id, x=52.5, y=34); x, y = 52.5, 34
                    else: x, y = 10, 34
                elif x > 72 and rng.random() < 0.35:
                    fx, fy = min(x, 88.0), max(14, min(54, y))         # fouls in the box that aren't pens → edge of area
                    add(type="free_kick", team=team, player=p.id, x=round(fx, 1), y=round(fy, 1), meta={"kind": "direct"})
                    goal, _ = shoot(team, p, fx, fy, max(0.02, xg_for(fx, fy) * 0.30), "free_kick")
                    team = opp
                    if goal: add(type="kickoff", team=team, player=outfield(team)[-1].id, x=52.5, y=34); x, y = 52.5, 34
                    else: x, y = 10, 34
                else:
                    add(type="free_kick", team=team, player=p.id, x=round(x, 1), y=round(y, 1), meta={"kind": "indirect"})
            else:
                won = u < foul_p + (1 - foul_p) * (0.50 + 0.16 * ost["pressing"] - 0.08 * fat)
                add(type="tackle", team=opp, player=d.id, x=round(105 - x, 1), y=round(68 - y, 1), outcome="won" if won else "lost", pressure=True)
                if won: team, x, y = opp, 105 - x, 68 - y
        else:
            dist = rng.uniform(12, 35); speed = round(20 + p.pace / 6 + rng.uniform(-2, 3) - 2.5 * fat, 1)
            add(type="carry", team=team, player=p.id, x=round(x, 1), y=round(y, 1), end_x=round(min(104, x + dist), 1), end_y=round(y, 1), meta={"top_speed_kmh": speed, "distance_m": round(dist, 1)})
            x = min(104, x + dist)
        # coordinates are always in the attacking frame of the team in possession
    add(type="full_time", team=home, player=squads[home][0].id, x=52.5, y=34, meta={"score": dict(score)})
    return meta, [e.to_dict() for e in events]
