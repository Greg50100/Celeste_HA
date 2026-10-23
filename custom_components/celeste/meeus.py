"""Calendrier astronomique d'après Jean Meeus, « Astronomical Algorithms » (2e éd.), chapitre 7.

Repris de l'intégration ha-meeus-astronomy, fusionnée dans Céleste.
Fonctions pures, sans dépendance externe.
"""
from __future__ import annotations

J2000 = 2451545.0
DAYS_FR = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"]


def is_leap_year(year: int) -> bool:
    """Année bissextile du calendrier grégorien."""
    return (year % 4 == 0 and year % 100 != 0) or year % 400 == 0


def gregorian_to_jd(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: float = 0.0) -> float:
    """Date grégorienne → jour julien (formule 7.1)."""
    if month <= 2:
        year -= 1
        month += 12
    a = int(year / 100)
    b = 2 - a + int(a / 4)
    day_fraction = day + (hour + minute / 60 + second / 3600) / 24.0
    return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day_fraction + b - 1524.5


def jd_to_gregorian(jd: float) -> tuple[int, int, int, int, int, float]:
    """Jour julien → (année, mois, jour, heure, minute, seconde), calendrier grégorien après 1582."""
    jd_adjusted = jd + 0.5
    z = int(jd_adjusted)
    f = jd_adjusted - z
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - int(alpha / 4)
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    day_with_fraction = b - d - int(30.6001 * e) + f
    day = int(day_with_fraction)
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    total_seconds = (day_with_fraction - day) * 86400
    hour = int(total_seconds // 3600)
    total_seconds %= 3600
    minute = int(total_seconds // 60)
    second = round(total_seconds % 60, 4)
    return year, month, day, hour, minute, second


def jd_to_mjd(jd: float) -> float:
    """Jour julien modifié : MJD = JD − 2 400 000,5."""
    return jd - 2400000.5


def day_of_week(jd: float) -> str:
    """Jour de la semaine (en français) : (JD + 1,5) modulo 7."""
    return DAYS_FR[int(jd + 1.5) % 7]


def day_of_year(year: int, month: int, day: int) -> int:
    """Rang du jour dans l'année."""
    k = 1 if is_leap_year(year) else 2
    return int((275 * month) / 9) - k * int((month + 9) / 12) + day - 30
