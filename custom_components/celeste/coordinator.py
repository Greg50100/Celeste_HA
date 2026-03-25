"""Coordinateur de données pour Céleste – IMCCE Éphémérides."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .astro_utils import find_rts
from .const import (
    CONF_ALTITUDE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_OBJECT_NAME,
    CONF_OBJECT_TYPE,
    DEFAULT_ALTITUDE,
    DOMAIN,
    MIRIADE_API_URL,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

# Timeout pour les appels API IMCCE (en secondes)
API_TIMEOUT = 30


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
        self._last_valid_data: dict | None = None

    async def _async_update_data(self) -> dict:
        """Récupère les données depuis l'API IMCCE (éphéméride J + positions horaires RTS)."""
        object_name = self.entry.data[CONF_OBJECT_NAME]
        obj_type = self.entry.data.get(CONF_OBJECT_TYPE, "planet")
        latitude = self.entry.data.get(CONF_LATITUDE, self.hass.config.latitude)
        longitude = self.entry.data.get(CONF_LONGITUDE, self.hass.config.longitude)
        altitude = self.entry.data.get(CONF_ALTITUDE, DEFAULT_ALTITUDE)

        epoch = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        # ── Appel 1 : éphéméride du jour (1 point, step=1d) ──────────────────
        params_daily = {
            "-name": object_name,
            "-type": obj_type,
            "-ep": epoch,
            "-step": "1d",
            "-nbd": "1",
            "-observer": f"{longitude},{latitude},{altitude}",
            "-output": "--ram --rv --mag --elo --pha",
            "-mime": "json",
        }

        try:
            daily_data = await self._fetch_api(params_daily, object_name)
        except asyncio.TimeoutError as err:
            _LOGGER.warning(
                "Timeout API IMCCE après %ds pour %s", API_TIMEOUT, object_name
            )
            if self._last_valid_data:
                return self._last_valid_data
            raise UpdateFailed(
                f"Timeout API IMCCE après {API_TIMEOUT}s pour {object_name}"
            ) from err
        except aiohttp.ClientError as err:
            _LOGGER.warning("Erreur réseau IMCCE pour %s : %s", object_name, err)
            if self._last_valid_data:
                return self._last_valid_data
            raise UpdateFailed(
                f"Erreur de connexion à l'API IMCCE : {err}"
            ) from err
        except UpdateFailed:
            if self._last_valid_data:
                return self._last_valid_data
            raise

        result = self._parse_response(daily_data)

        # ── Appel 2 : 25 positions horaires pour lever/transit/coucher ────────
        # Débute à minuit UTC du jour courant
        midnight = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        epoch_midnight = midnight.strftime("%Y-%m-%dT%H:%M:%S")

        params_hourly = {
            "-name": object_name,
            "-type": obj_type,
            "-ep": epoch_midnight,
            "-step": "1h",
            "-nbd": "25",
            "-observer": f"{longitude},{latitude},{altitude}",
            "-output": "--ram",
            "-mime": "json",
        }

        try:
            hourly_data = await self._fetch_api(params_hourly, object_name)
            hourly_points = hourly_data.get("data", [])
            rts = find_rts(hourly_points, latitude, longitude)
            result.update(rts)
            _LOGGER.debug(
                "RTS calculé pour %s : lever=%s transit=%s coucher=%s alt_max=%.1f°",
                object_name,
                rts.get("rise"),
                rts.get("transit"),
                rts.get("set"),
                rts.get("max_alt") or 0,
            )
        except Exception as err:  # noqa: BLE001
            # L'échec du second appel ne doit pas bloquer les données du jour
            _LOGGER.warning(
                "Calcul RTS indisponible pour %s : %s", object_name, err
            )
            result.setdefault("rise", None)
            result.setdefault("transit", None)
            result.setdefault("set", None)
            result.setdefault("max_alt", None)

        if result:
            self._last_valid_data = result
        return result

    async def _fetch_api(self, params: dict, object_name: str) -> dict:
        """Effectue un appel GET vers l'API IMCCE et retourne le JSON parsé.

        Lève UpdateFailed, asyncio.TimeoutError ou aiohttp.ClientError selon l'erreur.
        """
        try:
            async with self.session.get(
                MIRIADE_API_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    _LOGGER.error(
                        "API IMCCE HTTP %s pour %s : %s",
                        response.status,
                        object_name,
                        text[:200],
                    )
                    raise UpdateFailed(
                        f"Erreur API IMCCE : statut HTTP {response.status}"
                    )
                try:
                    data = await response.json(content_type=None)
                except (ValueError, TypeError) as err:
                    raise UpdateFailed(
                        f"Réponse JSON invalide de l'API IMCCE : {err}"
                    ) from err
        except (asyncio.TimeoutError, aiohttp.ClientError):
            raise
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Erreur inattendue : {err}") from err

        if not isinstance(data, dict) or "data" not in data:
            _LOGGER.error("Structure JSON inattendue de l'API IMCCE : %s", type(data))
            raise UpdateFailed("Structure JSON inattendue de l'API IMCCE")

        return data

    def _parse_response(self, data: dict) -> dict:
        """Parse la réponse JSON de l'API IMCCE Miriade.

        Structure réelle de la réponse (validée le 2026-03-25) :
        {
          "sso":      { "num", "name", "type", "parameters" },
          "coosys":   { "epoch", "equinox", "system" },
          "ephemeris":{ "time_scale", ... },
          "data":     [ { "Date", "IAU_code", "RA", "DEC", "Dobs",
                          "VMag", "Phase", "Elong.", "dRAcosDEC", "dDEC",
                          "RV", "RVc", "BERV", "RVs" } ],
          "datacol":  [...],
          "unit":     [...]
        }
        """
        try:
            ephemeris = data.get("data", [])
            if not ephemeris or not isinstance(ephemeris, list):
                _LOGGER.warning("Aucune donnée éphéméride reçue de l'API IMCCE")
                return {}

            ep = ephemeris[0]

            result = {
                "ra": ep.get("RA"),
                "dec": ep.get("DEC"),
                "distance": ep.get("Dobs"),
                "magnitude": ep.get("VMag"),
                "elongation": ep.get("Elong."),
                "phase": ep.get("Phase"),
                "radial_velocity": ep.get("RV"),
                "dra_cos_dec": ep.get("dRAcosDEC"),
                "ddec": ep.get("dDEC"),
                "date": ep.get("Date"),
            }

            # Métadonnées objet depuis "sso"
            sso = data.get("sso", {})
            result["object_name"] = sso.get("name")
            result["object_type"] = sso.get("type")
            result["object_num"] = sso.get("num")

            # ── Validation des clés critiques ──────────────────────────────
            critical_keys = ["elongation", "magnitude", "date"]
            missing_keys = [k for k in critical_keys if result.get(k) is None]
            if missing_keys:
                _LOGGER.warning(
                    "Clés critiques manquantes dans les données IMCCE pour %s : %s",
                    result.get("object_name"),
                    missing_keys,
                )

            _LOGGER.debug("Données IMCCE parsées pour %s : %s", result.get("object_name"), result)
            return result

        except (KeyError, IndexError, TypeError) as err:
            _LOGGER.error("Erreur lors du parsing de la réponse IMCCE : %s", err)
            return {}
