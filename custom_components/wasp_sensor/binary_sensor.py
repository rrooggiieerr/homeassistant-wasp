"""Binary sensor platform for Wasp Sensor."""

import asyncio
from datetime import timedelta
from functools import partial
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_START
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_BOX_INV_SENSORS,
    CONF_BOX_SENSORS,
    CONF_NAME,
    CONF_SENSOR_CHANGE_DELAY,
    CONF_TIMEOUT,
    CONF_WASP_INV_SENSORS,
    CONF_WASP_SENSORS,
    DEFAULT_SENSOR_CHANGE_DELAY,
    DOMAIN,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_platform(hass, _, async_add_entities, discovery_info=None):
    """Setup binary_sensor platform."""
    entities = []
    for config in discovery_info["entities"]:
        entity_description = BinarySensorEntityDescription(
            key="online",
            device_class=BinarySensorDeviceClass.OCCUPANCY,
            name=config[CONF_NAME],
        )
        entities.append(
            WaspBinarySensor(
                entity_description, f"{DOMAIN}_{config[CONF_NAME]}", hass, config
            )
        )

    async_add_entities(entities)
    await discovery_info["registrar"](entities)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Wasp in a Box sensor."""
    entities = []

    entity_description = BinarySensorEntityDescription(
        key=None,
        device_class=BinarySensorDeviceClass.OCCUPANCY,
        name=config_entry.data[CONF_NAME],
    )
    entities.append(
        WaspBinarySensor(
            entity_description,
            config_entry.entry_id,
            hass,
            config_entry.options,
        )
    )

    async_add_entities(entities)


class WaspBinarySensor(BinarySensorEntity, RestoreEntity):
    """Wasp binary_sensor class."""

    def __init__(
        self,
        entity_description: BinarySensorEntityDescription,
        unique_id: str,
        hass,
        config,
    ):
        self.hass = hass
        self._config = config

        self._attr_unique_id = unique_id
        self.entity_description = entity_description

        _LOGGER.debug("%s: startup %s", self.entity_description.name, self._config)

        self._wasp_in_box = False
        self._box_closed = False
        self._wasp_seen = False

    async def async_added_to_hass(self):
        """Handle added to Hass."""
        await super().async_added_to_hass()

        if state := await self.async_get_last_state():
            _LOGGER.debug("%s: restoring state %s", self.entity_description.name, state)
            self._wasp_in_box = state.attributes.get("wasp_in_box", False)
            self._box_closed = state.attributes.get("box_closed", False)
            self._wasp_seen = state.attributes.get("wasp_seen", False)

        # wait until full HASS Startup before starting event listeners
        if self.hass.is_running:
            await self._startup()
        else:
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, self._startup)

    async def _startup(self, _=None):
        await self._evaluate_wasp_sensors()
        await self._evaluate_box_sensors()

        # Wasp Sensor State Changes
        sensors = self._config.get(CONF_WASP_SENSORS)
        if sensors not in (None, []):
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    sensors,
                    partial(self._wasp_sensor_change_handler, expected_state="on"),
                )
            )

        # Wasp Inverted Sensor State Changes
        sensors = self._config.get(CONF_WASP_INV_SENSORS)
        if sensors not in (None, []):
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    sensors,
                    partial(self._wasp_sensor_change_handler, expected_state="off"),
                )
            )

        # Box Sensor State Changes
        sensors = self._config.get(CONF_BOX_SENSORS)
        if sensors not in (None, []):
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    sensors,
                    self._box_sensor_change_handler,
                )
            )

        # Box Inverted Sensor State Changes
        sensors = self._config.get(CONF_BOX_INV_SENSORS)
        if sensors not in (None, []):
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    sensors,
                    self._box_sensor_change_handler,
                )
            )

    @callback
    async def _box_sensor_change_handler(self, event: Event):
        this_entity_id = event.data["entity_id"]
        new_state = event.data["new_state"].state

        _LOGGER.debug(
            "%s: %s is now %s",
            self.entity_description.name,
            this_entity_id,
            new_state,
        )

        await self._evaluate_box_sensors()
        self._wasp_in_box = False

        await self.async_update_ha_state()

        if not self._box_closed or not self._wasp_seen:
            return

        _LOGGER.debug(
            "%s: box is closed and wasp is seen, waiting %s seconds",
            self.entity_description.name,
            self._config[CONF_TIMEOUT],
        )

        timeout = self._config[CONF_TIMEOUT]
        if isinstance(timeout, dict):
            timeout = timedelta(**timeout).total_seconds()
        await asyncio.sleep(timeout)

        if self._box_closed and self._wasp_seen:
            _LOGGER.debug(
                "%s: box is still closed and wasp is still seen after %s seconds",
                self.entity_description.name,
                self._config[CONF_TIMEOUT],
            )

            self._wasp_in_box = True
            await self.async_update_ha_state()
            return

    async def _evaluate_box_sensors(self):
        sensors = self._config.get(CONF_BOX_SENSORS)
        if sensors not in (None, []):
            for sensor in sensors:
                state = self.hass.states.get(sensor).state
                if state == "on":
                    self._box_closed = False
                    self._wasp_in_box = False
                    return

        sensors = self._config.get(CONF_BOX_INV_SENSORS)
        if sensors not in (None, []):
            for sensor in sensors:
                state = self.hass.states.get(sensor).state
                if state == "off":
                    self._box_closed = False
                    self._wasp_in_box = False
                    return

        self._box_closed = True
        return

    @callback
    async def _wasp_sensor_change_handler(
        self, event: Event, expected_state: str = "on"
    ):
        this_entity_id = event.data["entity_id"]
        new_state = event.data["new_state"].state

        sensor_change_delay = self._config.get(
            CONF_SENSOR_CHANGE_DELAY, DEFAULT_SENSOR_CHANGE_DELAY
        )
        if isinstance(sensor_change_delay, dict):
            sensor_change_delay = timedelta(**sensor_change_delay).total_seconds()

        _LOGGER.debug(
            "%s: waiting for %s, currently %s, for %s seconds",
            self.entity_description.name,
            this_entity_id,
            new_state,
            sensor_change_delay,
        )

        # Wait; some sensors send 'on' right before 'off'
        await asyncio.sleep(sensor_change_delay)

        this_state = self.hass.states.get(this_entity_id).state

        _LOGGER.debug(
            "%s: %s is %s after %s seconds",
            self.entity_description.name,
            this_entity_id,
            this_state,
            sensor_change_delay,
        )

        if this_state == expected_state:
            if self._box_closed:
                self._wasp_in_box = True

        await self._evaluate_wasp_sensors()
        await self.async_update_ha_state()

    async def _evaluate_wasp_sensors(self):
        sensors = self._config.get(CONF_WASP_SENSORS)
        if sensors not in (None, []):
            for this_wasp_sensor in sensors:
                this_state = self.hass.states.get(this_wasp_sensor).state
                if this_state == "on":
                    self._wasp_seen = True
                    return

        sensors = self._config.get(CONF_WASP_INV_SENSORS)
        if sensors not in (None, []):
            for this_wasp_sensor in sensors:
                this_state = self.hass.states.get(this_wasp_sensor).state
                if this_state == "off":
                    self._wasp_seen = True
                    return

        self._wasp_seen = False
        return

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            # "attribution": f"{DOMAIN} {BINARY_SENSOR}",
            # "id": str(self.unique_id),
            # "integration": DOMAIN,
            "wasp_in_box": self._wasp_in_box,
            "box_closed": self._box_closed,
            "wasp_seen": self._wasp_seen,
        }

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        return self._wasp_in_box
