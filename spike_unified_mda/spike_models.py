"""Toy disciplines for the unified_mda global-discipline spike.

Two models only, no dependency on the real AeroMAPS chain:

``SpikeClearing``
    GLOBAL, NOT namespaced, ``model_type="custom"``. Its I/O names are built
    dynamically in :meth:`custom_setup` from a region list read from
    configuration, so the grammar is *already* expressed in namespaced terms
    (``{r}:spike_demand`` -> ``{r}:spike_price``). This mirrors how
    ``RegionalAggregator`` declares its grammar, and is the pattern a real fuel
    market module would use.

``SpikeDemand``
    REGIONAL, namespaced normally by ``apply_namespace_to_disciplines``. Reads
    ``spike_price``, writes ``spike_demand``.

The load-bearing property under test: ``price[r]`` depends on the demand of
**every** region, not just region ``r``. That puts the clearing discipline and
all regional demand disciplines in a single strongly connected component.
"""

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class SpikeClearing(AeroMAPSModel):
    """Global market clearing: total demand across all regions sets every price.

    price[r] = p0 * (1 + stiffness * (D_tot / D_ref) ** gamma) + local_offset[r]

    ``stiffness`` and ``gamma`` are the loop-gain knobs swept in criterion 4.
    """

    def __init__(self, name="spike_clearing", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        # "Configuration" carried by the discipline itself (registry pattern of
        # air_transport/markets/: the model owns its YAML, the process does not
        # know its contents). Populated by configure() before custom_setup().
        self.regions = []
        self.p0 = 1.0
        self.stiffness = 0.3
        self.gamma = 1.0
        self.demand_ref = 1.0
        self.local_offset = {}
        # Placeholder grammar, overwritten by custom_setup() once regions are known.
        self.input_names = {}
        self.output_names = {}

    def configure(self, regions, p0, stiffness, gamma, demand_ref, local_offset=None):
        """Stand-in for reading the module's own YAML config."""
        self.regions = list(regions)
        self.p0 = float(p0)
        self.stiffness = float(stiffness)
        self.gamma = float(gamma)
        self.demand_ref = float(demand_ref)
        self.local_offset = dict(local_offset or {})
        return self

    def custom_setup(self):
        """Build the namespaced grammar from the configured region list."""
        if not self.regions:
            raise RuntimeError("SpikeClearing.custom_setup() called before configure().")
        self.input_names = {f"{r}:spike_demand": pd.Series([0.0]) for r in self.regions}
        self.output_names = {f"{r}:spike_price": pd.Series([0.0]) for r in self.regions}
        self.output_names["spike_total_demand"] = pd.Series([0.0])

    def _initialize_df(self):
        super()._initialize_df()
        # Seed the demand -> price coupling so the MDA has a starting point.
        # Per-region seed = demand_ref / n_regions (a flat, uninformed guess).
        # NB: AeroMAPSModel.__init__ calls _initialize_df() *before* the subclass
        # body runs, so these attributes may not exist yet on the first call.
        regions = getattr(self, "regions", [])
        if regions:
            seed = self.demand_ref / len(regions)
            self._coupling_defaults = {
                f"{r}:spike_demand": pd.Series(seed, index=self.df.index) for r in regions
            }

    def compute(self, input_data: dict) -> dict:
        total = None
        for r in self.regions:
            d = input_data[f"{r}:spike_demand"]
            total = d.copy() if total is None else total + d

        ratio = total / self.demand_ref
        common = self.p0 * (1.0 + self.stiffness * ratio**self.gamma)

        output_data = {"spike_total_demand": total}
        for r in self.regions:
            price = common + self.local_offset.get(r, 0.0)
            output_data[f"{r}:spike_price"] = price

        # Mirror the AeroMAPS convention: keep results on self.df too.
        for key, val in output_data.items():
            self.df.loc[:, key] = val
        return output_data


class SpikeDemand(AeroMAPSModel):
    """Regional demand response to the cleared price. Namespaced normally.

    demand = D0 * (price / p0) ** (-elasticity)
    """

    def __init__(self, name="spike_demand", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.d0 = 1.0
        self.p0 = 1.0
        self.elasticity = 0.5
        self.input_names = {"spike_price": pd.Series([0.0])}
        self.output_names = {"spike_demand": pd.Series([0.0])}

    def configure(self, d0, p0, elasticity):
        self.d0 = float(d0)
        self.p0 = float(p0)
        self.elasticity = float(elasticity)
        return self

    def _initialize_df(self):
        super()._initialize_df()
        self._coupling_defaults = {
            "spike_price": pd.Series(getattr(self, "p0", 1.0), index=self.df.index)
        }

    def compute(self, input_data: dict) -> dict:
        price = input_data["spike_price"]
        demand = self.d0 * (price / self.p0) ** (-self.elasticity)
        self.df.loc[:, "spike_demand"] = demand
        self.df.loc[:, "spike_price"] = price
        return {"spike_demand": demand}
