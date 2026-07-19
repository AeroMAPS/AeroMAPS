from dataclasses import dataclass
from typing import List


@dataclass
class OffsettingMechanismMetadata:
    """
    Dataclass to hold metadata for a carbon offsetting mechanism.

    Attributes
    ----------
    name : str
        Name of the offsetting mechanism.
    category : str
        Category of the offsetting mechanism (e.g., carbon_dioxide_removal, emissions_avoidance).
        Free to add more or decompose further (e.g., dac, beccs, afforestation).
    default : bool
        Indicates if this is the default offsetting mechanism, used to fulfill the
        carbon offsetting demand not covered by the other mechanisms.
    usage_type : str
        Type of usage the offsetting mechanism obeys to (share, quantity).
    cost_model : str
        Type of cost model used (e.g., top-down).
    """

    name: str = None
    category: str = None
    default: bool = False
    usage_type: str = None
    cost_model: str = None


class OffsettingMechanismManager:
    """
    Manager class to handle a collection of offsetting mechanisms and provide methods to add and retrieve them based on various criteria.

    Attributes
    ----------
    mechanisms : List[OffsettingMechanismMetadata]
        List of offsetting mechanism metadata instances.
    """

    def __init__(self, mechanisms: List[OffsettingMechanismMetadata] = None):
        """
        Initialize the OffsettingMechanismManager with an optional list of offsetting mechanisms.

        Parameters
        ----------
        mechanisms : List[OffsettingMechanismMetadata], optional
            Initial list of offsetting mechanism metadata instances.
        """
        self.mechanisms = mechanisms if mechanisms is not None else []

    def add(self, mechanism: OffsettingMechanismMetadata):
        """
        Add a new offsetting mechanism to the manager.

        Parameters
        ----------
        mechanism
            Offsetting mechanism metadata instance to add.
        """
        self.mechanisms.append(mechanism)

    def get(self, **criteria) -> List[OffsettingMechanismMetadata]:
        """
        Retrieve offsetting mechanisms that match all specified criteria.

        Parameters
        ----------
        criteria
            Keyword arguments used to match attributes of offsetting mechanisms; only mechanisms matching all provided criteria are returned.

        Returns
        -------
        matches
            Offsetting mechanism metadata instances that match the given criteria.
        """
        return [
            m
            for m in self.mechanisms
            if all(
                val in getattr(m, attr, {}).values()
                if isinstance(getattr(m, attr, None), dict)
                else val in getattr(m, attr, [])
                if isinstance(getattr(m, attr, None), list)
                else getattr(m, attr, None) == val
                for attr, val in criteria.items()
            )
        ]

    def get_all(self):
        """
        Return all offsetting mechanisms managed by this object.

        Returns
        -------
        mechanisms
            All offsetting mechanism metadata instances stored in the manager.
        """
        return self.mechanisms

    def get_all_types(self, parameter: str) -> List:
        """
        Retrieve unique values of a specified attribute across all offsetting mechanisms.

        Parameters
        ----------
        parameter
            Name of the attribute to aggregate unique values for.

        Returns
        -------
        values
            Unique values of the specified parameter across all offsetting mechanisms.
        """
        return list(
            {
                getattr(mechanism, parameter, None)
                for mechanism in self.mechanisms
                if getattr(mechanism, parameter, None) is not None
            }
        )
