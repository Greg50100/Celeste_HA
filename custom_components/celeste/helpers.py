"""Fonctions partagées par les entités Céleste."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import CONF_OBJECT_NAME, CONF_OBJECT_TYPE, CONF_SOURCE, DOMAIN, SOURCE_IMCCE, SOURCE_LOCAL, SOURCE_TIME


# Noms français des astres prédéfinis (les noms IMCCE sont en anglais)
DISPLAY_NAMES = {
    "Sun": "Soleil",
    "Moon": "Lune",
    "Mercury": "Mercure",
    "Venus": "Vénus",
    "Saturn": "Saturne",
}


def display_name(object_name: str) -> str:
    """Nom affiché d'un astre."""
    return DISPLAY_NAMES.get(object_name, object_name)


def get_source(entry: ConfigEntry) -> str:
    """Source des calculs d'une entrée : option, sinon donnée initiale, sinon IMCCE (entrées v0.1)."""
    source = entry.options.get(CONF_SOURCE) or entry.data.get(CONF_SOURCE)
    if source == SOURCE_TIME:
        return SOURCE_TIME
    if source == SOURCE_LOCAL:
        # Le calcul local ne couvre que le Soleil, la Lune et les planètes
        from .local_engine import LOCAL_BODIES  # import tardif : astronomy n'est chargé qu'au besoin

        name = entry.data.get(CONF_OBJECT_NAME)
        if entry.data.get(CONF_OBJECT_TYPE, "planet") == "planet" and name in LOCAL_BODIES:
            return SOURCE_LOCAL
    return SOURCE_IMCCE


def build_device_info(entry: ConfigEntry, object_name: str) -> DeviceInfo:
    """Regroupe les entités d'une entrée sous un appareil « service »."""
    source = get_source(entry)
    if source == SOURCE_TIME:
        return DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Céleste – {display_name(object_name)}",
            manufacturer="Céleste",
            model="Temps astronomique (Jean Meeus)",
            entry_type=DeviceEntryType.SERVICE,
        )
    if source == SOURCE_LOCAL:
        return DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Céleste – {display_name(object_name)}",
            manufacturer="Astronomy Engine",
            model="Calcul local",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://github.com/cosinekitty/astronomy",
        )
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"Céleste – {display_name(object_name)}",
        manufacturer="IMCCE (Observatoire de Paris)",
        model="Miriade Éphémérides",
        entry_type=DeviceEntryType.SERVICE,
        configuration_url="https://ssp.imcce.fr/webservices/miriade/",
    )
