from dataclasses import dataclass
from typing import List


@dataclass
class EnergyCarrierMetadata:
    name: str = None
    aircraft_type: str = None
    default: bool = False
    mandate_type: str = None
    energy_origin: str = None


class EnergyCarrierManager:
    def __init__(self, carriers: List[EnergyCarrierMetadata] = None):
        # Initialize the manager with a list of energy carriers or an empty list if none are provided
        self.carriers = carriers if carriers is not None else []

    def add(self, carrier: EnergyCarrierMetadata):
        # Add a new energy carrier to the list
        self.carriers.append(carrier)

    def get(self, **criteria) -> List[EnergyCarrierMetadata]:
        # Retrieve energy carriers that match all specified criteria
        return [
            c
            for c in self.carriers
            if all(getattr(c, attr, None) == val for attr, val in criteria.items())
        ]

    def get_all(self):
        # Return the complete list of energy carriers
        return self.carriers

    def get_all_types(self, parameter: str) -> List:
        # Retrieve all unique values of a specific parameter across all energy carriers
        return list(
            {
                getattr(carrier, parameter, None)
                for carrier in self.carriers
                if getattr(carrier, parameter, None) is not None
            }
        )
