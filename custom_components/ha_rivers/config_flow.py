"""Config flow for the Fiumi integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .catalog import async_fetch_time_series, async_get_catalog
from .const import (
    CONF_METADATA_INTERVAL,
    CONF_SCAN_INTERVAL,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    DEFAULT_METADATA_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DISCLAIMER,
    DOMAIN,
    MIN_METADATA_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class HaRiversConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the UI configuration flow (one station per entry)."""

    VERSION = 1

    def __init__(self) -> None:
        self._query: str = ""
        self._results: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ask the user what to search for."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._query = user_input["query"].strip()
            catalog = async_get_catalog(self.hass)
            try:
                stations = await catalog.async_search(self._query)
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            else:
                if not stations:
                    errors["base"] = "no_stations_found"
                else:
                    self._results = {station.id: station for station in stations}
                    return await self.async_step_select()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("query", default=self._query): str}),
            errors=errors,
            description_placeholders={"disclaimer": DISCLAIMER},
        )

    async def async_step_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Let the user pick one of the matching stations."""
        errors: dict[str, str] = {}

        if user_input is not None:
            station = self._results.get(str(user_input["station"]))
            if station is None:
                errors["base"] = "no_stations_found"
            else:
                await self.async_set_unique_id(station.id)
                self._abort_if_unique_id_configured()

                session = async_get_clientsession(self.hass)
                try:
                    series = await async_fetch_time_series(session, station.id)
                except (aiohttp.ClientError, TimeoutError):
                    errors["base"] = "cannot_connect"
                else:
                    if not series:
                        errors["base"] = "no_series_data"
                    else:
                        return self.async_create_entry(
                            title=station.name,
                            data={
                                CONF_STATION_ID: station.id,
                                CONF_STATION_NAME: station.name,
                            },
                        )

        options = {sid: station.label() for sid, station in self._results.items()}
        return self.async_show_form(
            step_id="select",
            data_schema=vol.Schema({vol.Required("station"): vol.In(options)}),
            errors=errors,
            description_placeholders={
                "query": self._query,
                "count": str(len(options)),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return HaRiversOptionsFlow()


class HaRiversOptionsFlow(OptionsFlow):
    """Options: refresh intervals."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        entry = self.config_entry
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)),
                vol.Optional(
                    CONF_METADATA_INTERVAL,
                    default=entry.options.get(
                        CONF_METADATA_INTERVAL, DEFAULT_METADATA_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_METADATA_INTERVAL)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
