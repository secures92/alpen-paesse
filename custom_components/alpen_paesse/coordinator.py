"""DataUpdateCoordinator for Alpen-Paesse."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import AVAILABLE_PASSES, CONF_SELECTED_PASSES, CONF_LANGUAGE, DOMAIN, UPDATE_INTERVAL
from .alpen_paesse_lib import AlpenPaesseFetcher

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
        language_path = f"/{self.language}"
        self.fetcher = AlpenPaesseFetcher(language_path=language_path)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the website using the library."""
        if not self.selected_passes:
            return {}

        try:
            # Run the synchronous fetcher in an executor
            passes_data = await self.hass.async_add_executor_job(
                self.fetcher.fetch_passes_data
            )
            
            if not passes_data:
                raise UpdateFailed("No data retrieved from website")
            
            # Map passes by name to match our selected passes
            data = {}
            for pass_data in passes_data:
                pass_name = pass_data.get("name", "")
                
                # Try to match pass names with our configured passes
                for pass_key, pass_info in AVAILABLE_PASSES.items():
                    if pass_key in self.selected_passes:
                        # Match by name (case insensitive)
                        if (pass_info["name"].lower() in pass_name.lower() or
                            pass_name.lower() in pass_info["name"].lower()):
                            
                            data[pass_key] = {
                                "name": pass_name,
                                "status": pass_data.get("current_status_description", "Unknown"),
                                "temperature": pass_data.get("temperature", ""),
                                "update": pass_data.get("status_last_update", ""),
                                "link": pass_data.get("detail_url", ""),
                            }
                            break
            
            if not data:
                _LOGGER.warning(
                    "No matching passes found. Selected: %s, Found passes: %s",
                    self.selected_passes,
                    [p.get("name") for p in passes_data[:5]]
                )
                raise UpdateFailed("No matching passes found in data")
            
            _LOGGER.debug("Successfully fetched data for %d passes", len(data))
            return data
            
        except Exception as err:
            _LOGGER.error("Error fetching data: %s", err)
            raise UpdateFailed(f"Error communicating with website: {err}") from err
