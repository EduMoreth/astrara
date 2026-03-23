from kerykeion import AstrologicalSubject
import json


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

    # Aspects
    aspects = []
    if hasattr(subject, "aspects_list"):
        for aspect in subject.aspects_list:
            aspects.append({
                "p1": aspect.get("p1_name", ""),
                "p2": aspect.get("p2_name", ""),
                "aspect": aspect.get("aspect", ""),
                "orbit": aspect.get("orbit", 0),
            })

    return {
        "positions": positions,
        "houses": houses,
        "aspects": aspects,
    }
