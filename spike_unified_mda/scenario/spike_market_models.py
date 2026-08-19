"""Step 2 of the spike: the toy market wired into the REAL AeroMAPS chain.

Three disciplines:

``SpikeFuelDemand`` (regional, namespaced)
    Reads the real ``rpk`` and turns it into a fuel-market demand proxy.

``SpikeFuelMarket`` (GLOBAL, NOT namespaced)
    Reads ``{r}:spike_fuel_demand`` for every region and writes ``{r}:spike_fuel_price``.
    Follows the ``air_transport/markets/`` pattern: it carries its OWN YAML
    configuration, loaded in :meth:`custom_setup` once the region list has been
    injected by ``MultiRegionalProcess._wrap_global_model``.

``SpikeMarketCarbonTax`` (regional, namespaced)
    Turns the cleared price into ``carbon_tax``, an input of the real energy-cost
    chain. It REPLACES the standard ``CarbonTax`` discipline, so the spike region
    config must not load ``models_energy_cost``.

Resulting cycle, entirely inside one SCC:

    {r}:rpk -> {r}:spike_fuel_demand -> SpikeFuelMarket -> {r}:spike_fuel_price
            -> {r}:carbon_tax -> DOC energy carbon tax -> total cost
            -> {r}:airfare_per_rpk -> RPKElasticity -> {r}:rpk
"""

import os

import pandas as pd
import yaml

from aeromaps.models.base import AeroMAPSModel

_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spike_market.yaml")


def _load_spike_config():
    """Load the module's own YAML, with env-var overrides used by the sweeps."""
    with open(_CONFIG_FILE) as stream:
        config = yaml.safe_load(stream)
    for key in ("stiffness", "gamma", "base_price", "demand_ref"):
        env = os.environ.get(f"SPIKE_{key.upper()}")
        if env is not None:
            config[key] = float(env)
    return config


class SpikeFuelDemand(AeroMAPSModel):
    """Regional: real RPK -> fuel-market demand proxy. Namespaced normally."""

    def __init__(self, name="spike_fuel_demand", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.input_names = {"rpk": pd.Series([0.0])}
        self.output_names = {"spike_fuel_demand": pd.Series([0.0])}

    def compute(self, input_data: dict) -> dict:
        # Demand proxy: RPK scaled to a market-size unit. The scale is irrelevant to
        # the coupling, only the ratio to demand_ref matters.
        demand = input_data["rpk"] / 1e12
        self.df.loc[:, "spike_fuel_demand"] = demand
        return {"spike_fuel_demand": demand}


class SpikeFuelMarket(AeroMAPSModel):
    """GLOBAL, NOT namespaced: total demand across all regions sets every price.

    price[r] = base_price * (1 + stiffness * (D_tot / D_ref) ** gamma) + offset[r]
    """

    def __init__(self, name="spike_fuel_market", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        # Injected by MultiRegionalProcess._wrap_global_model before custom_setup().
        self.regions = []
        self.global_namespace = "overall"
        # Loaded from this module's own YAML in custom_setup().
        self.config = {}
        self.input_names = {}
        self.output_names = {}

    def custom_setup(self):
        """Load the module's YAML and build the namespaced grammar from the regions."""
        if not self.regions:
            raise RuntimeError(
                "SpikeFuelMarket.custom_setup() ran before the region list was injected."
            )
        self.config = _load_spike_config()
        self.input_names = {f"{r}:spike_fuel_demand": pd.Series([0.0]) for r in self.regions}
        self.output_names = {f"{r}:spike_fuel_price": pd.Series([0.0]) for r in self.regions}
        self.output_names["spike_total_fuel_demand"] = pd.Series([0.0])

    def _initialize_df(self):
        super()._initialize_df()
        regions = getattr(self, "regions", [])
        config = getattr(self, "config", {})
        if regions and config:
            seed = config["demand_ref"] / len(regions)
            self._coupling_defaults = {
                f"{r}:spike_fuel_demand": pd.Series(seed, index=self.df.index) for r in regions
            }

    def compute(self, input_data: dict) -> dict:
        cfg = self.config
        total = None
        for r in self.regions:
            d = input_data[f"{r}:spike_fuel_demand"]
            total = d.copy() if total is None else total + d

        ratio = total / cfg["demand_ref"]
        common = cfg["base_price"] * (1.0 + cfg["stiffness"] * ratio ** cfg["gamma"])

        output_data = {"spike_total_fuel_demand": total}
        offsets = cfg.get("local_offset", {}) or {}
        for r in self.regions:
            output_data[f"{r}:spike_fuel_price"] = common + float(offsets.get(r, 0.0))

        for key, val in output_data.items():
            self.df.loc[:, key] = val
        return output_data


class SpikeMarketCarbonTax(AeroMAPSModel):
    """Regional: cleared market price -> ``carbon_tax`` fed to the real cost chain.

    Replaces the standard ``CarbonTax`` discipline (same output name), so the spike
    region config loads its own model instead of ``models_energy_cost``.
    """

    def __init__(self, name="spike_market_carbon_tax", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.input_names = {"spike_fuel_price": pd.Series([0.0])}
        self.output_names = {"carbon_tax": pd.Series([0.0])}

    def _initialize_df(self):
        super()._initialize_df()
        self._coupling_defaults = {
            "spike_fuel_price": pd.Series(0.0, index=self.df.index),
        }

    def compute(self, input_data: dict) -> dict:
        price = input_data["spike_fuel_price"]
        carbon_tax = pd.Series(0.0, index=self.df.index)
        # No tax over the historical years: the market only drives the projection.
        proj = slice(self.prospection_start_year, self.end_year)
        carbon_tax.loc[proj] = price.loc[proj]
        self.df.loc[:, "carbon_tax"] = carbon_tax
        return {"carbon_tax": carbon_tax}
