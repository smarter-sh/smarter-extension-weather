"""
Weather
=======

Current weather and a 24-hour forecast for any location, from the Open-Meteo api, with
locations found by the Google Maps Geocoding api.

Settings
--------

``google_maps_api_key``
    Required. A Google Maps API key with the Geocoding API enabled. See
    https://developers.google.com/maps/documentation/geocoding/get-api-key.

``weather_api_url``
    The Open-Meteo forecast api. Change it only to use a self-hosted Open-Meteo.

Tools
-----

``get_weather(location, unit)``
    The temperature, precipitation, wind speed and cloud cover, hour by hour, for the next 24
    hours, in metric or US customary units.
"""
