"""Sensors numériques pour Céleste – IMCCE Éphémérides."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ENABLE_SENSORS,
    CONF_MAGNITUDE_THRESHOLD,
    CONF_OBJECT_NAME,
    DEFAULT_ENABLE_SENSORS,
    DOMAIN,
    SENSORS_AVAILABLE,
)
from .coordinator import CelesteCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure les sensors numériques depuis une config entry."""
    coordinator: CelesteCoordinator = hass.data[DOMAIN][entry.entry_id]
    object_name = entry.data[CONF_OBJECT_NAME]

    # Vérifier si les sensors sont activés
    enable_sensors = entry.options.get(CONF_ENABLE_SENSORS, DEFAULT_ENABLE_SENSORS)
    if not enable_sensors:
        return

    # Créer un sensor pour chaque type de donnée disponible
    entities = [
        CelesteNumericSensor(coordinator, entry, object_name, sensor_type)
        for sensor_type in SENSORS_AVAILABLE.keys()
    ]

    async_add_entities(entities)


class CelesteNumericSensor(CoordinatorEntity, SensorEntity):
    """Sensor numérique pour une donnée éphéméride (magnitude, distance, etc.)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CelesteCoordinator,
        entry: ConfigEntry,
        object_name: str,
        sensor_type: str,
    ) -> None:
        """Initialise le sensor."""
        super().__init__(coordinator)
        self._object_name = object_name
        self._entry = entry
        self._sensor_type = sensor_type
        self._sensor_config = SENSORS_AVAILABLE[sensor_type]

        # Unique ID et nom
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"
        self._attr_name = self._sensor_config["name"]
        self._attr_icon = self._sensor_config["icon"]
        self._attr_native_unit_of_measurement = self._sensor_config["unit"]
        self._attr_state_class = SensorStateClass(
            self._sensor_config["state_class"]
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Regroupe les entités sous un appareil Céleste dans HA."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"Céleste – {self._object_name}",
            manufacturer="IMCCE (Observatoire de Paris)",
            model="Miriade Éphémérides",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://ssp.imcce.fr/webservices/miriade/",
        )

    @property
    def available(self) -> bool:
        """Disponible si le coordinator a des données valides et contient la clé."""
        if not super().available or not self.coordinator.data:
            return False
        return self._sensor_type in self.coordinator.data

    @property
    def native_value(self) -> Any:
        """Retourne la valeur du sensor depuis les données du coordinator."""
        if not self.coordinator.data:
            return None

        value = self.coordinator.data.get(self._sensor_type)

        # Log un avertissement si la donnée manque
        if value is None:
            _LOGGER.debug(
                "Donnée '%s' manquante pour %s",
                self._sensor_type,
                self._object_name,
            )

        return value
