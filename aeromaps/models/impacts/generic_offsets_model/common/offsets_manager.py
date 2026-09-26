from dataclasses import dataclass
from typing import List


@dataclass
class OffsetSchemeMetadata:
    """
    Dataclass to hold metadata for an offsetting scheme.

    An offsetting scheme is one mechanism through which residual CO2 emissions are
    compensated outside the sector: an emissions trading system, CORSIA, a future
    obligation, a removals purchase. Each scheme carries its own quantity rule and
    its own price, so that the aggregate carbon offset and its expense can be
    decomposed per scheme and per category of schemes.

    Attributes
    ----------
    name : str
        Name of the scheme.
    category : str
        Category of the scheme (e.g. offsets, allowances, removals). Free to add
        more or decompose further.
    quantity_mode : str
        How the offset quantity is set: ``share_of_residual`` (a share of the
        emissions left after the level-based schemes), ``level`` (the emissions
        above a baseline set relative to a reference year, CORSIA-style) or
        ``quantity`` (a prescribed annual quantity).
    """

    name: str = None
    category: str = None
    quantity_mode: str = None


class OffsetSchemeManager:
    """
    Manager class to handle a collection of offsetting schemes and provide methods
    to add and retrieve them based on various criteria.

    Attributes
    ----------
    schemes : List[OffsetSchemeMetadata]
        List of offsetting scheme metadata instances.
    """

    QUANTITY_MODES = ("share_of_residual", "level", "quantity")

    def __init__(self, schemes: List[OffsetSchemeMetadata] = None):
        self.schemes = schemes if schemes is not None else []

    def add(self, scheme: OffsetSchemeMetadata):
        """Add a new offsetting scheme to the manager."""
        if scheme.quantity_mode not in self.QUANTITY_MODES:
            raise ValueError(
                f"Offsetting scheme '{scheme.name}': quantity mode '{scheme.quantity_mode}' "
                f"is not one of {self.QUANTITY_MODES}."
            )
        self.schemes.append(scheme)

    def get(self, **criteria) -> List[OffsetSchemeMetadata]:
        """
        Retrieve offsetting schemes that match all specified criteria.

        Parameters
        ----------
        criteria
            Keyword arguments matched against scheme attributes; only schemes matching
            all provided criteria are returned.
        """
        return [
            s
            for s in self.schemes
            if all(getattr(s, attr, None) == val for attr, val in criteria.items())
        ]

    def get_all(self):
        """Return all offsetting schemes managed by this object."""
        return self.schemes

    def get_all_types(self, parameter: str) -> List:
        """Return the unique non-None values of an attribute across all schemes, in declaration order."""
        return list(
            dict.fromkeys(
                getattr(scheme, parameter)
                for scheme in self.schemes
                if getattr(scheme, parameter, None) is not None
            )
        )
