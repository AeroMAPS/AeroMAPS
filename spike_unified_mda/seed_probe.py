"""Open question: can _coupling_defaults be seeded with a computed TRAJECTORY?

``_coupling_defaults`` is only a dict merged into the wrapper's
``default_input_data`` (``aeromaps/core/gemseo.py``, ``update_defaults``). It is
built inside the model's ``_initialize_df()``, where ``self.parameters`` and the
year index are already available, so nothing constrains the value to a constant
series -- a computed trajectory is accepted just as well.

This probe seeds the demand -> price coupling four ways, ALWAYS before the
MDAChain is built (which is the real code path), and reports what changes.
"""

import warnings

import numpy as np
import pandas as pd
from gemseo.mda.mda_chain import MDAChain

from aeromaps.core.gemseo import (
    AeroMAPSCustomModelWrapper,
    apply_namespace_to_disciplines,
    disable_gemseo_execution_statistics,
)
from spike_unified_mda.spike_models import SpikeClearing, SpikeDemand
from spike_unified_mda.step1_plumbing import DEFAULT_REGIONS, SPIKE_PARAMETERS
from spike_unified_mda.step1_remedies import true_fixed_point

disable_gemseo_execution_statistics()
warnings.filterwarnings("ignore")


def run(seed_kind, s=0.3, g=15.0, e=0.5, p0=1.0, tol=1e-10, max_iter=2000):
    regions = DEFAULT_REGIONS
    region_ids = list(regions)
    dref = float(sum(regions.values()))
    x_star = true_fixed_point(s, g, e)
    price_star = p0 * (1.0 + s * x_star**g)

    clearing = SpikeClearing(name="SpikeClearing", parameters=SPIKE_PARAMETERS)
    clearing.configure(region_ids, p0, s, g, dref)
    clearing.custom_setup()
    clearing._initialize_df()

    discs = []
    for rid, d0 in regions.items():
        dm = SpikeDemand(name="SpikeDemand", parameters=SPIKE_PARAMETERS)
        dm.configure(d0=d0, p0=p0, elasticity=e)
        dm._initialize_df()
        idx = dm.df.index
        # Overwrite _coupling_defaults BEFORE the discipline wrapper reads them.
        if seed_kind == "flat_uninformed":
            seed = pd.Series(p0, index=idx)
        elif seed_kind == "flat_at_solution":
            seed = pd.Series(price_star, index=idx)
        elif seed_kind == "computed_trajectory":
            seed = pd.Series(np.linspace(p0, price_star, len(idx)), index=idx)
        elif seed_kind == "computed_trajectory_far":
            seed = pd.Series(np.linspace(p0, 10.0 * price_star, len(idx)), index=idx)
        else:
            raise ValueError(seed_kind)
        dm._coupling_defaults = {"spike_price": seed}
        discs.extend(apply_namespace_to_disciplines([AeroMAPSCustomModelWrapper(model=dm)], rid))

    discs.append(AeroMAPSCustomModelWrapper(model=clearing))
    mda = MDAChain(
        disciplines=discs,
        tolerance=tol,
        max_mda_iter=max_iter,
        initialize_defaults=True,
        inner_mda_name="MDAGaussSeidel",
    )
    out = mda.execute()
    h = list(mda.inner_mdas[0].residual_history)
    x_num = float(out["spike_total_demand"].iloc[-1]) / dref
    seeded = {
        d.name: float(np.asarray(d.default_input_data[f"{d.name.split('_')[0]}:spike_price"])[0])
        for d in discs
        if "SpikeDemand" in d.name
    }
    return len(h), float(h[-1]), x_num, x_star, seeded


if __name__ == "__main__":
    print("Toy system, stiffness=0.3, gamma=15 (near the plain-Gauss-Seidel limit), tol=1e-10")
    print("Seed set on the model's _coupling_defaults BEFORE wrapping (the real code path).\n")
    print(
        f"{'coupling seed':>26} {'accepted':>9} {'iterations':>11} {'residual':>11} "
        f"{'x found':>10} {'x true':>10}"
    )
    for kind in (
        "flat_uninformed",
        "flat_at_solution",
        "computed_trajectory",
        "computed_trajectory_far",
    ):
        n, r, x, xs, seeded = run(kind)
        print(f"{kind:>26} {'yes':>9} {n:>11} {r:>11.2e} {x:>10.6f} {xs:>10.6f}")
        print(
            f"{'':>26} seed value seen by the wrappers: "
            f"{ {k: round(v, 4) for k, v in seeded.items()} }"
        )
