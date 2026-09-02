"""
test_quantity_mandate_horizon
=============================

Guards the index of the per-pathway energy consumption emitted by
:class:`~aeromaps.models.impacts.generic_energy_model.common.energy_use_choice.EnergyUseChoice`
when a pathway carries a *quantity* mandate.

Background
----------
``EnergyUseChoice`` handles quantity mandates in two branches:

* the mandated volumes fit inside total energy, so they are published unchanged;
* they exceed it, so they are scaled down homogeneously.

The second branch builds its output from a series already reindexed onto the full
model horizon, while the first used to publish the mandate curve as-is -- and a
mandate curve only spans the prospective years. So the output length depended on
which branch ran: 27 elements (2024-2050) in one, 51 (2000-2050) in the other.

Under exogenous demand the branch never changes and nothing shows. Under
price-elastic demand, total energy moves between MDA iterations and can flip the
branch mid-solve. GEMSEO fixes its coupling slices on first resolution, so the
coupling vector then changes size underneath it and the Gauss-Seidel step dies
with a shape mismatch -- ``operands could not be broadcast together with shapes
(13358,) (12974,)``, the difference being exactly the number of affected
variables times the number of historic years.

Fixing the first branch to reindex also corrected a latent error in the historic
period: the drop-in massic shares read 0 % fossil over 2000-2023, when with no
SAF deployed fossil kerosene is by definition 100 % of drop-in fuel.

What is tested
--------------
1. Every per-pathway ``*_energy_consumption`` output spans the full model
   horizon, so the coupling vector cannot change size mid-solve.
2. Over the historic period the fossil massic share of drop-in fuel is 100 %,
   which is what "no SAF yet" means.
"""

import os

import pytest

from aeromaps import create_process
from aeromaps.utils.scenarios import find_scenario

# The third-edition S1 energy file is the repository's richest quantity-mandate
# case: eight drop-in pathways, all mandated by volume.
EDITION = find_scenario("atag_3rd_edition_full").path
CONFIG = "./config_files/config_s1.yaml"


@pytest.fixture(scope="module")
def process():
    if not (EDITION / "config_files" / "config_s1.yaml").exists():
        pytest.skip("ATAG third-edition scenario not available")
    cwd = os.getcwd()
    os.chdir(EDITION)
    try:
        built = create_process(configuration_file=CONFIG)
        built.compute()
        return built
    finally:
        os.chdir(cwd)


def test_pathway_energy_consumption_spans_full_horizon(process):
    """A quantity mandate must not publish a prospective-only series."""
    vector = process.data["vector_outputs"]
    horizon = len(process.data["years"]["full_years"])

    pathway_columns = [
        column
        for column in vector.columns
        if column.endswith("_energy_consumption") and not column.startswith("energy_consumption")
    ]
    assert pathway_columns, "no per-pathway energy consumption columns found"

    short = {
        column: int(vector[column].notna().sum())
        for column in pathway_columns
        if len(vector[column]) != horizon
    }
    assert not short, (
        f"these outputs do not span the {horizon}-year horizon: {short}. "
        "A coupling variable that changes length mid-solve breaks the MDA."
    )


def test_historic_dropin_fuel_is_entirely_fossil(process):
    """Before any SAF is deployed, fossil kerosene is 100 % of drop-in fuel."""
    vector = process.data["vector_outputs"]
    historic = process.data["years"]["historic_years"]
    share = vector.loc[historic, "fossil_kerosene_massic_share_dropin_fuel"]

    assert share.notna().all(), "historic fossil massic share has gaps"
    assert (share - 100.0).abs().max() < 1e-9, (
        "historic drop-in fuel is not fully fossil; the mandate curves are leaking "
        f"into the historic period (min {share.min()}, max {share.max()})"
    )
