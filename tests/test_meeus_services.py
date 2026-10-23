"""Calendrier de Meeus et services de conversion (repris de ha-meeus-astronomy)."""
from __future__ import annotations

import pytest

from custom_components.celeste import CONVERT_TO_GREGORIAN_SCHEMA, CONVERT_TO_JD_SCHEMA, convert_to_gregorian, convert_to_julian_day
from custom_components.celeste import meeus


class TestMeeusCalendar:
    """Exemples du chapitre 7 d'« Astronomical Algorithms »."""

    def test_spoutnik_jd(self):
        """Exemple 7.a : 4,81 octobre 1957 → JJ 2 436 116,31."""
        assert meeus.gregorian_to_jd(1957, 10, 4, 19, 26, 24) == pytest.approx(2436116.31, abs=1e-6)

    def test_j2000(self):
        assert meeus.gregorian_to_jd(2000, 1, 1, 12) == 2451545.0

    def test_inverse(self):
        assert meeus.jd_to_gregorian(2436116.31)[:5] == (1957, 10, 4, 19, 26)

    def test_day_of_week(self):
        """Exemple 7.e : le 30 juin 1954 était un mercredi."""
        assert meeus.day_of_week(meeus.gregorian_to_jd(1954, 6, 30)) == "mercredi"

    @pytest.mark.parametrize(("date", "expected"), [((1978, 11, 14), 318), ((1988, 4, 22), 113)])
    def test_day_of_year(self, date, expected):
        """Exemples 7.f et 7.g."""
        assert meeus.day_of_year(*date) == expected

    def test_mjd(self):
        assert meeus.jd_to_mjd(2400000.5) == 0


class TestServices:
    """Services celeste.convert_to_julian_day et celeste.convert_to_gregorian."""

    def test_convert_to_julian_day(self):
        data = CONVERT_TO_JD_SCHEMA({"year": 2026, "month": 10, "day": 23})
        result = convert_to_julian_day(data)
        assert result["julian_day"] == 2461336.5
        assert result["day_of_week"] == "vendredi"
        assert result["input_date"] == "2026-10-23 00:00:00.00"

    def test_convert_to_gregorian(self):
        result = convert_to_gregorian(CONVERT_TO_GREGORIAN_SCHEMA({"julian_day": 2451545.0}))
        assert (result["year"], result["month"], result["day"], result["hour"]) == (2000, 1, 1, 12)
        assert result["formatted"].startswith("2000-01-01 12:00")

    def test_schema_rejects_invalid_month(self):
        import voluptuous as vol

        with pytest.raises(vol.Invalid):
            CONVERT_TO_JD_SCHEMA({"year": 2026, "month": 13, "day": 1})
