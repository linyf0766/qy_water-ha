"""Config flow for qy_water integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_OID,
    CONF_UPDATE_TIME,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN
)

async def async_get_flow(
    hass: HomeAssistant,
    discovery_info: dict[str, Any] | None = None
) -> ConfigFlow:
    """Return the config flow."""
    return ConfigFlow()

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""
    
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_OID])
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title=f"清远水务 {user_input[CONF_OID]}",
                data=user_input
            )
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_OID): str,
                vol.Optional(
                    CONF_UPDATE_TIME,
                    default=DEFAULT_UPDATE_INTERVAL
                ): int
            }),
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """Get the options flow."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow."""
    
    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_UPDATE_TIME,
                    default=self.config_entry.options.get(
                        CONF_UPDATE_TIME,
                        self.config_entry.data.get(CONF_UPDATE_TIME, DEFAULT_UPDATE_INTERVAL)
                    )
                ): int
            })
        )