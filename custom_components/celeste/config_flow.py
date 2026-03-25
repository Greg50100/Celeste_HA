"""Config flow pour Céleste – IMCCE Éphémérides."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_ALTITUDE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_OBJECT_NAME,
    DEFAULT_ALTITUDE,
    DOMAIN,
    PREDEFINED_PLANETS,
)

_LOGGER = logging.getLogger(__name__)


def _build_schema(hass: HomeAssistant, user_input: dict | None = None) -> vol.Schema:
    """Construit le schéma de configuration."""
    defaults = user_input or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_OBJECT_NAME,
                default=defaults.get(CONF_OBJECT_NAME, "Mars"),
            ): vol.In(PREDEFINED_PLANETS + ["Autre"]),
            vol.Optional(
                CONF_LATITUDE,
                default=defaults.get(CONF_LATITUDE, hass.config.latitude),
            ): cv.latitude,
            vol.Optional(
                CONF_LONGITUDE,
                default=defaults.get(CONF_LONGITUDE, hass.config.longitude),
            ): cv.longitude,
            vol.Optional(
                CONF_ALTITUDE,
                default=defaults.get(CONF_ALTITUDE, DEFAULT_ALTITUDE),
            ): vol.Coerce(int),
        }
    )


class CelesteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestion du flux de configuration pour IMCCE Éphémérides."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape initiale : saisie du nom de l'objet et de la localisation."""
        errors: dict[str, str] = {}

        if user_input is not None:
            object_name = user_input[CONF_OBJECT_NAME]

            # Vérification d'unicité : un seul capteur par objet
            await self.async_set_unique_id(f"{DOMAIN}_{object_name.lower()}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Éphémérides – {object_name}",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(self.hass),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> CelesteOptionsFlow:
        """Retourne le flux d'options."""
        return CelesteOptionsFlow(config_entry)


class CelesteOptionsFlow(config_entries.OptionsFlow):
    """Gestion des options de l'intégration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialise le flux d'options."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape principale des options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(self.hass, current),
        )
