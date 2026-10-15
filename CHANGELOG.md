# Changelog

## [0.2.0](https://github.com/smarter-sh/smarter-extension-weather/compare/v0.1.0...v0.2.0) (2026-10-15)

### Features

* current conditions, local times and units ([51ec052](https://github.com/smarter-sh/smarter-extension-weather/commit/51ec052a5ffb8515b0ceff337d744b1ad5cd0e10))

### Bug Fixes

* force a new release ([8fccc9d](https://github.com/smarter-sh/smarter-extension-weather/commit/8fccc9dd543391096c5dc1305cc82791db9c5150))

## 0.2.0

- `get_weather` returns the current conditions, as well as the forecast.
- The forecast starts at the current hour, rather than at midnight UTC.
- Times are in the location's own timezone, which the result names.
- The result names the unit of each measurement, e.g. `km/h` or `mph`.
- No longer depends on pandas.

## 0.1.0

- The `get_weather` tool, ported from Smarter's former built-in `get_current_weather` function to
  the Smarter Extension protocol.
