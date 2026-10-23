"""Config flow pour Céleste : astre (calcul local ou IMCCE) ou temps astronomique."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .helpers import display_name
from .const import (
    CONF_ALTITUDE,
    CONF_ENABLE_SENSORS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_MAGNITUDE_THRESHOLD,
    CONF_OBJECT_NAME,
    CONF_OBJECT_TYPE,
    CONF_SOURCE,
    DEFAULT_ALTITUDE,
    DEFAULT_ENABLE_SENSORS,
    DOMAIN,
    MIRIADE_API_URL,
    OBJECT_TYPES,
    PREDEFINED_PLANETS,
    SOURCE_IMCCE,
    SOURCE_LOCAL,
    SOURCE_TIME,
    SOURCES,
    TIME_OBJECT_NAME,
)

_LOGGER = logging.getLogger(__name__)

# Choix principal : planète prédéfinie ou saisie libre
CHOICE_PREDEFINED = "predefined"
CHOICE_CUSTOM = "custom"
CHOICE_TIME = "time"


async def _validate_object_with_api(
    hass: HomeAssistant, name: str, obj_type: str
) -> dict | None:
    """Valide qu'un objet existe en appelant l'API IMCCE.

    Retourne le dict "sso" si trouvé, None sinon.
    """
    session = async_get_clientsession(hass)
    params = {
        "-name": name,
        "-type": obj_type,
        "-ep": "now",
        "-step": "1d",
        "-nbd": "1",
        "-observer": "0,0,0",
        "-output": "--mag",
        "-mime": "json",
    }
    try:
        async with session.get(
            MIRIADE_API_URL,
            params=params,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            if response.status != 200:
                return None
            data = await response.json(content_type=None)
            if isinstance(data, dict) and "data" in data and data["data"]:
                return data.get("sso", {})
            return None
    except Exception:  # noqa: BLE001
        return None


class CelesteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestion du flux de configuration pour Céleste."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise le flow."""
        self._user_data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Étape 1 : choix planète prédéfinie ou saisie personnalisée."""
        errors: dict[str, str] = {}

        if user_input is not None:
            choice = user_input.get("choice", CHOICE_PREDEFINED)

            if choice == CHOICE_CUSTOM:
                # Aller vers l'étape de saisie libre
                return await self.async_step_custom()

            if choice == CHOICE_TIME:
                # Temps astronomique (jour julien, temps sidéral…) : seule la longitude compte
                self._user_data[CONF_OBJECT_NAME] = TIME_OBJECT_NAME
                self._user_data[CONF_OBJECT_TYPE] = "time"
                self._user_data[CONF_SOURCE] = SOURCE_TIME
                return await self.async_step_location()

            # Planète prédéfinie : calcul local par défaut (modifiable dans les options)
            object_name = user_input.get(CONF_OBJECT_NAME, "Mars")
            self._user_data[CONF_OBJECT_NAME] = object_name
            self._user_data[CONF_OBJECT_TYPE] = "planet"
            self._user_data[CONF_SOURCE] = SOURCE_LOCAL
            return await self.async_step_location()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_OBJECT_NAME, default="Mars"
                ): vol.In(PREDEFINED_PLANETS),
                vol.Required("choice", default=CHOICE_PREDEFINED): vol.In(
                    {
                        CHOICE_PREDEFINED: "Soleil, Lune ou planète (calcul local)",
                        CHOICE_CUSTOM: "Autre objet : astéroïde, comète… (IMCCE, en ligne)",
                        CHOICE_TIME: "Temps astronomique (jour julien, temps sidéral)",
                    }
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_custom(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Étape 2a : saisie libre d'un objet céleste + type."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_OBJECT_NAME]
            obj_type = user_input[CONF_OBJECT_TYPE]

            # Valider l'objet auprès de l'API IMCCE
            sso = await _validate_object_with_api(self.hass, name, obj_type)
            if sso is None:
                errors["base"] = "object_not_found"
            else:
                resolved_name = sso.get("name", name)
                self._user_data[CONF_OBJECT_NAME] = resolved_name
                self._user_data[CONF_OBJECT_TYPE] = obj_type
                self._user_data[CONF_SOURCE] = SOURCE_IMCCE
                return await self.async_step_location()

        schema = vol.Schema(
            {
                vol.Required(CONF_OBJECT_NAME): str,
                vol.Required(
                    CONF_OBJECT_TYPE, default="asteroid"
                ): vol.In(OBJECT_TYPES),
            }
        )

        return self.async_show_form(
            step_id="custom",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_location(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Étape 3 : localisation de l'observateur."""
        if user_input is not None:
            self._user_data.update(user_input)

            object_name = self._user_data[CONF_OBJECT_NAME]

            # Vérification d'unicité : une seule entrée par objet (et une seule pour le temps)
            unique = "time" if self._user_data.get(CONF_SOURCE) == SOURCE_TIME else object_name.lower()
            await self.async_set_unique_id(f"{DOMAIN}_{unique}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Céleste – {display_name(object_name)}",
                data=self._user_data,
            )

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_LATITUDE,
                    default=self.hass.config.latitude,
                ): cv.latitude,
                vol.Optional(
                    CONF_LONGITUDE,
                    default=self.hass.config.longitude,
                ): cv.longitude,
                vol.Optional(
                    CONF_ALTITUDE,
                    default=DEFAULT_ALTITUDE,
                ): vol.Coerce(int),
            }
        )

        return self.async_show_form(
            step_id="location",
            data_schema=schema,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> CelesteOptionsFlow:
        """Retourne le flux d'options."""
        return CelesteOptionsFlow()


class CelesteOptionsFlow(config_entries.OptionsFlow):
    """Options : lieu d'observation, source des calculs, seuil de magnitude, capteurs numériques.

    `self.config_entry` est fourni par Home Assistant (l'affecter soi-même est obsolète depuis 2024.11).
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Étape principale des options : localisation et sensors numériques."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}
        fields: dict = {
            vol.Optional(
                CONF_LATITUDE,
                default=current.get(CONF_LATITUDE, self.hass.config.latitude),
            ): cv.latitude,
            vol.Optional(
                CONF_LONGITUDE,
                default=current.get(CONF_LONGITUDE, self.hass.config.longitude),
            ): cv.longitude,
            vol.Optional(
                CONF_ALTITUDE,
                default=current.get(CONF_ALTITUDE, DEFAULT_ALTITUDE),
            ): vol.Coerce(int),
        }
        if current.get(CONF_SOURCE) != SOURCE_TIME:
            if current.get(CONF_OBJECT_TYPE, "planet") == "planet" and current.get(CONF_OBJECT_NAME) in PREDEFINED_PLANETS:
                fields[vol.Optional(CONF_SOURCE, default=current.get(CONF_SOURCE, SOURCE_IMCCE))] = vol.In(SOURCES)
            fields[vol.Optional(CONF_MAGNITUDE_THRESHOLD, default=current.get(CONF_MAGNITUDE_THRESHOLD))] = vol.Any(None, vol.Coerce(float))
            fields[vol.Optional(CONF_ENABLE_SENSORS, default=current.get(CONF_ENABLE_SENSORS, DEFAULT_ENABLE_SENSORS))] = cv.boolean
        schema = vol.Schema(fields)
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
