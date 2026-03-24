import os
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import pytz
from datetime import datetime
from math import floor


def search_cities(query: str, country: str | None = None, limit: int = 5) -> list:
    """Search for cities matching query. Returns multiple results for autocomplete."""
    geolocator = Nominatim(user_agent="astrara-astrology")
    search = f"{query}, {country}" if country else query

    try:
        results = geolocator.geocode(
            search,
            exactly_one=False,
            limit=limit,
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
        city_name = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality") or query
        state = addr.get("state", "")
        country_name = addr.get("country", "")
        display = f"{city_name}, {state}, {country_name}" if state else f"{city_name}, {country_name}"

        # Dedup
        key = f"{round(loc.latitude, 2)},{round(loc.longitude, 2)}"
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

    return cities


def geocode(city: str, country: str | None = None) -> dict:
    """Convert city name to lat/lng/timezone using Nominatim (free)."""
    geolocator = Nominatim(user_agent="astrara-astrology")
    query = f"{city}, {country}" if country else city

    try:
        location = geolocator.geocode(query, language="en", timeout=10)
    except GeocoderTimedOut:
        raise ValueError("Geocoding timed out. Please try again.")

    if not location:
        raise ValueError(f"Could not find coordinates for '{query}'.")

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
    """Estimate timezone from longitude (simple approach).
    For production, consider timezonefinder package."""
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
