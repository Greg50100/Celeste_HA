"""Calcul local des éphémérides avec Astronomy Engine (Don Cross, licence MIT).

C'est le même moteur que le site Ganymede (https://greg50100.github.io/personnal-site/).
Aucune connexion réseau : les positions sont calculées sur la machine Home Assistant.
Fonctions synchrones, à appeler dans un exécuteur (hass.async_add_executor_job).
"""
from __future__ import annotations

from datetime import datetime, timezone

import astronomy as ae

from . import meeus
from .constellations import CONSTELLATIONS_FR

# Noms acceptés (ceux de la liste des planètes prédéfinies)
LOCAL_BODIES = {
    "Sun": ae.Body.Sun,
    "Moon": ae.Body.Moon,
    "Mercury": ae.Body.Mercury,
    "Venus": ae.Body.Venus,
    "Mars": ae.Body.Mars,
    "Jupiter": ae.Body.Jupiter,
    "Saturn": ae.Body.Saturn,
    "Uranus": ae.Body.Uranus,
    "Neptune": ae.Body.Neptune,
    "Pluto": ae.Body.Pluto,
}

MOON_PHASES = [
    (7, "Nouvelle lune"),
    (83, "Premier croissant"),
    (97, "Premier quartier"),
    (173, "Gibbeuse croissante"),
    (187, "Pleine lune"),
    (263, "Gibbeuse décroissante"),
    (277, "Dernier quartier"),
    (353, "Dernier croissant"),
    (360, "Nouvelle lune"),
]
SYNODIC_MONTH = 29.530588853


def _time(dt: datetime) -> ae.Time:
    dt = dt.astimezone(timezone.utc)
    return ae.Time.Make(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)


def _iso(t: ae.Time | None) -> str | None:
    return t.Utc().replace(tzinfo=timezone.utc).isoformat(timespec="seconds") if t else None


def _format_ra(hours: float) -> str:
    """Ascension droite au format IMCCE « +HH:MM:SS.sss »."""
    total = round(hours * 3600, 3) % 86400
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"+{int(h):02d}:{int(m):02d}:{s:06.3f}"


def _format_dec(deg: float) -> str:
    """Déclinaison au format IMCCE « ±DD:MM:SS.ss »."""
    sign = "-" if deg < 0 else "+"
    total = round(abs(deg) * 3600, 2)
    d, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{sign}{int(d):02d}:{int(m):02d}:{s:05.2f}"


def moon_phase_name(angle: float) -> str:
    """Nom de la phase à partir de l'angle de phase écliptique (0 = nouvelle lune, 180 = pleine lune)."""
    return next((name for limit, name in MOON_PHASES if angle < limit), "Nouvelle lune")


def compute_body(name: str, latitude: float, longitude: float, altitude: float, when: datetime) -> dict:
    """Éphémérides d'un astre du système solaire pour l'observateur, à l'instant `when`.

    Les clés reprennent celles de la source IMCCE (magnitude, elongation, distance, phase, ra, dec,
    rise, transit, set, max_alt) pour que les entités fonctionnent avec les deux sources.
    """
    body = LOCAL_BODIES[name]
    observer = ae.Observer(latitude, longitude, altitude)
    time = _time(when)

    eq = ae.Equator(body, time, observer, True, True)
    hor = ae.Horizon(time, observer, eq.ra, eq.dec, ae.Refraction.Normal)
    eq_j2000 = ae.Equator(body, time, observer, False, True)
    constellation = ae.Constellation(eq_j2000.ra, eq_j2000.dec)

    # Lever, passage au méridien et coucher du jour UTC en cours
    day_start = _time(when.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0))
    rise = ae.SearchRiseSet(body, observer, ae.Direction.Rise, day_start, 1.0)
    set_ = ae.SearchRiseSet(body, observer, ae.Direction.Set, day_start, 1.0)
    culmination = ae.SearchHourAngle(body, observer, 0.0, day_start, +1)
    transit = culmination.time if culmination.time.ut < day_start.ut + 1.0 else None

    result: dict = {
        "object_name": name,
        "object_type": "planet",
        "date": _iso(time),
        "ra": _format_ra(eq_j2000.ra),
        "dec": _format_dec(eq_j2000.dec),
        "distance": round(eq.dist, 6),
        "altitude": round(hor.altitude, 2),
        "azimuth": round(hor.azimuth, 2),
        "constellation": CONSTELLATIONS_FR.get(constellation.symbol, constellation.name),
        "rise": _iso(rise),
        "transit": _iso(transit),
        "set": _iso(set_),
        "max_alt": round(culmination.hor.altitude, 1) if transit else None,
    }

    if body == ae.Body.Sun:
        result["elongation"] = 0.0
        result["magnitude"] = -26.74
    else:
        illum = ae.Illumination(body, time)
        result["magnitude"] = round(illum.mag, 2)
        result["phase"] = round(illum.phase_angle, 2)
        result["illumination"] = round(illum.phase_fraction * 100, 1)
        result["elongation"] = round(ae.AngleFromSun(body, time), 2)

    if body == ae.Body.Moon:
        angle = ae.MoonPhase(time)
        result["moon_phase"] = moon_phase_name(angle)
        result["moon_age"] = round(angle / 360 * SYNODIC_MONTH, 1)
        result["distance_km"] = round(eq.dist * ae.KM_PER_AU)

    return result


def compute_time(longitude: float, when: datetime) -> dict:
    """Grandeurs de temps astronomique (reprises de ha-meeus-astronomy, plus temps sidéral et temps solaire)."""
    utc = when.astimezone(timezone.utc)
    jd = meeus.gregorian_to_jd(utc.year, utc.month, utc.day, utc.hour, utc.minute, utc.second + utc.microsecond / 1e6)
    time = _time(utc)
    gast = ae.SiderealTime(time)  # heures
    local_sidereal = (gast + longitude / 15.0) % 24.0
    # Temps solaire vrai : angle horaire du Soleil + 12 h ; temps solaire moyen : TU + longitude
    observer = ae.Observer(0.0, longitude, 0.0)
    apparent = (ae.HourAngle(ae.Body.Sun, time, observer) + 12.0) % 24.0
    mean = (utc.hour + utc.minute / 60 + utc.second / 3600 + longitude / 15.0) % 24.0
    eot = (apparent - mean) * 60.0
    if eot > 720:
        eot -= 1440
    elif eot < -720:
        eot += 1440
    return {
        "julian_day": round(jd, 6),
        "modified_julian_day": round(meeus.jd_to_mjd(jd), 6),
        "days_since_j2000": round(jd - meeus.J2000, 6),
        "day_of_week": meeus.day_of_week(jd),
        "day_of_year": meeus.day_of_year(utc.year, utc.month, utc.day),
        "local_sidereal_time": _hours_to_hms(local_sidereal),
        "greenwich_sidereal_time": _hours_to_hms(gast),
        "equation_of_time": round(eot, 2),
        "date": utc.isoformat(timespec="seconds"),
    }


def _hours_to_hms(hours: float) -> str:
    total = int(round(hours * 3600)) % 86400
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


