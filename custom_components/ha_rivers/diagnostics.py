"""Diagnostics support for the Fiumi integration."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DISCLAIMER


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    data = coordinator.data
    return {
        "disclaimer": DISCLAIMER,
        "entry": {
            "title": entry.title,
            "data": dict(entry.data),
            "options": dict(entry.options),
            "unique_id": entry.unique_id,
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval_seconds": (
                coordinator.update_interval.total_seconds()
                if coordinator.update_interval
                else None
            ),
            "metadata_interval_seconds": coordinator.metadata_interval,
        },
        "data": asdict(data) if data else None,
    }
