"""Hand-written EN/ES/IT templates for the offline (no-model) path. Written natively per language, not word-for-word."""
LANGS = ("en", "es", "it")

OUTCOME = {
    "en": {"saved": "saved", "off_target": "off target", "blocked": "blocked", "goal": "scored"},
    "es": {"saved": "parada del portero", "off_target": "se marchó fuera", "blocked": "rechazado", "goal": "gol"},
    "it": {"saved": "parata del portiere", "off_target": "fuori dallo specchio", "blocked": "murato", "goal": "gol"},
}
YESNO = {"en": ("yes", "no"), "es": ("sí", "no"), "it": ("sì", "no")}

# Analyst register: precise, cites numbers.
WHY = {
    "en": {
        "goal": "{name} converts a {xg:.2f} xG chance{surprise}; {team} total xG now {team_xg}.",
        "goal_surprise": " — well above expectation",
        "big_chance": "{name} had a {xg:.2f} xG look ({outcome}). {team} are creating quality, not just volume.",
        "shot": "Low-value attempt ({xg:.2f} xG) from {name}; pressure={pressure}.",
        "speed_burst": "{name} hits {speed} km/h over {dist} m, stretching {opp}'s line.",
        "line_breaking_pass": "{name} breaks lines with a {metres:.0f} m progressive pass, bypassing {opp}'s press.",
        "momentum_swing": "Momentum flips to {lead} ({momentum:+.2f}) — territory and duel wins over the last ~40 actions.",
        "chaos_spike": "Game turns chaotic (chaos index {chaos}): turnovers and pressured actions dominate; control is up for grabs.",
    },
    "es": {
        "goal": "{name} materializa una ocasión de {xg:.2f} xG{surprise}; el {team} ya suma {team_xg} xG.",
        "goal_surprise": ", muy por encima de lo esperado",
        "big_chance": "Ocasión clara para {name}: {xg:.2f} xG ({outcome}). El {team} está generando calidad, no solo volumen.",
        "shot": "Disparo de poco peligro de {name} ({xg:.2f} xG); con presión: {pressure}.",
        "speed_burst": "{name} se dispara hasta los {speed} km/h en {dist} m y estira la línea del {opp}.",
        "line_breaking_pass": "{name} rompe líneas con un pase progresivo de {metres:.0f} m y se salta la presión del {opp}.",
        "momentum_swing": "El dominio cambia de bando: ahora manda el {lead} ({momentum:+.2f}), por territorio y duelos ganados en las últimas ~40 acciones.",
        "chaos_spike": "El partido se rompe (índice de caos {chaos}): mandan las pérdidas y las acciones bajo presión; nadie controla.",
    },
    "it": {
        "goal": "{name} trasforma un'occasione da {xg:.2f} xG{surprise}; il {team} sale a {team_xg} xG complessivi.",
        "goal_surprise": ", ben oltre le attese",
        "big_chance": "Grande occasione per {name}: {xg:.2f} xG ({outcome}). Il {team} crea qualità, non solo volume.",
        "shot": "Tiro poco pericoloso di {name} ({xg:.2f} xG); sotto pressione: {pressure}.",
        "speed_burst": "{name} tocca i {speed} km/h in {dist} m e allunga la linea del {opp}.",
        "line_breaking_pass": "{name} spacca le linee con un passaggio progressivo di {metres:.0f} m e salta il pressing del {opp}.",
        "momentum_swing": "L'inerzia cambia: ora comanda il {lead} ({momentum:+.2f}), tra territorio e duelli vinti nelle ultime ~40 azioni.",
        "chaos_spike": "La partita si spezza (indice di caos {chaos}): palle perse e giocate sotto pressione, nessuno ha il controllo.",
    },
}

# Casual-fan register: short, warm, no jargon (no xG, no indices).
CASUAL = {
    "en": {
        "goal": "GOAL! {name} scores for {team}!",
        "big_chance": "So close! {name} nearly had it for {team}.",
        "shot": "{name} tries his luck from distance.",
        "speed_burst": "Rapid! {name} tears away from the {opp} defence.",
        "line_breaking_pass": "What a ball from {name}, right through {opp}!",
        "momentum_swing": "The tide is turning — {lead} are on top now!",
        "chaos_spike": "It's getting wild out there!",
    },
    "es": {
        "goal": "¡GOOOL! ¡{name} marca para el {team}!",
        "big_chance": "¡Uy, por poco! {name} la tuvo para el {team}.",
        "shot": "{name} prueba suerte desde lejos.",
        "speed_burst": "¡Qué velocidad! {name} deja atrás a la defensa del {opp}.",
        "line_breaking_pass": "¡Pasazo de {name}, filtrado entre las líneas del {opp}!",
        "momentum_swing": "¡El partido cambia de color: ahora aprieta el {lead}!",
        "chaos_spike": "¡Esto es un ida y vuelta, se ha vuelto loco!",
    },
    "it": {
        "goal": "GOOOL! {name} segna per il {team}!",
        "big_chance": "Che occasione! {name} va vicinissimo al gol per il {team}.",
        "shot": "{name} ci prova da lontano.",
        "speed_burst": "Che scatto! {name} brucia la difesa del {opp}.",
        "line_breaking_pass": "Che palla di {name}, dritta tra le linee del {opp}!",
        "momentum_swing": "Il vento sta cambiando: adesso spinge il {lead}!",
        "chaos_spike": "Partita impazzita, succede di tutto!",
    },
}

def norm(lang): return lang if lang in LANGS else "en"

def render(kind, params, lang="en", persona="analyst"):
    lang = norm(lang)
    p = dict(params)
    p["outcome"] = OUTCOME[lang].get(p.get("outcome"), p.get("outcome", ""))
    if "pressure" in p and isinstance(p["pressure"], bool):
        p["pressure"] = YESNO[lang][0 if p["pressure"] else 1]
    table = CASUAL if persona == "casual" else WHY
    if kind == "goal" and persona != "casual":
        p["surprise"] = WHY[lang]["goal_surprise"] if p.get("xg", 1) < 0.15 else ""
    return table[lang][kind].format(**p)
