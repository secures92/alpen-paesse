"""DataUpdateCoordinator for Alpen-Paesse."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import AVAILABLE_PASSES, CONF_SELECTED_PASSES, CONF_LANGUAGE, DOMAIN, UPDATE_INTERVAL
from .alpen_paesse import AlpenPasseScraper

_LOGGER = logging.getLogger(__name__)


class AlpenPasseCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from alpen-paesse.ch."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.selected_passes = config.get(CONF_SELECTED_PASSES, [])
        self.language = config.get(CONF_LANGUAGE, "de")
        self.scraper = AlpenPasseScraper(language=self.language)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the website using the library."""
        if not self.selected_passes:
            return {}

        try:
            # Run the synchronous scraper in an executor
            passes_data = await self.hass.async_add_executor_job(
                self.scraper.get_all_passes
            )
            
            # Map passes by name to match our selected passes
            data = {}
            for alpine_pass in passes_data:
                # Try to match pass names
                for pass_key, pass_info in AVAILABLE_PASSES.items():
                    if pass_key in self.selected_passes:
                        # Match by name (case insensitive)
                        if (pass_info["name"].lower() in alpine_pass.name.lower() or
                            alpine_pass.name.lower() in pass_info["name"].lower()):
                            
                            data[pass_key] = {
                                "name": alpine_pass.name,
                                "status": alpine_pass.status,
                                "temperature": alpine_pass.temperature,
                                "last_update": alpine_pass.last_update,
                                "route": alpine_pass.route,
                                "notes": alpine_pass.notes,
                            }
                            break
            
            # If we didn't find matches using the main page, try individual pass lookups
            if len(data) < len(self.selected_passes):
                missing_passes = [p for p in self.selected_passes if p not in data]
                for pass_key in missing_passes:
                    pass_info = AVAILABLE_PASSES[pass_key]
                    try:
                        alpine_pass = await self.hass.async_add_executor_job(
                            self.scraper.get_pass_details, pass_info["name"]
                        )
                        if alpine_pass:
                            data[pass_key] = {
                                "name": alpine_pass.name,
                                "status": alpine_pass.status,
                                "temperature": alpine_pass.temperature,
                                "last_update": alpine_pass.last_update,
                                "route": alpine_pass.route,
                                "notes": alpine_pass.notes,
                            }
                    except Exception as err:
                        _LOGGER.warning(
                            "Failed to fetch individual pass %s: %s", 
                            pass_info["name"], 
                            err
                        )
            
            if not data:
                raise UpdateFailed("No data retrieved from any passes")
            
            _LOGGER.debug("Successfully fetched data for %d passes", len(data))
            return data
            
        except Exception as err:
            _LOGGER.error("Error fetching data: %s", err)
            raise UpdateFailed(f"Error communicating with website: {err}") from err
