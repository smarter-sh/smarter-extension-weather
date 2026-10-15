"""Geocoding with Google Maps, and forecasts from Open-Meteo."""

from dataclasses import dataclass

import googlemaps
import openmeteo_requests
import pandas as pd

from .models import HourlyForecast, Unit

METRICS = ["temperature_2m", "precipitation", "windspeed_10m", "cloudcover"]
"""The hourly variables requested from Open-Meteo, in the order that they are returned."""
HOURS = 24
USCS_UNITS = {"temperature_unit": "fahrenheit", "wind_speed_unit": "mph", "precipitation_unit": "inch"}


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


def forecast(place: Place, unit: Unit, api_url: str) -> list[HourlyForecast]:
    """
    Return the next 24 hours' forecast for a place.

    :param place: The place.
    :param unit: ``METRIC`` or ``USCS``.
    :param api_url: The Open-Meteo forecast api.
    :returns: One forecast per hour.
    :raises ForecastError: If the api fails, or its response is not as expected.
    """
    params: dict = {"latitude": place.latitude, "longitude": place.longitude, "hourly": METRICS}
    if unit == "USCS":
        params.update(USCS_UNITS)
    try:
        hourly = openmeteo_requests.Client().weather_api(api_url, params=params)[0].Hourly()
        times = pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s"),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s"),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
        values = [hourly.Variables(i).ValuesAsNumpy() for i in range(len(METRICS))]
    # the client and the flatbuffers response raise many kinds of exceptions.
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise ForecastError(str(e)) from e
    return [
        HourlyForecast(
            time=time.strftime("%Y-%m-%d %H:%M"),
            temperature=round(float(values[0][i]), 1),
            precipitation=round(float(values[1][i]), 2),
            wind_speed=round(float(values[2][i]), 1),
            cloud_cover=round(float(values[3][i]), 0),
        )
        for i, time in enumerate(times[:HOURS])
    ]
