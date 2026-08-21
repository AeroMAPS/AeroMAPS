"""Is the ~1.6e-6 residual floor caused by all-NaN coupling variables?

Diagnostic only (NOT a proposed fix): neutralise the NaN sentinel so that a NaN
coupling contributes 0 to the residual instead of 999999, and see whether the
same, otherwise untouched, scenarios then reach the 1e-10 tolerance.
"""

import logging
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logging.disable(logging.INFO)

NEUTRALISE = "--neutralise" in sys.argv

if NEUTRALISE:
    from aeromaps.core.gemseo import CustomDataConverter

    _orig = CustomDataConverter.convert_value_to_array

    def _patched(self, name, value):
        if isinstance(value, pd.Series):
            value = value.fillna(0.0)
        return _orig(self, name, value)

    CustomDataConverter.convert_value_to_array = _patched


def report(label, mda):
    for m in mda.inner_mdas:
        h = list(m.residual_history)
        res = m._BaseMDASolver__current_residuals
        rows = sorted(((float(np.linalg.norm(v)), k) for k, v in res.items()), reverse=True)
        status = "CONVERGED" if h[-1] <= m.settings.tolerance else "NOT converged"
        print(
            f"{label}: {len(m.disciplines)} coupled disciplines, {len(h)} iterations, "
            f"residual {h[-1]:.3e} (tol {m.settings.tolerance:.0e}) -> {status}"
        )
        print(f"    top residual contributors: {[(k, f'{n:.2e}') for n, k in rows[:3]]}")


if __name__ == "__main__":
    mode = "NaN sentinel NEUTRALISED" if NEUTRALISE else "stock AeroMAPS"
    print(f"=== {mode} ===")

    from aeromaps.core.process import AeroMAPSProcess
    from aeromaps.core.multi_regional_process import MultiRegionalProcess

    from spike_unified_mda.mda_settings import tune

    cfg = (
        "aeromaps/notebooks/tutorials/08_use_variable_demand/data_elasticity/config_elasticity.yaml"
    )
    p = AeroMAPSProcess(configuration_file=cfg)
    p.compute()
    report("CONTROL single-region elasticity (stock AeroMAPS chain)", p.mda_chain)

    mp = MultiRegionalProcess("spike_unified_mda/scenario/regionalisation_spike.yaml")
    tune(mp)  # same solver settings as the single-region control above
    mp.compute()
    report("SPIKE two regions + global fuel market", mp.mda_chain)
    vo = mp.data["vector_outputs"]
    print(
        f"    2050: price_A={vo['region_A:spike_fuel_price'].loc[2050]:.6f} "
        f"price_B={vo['region_B:spike_fuel_price'].loc[2050]:.6f} "
        f"rpk_A={vo['region_A:rpk'].loc[2050]:.6e} rpk_B={vo['region_B:rpk'].loc[2050]:.6e}"
    )
