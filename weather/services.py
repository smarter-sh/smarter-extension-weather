"""Geocoding with Google Maps, and current conditions and forecasts from Open-Meteo."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import googlemaps
import openmeteo_requests

from .models import Conditions, Unit, Units

METRICS = ["temperature_2m", "precipitation", "windspeed_10m", "cloudcover"]
"""The variables requested from Open-Meteo, in the order that they are returned."""
HOURS = 24
USCS_PARAMETERS = {"temperature_unit": "fahrenheit", "wind_speed_unit": "mph", "precipitation_unit": "inch"}
UNITS = {
    "METRIC": Units(temperature="°C", precipitation="mm", wind_speed="km/h"),
    "USCS": Units(temperature="°F", precipitation="inch", wind_speed="mph"),
}
"""Open-Meteo's units: its defaults, or those that USCS_PARAMETERS request."""


class GeocodingError(Exception):
    """A location could not be found."""


class ForecastError(Exception):
    """The forecast api failed."""


@dataclass
class Place:
    """A location, as Google Maps found it."""

    address: str
    latitude: float
    longitude: float


@dataclass
class Weather:
    """A place's current conditions and forecast, in its local time."""

    timezone: str
    current: Conditions
    forecast: list[Conditions] = field(default_factory=list)


def geocode(location: str, api_key: str) -> Place:
    """
    Find a location's address, latitude and longitude.

    :param location: The location, e.g. ``Paris``.
    :param api_key: A Google Maps API key with the Geocoding API enabled.
    :returns: The place.
    :raises GeocodingError: If the location cannot be found, or the API key is not valid.
    """
    try:
        results = googlemaps.Client(key=api_key).geocode(location)
    except (ValueError, googlemaps.exceptions.ApiError, googlemaps.exceptions.TransportError) as e:
        raise GeocodingError(str(e)) from e
    if not results:
        raise GeocodingError("no such place")
    geometry = results[0]["geometry"]["location"]
    return Place(results[0].get("formatted_address", location), float(geometry["lat"]), float(geometry["lng"]))


def local_time(epoch: int, utc_offset: int) -> str:
    """Return a Unix time as a local time, e.g. ``2026-10-15 14:00``."""
    return datetime.fromtimestamp(epoch + utc_offset, timezone.utc).strftime("%Y-%m-%d %H:%M")


def conditions(time: str, values: list[float]) -> Conditions:
    """Return the conditions at a time, from the values of METRICS, in order."""
    return Conditions(
        time=time,
        temperature=round(values[0], 1),
        precipitation=round(values[1], 2),
        wind_speed=round(values[2], 1),
        cloud_cover=round(values[3], 0),
    )


def weather(place: Place, unit: Unit, api_url: str) -> Weather:
    """
    Return a place's current conditions, and its forecast for the next 24 hours, starting this hour.

    :param place: The place.
    :param unit: ``METRIC`` or ``USCS``.
    :param api_url: The Open-Meteo forecast api.
    :returns: The weather, with times in the place's timezone.
    :raises ForecastError: If the api fails, or its response is not as expected.
    """
    params: dict = {
        "latitude": place.latitude,
        "longitude": place.longitude,
        "current": METRICS,
        "hourly": METRICS,
        "forecast_hours": HOURS,
        "timezone": "auto",
    }
    if unit == "USCS":
        params.update(USCS_PARAMETERS)
    try:
        response = openmeteo_requests.Client().weather_api(api_url, params=params)[0]
        offset = response.UtcOffsetSeconds()
        zone = (response.Timezone() or b"UTC").decode()
        current = response.Current()
        now = conditions(
            local_time(current.Time(), offset), [float(current.Variables(i).Value()) for i in range(len(METRICS))]
        )
        hourly = response.Hourly()
        values = [hourly.Variables(i).ValuesAsNumpy() for i in range(len(METRICS))]
        start, interval = hourly.Time(), hourly.Interval()
        hours = (hourly.TimeEnd() - start) // interval
        forecast = [
            conditions(local_time(start + i * interval, offset), [float(values[m][i]) for m in range(len(METRICS))])
            for i in range(min(hours, HOURS))
        ]
    # the client and the flatbuffers response raise many kinds of exceptions.
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise ForecastError(str(e)) from e
    return Weather(timezone=zone, current=now, forecast=forecast)


__all__ = ["ForecastError", "GeocodingError", "Place", "UNITS", "Weather", "geocode", "weather"]
