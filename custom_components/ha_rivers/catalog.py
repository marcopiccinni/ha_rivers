"""Station catalog for the Fiumi integration.

Fetches and caches the station lists exposed by the two organizations:

* ARPAE (``meteo_osservati``) - authoritative metadata: river basin,
  municipality, thresholds, coordinates and the list of available variables.
* AllertaMeteoER (``get-stations``) - availability flag and consistent ids.

The catalog is cached in ``hass.data`` for :data:`CATALOG_TTL` so search
requests from the config flow never hit the network more than once per day.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    ALLERTA_STATIONS_URL,
    ALLERTA_TIME_SERIES_URL,
    ARPAE_STATIONS_URL,
    CATALOG_MAX_RESULTS,
    CATALOG_TTL,
    DOMAIN,
    LEVEL_SENSOR,
    LEVEL_VARIABLE,
    SEARCH_MAX_RESULTS,
    USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=30)


def _to_float(value: Any) -> float | None:
    """Best effort conversion to float."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass(slots=True)
class Station:
    """A hydrometric station."""

    id: str
    name: str
    basin: str | None = None
    sub_basin: str | None = None
    municipality: str | None = None
    province: str | None = None
    region: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    thresholds: list[float | None] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)
    active: bool | None = None

    def label(self) -> str:
        """Human readable label used in the config flow."""
        parts = [self.name]
        if self.basin:
            parts.append(self.basin)
        if self.municipality:
            parts.append(self.municipality)
        parts.append(self.id)
        return " - ".join(str(part) for part in parts)


def station_from_arpae(item: dict[str, Any]) -> Station:
    """Build a :class:`Station` from an ARPAE ``meteo_osservati`` record."""
    ana = item.get("anagrafica") or {}
    coordinates = (ana.get("geometry") or {}).get("coordinates") or []
    sensor = (ana.get("sensori") or {}).get(LEVEL_SENSOR) or {}
    soglie = list(sensor.get("soglie") or [])[:3]
    soglie += [None] * (3 - len(soglie))

    return Station(
        id=str(item.get("_id")),
        name=ana.get("nome") or f"Stazione {item.get('_id')}",
        basin=ana.get("bacino"),
        sub_basin=ana.get("sottobacino"),
        municipality=ana.get("comune"),
        province=ana.get("provincia"),
        region=ana.get("regione"),
        latitude=_to_float(coordinates[1]) if len(coordinates) > 1 else None,
        longitude=_to_float(coordinates[0]) if len(coordinates) > 0 else None,
        altitude=_to_float(ana.get("altitudine")),
        thresholds=[_to_float(value) for value in soglie],
        variables=list(ana.get("variabili") or []),
    )


async def _get_json(
    session: aiohttp.ClientSession, url: str, params: dict[str, str]
) -> Any:
    """GET ``url`` and decode the JSON payload."""
    async with session.get(
        url, params=params, headers={"User-Agent": USER_AGENT}, timeout=_TIMEOUT
    ) as response:
        response.raise_for_status()
        return await response.json(content_type=None)


async def async_search_arpae(
    session: aiohttp.ClientSession, query: str, limit: int = SEARCH_MAX_RESULTS
) -> list[Station]:
    """Server-side (case-insensitive, substring) search on ARPAE."""
    where: dict[str, Any] = {"anagrafica.variabili": LEVEL_SENSOR}
    query = (query or "").strip()
    if query:
        where["$or"] = [
            {"anagrafica.nome": {"$regex": query, "$options": "i"}},
            {"anagrafica.bacino": {"$regex": query, "$options": "i"}},
            {"anagrafica.comune": {"$regex": query, "$options": "i"}},
            {"anagrafica.provincia": {"$regex": query, "$options": "i"}},
            {"_id": query},
        ]

    payload = await _get_json(
        session,
        ARPAE_STATIONS_URL,
        {
            "where": json.dumps(where),
            "projection": json.dumps({"dati": 0}),
            "max_results": str(limit),
        },
    )
    return [station_from_arpae(item) for item in payload.get("_items", [])]


async def async_fetch_time_series(
    session: aiohttp.ClientSession, station_id: str
) -> list[dict[str, Any]]:
    """Fetch the near real-time level series for a station.

    An empty list means the station currently exposes no data.
    """
    payload = await _get_json(
        session,
        ALLERTA_TIME_SERIES_URL,
        {"stazione": str(station_id), "variabile": LEVEL_VARIABLE},
    )
    return payload if isinstance(payload, list) else []


async def async_fetch_station_metadata(
    session: aiohttp.ClientSession, station_id: str
) -> dict[str, Any] | None:
    """Fetch the full ARPAE record (including recent ``dati``) for a station."""
    payload = await _get_json(
        session,
        ARPAE_STATIONS_URL,
        {"where": json.dumps({"_id": str(station_id)}), "max_results": "1"},
    )
    items = payload.get("_items") or []
    return items[0] if items else None


def latest_metadata_values(metadata: dict[str, Any] | None) -> dict[str, float]:
    """Return the most recent values for every variable in an ARPAE record."""
    if not metadata:
        return {}
    dati = metadata.get("dati") or {}
    if not dati:
        return {}
    latest_day = max(dati)
    slots = dati.get(latest_day) or {}
    if not slots:
        return {}
    latest_slot = slots[max(slots)] or {}
    return {
        key: float(value)
        for key, value in latest_slot.items()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    }


class StationCatalog:
    """Cached access to the station catalogs of both organizations."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._session = async_get_clientsession(hass)
        self._allerta: dict[str, dict[str, Any]] | None = None
        self._allerta_ts = 0.0

    async def async_allerta_stations(
        self, force: bool = False
    ) -> dict[str, dict[str, Any]]:
        """Return the AllertaMeteoER station map keyed by station id."""
        fresh = (
            self._allerta is not None
            and (time.monotonic() - self._allerta_ts) <= CATALOG_TTL.total_seconds()
        )
        if force or not fresh:
            payload = await _get_json(self._session, ALLERTA_STATIONS_URL, {})
            self._allerta = {
                str(station.get("id_")): station
                for station in payload
                if isinstance(station, dict) and station.get("id_") is not None
            }
            self._allerta_ts = time.monotonic()
        return self._allerta or {}

    async def async_full_catalog(self) -> list[Station]:
        """Return every hydrometric station available in ARPAE."""
        payload = await _get_json(
            self._session,
            ARPAE_STATIONS_URL,
            {
                "where": json.dumps({"anagrafica.variabili": LEVEL_SENSOR}),
                "projection": json.dumps({"dati": 0}),
                "max_results": str(CATALOG_MAX_RESULTS),
            },
        )
        return [station_from_arpae(item) for item in payload.get("_items", [])]

    async def async_search(self, query: str) -> list[Station]:
        """Search stations by free text, enriched with the availability flag."""
        stations = await async_search_arpae(self._session, query)
        if not stations:
            return []

        try:
            allerta = await self.async_allerta_stations()
        except (aiohttp.ClientError, TimeoutError):
            _LOGGER.debug("AllertaMeteoER catalog unavailable, skipping flag")
            allerta = {}

        for station in stations:
            entry = allerta.get(station.id)
            if entry is not None:
                station.active = bool(entry.get("attivo", True))
        return stations


def async_get_catalog(hass: HomeAssistant) -> StationCatalog:
    """Return the shared, per-instance catalog."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    catalog = domain_data.get("catalog")
    if not isinstance(catalog, StationCatalog):
        catalog = StationCatalog(hass)
        domain_data["catalog"] = catalog
    return catalog
