"""Data update coordinator for the Fiumi integration."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .catalog import (
    StationCatalog,
    async_fetch_station_metadata,
    async_fetch_time_series,
    latest_metadata_values,
    station_from_arpae,
)
from .const import (
    CONF_METADATA_INTERVAL,
    CONF_SCAN_INTERVAL,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    DEFAULT_METADATA_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LEVEL_SENSOR,
)

_LOGGER = logging.getLogger(__name__)

ALERT_NORMAL: str = "normale"
ALERT_YELLOW: str = "gialla"
ALERT_ORANGE: str = "arancione"
ALERT_RED: str = "rossa"
ALERT_UNKNOWN: str = "nd"

ALERT_OPTIONS: list[str] = [
    ALERT_NORMAL,
    ALERT_YELLOW,
    ALERT_ORANGE,
    ALERT_RED,
    ALERT_UNKNOWN,
]

# Variables exposed as extra sensors, mapped to the metadata interval.
EXTRA_VARIABLES: dict[str, str] = {
    "portata_istantanea": "discharge",
    "precipitazione_cumulata_1h": "precipitation_1h",
    "temperatura_istantanea_2m": "temperature",
    "umidita_istantanea_2m": "humidity",
    "pressione_atmosferica": "pressure",
    "velocita_vento_istantanea_10m": "wind_speed",
    "direzione_vento_istantanea_10m": "wind_direction",
}


@dataclass(slots=True)
class RiverData:
    """Snapshot of a station returned by the coordinator."""

    station_id: str
    name: str
    level: float | None = None
    level_time: datetime | None = None
    trend: float | None = None
    thresholds: list[float | None] = field(default_factory=list)
    alert: str = ALERT_UNKNOWN
    active: bool | None = None
    basin: str | None = None
    sub_basin: str | None = None
    municipality: str | None = None
    province: str | None = None
    region: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    variables: list[str] = field(default_factory=list)
    metadata_time: datetime | None = None
    extras: dict[str, float] = field(default_factory=dict)
    series: list[dict[str, Any]] = field(default_factory=list)


def threshold_at(data: RiverData, index: int) -> float | None:
    """Return the threshold at ``index`` (0=yellow, 1=orange, 2=red)."""
    if len(data.thresholds) > index:
        return data.thresholds[index]
    return None


def _compute_trend(series: list[dict[str, Any]]) -> float | None:
    """Return the level variation (m/h) over roughly the last hour."""
    if len(series) < 2:
        return None
    ordered = sorted(series, key=lambda point: point.get("t", 0))
    last = ordered[-1]
    target = last.get("t", 0) - 3_600_000
    reference = None
    for point in reversed(ordered[:-1]):
        if point.get("t", 0) <= target:
            reference = point
            break
    if reference is None or reference.get("t") == last.get("t"):
        return None
    try:
        return round(float(last["v"]) - float(reference["v"]), 3)
    except (KeyError, TypeError, ValueError):
        return None


def _compute_alert(level: float | None, thresholds: list[float | None]) -> str:
    yellow, orange, red = (
        thresholds + [None, None, None]
    )[:3]
    if level is None or any(value is None for value in (yellow, orange, red)):
        return ALERT_UNKNOWN
    if level >= red:  # type: ignore[operator]
        return ALERT_RED
    if level >= orange:  # type: ignore[operator]
        return ALERT_ORANGE
    if level >= yellow:  # type: ignore[operator]
        return ALERT_YELLOW
    return ALERT_NORMAL


class RiverCoordinator(DataUpdateCoordinator[RiverData]):
    """Coordinator polling the level series and, less often, the metadata."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        catalog: StationCatalog,
    ) -> None:
        scan_interval = int(
            entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {entry.data[CONF_STATION_ID]}",
            update_interval=timedelta(seconds=scan_interval),
            config_entry=entry,
        )
        self.entry = entry
        self.catalog = catalog
        self.session = async_get_clientsession(hass)
        self.station_id: str = str(entry.data[CONF_STATION_ID])
        self.metadata_interval: int = int(
            entry.options.get(CONF_METADATA_INTERVAL, DEFAULT_METADATA_INTERVAL)
        )
        self._metadata: dict[str, Any] | None = None
        self._metadata_ts = 0.0
        self._metadata_station = None
        entry.async_on_unload(entry.add_update_listener(self._async_options_updated))

    async def _async_options_updated(
        self, hass: HomeAssistant, entry: ConfigEntry
    ) -> None:
        self.update_interval = timedelta(
            seconds=int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        )
        self.metadata_interval = int(
            entry.options.get(CONF_METADATA_INTERVAL, DEFAULT_METADATA_INTERVAL)
        )
        await self.async_request_refresh()

    async def _async_refresh_metadata(self) -> None:
        stale = (time.monotonic() - self._metadata_ts) >= self.metadata_interval
        if self._metadata is not None and not stale:
            return
        try:
            metadata = await async_fetch_station_metadata(
                self.session, self.station_id
            )
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            _LOGGER.debug("Metadata refresh failed for %s: %s", self.station_id, err)
            return
        if metadata is not None:
            self._metadata = metadata
            self._metadata_ts = time.monotonic()
            self._metadata_station = station_from_arpae(metadata)

    async def _async_update_data(self) -> RiverData:
        try:
            series, _ = await asyncio.gather(
                async_fetch_time_series(self.session, self.station_id),
                self._async_refresh_metadata(),
            )
        except TimeoutError as err:
            raise UpdateFailed("Timeout while fetching station data") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error fetching station data: {err}") from err

        values = latest_metadata_values(self._metadata)
        station = self._metadata_station

        level: float | None = None
        level_time: datetime | None = None
        if series:
            ordered = sorted(series, key=lambda point: point.get("t", 0))
            last = ordered[-1]
            raw_level = last.get("v")
            if isinstance(raw_level, (int, float)) and not isinstance(raw_level, bool):
                level = float(raw_level)
            timestamp = last.get("t")
            if isinstance(timestamp, (int, float)):
                level_time = datetime.fromtimestamp(timestamp / 1000, tz=UTC)

        thresholds: list[float | None] = station.thresholds if station else []
        metadata_time: datetime | None = None
        if self._metadata is not None:
            updated = self._metadata.get("_updated")
            parsed = _parse_http_date(updated)
            if parsed is not None:
                metadata_time = parsed

        extras = {
            key: value
            for key, value in values.items()
            if key in EXTRA_VARIABLES and key != LEVEL_SENSOR
        }

        active: bool | None = None
        try:
            allerta = await self.catalog.async_allerta_stations()
            record = allerta.get(self.station_id)
            if record is not None:
                active = bool(record.get("attivo", True))
        except (aiohttp.ClientError, TimeoutError):
            active = None

        return RiverData(
            station_id=self.station_id,
            name=(station.name if station else None)
            or self.entry.data.get(CONF_STATION_NAME)
            or self.station_id,
            level=level,
            level_time=level_time,
            trend=_compute_trend(series),
            thresholds=thresholds,
            alert=_compute_alert(level, thresholds),
            active=active,
            basin=station.basin if station else None,
            sub_basin=station.sub_basin if station else None,
            municipality=station.municipality if station else None,
            province=station.province if station else None,
            region=station.region if station else None,
            latitude=station.latitude if station else None,
            longitude=station.longitude if station else None,
            altitude=station.altitude if station else None,
            variables=station.variables if station else list(EXTRA_VARIABLES),
            metadata_time=metadata_time,
            extras=extras,
            series=series,
        )


def _parse_http_date(value: Any) -> datetime | None:
    """Parse an HTTP date string (ARPAE ``_updated``) into a datetime."""
    if not isinstance(value, str):
        return None
    from email.utils import parsedate_to_datetime

    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
