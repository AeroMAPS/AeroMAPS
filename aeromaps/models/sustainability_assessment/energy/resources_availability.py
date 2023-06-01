from typing import Tuple
from aeromaps.models.base import AeromapsModel


class BiomassAvailability(AeromapsModel):
    def __init__(self, name="biomass_availability", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        waste_biomass: float = 0.0,
        crops_biomass: float = 0.0,
        forest_residues_biomass: float = 0.0,
        agricultural_residues_biomass: float = 0.0,
        algae_biomass: float = 0.0,
        fog_waste_biomass: float = 0.0,
        oil_crops_biomass_share: float = 0.0,
        sugarystarchy_crops_biomass_share: float = 0.0,
        lignocellulosic_crops_biomass_share: float = 0.0,
        aviation_biomass_allocated_share: float = 0.0,
    ) -> Tuple[float, float, float, float, float, float, float, float, float, float, float]:
        """Biomass distribution for waste and crops, Biomass availability and Biomass for aviation."""

        solid_waste_biomass = waste_biomass - fog_waste_biomass
        oil_crops_biomass = oil_crops_biomass_share / 100 * crops_biomass
        sugarystarchy_crops_biomass = sugarystarchy_crops_biomass_share / 100 * crops_biomass
        lignocellulosic_crops_biomass = lignocellulosic_crops_biomass_share / 100 * crops_biomass

        available_biomass_hefa_fog = fog_waste_biomass
        available_biomass_hefa_others = algae_biomass + oil_crops_biomass
        available_biomass_ft_others = (
            lignocellulosic_crops_biomass + forest_residues_biomass + agricultural_residues_biomass
        )
        available_biomass_ft_msw = solid_waste_biomass
        available_biomass_atj = sugarystarchy_crops_biomass

        available_biomass_total = (
            waste_biomass
            + crops_biomass
            + forest_residues_biomass
            + agricultural_residues_biomass
            + algae_biomass
        )

        aviation_available_biomass = (
            aviation_biomass_allocated_share / 100 * available_biomass_total
        )

        self.float_outputs["solid_waste_biomass"] = solid_waste_biomass
        self.float_outputs["oil_crops_biomass"] = oil_crops_biomass
        self.float_outputs["sugarystarchy_crops_biomass"] = sugarystarchy_crops_biomass
        self.float_outputs["lignocellulosic_crops_biomass"] = lignocellulosic_crops_biomass
        self.float_outputs["available_biomass_hefa_fog"] = available_biomass_hefa_fog
        self.float_outputs["available_biomass_hefa_others"] = available_biomass_hefa_others
        self.float_outputs["available_biomass_ft_others"] = available_biomass_ft_others
        self.float_outputs["available_biomass_ft_msw"] = available_biomass_ft_msw
        self.float_outputs["available_biomass_atj"] = available_biomass_atj
        self.float_outputs["available_biomass_total"] = available_biomass_total
        self.float_outputs["aviation_available_biomass"] = aviation_available_biomass

        return (
            solid_waste_biomass,
            oil_crops_biomass,
            sugarystarchy_crops_biomass,
            lignocellulosic_crops_biomass,
            available_biomass_hefa_fog,
            available_biomass_hefa_others,
            available_biomass_ft_others,
            available_biomass_ft_msw,
            available_biomass_atj,
            available_biomass_total,
            aviation_available_biomass,
        )


class ElectricityAvailability(AeromapsModel):
    def __init__(self, name="electricity_availability", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        available_electricity: float = 0.0,
        aviation_electricity_allocated_share: float = 0.0,
    ) -> float:
        """Aviation electricity availability."""
        aviation_available_electricity = (
            aviation_electricity_allocated_share / 100 * available_electricity
        )
        self.float_outputs["aviation_available_electricity"] = aviation_available_electricity

        return aviation_available_electricity
