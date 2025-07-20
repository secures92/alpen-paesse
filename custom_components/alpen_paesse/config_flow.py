"""Config flow for Alpen-Paesse integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import AVAILABLE_PASSES, CONF_SELECTED_PASSES, CONF_LANGUAGE, DOMAIN, LANGUAGES

_LOGGER = logging.getLogger(__name__)

# Import cv for multi_select at module level
from homeassistant.helpers import config_validation as cv

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    
    if not data.get(CONF_SELECTED_PASSES):
        raise ValueError("At least one pass must be selected")
    
    # Return info that you want to store in the config entry.
    return {"title": f"Alpen-Paesse ({len(data[CONF_SELECTED_PASSES])} passes)"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Alpen-Paesse."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                
                await self.async_set_unique_id("alpen_paesse_config")
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(title=info["title"], data=user_input)
            except ValueError:
                errors["base"] = "no_passes_selected"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        data_schema = vol.Schema({
            vol.Required(CONF_LANGUAGE, default="de"): vol.In(LANGUAGES),
            vol.Required(CONF_SELECTED_PASSES, default=[]): 
                vol.All(cv.multi_select({
                    key: pass_info["name"] 
                    for key, pass_info in AVAILABLE_PASSES.items()
                }), vol.Length(min=1))
        })

        return self.async_show_form(
            step_id="user", 
            data_schema=data_schema, 
            errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration of the integration."""
        config_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_update_reload_and_abort(
                    config_entry, data=user_input, reason="reconfigure_successful"
                )
            except ValueError:
                return self.async_abort(reason="no_passes_selected")
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                return self.async_abort(reason="unknown")

        data_schema = vol.Schema({
            vol.Required(
                CONF_LANGUAGE, 
                default=config_entry.data.get(CONF_LANGUAGE, "de")
            ): vol.In(LANGUAGES),
            vol.Required(
                CONF_SELECTED_PASSES, 
                default=config_entry.data.get(CONF_SELECTED_PASSES, [])
            ): vol.All(cv.multi_select({
                key: pass_info["name"] 
                for key, pass_info in AVAILABLE_PASSES.items()
            }), vol.Length(min=1))
        })

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=data_schema
        )
