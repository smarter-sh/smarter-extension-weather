# Smarter Extension: Weather

An official [Smarter Extension](https://docs.smarter.sh/en/latest/smarter-framework/smarter-extensions.html)
that gives LLMs the current weather and a 24-hour forecast for any location. Its one tool,
`get_weather`, is the tool that the
[OpenAI function calling guide](https://platform.openai.com/docs/guides/function-calling) describes,
implemented for real: it finds the location with the Google Maps Geocoding API, and gets the
forecast from [Open-Meteo](https://open-meteo.com/).

It is the reference example of the
[Smarter Extension developer guide](https://docs.smarter.sh/en/latest/smarter-framework/extensions/developer-guide.html).

## Install

In the Django admin console of a Smarter platform, go to **LLMTool › Extensions › Browse
extensions**, and install **Weather**. Configure its `google_maps_api_key` setting, enable it, and
list it in an LLMClient's manifest:

```yaml
spec:
  extensions:
    - weather
```

## Develop

Run the tests in a Smarter development container:

```console
docker cp . smarter-app:/tmp/smarter-extension-weather
docker exec smarter-app bash -c "cd /home/smarter_user/smarter && python manage.py test_extension /tmp/smarter-extension-weather"
```

## Release

Bump `version` in `pyproject.toml`, update `CHANGELOG.md`, and push a `v<version>` tag. The release
workflow attaches the archive to a GitHub release and prints its sha256, for the release's entry in
[smarter-sh/extensions-registry](https://github.com/smarter-sh/extensions-registry).
