from dataclasses import dataclass
from typing import List


@dataclass
class EnergyCarrierMetadata:
    """
    Dataclass to hold metadata for an energy carrier.
    Attributes
    ----------
    name : str
        Name of the energy carrier.
    aircraft_type : str
        Type of aircraft the energy carrier is associated with.
    default : bool
        Indicates if this is the default energy carrier for the aircraft type.
    mandate_type : str
        Type of mandate the energy carrier obeys to (share, volume)
    energy_origin : str
        Origin of the energy (e.g., renewable, fossil).
    resources_used : List[str]
        List of resources used by the energy carrier.
    resources_used_processes : dict
        Dictionary mapping resources used by associated processes.
    cost_model : str
        Type of cost model used (e.g., top-down, bottom-up).
    environmental_model : str
        Type of environmental model used (e.g., top-down, bottom-up).

    """

    name: str = None
    aircraft_type: str = None
    default: bool = False
    mandate_type: str = None
    energy_origin: str = None
    resources_used: List[str] = None
    resources_used_processes: dict = None
    cost_model: str = None
    environmental_model: str = None


class EnergyCarrierManager:
    """
    Manager class to handle a collection of energy carriers and provide methods to add and retrieve them based on various criteria.

    Attributes
    ----------
    carriers : List[EnergyCarrierMetadata]
        List of energy carrier metadata instances.
    """

    def __init__(self, carriers: List[EnergyCarrierMetadata] = None):
        """
        Initialize the EnergyCarrierManager with an optional list of energy carriers.

        Parameters
        ----------
        carriers : List[EnergyCarrierMetadata], optional
            Initial list of energy carrier metadata instances.
        """
        self.carriers = carriers if carriers is not None else []

    def add(self, carrier: EnergyCarrierMetadata):
        """
        Add a new energy carrier to the manager.

        Parameters
        ----------
        carrier
            Energy carrier metadata instance to add.
        """
        self.carriers.append(carrier)

    def get(self, **criteria) -> List[EnergyCarrierMetadata]:
        """
        Retrieve energy carriers that match all specified criteria.

        Parameters
        ----------
        criteria
            Keyword arguments used to match attributes of energy carriers; only carriers matching all provided criteria are returned.

        Returns
        -------
        matches
            Energy carrier metadata instances that match the given criteria.
        """
        return [
            c
            for c in self.carriers
            if all(
                val in getattr(c, attr, {}).values()
                if isinstance(getattr(c, attr, None), dict)
                else val in getattr(c, attr, [])
                if isinstance(getattr(c, attr, None), list)
                else getattr(c, attr, None) == val
                for attr, val in criteria.items()
            )
        ]

    def get_all(self):
        """
        Return all energy carriers managed by this object.

        Returns
        -------
        carriers
            All energy carrier metadata instances stored in the manager.
        """
        return self.carriers

    def get_all_types(self, parameter: str) -> List:
        """
        Retrieve unique values of a specified attribute across all energy carriers.

        Parameters
        ----------
        parameter
            Name of the attribute to aggregate unique values for.

        Returns
        -------
        values
            Unique values of the specified parameter across all energy carriers.
        """
        return list(
            {
                getattr(carrier, parameter, None)
                for carrier in self.carriers
                if getattr(carrier, parameter, None) is not None
            }
        )
