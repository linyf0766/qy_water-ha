"""Sensor platform for qy_water integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER

SENSOR_TYPES = {
    "water_last_month_day": {
        "name": "上月月份",
        "icon": "mdi:calendar-month",
        "unit": None,
        "device_class": None,
        "state_class": None
    },
    "water_last_month_total_usage": {
        "name": "上月用水量",
        "device_class": SensorDeviceClass.WATER,
        "state_class": SensorStateClass.TOTAL,
        "unit": UnitOfVolume.CUBIC_METERS,
        "icon": "mdi:water"
    },
    "water_last_month_total_cost": {
        "name": "上月金额",
        "device_class": SensorDeviceClass.MONETARY,
        "state_class": SensorStateClass.TOTAL,
        "unit": "CNY",
        "icon": "mdi:cash"
    },
    "water_arrears": {
        "name": "总欠费",
        "device_class": SensorDeviceClass.MONETARY,
        "state_class": SensorStateClass.TOTAL,
        "unit": "CNY",
        "icon": "mdi:cash-minus"
    },
    "water_balance": {
        "name": "账户余额",
        "device_class": SensorDeviceClass.MONETARY,
        "state_class": SensorStateClass.TOTAL,
        "unit": "CNY",
        "icon": "mdi:cash"
    }
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    entities = [
        QYWaterSensor(coordinator, entry, key, config)
        for key, config in SENSOR_TYPES.items()
    ]
    
    async_add_entities(entities)

class QYWaterSensor(CoordinatorEntity, SensorEntity):
    """Representation of a sensor."""
    
    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        key: str,
        config: dict
    ):
        """Initialize sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"{entry.title} {config['name']}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data["oid"])},
        }
        
        # 设置所有属性
        self._attr_native_unit_of_measurement = config["unit"]
        self._attr_device_class = config["device_class"]
        self._attr_state_class = config["state_class"]
        if "icon" in config:
            self._attr_icon = config["icon"]

    @property
    def native_value(self):
        """Return sensor value."""
        data = self.coordinator.data or {}
        value = data.get(self._key)
        
        if value is None:
            if self._key == "water_last_month_day":
                return "未知"
            return 0
        
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available 
            and self.coordinator.data 
            and self._key in self.coordinator.data
        )