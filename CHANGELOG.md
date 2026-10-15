# Changelog

## 0.2.0

- `get_weather` returns the current conditions, as well as the forecast.
- The forecast starts at the current hour, rather than at midnight UTC.
- Times are in the location's own timezone, which the result names.
- The result names the unit of each measurement, e.g. `km/h` or `mph`.
- No longer depends on pandas.

## 0.1.0

- The `get_weather` tool, ported from Smarter's former built-in `get_current_weather` function to
  the Smarter Extension protocol.
