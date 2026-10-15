"""Sensor platform for the Fiumi integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfLength,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import (
    ALERT_OPTIONS,
    EXTRA_VARIABLES,
    RiverCoordinator,
    RiverData,
    threshold_at,
)

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class RiverSensorEntityDescription(SensorEntityDescription):
    """Describes a Fiumi sensor."""

    value_fn: Callable[[RiverData], Any]


CORE_SENSORS: tuple[RiverSensorEntityDescription, ...] = (
    RiverSensorEntityDescription(
        key="level",
        translation_key="level",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.METERS,
        icon="mdi:waves-arrow-up",
        value_fn=lambda data: data.level,
    ),
    RiverSensorEntityDescription(
        key="alert",
        translation_key="alert",
        device_class=SensorDeviceClass.ENUM,
        options=ALERT_OPTIONS,
        icon="mdi:alert",
        value_fn=lambda data: data.alert,
    ),
    RiverSensorEntityDescription(
        key="threshold_yellow",
        translation_key="threshold_yellow",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.METERS,
        icon="mdi:water-alert",
        value_fn=lambda data: threshold_at(data, 0),
    ),
    RiverSensorEntityDescription(
        key="threshold_orange",
        translation_key="threshold_orange",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.METERS,
        icon="mdi:water-alert",
        value_fn=lambda data: threshold_at(data, 1),
    ),
    RiverSensorEntityDescription(
        key="threshold_red",
        translation_key="threshold_red",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.METERS,
        icon="mdi:water-alert",
        value_fn=lambda data: threshold_at(data, 2),
    ),
    RiverSensorEntityDescription(
        key="trend",
        translation_key="trend",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="m/h",
        icon="mdi:trending-up",
        value_fn=lambda data: data.trend,
    ),
    RiverSensorEntityDescription(
        key="last_measurement",
        translation_key="last_measurement",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.level_time,
    ),
    RiverSensorEntityDescription(
        key="last_metadata_update",
        translation_key="last_metadata_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.metadata_time,
    ),
)

EXTRA_SENSOR_DESCRIPTIONS: dict[str, RiverSensorEntityDescription] = {
    "portata_istantanea": RiverSensorEntityDescription(
        key="discharge",
        translation_key="discharge",
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_SECOND,
        icon="mdi:water-pump",
        value_fn=lambda data: data.extras.get("portata_istantanea"),
    ),
    "precipitazione_cumulata_1h": RiverSensorEntityDescription(
        key="precipitation_1h",
        translation_key="precipitation_1h",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        icon="mdi:weather-rainy",
        value_fn=lambda data: data.extras.get("precipitazione_cumulata_1h"),
    ),
    "temperatura_istantanea_2m": RiverSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.extras.get("temperatura_istantanea_2m"),
    ),
    "umidita_istantanea_2m": RiverSensorEntityDescription(
        key="humidity",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.extras.get("umidita_istantanea_2m"),
    ),
    "pressione_atmosferica": RiverSensorEntityDescription(
        key="pressure",
        translation_key="pressure",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.HPA,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.extras.get("pressione_atmosferica"),
    ),
    "velocita_vento_istantanea_10m": RiverSensorEntityDescription(
        key="wind_speed",
        translation_key="wind_speed",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-windy",
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.extras.get("velocita_vento_istantanea_10m"),
    ),
    "direzione_vento_istantanea_10m": RiverSensorEntityDescription(
        key="wind_direction",
        translation_key="wind_direction",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="°",
        icon="mdi:compass",
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.extras.get("direzione_vento_istantanea_10m"),
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensors of a station."""
    coordinator: RiverCoordinator = entry.runtime_data
    data = coordinator.data

    descriptions = list(CORE_SENSORS)
    variables = set(data.variables) if data else set(EXTRA_VARIABLES)
    for variable, description in EXTRA_SENSOR_DESCRIPTIONS.items():
        if variable in variables:
            descriptions.append(description)

    async_add_entities(
        RiverSensor(coordinator, description) for description in descriptions
    )


class RiverSensor(CoordinatorEntity[RiverCoordinator], SensorEntity):
    """A single Fiumi sensor."""

    entity_description: RiverSensorEntityDescription
    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: RiverCoordinator,
        description: RiverSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.station_id}_{description.key}"

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
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key != "level" or self.coordinator.data is None:
            return None
        data = self.coordinator.data
        return {
            "station_id": data.station_id,
            "basin": data.basin,
            "sub_basin": data.sub_basin,
            "municipality": data.municipality,
            "province": data.province,
            "region": data.region,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "altitude": data.altitude,
            "thresholds": {
                "yellow": threshold_at(data, 0),
                "orange": threshold_at(data, 1),
                "red": threshold_at(data, 2),
            },
            "series_points": len(data.series or []),
            "active": data.active,
        }
