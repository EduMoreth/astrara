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


# Placeholder values shipped in .env.example — treat these as "not configured"
# so we fall straight through to Nominatim instead of wasting a call on a 401.
_KEY_PLACEHOLDERS = {"sua-chave-opencage-aqui", "your-opencage-key-here", "changeme"}


def _opencage_key() -> str:
    """Real OpenCage API key from env, or "" to fall back to Nominatim.

    Returns empty when the var is unset or still holds a placeholder value.
    """
    key = os.getenv("OPENCAGE_API_KEY", "").strip()
    if not key or key.lower() in _KEY_PLACEHOLDERS:
        return ""
    return key


# ─────────────────────────── Public API ───────────────────────────

def search_cities(query: str, country: str | None = None, limit: int = 8) -> list:
    """Search for cities matching query. Returns multiple results for autocomplete.

    Uses OpenCage (authenticated, reliable for production) when OPENCAGE_API_KEY is
    configured, otherwise falls back to the free Nominatim public server.
    """
    if _opencage_key():
        results = _search_cities_opencage(query, country, limit)
        if results:
            return results
        # If OpenCage returned nothing (e.g. transient error), try Nominatim.
    return _search_cities_nominatim(query, country, limit)


def geocode(city: str, country: str | None = None) -> dict:
    """Convert city name to lat/lng/timezone.

    Uses OpenCage when configured, otherwise Nominatim. Raises ValueError with a
    user-safe message when the city cannot be located (never leaks internal errors).
    """
    if _opencage_key():
        try:
            return _geocode_opencage(city, country)
        except ValueError:
            # Genuine "not found" — try Nominatim as a second opinion before giving up.
            return _geocode_nominatim(city, country)
    return _geocode_nominatim(city, country)


# ─────────────────────────── OpenCage ───────────────────────────

# OSM/OpenCage place types we accept as a "city" for autocomplete.
_PLACE_TYPES = {
    "city", "town", "village", "municipality", "hamlet", "suburb",
    "neighbourhood", "county", "administrative",
}


def _city_from_components(comp: dict) -> str:
    """Extract the best city-level name from OpenCage address components."""
    return (
        comp.get("city")
        or comp.get("town")
        or comp.get("village")
        or comp.get("municipality")
        or comp.get("county")
        or comp.get("hamlet")
        or comp.get("_normalized_city")
        or ""
    )


def _search_cities_opencage(query: str, country: str | None, limit: int) -> list:
    try:
        from opencage.geocoder import OpenCageGeocode, RateLimitExceededError
    except ImportError:
        return []

    country_code = COUNTRY_CODES.get(country, "") if country else ""

    params = {"language": "pt", "limit": max(limit * 2, 10), "no_annotations": 0}
    if country_code:
        params["countrycode"] = country_code.lower()

    try:
        geocoder = OpenCageGeocode(_opencage_key())
        raw = geocoder.geocode(query, **params)
    except RateLimitExceededError:
        return []
    except Exception:
        # Any transient/network error: caller falls back to Nominatim.
        return []

    if not raw:
        return []

    cities = []
    seen = set()
    query_lower = query.lower().strip()

    for loc in raw:
        comp = loc.get("components", {}) or {}
        comp_type = comp.get("_type", "")

        city_name = _city_from_components(comp)
        country_name = comp.get("country") or ""

        # Skip non-city results (countries, states, roads, buildings, etc.).
        if not city_name or city_name == country_name:
            continue
        if comp_type and comp_type not in _PLACE_TYPES and not (
            comp.get("city") or comp.get("town") or comp.get("village")
        ):
            continue

        state = comp.get("state") or ""
        display = (
            f"{city_name}, {state}, {country_name}" if state
            else f"{city_name}, {country_name}"
        )

        dedup_key = f"{city_name.lower()}|{state.lower()}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        geom = loc.get("geometry", {}) or {}
        lat = geom.get("lat")
        lng = geom.get("lng")
        if lat is None or lng is None:
            continue

        # OpenCage returns the IANA timezone directly in annotations.
        tz_str = (
            loc.get("annotations", {}).get("timezone", {}).get("name")
            or _get_timezone(lat, lng)
        )

        name_lower = city_name.lower()
        if name_lower == query_lower:
            relevance = 0
        elif name_lower.startswith(query_lower):
            relevance = 1
        elif query_lower in name_lower:
            relevance = 2
        else:
            relevance = 3

        # OpenCage confidence: 1 (low) .. 10 (high). Higher is better.
        confidence = float(loc.get("confidence", 0))

        cities.append({
            "city": city_name,
            "state": state,
            "country": country_name,
            "display": display,
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "tz_str": tz_str,
            "_relevance": relevance,
            "_confidence": confidence,
        })

    cities.sort(key=lambda c: (c["_relevance"], -c["_confidence"]))
    for c in cities:
        del c["_relevance"]
        del c["_confidence"]

    return cities[:limit]


