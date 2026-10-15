"""The arguments and result of the get_weather tool."""

from typing import Literal

from pydantic import BaseModel, Field

Unit = Literal["METRIC", "USCS"]
"""Metric, or US customary, units."""


class WeatherArguments(BaseModel):
    """The arguments of get_weather."""

    location: str = Field(..., min_length=1, description="The city and state or country, e.g. San Francisco, CA")
    unit: Unit = Field("METRIC", description="Metric, or US customary, units.")


class HourlyForecast(BaseModel):
    """The weather in one hour."""

    time: str = Field(..., description="The hour, in UTC, e.g. 2026-10-15 14:00.")
    temperature: float = Field(..., description="The temperature at 2 m, in degrees Celsius or Fahrenheit.")
    precipitation: float = Field(..., description="The precipitation, in millimeters or inches.")
    wind_speed: float = Field(..., description="The wind speed at 10 m, in km/h or mph.")
    cloud_cover: float = Field(..., description="The cloud cover, in percent.")


class WeatherResult(BaseModel):
    """What get_weather returns to the LLM."""

    location: str = Field(..., description="The location's address, as Google Maps found it.")
    latitude: float
    longitude: float
    unit: Unit
    forecast: list[HourlyForecast]
