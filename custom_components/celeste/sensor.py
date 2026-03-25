"""Capteurs pour Céleste – IMCCE Éphémérides."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_OBJECT_NAME,
    DOMAIN,
)
from .coordinator import CelesteCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure les capteurs depuis une config entry."""
    coordinator: CelesteCoordinator = hass.data[DOMAIN][entry.entry_id]
    object_name = entry.data[CONF_OBJECT_NAME]

    async_add_entities([CelesteMainSensor(coordinator, entry, object_name)])


class CelesteMainSensor(CoordinatorEntity, SensorEntity):
    """Capteur principal pour les éphémérides d'un objet céleste."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True
    _attr_icon = "mdi:telescope"

    def __init__(
        self,
        coordinator: CelesteCoordinator,
        entry: ConfigEntry,
        object_name: str,
    ) -> None:
        """Initialise le capteur."""
        super().__init__(coordinator)
        self._object_name = object_name
        self._attr_unique_id = f"{entry.entry_id}_ephemerides"
        self._attr_name = f"Éphémérides {object_name}"

    @property
    def native_value(self) -> float | None:
        """Retourne la magnitude visuelle comme valeur principale."""
        if self.coordinator.data:
            return self.coordinator.data.get("magnitude")
        return None

    @property
    def native_unit_of_measurement(self) -> str:
        """Unité : magnitude (sans dimension)."""
        return "mag"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Retourne tous les attributs des éphémérides."""
        if not self.coordinator.data:
            return {}

        data = self.coordinator.data
        attrs: dict[str, Any] = {}

        if data.get("ra") is not None:
            attrs["ascension_droite"] = data["ra"]
        if data.get("dec") is not None:
            attrs["declinaison"] = data["dec"]
        if data.get("distance") is not None:
            attrs["distance_ua"] = data["distance"]
        if data.get("elongation") is not None:
            attrs["elongation_deg"] = data["elongation"]
        if data.get("phase") is not None:
            attrs["phase_deg"] = data["phase"]
        if data.get("constellation") is not None:
            attrs["constellation"] = data["constellation"]
        if data.get("radial_velocity") is not None:
            attrs["vitesse_radiale_km_s"] = data["radial_velocity"]
        if data.get("julian_date") is not None:
            attrs["date_julienne"] = data["julian_date"]

        attrs["objet"] = self._object_name

        return attrs
