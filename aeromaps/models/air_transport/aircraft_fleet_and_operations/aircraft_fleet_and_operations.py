"""
aircraft_fleet_and_operations
===============

Models to compute energy intensities per ASK/RTK for different aircraft pathways
including effects of operations and contrails.
"""

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class EnergyIntensity(AeroMAPSModel):
    """Apply operational efficiency corrections to aircraft energy-per-distance metrics.

    For every market (passenger and freight) and every energy type (drop-in fuel,
    hydrogen, electric) the model applies two corrections to the bare aircraft
    efficiency values that come from the upstream fleet/efficiency models:

    - ``operations_gain``: percentage reduction from operational improvements
      (e.g. better routing, airlines practices improvement) [%].
    - ``operations_contrails_overconsumption``: percentage increase due to
      contrail-avoidance manoeuvres [%].

    The combined factor applied to each input series is::

        (1 - operations_gain / 100) * (1 + operations_contrails_overconsumption / 100)

    Parameters
    ----------
    name : str
        Name of the model instance (``'energy_intensity'`` by default).

    Documentation
    --------------
    Inputs
        - operations_gain: Operational efficiency improvement [%].
        - operations_contrails_overconsumption: Contrail-avoidance fuel penalty [%].
        - energy_per_ask_without_operations_<market>_<energy>: Passenger energy per ASK
          before operational corrections [MJ/ASK].
        - energy_per_rtk_without_operations_<freight>_<energy>: Freight energy per RTK
          before operational corrections [MJ/RTK].
    Outputs
        - energy_per_ask_<market>_<energy>: Passenger energy per ASK after corrections
          [MJ/ASK].
        - energy_per_rtk_<freight>_<energy>: Freight energy per RTK after corrections
          [MJ/RTK].
    Notes
        - <market> is the MarketManager id (passenger markets).
        - <freight> is the MarketManager id (freight markets).
        - <energy> is one of: dropin_fuel, hydrogen, electric.
        - I/O names are generated from configuration and passed to GEMSEO via
          self.input_names and self.output_names grammars.
    """

    def __init__(self, name="energy_intensity", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        passenger_markets = self.markets.get(traffic_type="passenger")
        freight_markets = self.markets.get(traffic_type="freight")

        self.input_names = {
            "operations_gain": pd.Series([0.0]),
            "operations_contrails_overconsumption": pd.Series([0.0]),
        }
        for m in passenger_markets:
            mid = m.id
            for energy_type in ("dropin_fuel", "hydrogen", "electric"):
                self.input_names[f"energy_per_ask_without_operations_{mid}_{energy_type}"] = (
                    pd.Series([0.0])
                )

        for m in freight_markets:
            mid = m.id
            for energy_type in ("dropin_fuel", "hydrogen", "electric"):
                self.input_names[f"energy_per_rtk_without_operations_{mid}_{energy_type}"] = (
                    pd.Series([0.0])
                )

        self.output_names = {}
        for m in passenger_markets:
            mid = m.id
            for energy_type in ("dropin_fuel", "hydrogen", "electric"):
                self.output_names[f"energy_per_ask_{mid}_{energy_type}"] = pd.Series([0.0])

        for m in freight_markets:
            mid = m.id
            for energy_type in ("dropin_fuel", "hydrogen", "electric"):
                self.output_names[f"energy_per_rtk_{mid}_{energy_type}"] = pd.Series([0.0])

    def compute(self, input_data: dict) -> dict:
        """Apply operational corrections to per-market energy intensities.

        Parameters
        ----------
        input_data : dict
            Model inputs keyed by configured grammar names.

        Returns
        -------
        dict
            Computed energy intensity series per market and energy type.
        """
        passenger_markets = self.markets.get(traffic_type="passenger")
        freight_markets = self.markets.get(traffic_type="freight")

        operations_gain = input_data["operations_gain"]
        operations_contrails_overconsumption = input_data["operations_contrails_overconsumption"]

        operations_factor = (1 - operations_gain / 100) * (
            1 + operations_contrails_overconsumption / 100
        )

        output_data = {}

        for m in passenger_markets:
            mid = m.id
            for energy_type in ("dropin_fuel", "hydrogen", "electric"):
                col = f"energy_per_ask_{mid}_{energy_type}"
                value = (
                    input_data[f"energy_per_ask_without_operations_{mid}_{energy_type}"]
                    * operations_factor
                )
                self.df.loc[:, col] = value
                output_data[col] = value

        for m in freight_markets:
            mid = m.id
            for energy_type in ("dropin_fuel", "hydrogen", "electric"):
                col = f"energy_per_rtk_{mid}_{energy_type}"
                value = (
                    input_data[f"energy_per_rtk_without_operations_{mid}_{energy_type}"]
                    * operations_factor
                )
                self.df.loc[:, col] = value
                output_data[col] = value

        self._store_outputs(output_data)
        return output_data
