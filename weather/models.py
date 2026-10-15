"""The arguments and result of the get_weather tool."""

from typing import Literal

from pydantic import BaseModel, Field

Unit = Literal["METRIC", "USCS"]
"""Metric, or US customary, units."""


class WeatherArguments(BaseModel):
    """The arguments of get_weather."""

    location: str = Field(..., min_length=1, description="The city and state or country, e.g. San Francisco, CA")
    unit: Unit = Field("METRIC", description="Metric, or US customary, units.")


class Units(BaseModel):
    """The units of the weather's measurements."""

    temperature: str = Field(..., description="e.g. °C or °F.")
    precipitation: str = Field(..., description="e.g. mm or inch.")
    wind_speed: str = Field(..., description="e.g. km/h or mph.")
    cloud_cover: str = Field("%", description="Percent of the sky.")


class Conditions(BaseModel):
    """The weather at one time."""

    time: str = Field(..., description="The location's local time, e.g. 2026-10-15 14:00.")
    temperature: float = Field(..., description="The temperature at 2 m.")
    precipitation: float = Field(..., description="The precipitation.")
    wind_speed: float = Field(..., description="The wind speed at 10 m.")
    cloud_cover: float = Field(..., description="The cloud cover.")


class WeatherResult(BaseModel):
    """What get_weather returns to the LLM."""

    location: str = Field(..., description="The location's address, as Google Maps found it.")
    latitude: float
    longitude: float
    timezone: str = Field(..., description="The location's timezone, e.g. Europe/Paris, in which times are given.")
    units: Units = Field(..., description="The units of every measurement.")
    current: Conditions = Field(..., description="The weather now.")
    forecast: list[Conditions] = Field(..., description="The weather in each of the next 24 hours.")
