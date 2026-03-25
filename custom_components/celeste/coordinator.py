"""Coordinateur de données pour Céleste – IMCCE Éphémérides."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_ALTITUDE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_OBJECT_NAME,
    DEFAULT_ALTITUDE,
    DOMAIN,
    MIRIADE_API_URL,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class CelesteCoordinator(DataUpdateCoordinator):
    """Coordonne les mises à jour depuis l'API IMCCE Miriade."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialise le coordinateur."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.entry = entry
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict:
        """Récupère les données depuis l'API IMCCE."""
        object_name = self.entry.data[CONF_OBJECT_NAME]
        latitude = self.entry.data.get(CONF_LATITUDE, self.hass.config.latitude)
        longitude = self.entry.data.get(CONF_LONGITUDE, self.hass.config.longitude)
        altitude = self.entry.data.get(CONF_ALTITUDE, DEFAULT_ALTITUDE)

        now = datetime.utcnow()
        epoch = now.strftime("%Y-%m-%dT%H:%M:%S")

        params = {
            "-name": object_name,
            "-type": "object",
            "-ep": epoch,
            "-step": "1d",
            "-nbd": "1",
            "-observer": f"{longitude},{latitude},{altitude}",
            "-output": "--jul --ram --rv --mag --elo --pha --con",
            "-mime": "json",
        }

        try:
            async with self.session.get(
                MIRIADE_API_URL, params=params, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    raise UpdateFailed(
                        f"Erreur API IMCCE : statut HTTP {response.status}"
                    )
                data = await response.json(content_type=None)

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Erreur de connexion à l'API IMCCE : {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Erreur inattendue : {err}") from err

        return self._parse_response(data)

    def _parse_response(self, data: dict) -> dict:
        """Parse la réponse JSON de l'API IMCCE Miriade."""
        result = {}

        try:
            # La réponse Miriade contient un champ "data" avec les éphémérides
            ephemeris = data.get("data", [])
            if not ephemeris:
                _LOGGER.warning("Aucune donnée éphéméride reçue de l'API IMCCE")
                return result

            # Prendre le premier (et unique) enregistrement
            ep = ephemeris[0]

            # Ascension droite et déclinaison
            result["ra"] = ep.get("RA", None)
            result["dec"] = ep.get("DEC", None)

            # Distance (en UA)
            result["distance"] = ep.get("Delta", None)

            # Magnitude visuelle
            result["magnitude"] = ep.get("V", None)

            # Élongation (angle par rapport au Soleil)
            result["elongation"] = ep.get("Elo", None)

            # Phase
            result["phase"] = ep.get("Phase", None)

            # Constellation
            result["constellation"] = ep.get("Const", None)

            # Vitesse radiale (km/s)
            result["radial_velocity"] = ep.get("dDelta", None)

            # Date julienne
            result["julian_date"] = ep.get("jd", None)

            _LOGGER.debug("Données IMCCE parsées : %s", result)

        except (KeyError, IndexError, TypeError) as err:
            _LOGGER.error("Erreur lors du parsing de la réponse IMCCE : %s", err)

        return result
