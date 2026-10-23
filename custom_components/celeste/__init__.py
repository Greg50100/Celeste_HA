"""Intégration Céleste pour Home Assistant : éphémérides (calcul local ou IMCCE) et temps astronomique."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from . import meeus
from .const import DOMAIN, PLATFORMS
from .coordinator import CelesteCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

# Services repris de ha-meeus-astronomy (mêmes noms, domaine « celeste »)
SERVICE_CONVERT_TO_JD = "convert_to_julian_day"
SERVICE_CONVERT_TO_GREGORIAN = "convert_to_gregorian"

CONVERT_TO_JD_SCHEMA = vol.Schema(
    {
        vol.Required("year"): vol.Coerce(int),
        vol.Required("month"): vol.All(vol.Coerce(int), vol.Range(min=1, max=12)),
        vol.Required("day"): vol.All(vol.Coerce(int), vol.Range(min=1, max=31)),
        vol.Optional("hour", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
        vol.Optional("minute", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=59)),
        vol.Optional("second", default=0.0): vol.All(vol.Coerce(float), vol.Range(min=0, max=60)),
    }
)
CONVERT_TO_GREGORIAN_SCHEMA = vol.Schema({vol.Required("julian_day"): vol.Coerce(float)})


def convert_to_julian_day(data: dict) -> dict:
    """Date grégorienne (TU) → jour julien."""
    jd = meeus.gregorian_to_jd(data["year"], data["month"], data["day"], data["hour"], data["minute"], data["second"])
    return {
        "julian_day": round(jd, 6),
        "modified_julian_day": round(meeus.jd_to_mjd(jd), 6),
        "day_of_week": meeus.day_of_week(jd),
        "input_date": f"{data['year']}-{data['month']:02d}-{data['day']:02d} "
        f"{data['hour']:02d}:{data['minute']:02d}:{data['second']:05.2f}",
    }


def convert_to_gregorian(data: dict) -> dict:
    """Jour julien → date grégorienne (TU)."""
    y, m, d, h, mn, s = meeus.jd_to_gregorian(data["julian_day"])
    return {
        "year": y,
        "month": m,
        "day": d,
        "hour": h,
        "minute": mn,
        "second": s,
        "day_of_week": meeus.day_of_week(data["julian_day"]),
        "formatted": f"{y}-{m:02d}-{d:02d} {h:02d}:{mn:02d}:{s:05.2f}",
    }


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Enregistre les services de conversion du jour julien."""

    async def handle_convert_to_jd(call: ServiceCall) -> ServiceResponse:
        return convert_to_julian_day(call.data)

    async def handle_convert_to_gregorian(call: ServiceCall) -> ServiceResponse:
        return convert_to_gregorian(call.data)

    hass.services.async_register(
        DOMAIN, SERVICE_CONVERT_TO_JD, handle_convert_to_jd, schema=CONVERT_TO_JD_SCHEMA, supports_response=SupportsResponse.ONLY
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CONVERT_TO_GREGORIAN,
        handle_convert_to_gregorian,
        schema=CONVERT_TO_GREGORIAN_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Initialise l'intégration depuis une config entry."""
    coordinator = CelesteCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharge une config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Recharge une config entry après modification des options."""
    await hass.config_entries.async_reload(entry.entry_id)
