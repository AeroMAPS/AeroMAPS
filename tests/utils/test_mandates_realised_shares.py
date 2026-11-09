"""``realised_dropin_shares`` reads the drop-in carriers only, and sums to 100 %."""

import pytest

from aeromaps.utils.mandates import realised_dropin_shares

CARRIERS = {
    "bio": {"aircraft_type": "dropin_fuel"},
    "fossil": {"aircraft_type": "dropin_fuel"},
    "h2": {"aircraft_type": "hydrogen"},
}


def _outputs():
    return {
        "vector_outputs": {
            "energy_consumption_dropin_fuel": [0.0, 10.0, 10.0],
            "bio_energy_consumption": [0.0, 2.0, 5.0],
            "fossil_energy_consumption": [0.0, 8.0, 5.0],
            "h2_energy_consumption": [0.0, 99.0, 99.0],
            # an aggregate the run also writes, which is not a carrier
            "dropin_fuel_biomass_energy_consumption": [0.0, 2.0, 5.0],
        }
    }


def test_only_dropin_carriers_and_sum_to_one_hundred():
    shares = realised_dropin_shares(_outputs(), CARRIERS, first_year=2000)
    assert set(shares) == {"bio", "fossil"}
    assert shares["bio"][2001] == pytest.approx(20.0)
    for year in (2001, 2002):
        assert sum(s[year] for s in shares.values()) == pytest.approx(100.0)
    # no drop-in energy in a year: no share, not a division by zero
    assert shares["bio"][2000] == 0.0
