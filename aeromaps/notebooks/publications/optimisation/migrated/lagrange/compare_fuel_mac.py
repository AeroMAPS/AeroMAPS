"""Is the shadow carbon price the same thing as a fuel's abatement cost? No.

lambda_G1 prices the *cumulative* carbon budget, which the constraint treats as
a stock: a tonne in 2030 and a tonne in 2050 are perfectly substitutable, so the
whole 2025-2050 window carries a single multiplier, in euros discounted to 2020.
A fuel's abatement cost is a different object - a per-year, per-fuel cost ratio
in that year's euros.

This script puts the two side by side. The budget being a stock constraint, the
first-order condition equates *discounted* marginal abatement costs across
years, so the year-t price implied by lambda is lambda * (1+r)^(t-2020). That
identity holds only in years where the budget is the sole binding constraint,
and the divergence from the fuel costs is exactly the effect of the resource and
ramp-up constraints plus the demand-side welfare loss.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from extract_multipliers import DISCOUNT_RATE, OPTIM_YEARS, OUT, RESULTS, SERIES_START_YEAR

BASELINE = "opt_main_2_6"


def series(payload, name):
    values = np.asarray(payload["vector_outputs"][name], float)
    return pd.Series(values, index=range(SERIES_START_YEAR, SERIES_START_YEAR + len(values)))


def fuel_abatement_costs(run: str = BASELINE) -> pd.DataFrame:
    payload = json.loads((RESULTS / f"{run}.json").read_text())
    # MFSP is EUR/MJ and the emission factor gCO2/MJ, so the ratio is EUR/gCO2;
    # 1e6 puts it in EUR/tCO2. Carbon tax is excluded, otherwise the comparison
    # would be circular.
    kero_mfsp = series(payload, "fossil_kerosene_net_mfsp_without_carbon_tax")
    kero_ef = series(payload, "fossil_kerosene_mean_co2_emission_factor")

    def mac(prefix):
        mfsp = series(payload, f"{prefix}_net_mfsp_without_carbon_tax")
        ef = series(payload, f"{prefix}_mean_co2_emission_factor")
        return (mfsp - kero_mfsp) / (kero_ef - ef) * 1e6

    table = pd.DataFrame(
        {
            "biofuel_mac_eur_per_tco2": mac("generic_biofuel"),
            "electrofuel_mac_eur_per_tco2": mac("generic_electrofuel"),
        }
    ).loc[OPTIM_YEARS]

    multipliers = pd.read_csv(OUT / "lagrange_multipliers.csv")
    row = multipliers[(multipliers.run == run) & (multipliers.constraint == "G1")].iloc[0]
    shadow = row.shadow_price_eur_per_tco2_discounted2020
    table["lambda_G1_implied_eur_per_tco2"] = [
        shadow * (1 + DISCOUNT_RATE) ** (year - 2020) for year in OPTIM_YEARS
    ]
    table["ratio_to_biofuel_mac"] = (
        table.lambda_G1_implied_eur_per_tco2 / table.biofuel_mac_eur_per_tco2
    )
    # Which constraints bind in each year: the reason the two diverge.
    binding = (
        multipliers[(multipliers.run == run) & multipliers.active & (multipliers.lambda_raw > 0)]
        .groupby("year")
        .constraint.apply(lambda c: "+".join(sorted(set(c))))
    )
    table["binding_constraints"] = [binding.get(year, "-") for year in OPTIM_YEARS]
    table.attrs["shadow_price_discounted2020"] = shadow
    return table


if __name__ == "__main__":
    table = fuel_abatement_costs()
    table.to_csv(OUT / "shadow_price_vs_fuel_mac.csv")
    print(
        f"Baseline {BASELINE}: lambda_G1 = "
        f"{table.attrs['shadow_price_discounted2020']:.0f} EUR/tCO2 discounted to 2020\n"
    )
    print(table.to_string(float_format=lambda v: f"{v:9.1f}"))
