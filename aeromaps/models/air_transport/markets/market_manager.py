from typing import List, Optional

from aeromaps.models.air_transport.markets.market import Market


class MarketManager:
    """Manager for a collection of :class:`Market` instances.

    Analogous to :class:`~aeromaps.models.impacts.generic_energy_model.common.energy_carriers_manager.EnergyCarrierManager`.
    Built once in ``AeroMAPSProcess._initialize_markets()`` and stored as
    ``self.markets``.

    Parameters
    ----------
    markets : list of Market, optional
        Initial list of market instances.
    """

    def __init__(self, markets: List[Market] = None):
        self.markets: List[Market] = markets if markets is not None else []

    def add(self, market: Market) -> None:
        """Append a market to the manager."""
        self.markets.append(market)

    def get_all(self) -> List[Market]:
        """Return all markets."""
        return self.markets

    def get_ids(self) -> List[str]:
        """Return the id of every market, in declaration order."""
        return [m.id for m in self.markets]

    def get(self, traffic_type: Optional[str] = None) -> List[Market]:
        """Return markets matching the given criteria.

        Parameters
        ----------
        traffic_type : str, optional
            Filter by ``"passenger"`` or ``"freight"``.  When ``None`` all
            markets are returned.

        Returns
        -------
        list of Market
        """
        result = self.markets
        if traffic_type is not None:
            result = [m for m in result if m.traffic_type == traffic_type]
        return result

    def __iter__(self):
        return iter(self.markets)

    def __len__(self):
        return len(self.markets)
