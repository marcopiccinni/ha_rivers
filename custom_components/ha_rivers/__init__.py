"""The Fiumi (Emilia-Romagna rivers) integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .catalog import async_get_catalog
from .coordinator import RiverCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]

type HaRiversConfigEntry = ConfigEntry[RiverCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: HaRiversConfigEntry) -> bool:
    """Set up a station from a config entry."""
    catalog = async_get_catalog(hass)
    coordinator = RiverCoordinator(hass, entry, catalog)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HaRiversConfigEntry) -> bool:
    """Unload a station config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
