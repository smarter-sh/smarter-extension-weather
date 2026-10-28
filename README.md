# Smarter Extension: Weather

[![Build Status](https://img.shields.io/github/actions/workflow/status/smarter-sh/smarter-extension-weather/release.yml?label=build&logo=github)](https://github.com/smarter-sh/smarter-extension-weather/actions/workflows/release.yml)
[![Test Status](https://github.com/smarter-sh/smarter-extension-weather/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/smarter-sh/smarter-extension-weather/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/codecov/c/github/smarter-sh/smarter-extension-weather/main?label=coverage&logo=codecov)](https://codecov.io/gh/smarter-sh/smarter-extension-weather)
[![Latest Release](https://img.shields.io/github/v/release/smarter-sh/smarter-extension-weather?label=release)](https://github.com/smarter-sh/smarter-extension-weather/releases)
[![Official Smarter Extension](https://img.shields.io/badge/Smarter%20Extension-official-0b6e4f)](https://github.com/smarter-sh/extensions-registry)
[![Docs](https://img.shields.io/badge/Read%20the%20Docs-smarter.sh-blue?logo=readthedocs)](https://docs.smarter.sh/en/latest/smarter-framework/smarter-extensions.html)
[![License: GNU AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

An official [Smarter Extension](https://docs.smarter.sh/en/latest/smarter-framework/smarter-extensions.html)
that gives LLMs the current weather and a 24-hour forecast for any location. Its one tool,
`get_weather`, is the tool that the
[OpenAI function calling guide](https://platform.openai.com/docs/guides/function-calling) describes,
implemented for real: it finds the location with the Google Maps Geocoding API, and gets the
forecast from [Open-Meteo](https://open-meteo.com/). A forecast is cached for an hour (the tool's
`cache_ttl`), so the same location and unit, from any LLMClient, are answered without calling
either service again, on platforms that cache tool results.

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

CI runs the tests on every push and pull request, against a source checkout of Smarter, and reports
coverage to Codecov. To run them yourself, in a Smarter development container:

```console
docker cp . smarter-app:/tmp/smarter-extension-weather
docker exec smarter-app bash -c "cd /home/smarter_user/smarter && python manage.py test_extension /tmp/smarter-extension-weather"
```

## Release

Releases are made by [semantic-release](https://semantic-release.gitbook.io/), on each push to
`main`, from the commits' [conventional commit](https://www.conventionalcommits.org/) types: a
`fix:` releases a patch, a `feat:` a minor version, and a `BREAKING CHANGE:` a major version. Don't
edit `version` in `pyproject.toml` or `CHANGELOG.md` by hand: the release sets the version, adds
its notes to the changelog, tags the commit `v<version>`, and attaches the archive and its sha256
to the GitHub release. The release workflow's summary prints them, for the release's entry in
[smarter-sh/extensions-registry](https://github.com/smarter-sh/extensions-registry). See
`release.config.js`.
