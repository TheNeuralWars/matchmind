"""Post-match recap article + social post (EN/ES/IT), built only from facts in the synthetic event stream."""
from .i18n import norm
from .state import MatchState

def facts(meta, events):
    """Language-neutral match facts (all derivable from events)."""
    st = MatchState(meta)
    goals, reds, sc, lead_changes, max_deficit = [], [], {meta["home"]: 0, meta["away"]: 0}, 0, {meta["home"]: 0, meta["away"]: 0}
    leader = None
    for e in events:
        st.ingest(e)
        if e["type"] == "shot" and e["outcome"] == "goal":
            sc[e["team"]] += 1
            goals.append({"minute": e["minute"], "team": e["team"], "player": meta["players"][e["player"]]["name"], "pen": e["meta"].get("set_piece") == "penalty"})
            h, a = sc[meta["home"]], sc[meta["away"]]
            for tm, d in ((meta["home"], a - h), (meta["away"], h - a)): max_deficit[tm] = max(max_deficit[tm], d)
            now = None if h == a else (meta["home"] if h > a else meta["away"])
            if now and leader and now != leader: lead_changes += 1
            if now: leader = now
        if e["type"] == "card" and e["outcome"] == "red":
            reds.append({"minute": e["minute"], "team": e["team"], "player": meta["players"][e["player"]]["name"]})
    s = st.snapshot(); h, a = meta["home"], meta["away"]
    winner = None if sc[h] == sc[a] else (h if sc[h] > sc[a] else a)
    loser = None if not winner else (a if winner == h else h)
    pl = st.player
    star_id = max(pl, key=lambda k: pl[k]["goals"] * 2 + pl[k]["xg"] + 0.01 * pl[k]["passes_ok"]
                  + (1.5 if winner and meta["players"][k]["team"] == winner else 0), default=None)   # player of the match leans to the winners
    star = meta["players"][star_id]["name"] if star_id else None
    xg = {t: s["teams"][t]["xg"] for t in (h, a)}
    return {"home": h, "away": a, "score": sc, "winner": winner, "goals": goals, "reds": reds, "xg": xg,
            "possession": s["possession"], "shots": {t: s["teams"][t]["shots"] for t in (h, a)}, "star": star,
            "star_goals": int(pl[star_id]["goals"]) if star_id else 0,
            "comeback": bool(winner and max_deficit[winner] >= 1), "clean_sheet": [t for t in (h, a) if sc[a if t == h else h] == 0],
            "against_xg": bool(winner and xg[winner] + 0.3 < xg[loser]), "lead_changes": lead_changes}

