"""Binary sensor platform for the Fiumi integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import RiverCoordinator

PARALLEL_UPDATES = 1

DESCRIPTION = BinarySensorEntityDescription(
    key="station_active",
    translation_key="station_active",
    device_class=BinarySensorDeviceClass.RUNNING,
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensors of a station."""
    coordinator: RiverCoordinator = entry.runtime_data
    async_add_entities([StationActiveBinarySensor(coordinator)])


class StationActiveBinarySensor(CoordinatorEntity[RiverCoordinator], BinarySensorEntity):
    """Whether the station is currently active according to AllertaMeteoER."""

    entity_description = DESCRIPTION
    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: RiverCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.station_id}_{DESCRIPTION.key}"

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
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.active
