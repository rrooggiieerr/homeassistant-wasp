"""Config flow for the Wasp in a Box integration."""

from __future__ import annotations

import logging
from typing import Any, Final

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    DurationSelector,
    DurationSelectorConfig,
    EntitySelector,
    EntitySelectorConfig,
    TextSelector,
)
import voluptuous as vol

from .const import (
    CONF_BOX_INV_SENSORS,
    CONF_BOX_SENSORS,
    CONF_NAME,
    CONF_SENSOR_CHANGE_DELAY,
    CONF_TIMEOUT,
    CONF_WASP_INV_SENSORS,
    CONF_WASP_SENSORS,
    DEFAULT_SENSOR_CHANGE_DELAY,
    DEFAULT_WASP_TIMEOUT,
    DOMAIN,
)

_LOGGER: Final = logging.getLogger(__name__)


class WaspConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Wasp in a Box."""

    VERSION = 1

    SCHEMA = vol.Schema(
        {
            vol.Required(CONF_NAME): TextSelector(),
            vol.Optional(CONF_WASP_SENSORS, default=[]): EntitySelector(
                EntitySelectorConfig(multiple=True)
            ),
            vol.Optional(CONF_WASP_INV_SENSORS, default=[]): EntitySelector(
                EntitySelectorConfig(multiple=True)
            ),
            vol.Optional(CONF_BOX_SENSORS, default=[]): EntitySelector(
                EntitySelectorConfig(multiple=True)
            ),
            vol.Optional(CONF_BOX_INV_SENSORS, default=[]): EntitySelector(
                EntitySelectorConfig(multiple=True)
            ),
            vol.Optional(
                CONF_TIMEOUT,
                default={
                    "seconds": DEFAULT_WASP_TIMEOUT,
                },
            ): DurationSelector(
                DurationSelectorConfig(enable_day=False, enable_millisecond=True)
            ),
            vol.Optional(
                CONF_SENSOR_CHANGE_DELAY,
                default={
                    "seconds": DEFAULT_SENSOR_CHANGE_DELAY,
                },
            ): DurationSelector(
                DurationSelectorConfig(enable_day=False, enable_millisecond=True)
            ),
        }
    )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.SCHEMA(user_input)

            title = user_input.get(CONF_NAME)
            data = {CONF_NAME: title}
            options = {
                CONF_WASP_SENSORS: user_input.get(CONF_WASP_SENSORS),
                CONF_WASP_INV_SENSORS: user_input.get(CONF_WASP_INV_SENSORS),
                CONF_BOX_SENSORS: user_input.get(CONF_BOX_SENSORS),
                CONF_BOX_INV_SENSORS: user_input.get(CONF_BOX_INV_SENSORS),
                CONF_TIMEOUT: user_input.get(CONF_TIMEOUT),
                CONF_SENSOR_CHANGE_DELAY: user_input.get(CONF_SENSOR_CHANGE_DELAY),
            }

            if not errors:
                return self.async_create_entry(title=title, data=data, options=options)

        if user_input is not None:
            data_schema = self.add_suggested_values_to_schema(self.SCHEMA, user_input)
        else:
            data_schema = self.SCHEMA

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return WaspOptionsFlowHandler()


class WaspOptionsFlowHandler(OptionsFlow):
    """Handle the options flow for Wasp in a Box."""

    OPTIONS_SCHEMA = vol.Schema(
        {
            vol.Optional(CONF_WASP_SENSORS, default=[]): EntitySelector(
                EntitySelectorConfig(multiple=True)
            ),
            vol.Optional(CONF_WASP_INV_SENSORS, default=[]): EntitySelector(
                EntitySelectorConfig(multiple=True)
            ),
            vol.Optional(CONF_BOX_SENSORS, default=[]): EntitySelector(
                EntitySelectorConfig(multiple=True)
            ),
            vol.Optional(CONF_BOX_INV_SENSORS, default=[]): EntitySelector(
                EntitySelectorConfig(multiple=True)
            ),
            vol.Optional(
                CONF_TIMEOUT, default={"seconds": DEFAULT_WASP_TIMEOUT}
            ): DurationSelector(
                DurationSelectorConfig(enable_day=False, enable_millisecond=True)
            ),
            vol.Optional(
                CONF_SENSOR_CHANGE_DELAY,
                default={"seconds": DEFAULT_SENSOR_CHANGE_DELAY},
            ): DurationSelector(
                DurationSelectorConfig(enable_day=False, enable_millisecond=True)
            ),
        }
    )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.OPTIONS_SCHEMA(user_input)

            if not errors:
                return self.async_create_entry(title="", data=user_input)

        if user_input is not None:
            data_schema = self.add_suggested_values_to_schema(
                self.OPTIONS_SCHEMA, user_input
            )
        else:
            data_schema = self.add_suggested_values_to_schema(
                self.OPTIONS_SCHEMA, self.config_entry.options
            )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )
