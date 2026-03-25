"""Utilitaires astronomiques pour Céleste — calculs de position et de visibilité.

Toutes les fonctions sont en pur Python, sans dépendance externe.
Précision suffisante pour déterminer les heures de lever/transit/coucher (±2 min).
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone


# ─── Parsing des coordonnées IMCCE ───────────────────────────────────────────

def parse_ra_deg(ra_str: str) -> float | None:
    """Convertit l'ascension droite IMCCE en degrés décimaux.

    Format IMCCE : "+HH:MM:SS.sssss" (heures, minutes, secondes)
    Retourne des degrés (0–360).
    """
    if not ra_str:
        return None
    try:
        parts = ra_str.strip().lstrip("+").split(":")
        h = float(parts[0])
        m = float(parts[1]) if len(parts) > 1 else 0.0
        s = float(parts[2]) if len(parts) > 2 else 0.0
        deg = (h + m / 60.0 + s / 3600.0) * 15.0  # heures → degrés
        return deg
    except (ValueError, IndexError, AttributeError):
        return None


def parse_dec_deg(dec_str: str) -> float | None:
    """Convertit la déclinaison IMCCE en degrés décimaux.

    Format IMCCE : "±DD:MM:SS.ssss" (degrés, minutes, arcsecondes)
    Retourne des degrés (-90 à +90).
    """
    if not dec_str:
        return None
    try:
        s = dec_str.strip()
        negative = s.startswith("-")
        parts = s.lstrip("+-").split(":")
        d = float(parts[0])
        m = float(parts[1]) if len(parts) > 1 else 0.0
        sc = float(parts[2]) if len(parts) > 2 else 0.0
        deg = d + m / 60.0 + sc / 3600.0
        return -deg if negative else deg
    except (ValueError, IndexError, AttributeError):
        return None


# ─── Temps sidéral local ─────────────────────────────────────────────────────

def compute_gmst(dt: datetime) -> float:
    """Calcule le Temps Sidéral Moyen de Greenwich (GMST) en degrés.

    Formule simplifiée (précision ~0.1° ≈ 24 sec), suffisante pour RTS.
    Référence : Astronomical Algorithms, Jean Meeus (chap. 12).
    """
    # Assurer que dt est en UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    # Jour Julien
    y, mo, d = dt.year, dt.month, dt.day
    ut = dt.hour + dt.minute / 60.0 + dt.second / 3600.0

    if mo <= 2:
        y -= 1
        mo += 12

    A = int(y / 100)
    B = 2 - A + int(A / 4)
    jd = int(365.25 * (y + 4716)) + int(30.6001 * (mo + 1)) + d + B - 1524.5 + ut / 24.0

    t = (jd - 2451545.0) / 36525.0  # siècles juliens depuis J2000.0

    # GMST en degrés
    gmst = (280.46061837
            + 360.98564736629 * (jd - 2451545.0)
            + 0.000387933 * t ** 2
            - t ** 3 / 38710000.0)
    return gmst % 360.0


def compute_lst(dt: datetime, longitude_deg: float) -> float:
    """Calcule le Temps Sidéral Local (LST) en degrés.

    longitude_deg : longitude de l'observateur en degrés (est positif).
    """
    return (compute_gmst(dt) + longitude_deg) % 360.0


# ─── Altitude d'un astre ─────────────────────────────────────────────────────

def compute_altitude(
    ra_str: str,
    dec_str: str,
    lat_deg: float,
    lon_deg: float,
    dt: datetime,
) -> float | None:
    """Calcule l'altitude d'un astre au-dessus de l'horizon local (en degrés).

    ra_str   : ascension droite au format IMCCE "+HH:MM:SS.sssss"
    dec_str  : déclinaison au format IMCCE "±DD:MM:SS.ssss"
    lat_deg  : latitude de l'observateur (degrés, nord positif)
    lon_deg  : longitude de l'observateur (degrés, est positif)
    dt       : date/heure UTC

    Retourne l'altitude en degrés (-90 à +90), ou None si les données manquent.
    Formule : sin(alt) = sin(lat)·sin(dec) + cos(lat)·cos(dec)·cos(H)
    où H est l'angle horaire = LST - RA
    """
    ra_deg = parse_ra_deg(ra_str)
    dec_deg = parse_dec_deg(dec_str)
    if ra_deg is None or dec_deg is None:
        return None

    lst = compute_lst(dt, lon_deg)
    hour_angle = math.radians(lst - ra_deg)

    lat = math.radians(lat_deg)
    dec = math.radians(dec_deg)

    sin_alt = (math.sin(lat) * math.sin(dec)
               + math.cos(lat) * math.cos(dec) * math.cos(hour_angle))
    # Clamp pour éviter les erreurs d'arrondi
    sin_alt = max(-1.0, min(1.0, sin_alt))
    return math.degrees(math.asin(sin_alt))


# ─── Calcul Lever / Transit / Coucher ────────────────────────────────────────

def find_rts(
    hourly_data: list[dict],
    lat_deg: float,
    lon_deg: float,
) -> dict:
    """Détecte les heures de lever, transit et coucher depuis des éphémérides horaires.

    hourly_data : liste de dicts {"ra": str, "dec": str, "date": str, ...}
                  issus de l'API IMCCE avec step=1h, sur 25h.
    lat_deg     : latitude observateur
    lon_deg     : longitude observateur

    Retourne : {
        "rise"    : str ISO ou None,   # UTC de franchissement ascendant de 0°
        "transit" : str ISO ou None,   # UTC d'altitude maximale
        "set"     : str ISO ou None,   # UTC de franchissement descendant de 0°
        "max_alt" : float ou None,     # altitude maximale (degrés)
    }
    """
    altitudes: list[tuple[datetime, float]] = []

    for point in hourly_data:
        ra_str = point.get("ra") or point.get("RA")
        dec_str = point.get("dec") or point.get("DEC")
        date_str = point.get("date") or point.get("Date")
        if not ra_str or not dec_str or not date_str:
            continue
        try:
            # Parser la date ISO de l'API IMCCE : "2026-03-25T12:00:00.000"
            dt_str = date_str[:19]  # Tronquer les millisecondes
            dt = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

        alt = compute_altitude(ra_str, dec_str, lat_deg, lon_deg, dt)
        if alt is not None:
            altitudes.append((dt, alt))

    if len(altitudes) < 3:
        return {"rise": None, "transit": None, "set": None, "max_alt": None}

    rise_dt: datetime | None = None
    set_dt: datetime | None = None
    max_alt: float = altitudes[0][1]
    transit_dt: datetime = altitudes[0][0]

    for i in range(1, len(altitudes)):
        prev_dt, prev_alt = altitudes[i - 1]
        curr_dt, curr_alt = altitudes[i]

        # Mise à jour du transit (altitude maximale)
        if curr_alt > max_alt:
            max_alt = curr_alt
            transit_dt = curr_dt

        # Détection lever : passage de négatif à positif
        if prev_alt < 0 and curr_alt >= 0 and rise_dt is None:
            # Interpolation linéaire pour affiner
            frac = (-prev_alt) / (curr_alt - prev_alt) if curr_alt != prev_alt else 0
            delta = (curr_dt - prev_dt) * frac
            rise_dt = prev_dt + delta

        # Détection coucher : passage de positif à négatif
        if prev_alt >= 0 and curr_alt < 0 and rise_dt is not None:
            frac = prev_alt / (prev_alt - curr_alt) if prev_alt != curr_alt else 0
            delta = (curr_dt - prev_dt) * frac
            set_dt = prev_dt + delta

    def fmt(dt: datetime | None) -> str | None:
        if dt is None:
            return None
        return dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    return {
        "rise": fmt(rise_dt),
        "transit": fmt(transit_dt) if rise_dt else None,
        "set": fmt(set_dt),
        "max_alt": round(max_alt, 1),
    }


# ─── Critère de visibilité combiné ───────────────────────────────────────────

def is_observable(
    elongation: float | None,
    magnitude: float | None,
    elongation_threshold: float = 15.0,
    magnitude_threshold: float | None = None,
) -> bool | None:
    """Détermine si un astre est potentiellement observable.

    Critères :
    1. Élongation solaire > elongation_threshold (astre hors éblouissement solaire)
    2. Si magnitude_threshold renseigné : magnitude < magnitude_threshold
       (astre suffisamment brillant)

    Retourne True, False ou None (données manquantes).
    """
    if elongation is None:
        return None

    try:
        elong_ok = float(elongation) > elongation_threshold
    except (ValueError, TypeError):
        return None

    if not elong_ok:
        return False

    # Critère magnitude (optionnel)
    if magnitude_threshold is not None and magnitude is not None:
        try:
            mag_ok = float(magnitude) < float(magnitude_threshold)
        except (ValueError, TypeError):
            mag_ok = True  # On ne pénalise pas si la valeur est inutilisable
        return elong_ok and mag_ok

    return elong_ok
