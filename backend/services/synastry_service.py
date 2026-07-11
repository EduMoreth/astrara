"""Synastry (sinastria): correlational affinity analysis between two natal charts.

Pure-math module: computes inter-chart aspects (person A's planets vs person B's
planets) and affinity scores per relationship dimension. No external deps, so it
is unit-testable offline and independent of kerykeion.
"""

# Sign order for absolute degree calculation (kerykeion abbreviated names)
SIGN_ORDER = [
    "Ari", "Tau", "Gem", "Can", "Leo", "Vir",
    "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis",
]
SIGN_OFFSETS = {s: i * 30 for i, s in enumerate(SIGN_ORDER)}

# Also accept full sign names (cached/saved charts may hold either form)
_FULL_TO_ABBR = {
    "Aries": "Ari", "Taurus": "Tau", "Gemini": "Gem", "Cancer": "Can",
    "Leo": "Leo", "Virgo": "Vir", "Libra": "Lib", "Scorpio": "Sco",
    "Sagittarius": "Sag", "Capricorn": "Cap", "Aquarius": "Aqu", "Pisces": "Pis",
}

# Synastry uses slightly tighter orbs than natal charts (standard practice)
ASPECT_DEFS = [
    ("conjunction", 0, 8),
    ("opposition", 180, 8),
    ("trine", 120, 6),
    ("square", 90, 6),
    ("sextile", 60, 4),
    ("quincunx", 150, 3),
]

PLANETS = [
    "sun", "moon", "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
]
POINTS = PLANETS + ["ascendant", "midheaven"]

# Harmony weight of each aspect type. Conjunction is contextual: harmonious for
# benefics/luminaries pairs, tense for saturn/mars/pluto contacts — handled below.
ASPECT_HARMONY = {
    "trine": 1.0,
    "sextile": 0.7,
    "conjunction": 0.6,
    "quincunx": -0.3,
    "square": -0.8,
    "opposition": -0.5,
}

_HARD_PLANETS = {"mars", "saturn", "pluto"}

# Relationship dimensions and the inter-chart point pairs that feed each one.
# Pairs are unordered across charts: (a_point, b_point) matches both directions.
DIMENSIONS = {
    "amor": {
        "label": "Amor & Atracao",
        "pairs": [
            ("venus", "mars"), ("venus", "venus"), ("mars", "mars"),
            ("venus", "sun"), ("venus", "moon"), ("mars", "moon"),
            ("venus", "ascendant"), ("mars", "ascendant"),
        ],
    },
    "emocional": {
        "label": "Conexao Emocional",
        "pairs": [
            ("moon", "moon"), ("moon", "sun"), ("moon", "venus"),
            ("moon", "neptune"), ("moon", "ascendant"),
        ],
    },
    "comunicacao": {
        "label": "Comunicacao & Ideias",
        "pairs": [
            ("mercury", "mercury"), ("mercury", "sun"), ("mercury", "moon"),
            ("mercury", "jupiter"), ("mercury", "ascendant"),
        ],
    },
    "identidade": {
        "label": "Identidade & Proposito",
        "pairs": [
            ("sun", "sun"), ("sun", "ascendant"), ("sun", "midheaven"),
            ("sun", "jupiter"), ("ascendant", "ascendant"),
        ],
    },
    "estabilidade": {
        "label": "Compromisso & Estabilidade",
        "pairs": [
            ("saturn", "sun"), ("saturn", "moon"), ("saturn", "venus"),
            ("saturn", "saturn"), ("jupiter", "saturn"), ("jupiter", "jupiter"),
        ],
    },
    "transformacao": {
        "label": "Intensidade & Transformacao",
        "pairs": [
            ("pluto", "sun"), ("pluto", "moon"), ("pluto", "venus"),
            ("uranus", "sun"), ("uranus", "venus"), ("neptune", "venus"),
            ("neptune", "sun"),
        ],
    },
}


