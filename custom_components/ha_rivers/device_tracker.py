"""Device tracker platform for the Fiumi integration.

Exposes the fixed position of a station so it shows up automatically on the
Home Assistant map (Map dashboard, *Devices* tab) without having to list the
sensor entities by hand.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import RiverCoordinator

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the map position of a station."""
    coordinator: RiverCoordinator = entry.runtime_data
    async_add_entities([StationTracker(coordinator)])


class StationTracker(CoordinatorEntity[RiverCoordinator], TrackerEntity):
    """Fixed geographic position of a hydrometric station."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_source_type = SourceType.GPS
    _attr_location_accuracy = 0

    def __init__(self, coordinator: RiverCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.station_id}_location"

    @property
    def device_info(self) -> DeviceInfo:
        data = self.coordinator.data
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.station_id)},
            name=data.name if data else self.coordinator.station_id,
            manufacturer="ARPAE / AllertaMeteoER",
            model="Stazione idrometrica",
            configuration_url="https://allertameteo.regione.emilia-romagna.it/",
        )

    @property
    def latitude(self) -> float | None:
        return self.coordinator.data.latitude if self.coordinator.data else None

    @property
    def longitude(self) -> float | None:
        return self.coordinator.data.longitude if self.coordinator.data else None

    @property
    def location_name(self) -> str | None:
        data = self.coordinator.data
        return data.name if data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        data = self.coordinator.data
        if data is None:
            return None
        return {
            "station_id": data.station_id,
            "basin": data.basin,
            "municipality": data.municipality,
            "province": data.province,
            "level": data.level,
            "alert": data.alert,
            "active": data.active,
        }
