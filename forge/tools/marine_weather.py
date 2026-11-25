"""Keyless open-meteo forecast: wave height and wind. Fixed hosts, numeric parameters only."""

import json
import urllib.parse
import urllib.request

SOURCES = [
    ("https://marine-api.open-meteo.com/v1/marine", "wave_height_max"),
    ("https://api.open-meteo.com/v1/forecast", "wind_speed_10m_max"),
]


def run(latitude: float, longitude: float, days: int = 3) -> str:
    latitude, longitude = float(latitude), float(longitude)
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("latitude or longitude out of range")
    days = max(1, min(int(days), 7))
    lines = [f"forecast for {latitude}, {longitude}"]
    for url, field in SOURCES:
        query = urllib.parse.urlencode({"latitude": latitude, "longitude": longitude, "daily": field,
                                        "forecast_days": days, "timezone": "UTC"})
        with urllib.request.urlopen(f"{url}?{query}", timeout=20) as response:
            data = json.load(response)
        unit = data["daily_units"][field]
        lines += [f"{day} {field}: {value} {unit}" for day, value in zip(data["daily"]["time"], data["daily"][field])]
    return "\n".join(lines)
