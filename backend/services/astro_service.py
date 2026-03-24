from kerykeion import AstrologicalSubject


# Sign order for absolute degree calculation
SIGN_ORDER = [
    "Ari", "Tau", "Gem", "Can", "Leo", "Vir",
    "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis",
]

SIGN_OFFSETS = {s: i * 30 for i, s in enumerate(SIGN_ORDER)}

# Aspect definitions: name, exact_angle, orb_tolerance
ASPECT_DEFS = [
    ("conjunction", 0, 8),
    ("opposition", 180, 8),
    ("trine", 120, 7),
    ("square", 90, 7),
    ("sextile", 60, 5),
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

    def _deg_in_sign(position: float) -> float:
        """Convert absolute zodiac position (0-360) to degree within sign (0-30).
        Kerykeion .position returns absolute ecliptic longitude, not degree within sign."""
        return round(position % 30, 2)

    positions = {
        "sun": {"sign": subject.sun.sign, "deg": _deg_in_sign(subject.sun.position)},
        "moon": {"sign": subject.moon.sign, "deg": _deg_in_sign(subject.moon.position)},
        "mercury": {"sign": subject.mercury.sign, "deg": _deg_in_sign(subject.mercury.position)},
        "venus": {"sign": subject.venus.sign, "deg": _deg_in_sign(subject.venus.position)},
        "mars": {"sign": subject.mars.sign, "deg": _deg_in_sign(subject.mars.position)},
        "jupiter": {"sign": subject.jupiter.sign, "deg": _deg_in_sign(subject.jupiter.position)},
        "saturn": {"sign": subject.saturn.sign, "deg": _deg_in_sign(subject.saturn.position)},
        "uranus": {"sign": subject.uranus.sign, "deg": _deg_in_sign(subject.uranus.position)},
        "neptune": {"sign": subject.neptune.sign, "deg": _deg_in_sign(subject.neptune.position)},
        "pluto": {"sign": subject.pluto.sign, "deg": _deg_in_sign(subject.pluto.position)},
        "ascendant": {"sign": subject.first_house.sign, "deg": _deg_in_sign(subject.first_house.position)},
        "midheaven": {"sign": subject.tenth_house.sign, "deg": _deg_in_sign(subject.tenth_house.position)},
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
