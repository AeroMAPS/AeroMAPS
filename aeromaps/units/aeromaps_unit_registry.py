from enum import Enum, StrEnum
from pint import UnitRegistry, Quantity
from pint.util import UnitsContainer
import re

CAPITA = "capita"


class AirTransportQuantities(StrEnum):
    """Air transport quantities dimensions."""

    ASK = "ASK"
    PAX = "PAX"
    RPK = "RPK"
    SEAT = "seat"
    AIRCRAFT = "aircraft"


def _units_preprocessor(expr):
    """Group number-unit pairs: 100km -> (100*km).

    Args:
        expr: the expression to preprocess.

    Return:
        The grouped magnitude-unit.
    """
    return re.sub(
        r"(?<![\w.])(\d+(?:\.\d+)?)([a-zA-Z_]\w*)",
        r"(\1*\2)",
        expr,
    )


class MassSpeciesTags(StrEnum):
    """The names of the different species for species-tagged masses."""

    CO2 = "CO2"
    CO2E = "CO2e"
    CO2WE = "CO2we"
    NOX = "NOx"
    FUEL = "fuel"


class QuantitiesDimensions(Enum):
    ENERGY = "energy"
    MASS = "mass"
    DISTANCE = "distance"
    TIME = "time"
    VOLUME = "volume"
    AREA = "area"
    CURRENCY = "currency"
    TEMPERATURE = "temperature"
    POWER = "power"
    CAPITA = "capita"


__DERIVATE_DIMENSIONS_MAPPING = {
    Quantity("J").dimensionality: QuantitiesDimensions.ENERGY,
    Quantity("meter").dimensionality: QuantitiesDimensions.DISTANCE,
    Quantity("meter**2").dimensionality: QuantitiesDimensions.AREA,
    Quantity("meter**3").dimensionality: QuantitiesDimensions.VOLUME,
    Quantity("W").dimensionality: QuantitiesDimensions.POWER,
}


class AeroMAPSUnitRegistry(UnitRegistry):
    _DERIVATE_DIMENSIONS_MAPPING: dict[UnitsContainer, str] = {
        Quantity("J").dimensionality: QuantitiesDimensions.ENERGY,
        Quantity("meter").dimensionality: QuantitiesDimensions.DISTANCE,
        Quantity("meter**2").dimensionality: QuantitiesDimensions.AREA,
        Quantity("meter**3").dimensionality: QuantitiesDimensions.VOLUME,
        Quantity("W").dimensionality: QuantitiesDimensions.POWER,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            preprocessors=[
                lambda s: s.replace("€", "EUR"),
                lambda s: s.replace("$", "USD"),
                _units_preprocessor,
            ],
        )

        self.__define_air_transport_units()
        self.__define_species_tags()
        self.__define_currencies()
        self.__define_mass_tags()
        self.define("m2 = meter **2")
        self.define("Years = year = yr")

        self.define(f"{CAPITA} = [{CAPITA}]")

    def unit_quantity(self, unit: str) -> str | list[str]:
        """Return the quantity that a unit represents.
        Args:
            unit: the unit.

        Return:
            The physical quantity (or quantities) that the unit represents.
        """

        quantities = [key[1:-1] for key in self.dimension(unit).keys()]

        return quantities if len(quantities) > 1 else quantities[0]

    def dimension(self, unit: str) -> dict[str, int] | str:
        """Return the dimensionality of the quantity considering derivate dimensions.

        Args:
            unit: The unit as a string to get the dimensionality from.

        Returns:
            The dimensionality of the unit considering derivate dimensions as
            dict[dimension_name,dimension_magnitude] or "dimensionless".
        """
        if self(unit).dimensionless:
            return "dimensionless"
        units = self(unit).units

        components = [
            "1" + item if "/" in item else item
            for part in re.split(r"(?<!\*)\*(?!\*)", str(units))
            for item in (re.split(r"(?=/)", part) if "/" in part else [part])
        ]

        dimensions = {}
        for unit_component in components:
            _Q = self(unit_component)
            dimensionality = _Q.dimensionality
            inv_dimensionality = "/" in unit_component
            derivate_dimension = self._DERIVATE_DIMENSIONS_MAPPING.get(
                dimensionality if not inv_dimensionality else 1 / dimensionality, None
            )
            unit_dimension = (
                {f"[{derivate_dimension.value}]": 1 if not inv_dimensionality else -1}
                if derivate_dimension
                else dict(dimensionality)
            )

            if len(dimensionality) == 2 and "[mass]" in dimensionality:
                tagged_mass = self._tag_masses_dimensions(unit_dimension)
                unit_dimension = {tagged_mass: unit_dimension["[mass]"]}

            dimensions.update(unit_dimension)
        return dimensions

    def __define_mass_tags(self):
        self.define("tCO2e = tonne * CO2e")
        self.define("tCO2 = tonne * CO2")
        self.define("gCO2 = gram * CO2")
        self.define("GtCO2 = gigatonne * CO2")
        self.define("GtCO2we = gigatonne * CO2we")
        self.define("gNOx = g * NOx")
        self.define("kg_NOx = kg * NOx")
        self.define("gfuel = g * fuel")
        self.define("kg_fuel = kg * fuel")

    def __define_currencies(self):
        self.define("euro = [currency] = € = EUR")
        self.define("kEUR = euro * 1000 = k€")
        self.define("MEUR = euro * 1e6 = M€")
        self.define("dollar = [currency_USD]= $ = USD")
        self.define("kUSD = dollar * 1000 = k$")
        self.define("MUSD = dollar * 1e6 = M$")

    def __define_self_defining_dimensions(self, unit: str):
        self.define(f"{unit} = [{unit}]")

    def __define_species_tags(self):
        for species in MassSpeciesTags:
            self.__define_self_defining_dimensions(species.value)

    def __define_air_transport_units(self):

        for quantity in AirTransportQuantities:
            self.__define_self_defining_dimensions(quantity.value)

    def _tag_masses_dimensions(self, dimension: dict[str, int]) -> str:
        """Tag masses for dimensions."""

        species_tag = [
            species
            for species in dimension.keys()
            if species.strip().strip("[]") in iter(MassSpeciesTags)
        ]

        assert len(species_tag) == 1

        return f"[mass{species_tag[0]}]"
