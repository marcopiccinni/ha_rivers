"""Constants for the Fiumi (Emilia-Romagna rivers) integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "ha_rivers"

VERSION: Final = "0.1.0"

# ARPAE - Agenzia regionale prevenzione, ambiente ed energia dell'Emilia-Romagna.
# Eve-style REST API. Station metadata (thresholds, geodata, historical data).
ARPAE_STATIONS_URL: Final = "https://apps.arpae.it/REST/meteo_osservati/"

# AllertaMeteo Emilia-Romagna. Time-series (near real-time water level).
ALLERTA_BASE_URL: Final = (
    "https://allertameteo.regione.emilia-romagna.it/o/api/allerta"
)
ALLERTA_TIME_SERIES_URL: Final = f"{ALLERTA_BASE_URL}/get-time-series"
ALLERTA_STATIONS_URL: Final = f"{ALLERTA_BASE_URL}/get-stations"

# Hydrometric level variable used by AllertaMeteoER (self-describing id).
LEVEL_VARIABLE: Final = "254,0,0/1,-,-,-/B13215"

# Sensor key used by ARPAE for the hydrometric level.
LEVEL_SENSOR: Final = "livello_idro"

USER_AGENT: Final = f"ha_rivers/{VERSION} (Home Assistant custom integration)"

# Defaults, tuned on the values used by the reference (unofficial) setup.
DEFAULT_SCAN_INTERVAL: Final = 120  # seconds, near real-time level series
DEFAULT_METADATA_INTERVAL: Final = 12000  # seconds, thresholds/geodata extras
MIN_SCAN_INTERVAL: Final = 30
MIN_METADATA_INTERVAL: Final = 300

# The catalog of stations is cached for this long.
CATALOG_TTL: Final = timedelta(hours=24)
CATALOG_MAX_RESULTS: Final = 500
SEARCH_MAX_RESULTS: Final = 25

CONF_STATION_ID: Final = "station_id"
CONF_STATION_NAME: Final = "station_name"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_METADATA_INTERVAL: Final = "metadata_interval"

ATTRIBUTION: Final = "Dati: ARPAE e AllertaMeteoER (Regione Emilia-Romagna)"

DISCLAIMER: Final = (
    "Integrazione NON ufficiale, non affiliata ad ARPAE, AllertaMeteoER o "
    "Regione Emilia-Romagna. La disponibilita' e la continuita' del servizio "
    "non sono in alcun modo garantite."
)
