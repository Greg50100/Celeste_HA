"""Capteurs de Céleste : éphémérides d'un astre ou temps astronomique."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ALL_SENSORS,
    CONF_ENABLE_SENSORS,
    CONF_OBJECT_NAME,
    DEFAULT_ENABLE_SENSORS,
    DOMAIN,
    LOCAL_SENSORS,
    MOON_SENSORS,
    SENSORS_AVAILABLE,
    SOURCE_LOCAL,
    SOURCE_TIME,
    TIME_SENSORS,
)
from .coordinator import CelesteCoordinator
from .helpers import build_device_info, get_source

_LOGGER = logging.getLogger(__name__)


def sensor_types_for(source: str, object_name: str) -> list[str]:
    """Types de capteurs à créer pour une entrée, selon la source et l'astre."""
    if source == SOURCE_TIME:
        return list(TIME_SENSORS)
    if source != SOURCE_LOCAL:
        return list(SENSORS_AVAILABLE)
    # Calcul local : pas de vitesse radiale ; Soleil sans phase ; Lune avec distance en km
    types = ["magnitude", "elongation"]
    if object_name != "Moon":
        types.append("distance")
    if object_name != "Sun":
        types += ["phase", "illumination"]
    types += [t for t in LOCAL_SENSORS if t != "illumination"]
    if object_name == "Moon":
        types += list(MOON_SENSORS)
    return types


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure les capteurs depuis une config entry."""
    coordinator: CelesteCoordinator = hass.data[DOMAIN][entry.entry_id]
    object_name = entry.data[CONF_OBJECT_NAME]
    source = get_source(entry)

    # Les capteurs d'éphémérides peuvent être désactivés (le capteur de visibilité reste)
    if source != SOURCE_TIME and not entry.options.get(CONF_ENABLE_SENSORS, DEFAULT_ENABLE_SENSORS):
        return

    async_add_entities(
        CelesteNumericSensor(coordinator, entry, object_name, sensor_type)
        for sensor_type in sensor_types_for(source, object_name)
    )


class CelesteNumericSensor(CoordinatorEntity, SensorEntity):
    """Capteur d'une donnée de Céleste (magnitude, hauteur, lever, jour julien…)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CelesteCoordinator,
        entry: ConfigEntry,
        object_name: str,
        sensor_type: str,
    ) -> None:
        """Initialise le capteur."""
        super().__init__(coordinator)
        self._object_name = object_name
        self._entry = entry
        self._sensor_type = sensor_type
        self._sensor_config = ALL_SENSORS[sensor_type]

        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"
        self._attr_name = self._sensor_config["name"]
        self._attr_icon = self._sensor_config["icon"]
        self._attr_native_unit_of_measurement = self._sensor_config["unit"]
        if self._sensor_config["state_class"]:
            self._attr_state_class = SensorStateClass(self._sensor_config["state_class"])
        if self._sensor_config["device_class"]:
            self._attr_device_class = SensorDeviceClass(self._sensor_config["device_class"])

    @property
    def device_info(self) -> DeviceInfo:
        """Regroupe les entités sous un appareil Céleste dans HA."""
        return build_device_info(self._entry, self._object_name)

    @property
    def available(self) -> bool:
        """Disponible si le coordinator a des données valides et contient la clé."""
        if not super().available or not self.coordinator.data:
            return False
        return self._sensor_type in self.coordinator.data

    @property
    def native_value(self) -> Any:
        """Retourne la valeur du capteur depuis les données du coordinator."""
        if not self.coordinator.data:
            return None

        value = self.coordinator.data.get(self._sensor_type)
        if value is None:
            _LOGGER.debug("Donnée '%s' manquante pour %s", self._sensor_type, self._object_name)
            return None

        # Les horaires sont stockés en ISO 8601 (UTC) : HA attend un datetime avec fuseau
        if self._sensor_config["device_class"] == "timestamp" and isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return value
