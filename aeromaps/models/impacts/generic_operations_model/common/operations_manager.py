from dataclasses import dataclass
from typing import List


@dataclass
class OperationalConceptMetadata:
    """
    Dataclass to hold metadata for an operational concept.

    An operational concept is a lever of operational improvement (e.g. air traffic
    management, continuous descent, single-engine taxi, contrail avoidance) that
    contributes one or more gains: a fuel-efficiency gain (percentage reduction in
    energy per ASK, affecting CO2) and/or a contrail gain (percentage reduction in
    contrail climate impact, affecting non-CO2) together with the fuel-burn penalty
    of contrail avoidance.

    Attributes
    ----------
    name : str
        Name of the operational concept.
    category : str
        Category of the concept (e.g. flight_operations, ground_operations,
        contrails). Free to add more or decompose further.
    has_fuel_efficiency : bool
        Whether the concept contributes a fuel-efficiency gain (energy per ASK).
    has_contrails : bool
        Whether the concept contributes a contrail gain (and its fuel penalty).
    """

    name: str = None
    category: str = None
    has_fuel_efficiency: bool = False
    has_contrails: bool = False


class OperationalConceptManager:
    """
    Manager class to handle a collection of operational concepts and provide
    methods to add and retrieve them based on various criteria.

    Attributes
    ----------
    concepts : List[OperationalConceptMetadata]
        List of operational concept metadata instances.
    """

    def __init__(self, concepts: List[OperationalConceptMetadata] = None):
        self.concepts = concepts if concepts is not None else []

    def add(self, concept: OperationalConceptMetadata):
        """Add a new operational concept to the manager."""
        self.concepts.append(concept)

    def get(self, **criteria) -> List[OperationalConceptMetadata]:
        """
        Retrieve operational concepts that match all specified criteria.

        Parameters
        ----------
        criteria
            Keyword arguments matched against concept attributes; only concepts
            matching all provided criteria are returned.
        """
        return [
            c
            for c in self.concepts
            if all(getattr(c, attr, None) == val for attr, val in criteria.items())
        ]

    def get_all(self):
        """Return all operational concepts managed by this object."""
        return self.concepts

    def get_all_types(self, parameter: str) -> List:
        """Return the unique non-None values of an attribute across all concepts."""
        return list(
            {
                getattr(concept, parameter, None)
                for concept in self.concepts
                if getattr(concept, parameter, None) is not None
            }
        )
