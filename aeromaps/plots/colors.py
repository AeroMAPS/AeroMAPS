"""
Shared colour system for the AeroMAPS CO2 lever-of-action plots.

Colour is assigned by the *role* the data plays, following the data-viz
literature (Brewer / ColorBrewer: nominal -> distinct hues, ordinal -> one hue
light->dark, polarity -> diverging with a neutral zero) and the
aviation-decarbonisation "wedge" conventions used by ATAG Waypoint 2050, IEA and
ICCT (technology/efficiency = blue, sustainable aviation fuels / energy = green,
market-based measures / offset = grey), together with the energy-system
fuel-origin convention (biomass = green, electricity / e-fuel = blue,
fossil = red, other = violet).

The hex values are the colour-vision-deficiency-validated data-viz reference
palette, so lever identity, market identity and the sequential sub-lever ramps
are all readable for colour-blind viewers and in print.

Channels
--------
* ``LEVER_COLORS``        -- one categorical hue per lever of action.
* ``LEVER_SEQUENTIAL_CMAP`` -- the single-hue ramp used to shade the *ordinal*
  sub-levers of a lever (e.g. fleet renewal -> each newer aircraft).
* ``ENERGY_ORIGIN_COLORMAPS`` -- fuel-origin ramps for the energy sub-levers.
* ``market_colors``       -- stable, validated categorical hue per market id.
* ``NEUTRAL``             -- residual / non-identity marks (cross-market mix).
"""

import matplotlib.pyplot as plt

# --- Lever identity (categorical, wedge-aligned) -------------------------------
LEVER_COLORS = {
    "demand": "#4a3aa7",  # violet  -- demand / supply side management
    "efficiency": "#2a78d6",  # blue    -- aircraft (and engine) technology
    "operations": "#1baf7a",  # aqua    -- fleet operations
    "loadfactor": "#5cc3a0",  # aqua, lighter -- load factor (operations family)
    "energy": "#008300",  # green   -- aircraft energy / SAF
    "offset": "#9a9a95",  # grey    -- carbon offset / market-based measures
}

# Colour of the merged "fleet operations and load factor" band (aggregate plot).
LEVER_OPERATIONS_LOADFACTOR = LEVER_COLORS["operations"]

# Neutral, non-identity marks: cross-market-mix residual, offsets.
NEUTRAL = "#9a9a95"

# --- Ordinal sub-levers: one hue ramp per lever --------------------------------
# Ordinal sub-levers (fleet renewal, then each newer aircraft ordered by entry
# into service) read as steps of the lever's own hue.
LEVER_SEQUENTIAL_CMAP = {
    "efficiency": plt.cm.Blues,
    "energy": plt.cm.Greens,
}

# --- Energy sub-levers: fuel-family convention ---------------------------------
# Energy sub-levers are grouped by *fuel family*, not by raw energy origin, so
# that hydrogen (used through hydrogen aircraft, a distinct technology) is never
# merged with drop-in electrofuels even though electrolytic hydrogen and
# electrofuels share the "electricity" origin. Hydrogen aircraft are often
# credited to the technology/efficiency side of decarbonisation scenarios, so
# hydrogen keeps its own family, label and colour.


def energy_family(aircraft_type, energy_origin):
    """Fuel family of a pathway.

    Drop-in fuels keep their energy origin (biomass / electricity / fossil);
    hydrogen and battery-electric carriers form their own families regardless of
    origin, so e-hydrogen is never lumped in with drop-in electrofuels.
    """
    if aircraft_type == "hydrogen":
        return "hydrogen"
    if aircraft_type == "electric":
        return "electric"
    return energy_origin


ENERGY_FAMILY_COLORMAPS = {
    "biomass": plt.cm.Greens,  # biofuels
    "electricity": plt.cm.Blues,  # drop-in electrofuels
    "fossil": plt.cm.Reds,  # fossil kerosene
    "hydrogen": plt.cm.RdPu,  # hydrogen aircraft (magenta: kept clear of the efuel blue)
    "electric": plt.cm.GnBu,  # battery-electric aircraft
}
ENERGY_FAMILY_FALLBACK_COLORMAP = plt.cm.Oranges

ENERGY_FAMILY_LABELS = {
    "biomass": "Biofuels",
    "electricity": "Electrofuels",
    "fossil": "Fossil-derived",
    "hydrogen": "Hydrogen",
    "electric": "Electric",
}

# --- Market identity (categorical, CVD-validated slots) ------------------------
# First four slots validate all-pairs in both light and dark surfaces; markets
# keep their colour across every panel of the per-market plot. Direct labels /
# the legend provide the secondary encoding the validator requires.
MARKET_PALETTE = (
    "#2a78d6",  # blue
    "#008300",  # green
    "#e87ba4",  # magenta
    "#eda100",  # yellow
    "#4a3aa7",  # violet
    "#e34948",  # red
    "#1baf7a",  # aqua
    "#eb6834",  # orange
)


def market_colors(market_ids):
    """Return a stable ``{market_id: hex}`` mapping.

    Colours are assigned in the given order and never cycled before the eighth
    market, so a market keeps its colour regardless of how many markets exist.
    """
    return {mid: MARKET_PALETTE[i % len(MARKET_PALETTE)] for i, mid in enumerate(market_ids)}
