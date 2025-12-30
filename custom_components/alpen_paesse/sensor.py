"""Platform for sensor integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import AVAILABLE_PASSES, DOMAIN
from .coordinator import AlpenPasseCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    coordinator: AlpenPasseCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    for pass_key in coordinator.selected_passes:
        if pass_key in AVAILABLE_PASSES:
            pass_info = AVAILABLE_PASSES[pass_key]
            
            # Create four sensors for each pass: status, update, temperature, link
            entities.extend([
                AlpenPassStatusSensor(coordinator, pass_key, pass_info),
                AlpenPassUpdateSensor(coordinator, pass_key, pass_info),
                AlpenPassTemperatureSensor(coordinator, pass_key, pass_info),
                AlpenPassLinkSensor(coordinator, pass_key, pass_info),
            ])
    
    async_add_entities(entities, update_before_add=True)


class AlpenPassSensorBase(CoordinatorEntity[AlpenPasseCoordinator], SensorEntity):
    """Base class for Alpen-Paesse sensors."""
    
    def __init__(
        self, 
        coordinator: AlpenPasseCoordinator, 
        pass_key: str, 
        pass_info: dict[str, Any]
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.pass_key = pass_key
        self.pass_info = pass_info
        
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.pass_key)},
            name=self.pass_info["name"],
            manufacturer="alpen-paesse.ch",
            model="Swiss Alpine Pass",
            suggested_area="Alps",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success 
            and self.pass_key in self.coordinator.data
        )


class AlpenPassStatusSensor(AlpenPassSensorBase):
    """Representation of an Alpine Pass Status Sensor."""
    
    def __init__(
        self, 
        coordinator: AlpenPasseCoordinator, 
        pass_key: str, 
        pass_info: dict[str, Any]
    ) -> None:
        """Initialize the status sensor."""
        super().__init__(coordinator, pass_key, pass_info)
        self._attr_name = f"{pass_info['name']} Status"
        self._attr_unique_id = f"{pass_key}_status"
        self._attr_icon = "mdi:road"

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        if self.pass_key not in self.coordinator.data:
            return None
        return self.coordinator.data[self.pass_key].get("status")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "route": self.pass_info["route"],
            "pass_key": self.pass_key,
        }


class AlpenPassUpdateSensor(AlpenPassSensorBase):
    """Representation of an Alpine Pass Last Update Sensor."""
    
    def __init__(
        self, 
        coordinator: AlpenPasseCoordinator, 
        pass_key: str, 
        pass_info: dict[str, Any]
    ) -> None:
        """Initialize the last update sensor."""
        super().__init__(coordinator, pass_key, pass_info)
        self._attr_name = f"{pass_info['name']} Update"
        self._attr_unique_id = f"{pass_key}_update"
        self._attr_icon = "mdi:clock-check-outline"

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        if self.pass_key not in self.coordinator.data:
            return None
        return self.coordinator.data[self.pass_key].get("update")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "route": self.pass_info["route"],
            "pass_key": self.pass_key,
        }


class AlpenPassTemperatureSensor(AlpenPassSensorBase):
    """Representation of an Alpine Pass Temperature Sensor."""
    
    def __init__(
        self, 
        coordinator: AlpenPasseCoordinator, 
        pass_key: str, 
        pass_info: dict[str, Any]
    ) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, pass_key, pass_info)
        self._attr_name = f"{pass_info['name']} Temperature"
        self._attr_unique_id = f"{pass_key}_temperature"
        self._attr_icon = "mdi:thermometer"

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        if self.pass_key not in self.coordinator.data:
            return None
        # Return temperature as-is (it's already a string from the website)
        return self.coordinator.data[self.pass_key].get("temperature")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "route": self.pass_info["route"],
            "pass_key": self.pass_key,
        }


class AlpenPassLinkSensor(AlpenPassSensorBase):
    """Representation of an Alpine Pass Detail Link Sensor."""
    
    def __init__(
        self, 
        coordinator: AlpenPasseCoordinator, 
        pass_key: str, 
        pass_info: dict[str, Any]
    ) -> None:
        """Initialize the link sensor."""
        super().__init__(coordinator, pass_key, pass_info)
        self._attr_name = f"{pass_info['name']} Link"
        self._attr_unique_id = f"{pass_key}_link"
        self._attr_icon = "mdi:link-variant"

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        if self.pass_key not in self.coordinator.data:
            return None
        return self.coordinator.data[self.pass_key].get("link")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "route": self.pass_info["route"],
            "pass_key": self.pass_key,
        }
