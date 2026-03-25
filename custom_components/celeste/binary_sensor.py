"""Capteur de visibilité pour Céleste – IMCCE Éphémérides."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .astro_utils import is_observable
from .const import (
    CONF_MAGNITUDE_THRESHOLD,
    CONF_OBJECT_NAME,
    DOMAIN,
    ELONGATION_VISIBILITY_THRESHOLD,
)
from .coordinator import CelesteCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure le capteur de visibilité depuis une config entry."""
    coordinator: CelesteCoordinator = hass.data[DOMAIN][entry.entry_id]
    object_name = entry.data[CONF_OBJECT_NAME]

    async_add_entities([CelesteVisibilitySensor(coordinator, entry, object_name)])


class CelesteVisibilitySensor(CoordinatorEntity, BinarySensorEntity):
    """Capteur binaire de visibilité d'un objet céleste.

    État principal : True = potentiellement visible (hors éblouissement solaire).
    Critères       :
      1. Élongation solaire > seuil (défaut 15°)
      2. Si seuil_magnitude configuré : magnitude < seuil_magnitude
    Attributs      : toutes les données éphémérides + lever/transit/coucher.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CelesteCoordinator,
        entry: ConfigEntry,
        object_name: str,
    ) -> None:
        """Initialise le capteur."""
        super().__init__(coordinator)
        self._object_name = object_name
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_visibility"
        self._attr_name = f"Visibilité {object_name}"

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

    def _is_data_valid(self) -> bool:
        """Vérifie que les données du coordinator contiennent les clés critiques.

        Clés critiques : elongation (obligatoire pour is_on).
        """
        if not self.coordinator.data or not isinstance(self.coordinator.data, dict):
            return False
        # elongation est critique pour is_on
        return "elongation" in self.coordinator.data

    @property
    def available(self) -> bool:
        """Disponible si le coordinator a des données valides et complètes."""
        return super().available and self._is_data_valid()

    @property
    def is_on(self) -> bool | None:
        """True si l'astre est potentiellement observable.

        Critère principal : élongation solaire > seuil_elongation (défaut 15°).
        Critère optionnel : magnitude < seuil_magnitude (si configuré).
        """
        if not self.coordinator.data or not isinstance(self.coordinator.data, dict):
            return None

        elongation = self.coordinator.data.get("elongation")
        magnitude = self.coordinator.data.get("magnitude")

        # Logging d'alerte si les données critiques manquent
        if elongation is None:
            _LOGGER.warning(
                "Donnée 'elongation' manquante pour %s", self._object_name
            )
            return None

        # Seuil magnitude depuis les options (peut être None = désactivé)
        mag_threshold = self._entry.options.get(CONF_MAGNITUDE_THRESHOLD)

        return is_observable(
            elongation=elongation,
            magnitude=magnitude,
            elongation_threshold=ELONGATION_VISIBILITY_THRESHOLD,
            magnitude_threshold=mag_threshold,
        )

    @property
    def icon(self) -> str:
        """Icône dynamique : œil ouvert si visible, fermé sinon."""
        if self.is_on is True:
            return "mdi:eye"
        if self.is_on is False:
            return "mdi:eye-off"
        return "mdi:telescope"
