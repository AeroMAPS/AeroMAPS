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


def build_pathways_manager(energy_carriers_data, energy_processes_data=None):
    """Build a manager from the raw contents of the energy-carrier YAML.

    Split out of ``AeroMAPSProcess`` so that results loaded from committed JSON
    can carry a manager too. The pathway metadata the plots need is entirely
    declared in the YAML, so it does not require running the model, and without
    it every pathway-aware plot falls back to an empty figure.

    Parameters
    ----------
    energy_carriers_data : dict
        Parsed energy-carrier YAML, one entry per pathway.
    energy_processes_data : dict, optional
        Parsed processes YAML, used to map each pathway's processes onto the
        resource each of them consumes.

    Returns
    -------
    EnergyCarrierManager
        Manager holding one metadata entry per declared pathway.
    """
    processes = energy_processes_data or {}
    manager = EnergyCarrierManager()
    for pathway, pathway_data in energy_carriers_data.items():
        if "name" not in pathway_data or "inputs" not in pathway_data:
            raise ValueError(f"pathway {pathway!r} must declare both a name and inputs")
        technical = pathway_data.get("inputs", {}).get("technical", {})
        manager.add(
            EnergyCarrierMetadata(
                name=pathway,
                aircraft_type=pathway_data.get("aircraft_type"),
                default=pathway_data.get("default"),
                mandate_type=pathway_data.get("inputs").get("mandate", {}).get("mandate_type"),
                energy_origin=pathway_data.get("energy_origin"),
                resources_used=technical.get("resource_names", []),
                resources_used_processes={
                    name: (
                        list(
                            processes.get(name, {})
                            .get("inputs", {})
                            .get("technical", {})
                            .get(f"{name}_resource_names", [])
                        )
                        or [None]
                    )[0]
                    for name in technical.get("processes_names", [])
                },
                cost_model=pathway_data.get("cost_model"),
                environmental_model=pathway_data.get("environmental_model"),
            )
        )
    return manager
