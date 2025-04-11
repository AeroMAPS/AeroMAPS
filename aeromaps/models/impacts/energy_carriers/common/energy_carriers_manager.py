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
        self.carriers = carriers if carriers is not None else []

    def add(self, carrier: EnergyCarrierMetadata):
        self.carriers.append(carrier)

    def get(self, **criteria) -> List[EnergyCarrierMetadata]:
        return [
            c
            for c in self.carriers
            if all(getattr(c, attr, None) == val for attr, val in criteria.items())
        ]

    def get_all(self):
        return self.carriers
