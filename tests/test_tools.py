"""Tests of the get_weather tool, with its services mocked."""

import unittest
from unittest.mock import MagicMock, patch

import googlemaps
import numpy as np
from pydantic import SecretStr
from weather.services import ForecastError, Place, forecast, geocode
from weather.tools import GetWeather

from smarter.apps.llmtool.extension.testing import call_tool, tool_context

API_URL = "https://api.open-meteo.com/v1/forecast"
CONTEXT = tool_context("weather", google_maps_api_key=SecretStr("test-key"), weather_api_url=API_URL)
PARIS = Place("Paris, France", 48.85, 2.35)


def open_meteo_response(hours: int = 30) -> MagicMock:
    """An Open-Meteo response with ``hours`` hours of each variable, starting at 0:00 UTC."""
    hourly = MagicMock()
    hourly.Time.return_value = 1_760_486_400
    hourly.TimeEnd.return_value = 1_760_486_400 + hours * 3600
    hourly.Interval.return_value = 3600
    hourly.Variables.side_effect = lambda i: MagicMock(ValuesAsNumpy=MagicMock(return_value=np.arange(hours) + i))
    response = MagicMock()
    response.Hourly.return_value = hourly
    return response


class TestGetWeather(unittest.TestCase):
    """Test the tool."""

    def test_forecast(self):
        with patch("weather.tools.geocode", return_value=PARIS), patch("weather.tools.forecast", return_value=[]):
            result = call_tool(GetWeather, {"location": "Paris"}, CONTEXT)
        self.assertEqual(
            result,
            {"location": "Paris, France", "latitude": 48.85, "longitude": 2.35, "unit": "METRIC", "forecast": []},
        )

    def test_unknown_place(self):
        with patch("weather.services.googlemaps.Client") as client:
            client.return_value.geocode.return_value = []
            result = call_tool(GetWeather, {"location": "Atlantis"}, CONTEXT)
        self.assertEqual(result, {"error": "Could not find Atlantis: no such place"})

    def test_forecast_unavailable(self):
        with (
            patch("weather.tools.geocode", return_value=PARIS),
            patch("weather.tools.forecast", side_effect=ForecastError("timed out")),
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
    """Test geocoding and the forecast, with their clients mocked."""

    def test_geocode(self):
        with patch("weather.services.googlemaps.Client") as client:
            client.return_value.geocode.return_value = [
                {"formatted_address": "Paris, France", "geometry": {"location": {"lat": 48.85, "lng": 2.35}}}
            ]
            self.assertEqual(geocode("Paris", "key"), PARIS)
        with patch("weather.services.googlemaps.Client", side_effect=ValueError("Invalid API key provided.")):
            with self.assertRaises(Exception):
                geocode("Paris", "not-a-key")
        with patch("weather.services.googlemaps.Client") as client:
            client.return_value.geocode.side_effect = googlemaps.exceptions.ApiError("REQUEST_DENIED")
            with self.assertRaises(Exception):
                geocode("Paris", "key")

    def test_forecast(self):
        with patch("weather.services.openmeteo_requests.Client") as client:
            client.return_value.weather_api.return_value = [open_meteo_response()]
            hours = forecast(PARIS, "USCS", API_URL)
        self.assertEqual(len(hours), 24)
        self.assertEqual(hours[0].time, "2025-10-15 00:00")
        self.assertEqual(
            (hours[1].temperature, hours[1].precipitation, hours[1].wind_speed, hours[1].cloud_cover),
            (1.0, 2.0, 3.0, 4.0),
        )
        params = client.return_value.weather_api.call_args.kwargs["params"]
        self.assertEqual(params["temperature_unit"], "fahrenheit")

    def test_forecast_failure(self):
        with patch("weather.services.openmeteo_requests.Client") as client:
            client.return_value.weather_api.side_effect = RuntimeError("down")
            with self.assertRaises(ForecastError):
                forecast(PARIS, "METRIC", API_URL)