def _geocode_opencage(city: str, country: str | None) -> dict:
    from opencage.geocoder import OpenCageGeocode

    country_code = COUNTRY_CODES.get(country, "") if country else ""
    query = f"{city}, {country}" if country else city

    params = {"language": "pt", "limit": 1, "no_annotations": 0}
    if country_code:
        params["countrycode"] = country_code.lower()

    try:
        geocoder = OpenCageGeocode(_opencage_key())
        raw = geocoder.geocode(query, **params)
    except Exception:
        # Network/rate-limit issue — signal "not found" so caller can fall back.
        raise ValueError(f"Nao foi possivel encontrar coordenadas para '{city}'.")

    if not raw:
        raise ValueError(f"Nao foi possivel encontrar coordenadas para '{city}'.")

    loc = raw[0]
    geom = loc.get("geometry", {}) or {}
    lat = geom.get("lat")
    lng = geom.get("lng")
    if lat is None or lng is None:
        raise ValueError(f"Nao foi possivel encontrar coordenadas para '{city}'.")

    tz_str = (
        loc.get("annotations", {}).get("timezone", {}).get("name")
        or _get_timezone(lat, lng)
    )

    return {
        "lat": round(lat, 6),
        "lng": round(lng, 6),
        "tz_str": tz_str,
        "display_name": loc.get("formatted", query),
    }


# ─────────────────────────── Nominatim (fallback) ───────────────────────────

def _search_cities_nominatim(query: str, country: str | None = None, limit: int = 8) -> list:
    """Free-text city search via Nominatim. Used only as a fallback."""
    geolocator = Nominatim(user_agent="astrara-astrology-v2")

    country_code = COUNTRY_CODES.get(country, "") if country else ""
    all_results = []

    try:
        # Strategy 1: Free-text search with country_codes filter (best for partial names)
        results1 = geolocator.geocode(
            query,
            exactly_one=False,
            limit=10,
            language="pt",
            timeout=10,
            addressdetails=True,
            country_codes=country_code.lower() if country_code else None,
        )
        if results1:
            all_results.extend(results1)

        # Strategy 2: Free-text with country name appended (catches more matches)
        search_text = f"{query}, {country}" if country else query
        results2 = geolocator.geocode(
            search_text,
            exactly_one=False,
            limit=10,
            language="pt",
            timeout=10,
            addressdetails=True,
            country_codes=country_code.lower() if country_code else None,
        )
        if results2:
            all_results.extend(results2)

        # Strategy 3: Append " city" hint to bias towards city results
        if len(all_results) < 3:
            results3 = geolocator.geocode(
                f"{query} city",
                exactly_one=False,
                limit=10,
                language="pt",
                timeout=10,
                addressdetails=True,
                country_codes=country_code.lower() if country_code else None,
            )
            if results3:
                all_results.extend(results3)

    except GeocoderTimedOut:
        return []
    except Exception:
        # Catch rate-limit errors and other geocoding failures gracefully
        if not all_results:
            return []

    if not all_results:
        return []

    cities = []
    seen = set()
    query_lower = query.lower().strip()

    for loc in all_results:
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
        state = addr.get("state") or ""
        country_name = addr.get("country") or ""

        # Skip if this is clearly a country-level or state-level result
        if not city_name or city_name == country_name:
            continue

        display = f"{city_name}, {state}, {country_name}" if state else f"{city_name}, {country_name}"

        # Dedup by city name + state (prevents "Brasilia, DF" appearing twice)
        dedup_key = f"{city_name.lower()}|{state.lower()}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        tz_str = _get_timezone(loc.latitude, loc.longitude)

        # Compute relevance score for sorting:
        # 0 = exact match, 1 = starts with query, 2 = contains query, 3 = other
        name_lower = city_name.lower()
        if name_lower == query_lower:
            relevance = 0
        elif name_lower.startswith(query_lower):
            relevance = 1
        elif query_lower in name_lower:
            relevance = 2
        else:
            relevance = 3

        # OSM importance (higher = more populous/important), default 0
        importance = float(loc.raw.get("importance", 0))

        cities.append({
            "city": city_name,
            "state": state,
            "country": country_name,
            "display": display,
            "lat": round(loc.latitude, 6),
            "lng": round(loc.longitude, 6),
            "tz_str": tz_str,
            "_relevance": relevance,
            "_importance": importance,
        })

    # Sort: best relevance first, then by OSM importance (descending)
    cities.sort(key=lambda c: (c["_relevance"], -c["_importance"]))

    # Remove internal sort keys before returning
    for c in cities:
        del c["_relevance"]
        del c["_importance"]

    return cities[:limit]


def _geocode_nominatim(city: str, country: str | None = None) -> dict:
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