def _abs_degree(pos: dict) -> float | None:
    """Convert a {sign, deg} position to absolute ecliptic degree (0-360)."""
    if not isinstance(pos, dict):
        return None
    sign = pos.get("sign")
    deg = pos.get("deg")
    if sign is None or deg is None:
        return None
    sign = _FULL_TO_ABBR.get(sign, sign)
    if sign not in SIGN_OFFSETS:
        return None
    try:
        return SIGN_OFFSETS[sign] + float(deg)
    except (TypeError, ValueError):
        return None


def compute_inter_aspects(positions_a: dict, positions_b: dict) -> list:
    """All aspects between person A's points and person B's points.

    Returns [{p1, p2, aspect, orbit}] where p1 is A's point and p2 is B's point
    (capitalized, matching the natal-aspect wire format).
    """
    degrees_a = {}
    degrees_b = {}
    for key in POINTS:
        da = _abs_degree((positions_a or {}).get(key))
        if da is not None:
            degrees_a[key] = da
        db = _abs_degree((positions_b or {}).get(key))
        if db is not None:
            degrees_b[key] = db

    aspects = []
    for pa, deg_a in degrees_a.items():
        for pb, deg_b in degrees_b.items():
            diff = abs(deg_a - deg_b)
            if diff > 180:
                diff = 360 - diff
            for aspect_name, exact, orb in ASPECT_DEFS:
                deviation = abs(diff - exact)
                if deviation <= orb:
                    aspects.append({
                        "p1": pa.capitalize(),
                        "p2": pb.capitalize(),
                        "aspect": aspect_name,
                        "orbit": round(deviation, 2),
                    })
                    break
    return aspects


def _aspect_score(p1: str, p2: str, aspect: str, orbit: float) -> float:
    """Harmony contribution of one inter-aspect, weighted by exactness."""
    base = ASPECT_HARMONY.get(aspect, 0.0)
    # Conjunctions with hard planets are tense rather than flowing
    if aspect == "conjunction" and (p1 in _HARD_PLANETS or p2 in _HARD_PLANETS):
        base = -0.3
    # Tighter orb = stronger effect (1.0 at exact, 0.4 at max orb)
    max_orb = next((o for n, _, o in ASPECT_DEFS if n == aspect), 8)
    tightness = 1.0 - 0.6 * (min(orbit, max_orb) / max_orb)
    return base * tightness


def compute_affinity_scores(inter_aspects: list) -> dict:
    """Affinity score (0-100) per relationship dimension + overall.

    Neutral baseline is 50; harmonious aspects push up, tense push down.
    """
    # Index aspects by unordered pair for dimension lookup
    by_pair = {}
    for a in inter_aspects:
        p1 = a["p1"].lower()
        p2 = a["p2"].lower()
        key = frozenset((p1, p2)) if p1 != p2 else frozenset((p1,))
        by_pair.setdefault(key, []).append(
            _aspect_score(p1, p2, a["aspect"], a["orbit"])
        )

    dimensions = {}
    dim_values = []
    for dim_key, dim in DIMENSIONS.items():
        total = 0.0
        hits = 0
        for pa, pb in dim["pairs"]:
            key = frozenset((pa, pb)) if pa != pb else frozenset((pa,))
            for score in by_pair.get(key, []):
                total += score
                hits += 1
        # 50 = neutral. Each strong harmonious aspect adds ~12 points, each
        # strong tense one removes ~10. Clamped to [5, 98] so extremes stay
        # plausible rather than absolute.
        raw = 50.0 + total * 12.0
        value = max(5, min(98, round(raw)))
        dimensions[dim_key] = {
            "label": dim["label"],
            "score": value,
            "aspect_count": hits,
        }
        dim_values.append(value)

    overall = round(sum(dim_values) / len(dim_values)) if dim_values else 50
    return {"overall": overall, "dimensions": dimensions}


def compute_synastry(positions_a: dict, positions_b: dict) -> dict:
    """Full synastry: inter-chart aspects + affinity scores."""
    inter_aspects = compute_inter_aspects(positions_a, positions_b)
    scores = compute_affinity_scores(inter_aspects)
    return {"inter_aspects": inter_aspects, "scores": scores}
