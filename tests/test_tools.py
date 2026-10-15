"""Tests of the get_weather tool, with its services mocked."""

import unittest
from unittest.mock import MagicMock, patch

import googlemaps
import numpy as np
from pydantic import SecretStr
from smarter.apps.llmtool.extension.testing import call_tool, tool_context

from weather.models import Conditions
from weather.services import UNITS, ForecastError, GeocodingError, Place, Weather, geocode, weather
from weather.tools import GetWeather

API_URL = "https://api.open-meteo.com/v1/forecast"
CONTEXT = tool_context("weather", google_maps_api_key=SecretStr("test-key"), weather_api_url=API_URL)
PARIS = Place("Paris, France", 48.85, 2.35)
NOW = Conditions(time="2026-10-15 14:00", temperature=18.5, precipitation=0.0, wind_speed=12.0, cloud_cover=40)
START = 1_792_065_600
"""2026-10-15 12:00 UTC: 14:00 in Paris."""


def open_meteo_response(hours: int = 24) -> MagicMock:
    """An Open-Meteo response for Paris, with current conditions and ``hours`` hours of each variable."""
    response = MagicMock()
    response.UtcOffsetSeconds.return_value = 7200
    response.Timezone.return_value = b"Europe/Paris"
    current = MagicMock()
    current.Time.return_value = START
    current.Variables.side_effect = lambda i: MagicMock(Value=MagicMock(return_value=[18.5, 0.0, 12.0, 40.0][i]))
    response.Current.return_value = current
    hourly = MagicMock()
    hourly.Time.return_value = START
    hourly.TimeEnd.return_value = START + hours * 3600
    hourly.Interval.return_value = 3600
    hourly.Variables.side_effect = lambda i: MagicMock(ValuesAsNumpy=MagicMock(return_value=np.arange(hours) + i))
    response.Hourly.return_value = hourly
    return response


class TestGetWeather(unittest.TestCase):
    """Test the tool."""

    def test_weather(self):
        found = Weather(timezone="Europe/Paris", current=NOW, forecast=[NOW])
        with patch("weather.tools.geocode", return_value=PARIS), patch("weather.tools.weather", return_value=found):
            result = call_tool(GetWeather, {"location": "Paris", "unit": "USCS"}, CONTEXT)
        self.assertEqual(result["location"], "Paris, France")
        self.assertEqual(result["timezone"], "Europe/Paris")
        self.assertEqual(
            result["units"], {"temperature": "°F", "precipitation": "inch", "wind_speed": "mph", "cloud_cover": "%"}
        )
        self.assertEqual(result["current"]["time"], "2026-10-15 14:00")
        self.assertEqual(len(result["forecast"]), 1)

    def test_unknown_place(self):
        with patch("weather.services.googlemaps.Client") as client:
            client.return_value.geocode.return_value = []
            result = call_tool(GetWeather, {"location": "Atlantis"}, CONTEXT)
        self.assertEqual(result, {"error": "Could not find Atlantis: no such place"})

    def test_weather_unavailable(self):
        with (
            patch("weather.tools.geocode", return_value=PARIS),
            patch("weather.tools.weather", side_effect=ForecastError("timed out")),
        ):
            result = call_tool(GetWeather, {"location": "Paris"}, CONTEXT)
        self.assertEqual(result, {"error": "The weather service is unavailable: timed out"})

    def test_invalid_arguments(self):
        self.assertIn("Invalid arguments", call_tool(GetWeather, {"location": "Paris", "unit": "KELVIN"})["error"])
        self.assertIn("Invalid arguments", call_tool(GetWeather, {})["error"])

    def test_definition(self):
        self.assertEqual(GetWeather.problems(), [])
        self.assertEqual(GetWeather.parameters()["required"], ["location"])


class TestServices(unittest.TestCase):
    """Test geocoding and the weather, with their clients mocked."""

    def test_geocode(self):
        with patch("weather.services.googlemaps.Client") as client:
            client.return_value.geocode.return_value = [
                {"formatted_address": "Paris, France", "geometry": {"location": {"lat": 48.85, "lng": 2.35}}}
            ]
            self.assertEqual(geocode("Paris", "key"), PARIS)
        with patch("weather.services.googlemaps.Client", side_effect=ValueError("Invalid API key provided.")):
            with self.assertRaises(GeocodingError):
                geocode("Paris", "not-a-key")
        with patch("weather.services.googlemaps.Client") as client:
            client.return_value.geocode.side_effect = googlemaps.exceptions.ApiError("REQUEST_DENIED")
            with self.assertRaises(GeocodingError):
                geocode("Paris", "key")

    def test_weather(self):
        with patch("weather.services.openmeteo_requests.Client") as client:
            client.return_value.weather_api.return_value = [open_meteo_response()]
            found = weather(PARIS, "USCS", API_URL)
        self.assertEqual(found.timezone, "Europe/Paris")
        self.assertEqual(found.current, NOW)
        self.assertEqual(len(found.forecast), 24)
        self.assertEqual(found.forecast[0].time, "2026-10-15 14:00")
        self.assertEqual(found.forecast[23].time, "2026-10-16 13:00")
        hour = found.forecast[1]
        self.assertEqual(
            (hour.temperature, hour.precipitation, hour.wind_speed, hour.cloud_cover), (1.0, 2.0, 3.0, 4.0)
        )
        params = client.return_value.weather_api.call_args.kwargs["params"]
        self.assertEqual(
            (params["forecast_hours"], params["timezone"], params["temperature_unit"]), (24, "auto", "fahrenheit")
        )
        self.assertEqual(UNITS["METRIC"].wind_speed, "km/h")

    def test_weather_failure(self):
        with patch("weather.services.openmeteo_requests.Client") as client:
            client.return_value.weather_api.side_effect = RuntimeError("down")
            with self.assertRaises(ForecastError):
                weather(PARIS, "METRIC", API_URL)
