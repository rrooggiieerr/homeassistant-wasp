"""
Custom integration for Wasp Sensor

For more details about this integration, please refer to
https://github.com/rrooggiieerr/homeassistant-wasp
"""

import logging
from typing import Dict, List

from homeassistant import config as conf_util
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.core_config import Config
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.loader import async_get_integration
import voluptuous as vol
from voluptuous.schema_builder import ALLOW_EXTRA, PREVENT_EXTRA

from .const import (
    BINARY_SENSOR,
    CONF_BOX_INV_SENSORS,
    CONF_BOX_SENSORS,
    CONF_NAME,
    CONF_TIMEOUT,
    CONF_WASP_INV_SENSORS,
    CONF_WASP_SENSORS,
    DEFAULT_WASP_TIMEOUT,
    DOMAIN,
    SERVICE_RELOAD,
    STARTUP_MESSAGE,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
]

ENTRY_SCHEMA = vol.Schema(
    {
        CONF_NAME: str,
        vol.Optional(CONF_WASP_SENSORS, default=[]): cv.entity_ids,
        vol.Optional(CONF_WASP_INV_SENSORS, default=[]): cv.entity_ids,
        vol.Optional(CONF_BOX_SENSORS, default=[]): cv.entity_ids,
        vol.Optional(CONF_BOX_INV_SENSORS, default=[]): cv.entity_ids,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_WASP_TIMEOUT): vol.Coerce(int),
    },
    extra=PREVENT_EXTRA,
)

CONFIG_SCHEMA = vol.Schema({DOMAIN: [ENTRY_SCHEMA]}, extra=ALLOW_EXTRA)


class EntityRegistry:
    """Handle Registering Entities for later Destruction"""

    def __init__(self) -> None:
        self.registered_entities: List[BinarySensorEntity] = []

    async def register_entities(self, entities: List[BinarySensorEntity]) -> None:
        """Perform Entity Registration"""
        for entity in entities:
            self.registered_entities.append(entity)

    async def shutdown(self):
        """Destroy all Entities"""
        for entity in self.registered_entities:
            await entity.async_remove()

        self.registered_entities = []


async def async_setup(hass: HomeAssistant, hass_config: Config) -> bool:
    """Component setup."""
    if hass.data.get(DOMAIN) is None:
        _LOGGER.info(STARTUP_MESSAGE)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN] = hass_config[DOMAIN]

    registry = EntityRegistry()

    await start_it_up(hass, hass_config, registry)

    async def reload_scripts_handler(_) -> None:
        """Handle reload service calls."""
        _LOGGER.debug("reloading")

        await registry.shutdown()

        try:
            unprocessed_conf = await conf_util.async_hass_config_yaml(hass)
        except HomeAssistantError as err:
            _LOGGER.error(err)
            return

        conf = await conf_util.async_process_component_config(
            hass, unprocessed_conf, await async_get_integration(hass, DOMAIN)
        )

        if conf is None:
            return

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN] = conf[DOMAIN]
        await start_it_up(hass, conf, registry)

    hass.services.async_register(DOMAIN, SERVICE_RELOAD, reload_scripts_handler)

    return True


async def start_it_up(
    hass: HomeAssistant, hass_config: Config, registry: EntityRegistry
):
    """Handle Startup Tasks"""

    config = {"registrar": registry.register_entities, "entities": hass.data[DOMAIN]}

    hass.async_create_task(
        discovery.async_load_platform(
            hass,
            BINARY_SENSOR,
            DOMAIN,
            config,
            hass_config,
        )
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Wasp in a Box from a config entry."""

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("Configuration options updated, reloading Wasp in a Box integration")
    hass.config_entries.async_schedule_reload(entry.entry_id)(entry.entry_id)
