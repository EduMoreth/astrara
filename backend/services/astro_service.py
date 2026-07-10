from kerykeion import AstrologicalSubject


# Sign order for absolute degree calculation
SIGN_ORDER = [
    "Ari", "Tau", "Gem", "Can", "Leo", "Vir",
    "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis",
]

SIGN_OFFSETS = {s: i * 30 for i, s in enumerate(SIGN_ORDER)}

# Aspect definitions: name, exact_angle, orb_tolerance
# Orbs match Astro.com defaults (generous for major aspects)
ASPECT_DEFS = [
    ("conjunction", 0, 10),
    ("opposition", 180, 10),
    ("trine", 120, 8),
    ("square", 90, 8),
    ("sextile", 60, 6),
    ("quincunx", 150, 3),
    ("semisextile", 30, 2),
]

# Planets that participate in aspects
ASPECT_PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]


def _absolute_degree(sign: str, deg: float) -> float:
    """Convert sign + degree to absolute ecliptic degree (0-360)."""
    offset = SIGN_OFFSETS.get(sign, 0)
    return offset + deg


def _calculate_aspects(positions: dict) -> list:
    """Calculate aspects between planets based on angular distances."""
    aspects = []

    # Get absolute degrees for each planet
    planet_degrees = {}
    for key in ASPECT_PLANETS:
        pos = positions.get(key)
        if pos:
            planet_degrees[key] = _absolute_degree(pos["sign"], pos["deg"])

    # Check every pair of planets
    planet_keys = list(planet_degrees.keys())
    for i in range(len(planet_keys)):
        for j in range(i + 1, len(planet_keys)):
            p1 = planet_keys[i]
            p2 = planet_keys[j]
            deg1 = planet_degrees[p1]
            deg2 = planet_degrees[p2]

            # Angular distance (shortest arc)
            diff = abs(deg1 - deg2)
            if diff > 180:
                diff = 360 - diff

            # Check against each aspect definition
            for aspect_name, exact_angle, orb in ASPECT_DEFS:
                deviation = abs(diff - exact_angle)
                if deviation <= orb:
                    aspects.append({
                        "p1": p1.capitalize(),
                        "p2": p2.capitalize(),
                        "aspect": aspect_name,
                        "orbit": round(deviation, 2),
                    })
                    break  # Only one aspect per pair

    return aspects


def generate_chart(
    name: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lng: float,
    tz_str: str,
) -> dict:
    """Generate natal chart using Kerykeion (offline, zero API cost)."""
    subject = AstrologicalSubject(
        name,
        year,
        month,
        day,
        hour,
        minute,
        lng=lng,
        lat=lat,
        tz_str=tz_str,
        online=False,
    )

    # Debug logging for Kerykeion output

    positions = {
        "sun": {"sign": subject.sun.sign, "deg": round(subject.sun.position, 2)},
        "moon": {"sign": subject.moon.sign, "deg": round(subject.moon.position, 2)},
        "mercury": {"sign": subject.mercury.sign, "deg": round(subject.mercury.position, 2)},
        "venus": {"sign": subject.venus.sign, "deg": round(subject.venus.position, 2)},
        "mars": {"sign": subject.mars.sign, "deg": round(subject.mars.position, 2)},
        "jupiter": {"sign": subject.jupiter.sign, "deg": round(subject.jupiter.position, 2)},
        "saturn": {"sign": subject.saturn.sign, "deg": round(subject.saturn.position, 2)},
        "uranus": {"sign": subject.uranus.sign, "deg": round(subject.uranus.position, 2)},
        "neptune": {"sign": subject.neptune.sign, "deg": round(subject.neptune.position, 2)},
        "pluto": {"sign": subject.pluto.sign, "deg": round(subject.pluto.position, 2)},
        "ascendant": {"sign": subject.first_house.sign, "deg": round(subject.first_house.position, 2)},
        "midheaven": {"sign": subject.tenth_house.sign, "deg": round(subject.tenth_house.position, 2)},
    }

    # Build houses data for frontend chart rendering
    houses = []
    house_attrs = [
        "first_house", "second_house", "third_house", "fourth_house",
        "fifth_house", "sixth_house", "seventh_house", "eighth_house",
        "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
    ]
    for attr in house_attrs:
        house = getattr(subject, attr)
        houses.append({
            "sign": house.sign,
            "deg": round(house.position, 2),
        })

    # Calculate aspects manually from planet positions
    aspects = _calculate_aspects(positions)

    return {
        "positions": positions,
        "houses": houses,
        "aspects": aspects,
    }
