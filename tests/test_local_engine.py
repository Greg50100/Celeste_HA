"""Calcul local (Astronomy Engine) : mêmes résultats que le site Ganymede."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from custom_components.celeste import local_engine

CHERBOURG = (49.6337, -1.6222, 10)
INSTANT = datetime(2026, 10, 23, 4, 27, 13, tzinfo=timezone.utc)


class TestLocalBodies:
    def test_sun_day(self):
        sun = local_engine.compute_body("Sun", *CHERBOURG, INSTANT)
        assert sun["rise"].startswith("2026-10-23T06:40")
        assert sun["transit"].startswith("2026-10-23T11:50")
        assert sun["set"].startswith("2026-10-23T17:00")
        assert sun["max_alt"] == pytest.approx(28.9, abs=0.1)
        assert sun["altitude"] < 0
        assert "phase" not in sun

    def test_moon(self):
        moon = local_engine.compute_body("Moon", *CHERBOURG, INSTANT)
        assert moon["illumination"] == pytest.approx(89.2, abs=0.2)
        assert moon["moon_phase"] == "Gibbeuse croissante"
        assert moon["moon_age"] == pytest.approx(11.6, abs=0.1)
        assert 370_000 < moon["distance_km"] < 400_000
        assert moon["constellation"] == "Poissons"

    def test_planet_keys_match_imcce(self):
        """Les clés partagées avec la source IMCCE sont présentes (capteur de visibilité compatible)."""
        mars = local_engine.compute_body("Mars", *CHERBOURG, INSTANT)
        for key in ("magnitude", "elongation", "distance", "phase", "ra", "dec", "rise", "set", "date"):
            assert key in mars
        assert mars["ra"].startswith("+") and mars["ra"].count(":") == 2
        assert 0 < mars["elongation"] < 180

    def test_moon_phase_names(self):
        assert local_engine.moon_phase_name(0) == "Nouvelle lune"
        assert local_engine.moon_phase_name(180) == "Pleine lune"
        assert local_engine.moon_phase_name(359) == "Nouvelle lune"


class TestTime:
    def test_time_values(self):
        values = local_engine.compute_time(-1.6222, INSTANT)
        assert values["julian_day"] == pytest.approx(2461336.68557, abs=1e-5)
        assert values["day_of_week"] == "vendredi"
        assert values["day_of_year"] == 296
        assert values["local_sidereal_time"] == "06:27:10"
        assert values["equation_of_time"] == pytest.approx(15.6, abs=0.1)
