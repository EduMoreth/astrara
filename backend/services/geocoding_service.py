import os
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import pytz
from datetime import datetime
from math import floor


# Map country display names to country codes for better geocoding
COUNTRY_CODES = {
    "Brasil": "BR", "Africa do Sul": "ZA", "Alemanha": "DE", "Angola": "AO",
    "Argentina": "AR", "Australia": "AU", "Bolivia": "BO", "Canada": "CA",
    "Chile": "CL", "China": "CN", "Colombia": "CO", "Coreia do Sul": "KR",
    "Cuba": "CU", "Equador": "EC", "Espanha": "ES", "Estados Unidos": "US",
    "Franca": "FR", "India": "IN", "Irlanda": "IE", "Israel": "IL",
    "Italia": "IT", "Japao": "JP", "Mexico": "MX", "Mocambique": "MZ",
    "Nigeria": "NG", "Noruega": "NO", "Nova Zelandia": "NZ", "Paraguai": "PY",
    "Peru": "PE", "Portugal": "PT", "Reino Unido": "GB", "Russia": "RU",
    "Suecia": "SE", "Suica": "CH", "Turquia": "TR", "Uruguai": "UY",
    "Venezuela": "VE",
}


def search_cities(query: str, country: str | None = None, limit: int = 5) -> list:
    """Search for cities matching query. Returns multiple results for autocomplete.
    Uses structured query to avoid returning country-level results."""
    geolocator = Nominatim(user_agent="astrara-astrology-v2")

    # Get country code for better results
    country_code = COUNTRY_CODES.get(country, "") if country else ""

    try:
        # Use structured query: city + countrycodes parameter
        # This is MUCH more accurate than free-text search
        results = geolocator.geocode(
            query={"city": query},
            exactly_one=False,
            limit=limit * 2,  # fetch more, filter later
            language="pt",
            timeout=10,
            addressdetails=True,
            country_codes=country_code.lower() if country_code else None,
        )

        # If structured query returns nothing, try free-text with country
        if not results:
            search_text = f"{query}, {country}" if country else query
            results = geolocator.geocode(
                search_text,
                exactly_one=False,
                limit=limit * 2,
                language="pt",
                timeout=10,
                addressdetails=True,
            )
    except GeocoderTimedOut:
        return []

    if not results:
        return []

    cities = []
    seen = set()

    for loc in results:
        addr = loc.raw.get("address", {})
        osm_type = loc.raw.get("type", "")
        osm_class = loc.raw.get("class", "")

        # Skip non-city results (countries, states, etc.)
        # Allow: city, town, village, municipality, hamlet
        valid_types = {"city", "town", "village", "municipality", "hamlet", "suburb",
                       "administrative", "residential"}
        if osm_type not in valid_types and osm_class != "place":
            # Still allow if it has city/town in address
            if not (addr.get("city") or addr.get("town") or addr.get("village")):
                continue

        city_name = (addr.get("city") or addr.get("town") or addr.get("village")
                     or addr.get("municipality") or addr.get("hamlet") or query)
        state = addr.get("state", "")
        country_name = addr.get("country", "")

        # Skip if this is clearly a country-level or state-level result
        if not city_name or city_name == country_name:
            continue

        display = f"{city_name}, {state}, {country_name}" if state else f"{city_name}, {country_name}"

        # Dedup by rounded coordinates
        key = f"{round(loc.latitude, 1)},{round(loc.longitude, 1)}"
        if key in seen:
            continue
        seen.add(key)

        tz_str = _get_timezone(loc.latitude, loc.longitude)

        cities.append({
            "city": city_name,
            "state": state,
            "country": country_name,
            "display": display,
            "lat": round(loc.latitude, 6),
            "lng": round(loc.longitude, 6),
            "tz_str": tz_str,
        })

        if len(cities) >= limit:
            break

    return cities


def geocode(city: str, country: str | None = None) -> dict:
    """Convert city name to lat/lng/timezone using Nominatim (free).
    Uses structured query for accuracy."""
    geolocator = Nominatim(user_agent="astrara-astrology-v2")

    country_code = COUNTRY_CODES.get(country, "") if country else ""

    try:
        # Try structured query first (more accurate)
        location = geolocator.geocode(
            query={"city": city},
            language="pt",
            timeout=10,
            addressdetails=True,
            country_codes=country_code.lower() if country_code else None,
        )

        # Fallback to free-text
        if not location:
            query = f"{city}, {country}" if country else city
            location = geolocator.geocode(query, language="pt", timeout=10)

    except GeocoderTimedOut:
        raise ValueError("Geocoding expirou. Tente novamente.")

    if not location:
        raise ValueError(f"Nao foi possivel encontrar coordenadas para '{city}'.")

    lat = location.latitude
    lng = location.longitude

    # Determine timezone from coordinates
    tz_str = _get_timezone(lat, lng)

    return {
        "lat": round(lat, 6),
        "lng": round(lng, 6),
        "tz_str": tz_str,
        "display_name": location.address,
    }


def _get_timezone(lat: float, lng: float) -> str:
    """Get timezone from coordinates using timezonefinder."""
    try:
        from timezonefinder import TimezoneFinder
        tf = TimezoneFinder()
        tz = tf.timezone_at(lng=lng, lat=lat)
        if tz:
            return tz
    except ImportError:
        pass

    # Fallback: estimate from longitude
    offset_hours = round(lng / 15)
    for tz_name in pytz.all_timezones:
        try:
            tz = pytz.timezone(tz_name)
            now = datetime.now(tz)
            tz_offset = now.utcoffset()
            if tz_offset and floor(tz_offset.total_seconds() / 3600) == offset_hours:
                return tz_name
        except Exception:
            continue

    return "UTC"