T = {
    "en": {"win": "{w} beat {l} {ws}-{ls}", "draw": "{h} and {a} drew {hs}-{as_}", "goalless": "{h} and {a} played out a goalless draw",
           "comeback": " after coming from behind", "against_xg": ", despite losing the xG battle ({wx} vs {lx})",
           "scorers": "Goals: {list}.", "pen": " (pen.)", "none": "",
           "stats": "{h} had {hp}% of the ball; shots {hsh}-{ash}, xG {hx}-{ax}.",
           "red": "{player} ({team}) was sent off in the {m}th minute.", "cs": "{t} kept a clean sheet.",
           "star": "Player of the match: {star}{brace}.", "brace": {2: ", with two goals", 3: ", with a hat-trick"},
           "social": "FT {h} {hs}-{as_} {a}. {hook} xG {hx}-{ax}. ⭐ {star}"},
    "es": {"win": "El {w} se impone al {l} por {ws}-{ls}", "draw": "{h} y {a} empatan {hs}-{as_}", "goalless": "{h} y {a} firman un empate sin goles",
           "comeback": " tras remontar", "against_xg": ", pese a perder la batalla del xG ({wx} frente a {lx})",
           "scorers": "Goles: {list}.", "pen": " (pen.)", "none": "",
           "stats": "El {h} tuvo el {hp}% de posesión; tiros {hsh}-{ash}, xG {hx}-{ax}.",
           "red": "{player} ({team}) vio la roja en el minuto {m}.", "cs": "El {t} dejó la portería a cero.",
           "star": "Jugador del partido: {star}{brace}.", "brace": {2: ", autor de un doblete", 3: ", con hat-trick incluido"},
           "social": "Final: {h} {hs}-{as_} {a}. {hook} xG {hx}-{ax}. ⭐ {star}"},
    "it": {"win": "Il {w} batte il {l} {ws}-{ls}", "draw": "{h} e {a} pareggiano {hs}-{as_}", "goalless": "{h} e {a} non vanno oltre lo 0-0",
           "comeback": " in rimonta", "against_xg": ", pur perdendo la sfida degli xG ({wx} contro {lx})",
           "scorers": "Marcatori: {list}.", "pen": " (rig.)", "none": "",
           "stats": "Il {h} ha avuto il {hp}% di possesso; tiri {hsh}-{ash}, xG {hx}-{ax}.",
           "red": "{player} ({team}) è stato espulso al {m}'.", "cs": "Il {t} chiude con la porta inviolata.",
           "star": "Migliore in campo: {star}{brace}.", "brace": {2: ", autore di una doppietta", 3: ", con una tripletta"},
           "social": "Finale: {h} {hs}-{as_} {a}. {hook} xG {hx}-{ax}. ⭐ {star}"},
}
HOOK = {
    "en": {"comeback": "What a comeback! 🔥", "against_xg": "Clinical finishing beat the numbers. 🎯", "red": "Ten men and drama. 🟥", "draw": "Honours even. 🤝", "goalless": "Tight, tense, no goals. 🧱", "win": "Job done. ✅"},
    "es": {"comeback": "¡Qué remontada! 🔥", "against_xg": "Pegada por encima de los números. 🎯", "red": "Diez contra once y mucho drama. 🟥", "draw": "Reparto de puntos. 🤝", "goalless": "Partido cerrado, sin goles. 🧱", "win": "Misión cumplida. ✅"},
    "it": {"comeback": "Che rimonta! 🔥", "against_xg": "Cinismo puro, oltre i numeri. 🎯", "red": "In dieci e tanto dramma. 🟥", "draw": "Un punto a testa. 🤝", "goalless": "Partita bloccata, nessun gol. 🧱", "win": "Missione compiuta. ✅"},
}
TAGS = " #MatchMind #SyntheticFootball"

def headline(f, lang="en"):
    t = T[norm(lang)]; h, a, sc = f["home"], f["away"], f["score"]
    if f["winner"]:
        l = a if f["winner"] == h else h
        s = t["win"].format(w=f["winner"], l=l, ws=sc[f["winner"]], ls=sc[l])
        if f["comeback"]: s += t["comeback"]
        if f["against_xg"]: s += t["against_xg"].format(wx=f["xg"][f["winner"]], lx=f["xg"][l])
        return s + "."
    return (t["draw"] if sc[h] else t["goalless"]).format(h=h, a=a, hs=sc[h], as_=sc[a]) + "."

def article(f, lang="en"):
    lang = norm(lang); t = T[lang]; h, a = f["home"], f["away"]
    parts = [headline(f, lang)]
    if f["goals"]:
        parts.append(t["scorers"].format(list=", ".join(f"{g['player']} ({g['team']}) {g['minute']}'{t['pen'] if g['pen'] else ''}" for g in f["goals"])))
    parts.append(t["stats"].format(h=h, hp=f["possession"][h], hsh=f["shots"][h], ash=f["shots"][a], hx=f["xg"][h], ax=f["xg"][a]))
    parts += [t["red"].format(player=r["player"], team=r["team"], m=r["minute"]) for r in f["reds"]]
    parts += [t["cs"].format(t=c) for c in f["clean_sheet"] if f["goals"]]
    if f["star"]: parts.append(t["star"].format(star=f["star"], brace=t["brace"].get(min(3, f["star_goals"]), "")))
    return " ".join(parts)

def social(f, lang="en", limit=280):
    lang = norm(lang); h, a, sc = f["home"], f["away"], f["score"]
    key = ("comeback" if f["comeback"] else "against_xg" if f["against_xg"] else "red" if f["reds"] else
           "win" if f["winner"] else "draw" if sc[h] else "goalless")
    txt = T[lang]["social"].format(h=h, a=a, hs=sc[h], as_=sc[a], hook=HOOK[lang][key], hx=f["xg"][h], ax=f["xg"][a], star=f["star"] or "-")
    return (txt + TAGS)[:limit] if len(txt + TAGS) <= limit else txt[:limit]

def post_match(meta, events, lang="en"):
    f = facts(meta, events)
    return {"lang": norm(lang), "headline": headline(f, lang), "article": article(f, lang), "social": social(f, lang), "facts": f}
