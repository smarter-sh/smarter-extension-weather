"""The weather extension's tools."""

from pydantic import JsonValue
from smarter.apps.llmtool.extension import ExtensionContext, ExtensionToolError, SmarterExtensionTool

from .models import WeatherArguments, WeatherResult
from .services import UNITS, ForecastError, GeocodingError, geocode, weather


class GetWeather(SmarterExtensionTool):
    """Get the current weather, and the forecast for the next 24 hours, for a location."""

    name = "get_weather"
    arguments_model = WeatherArguments

    def call(self, arguments: WeatherArguments, context: ExtensionContext) -> JsonValue:
        settings = context.settings
        try:
            place = geocode(arguments.location, settings.google_maps_api_key.get_secret_value())
            found = weather(place, arguments.unit, settings.weather_api_url)
        except GeocodingError as e:
            raise ExtensionToolError(f"Could not find {arguments.location}: {e}") from e
        except ForecastError as e:
            raise ExtensionToolError(f"The weather service is unavailable: {e}") from e
        context.logger.info("get_weather found %s", place.address)
        return WeatherResult(
            location=place.address,
            latitude=place.latitude,
            longitude=place.longitude,
            timezone=found.timezone,
            units=UNITS[arguments.unit],
            current=found.current,
            forecast=found.forecast,
        ).model_dump(mode="json")
