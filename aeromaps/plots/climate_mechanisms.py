"""Shared grouping and palette for climate forcing mechanisms.

The climate module resolves twelve forcing mechanisms, which is well past the
number of hues a reader can hold apart. They are grouped here into five
families for plotting -- the four NOx terms sum to a single net NOx
contribution, and soot and sulfur to a single aerosol term -- leaving the full
twelve-way split to the tables.

This grouping is shared by the single-scenario and multi-scenario climate
plots so that a mechanism keeps the same name and the same colour wherever it
appears.
"""

# Family key -> (display label, list of mechanism names used in column names)
MECHANISM_GROUPS = {
    "co2": ("CO$_2$", ["co2"]),
    "contrails": ("Contrails", ["contrails"]),
    "nox": (
        "NO$_x$ (net)",
        [
            "nox_short_term_o3_increase",
            "nox_long_term_o3_decrease",
            "nox_ch4_decrease",
            "nox_stratospheric_water_vapor_decrease",
        ],
    ),
    "h2o": ("H$_2$O", ["h2o"]),
    "aerosol": ("Aerosols (soot + sulfur)", ["soot", "sulfur"]),
}

# Categorical slots 1-5 of the reference palette, assigned in fixed order.
# Never cycled: a sixth family would be folded into an existing one rather than
# given a new hue.
MECHANISM_COLORS = {
    "co2": "#2a78d6",
    "contrails": "#eb6834",
    "nox": "#1baf7a",
    "h2o": "#eda100",
    "aerosol": "#e87ba4",
}

TOTAL_COLOR = "#0b0b0b"

# Contrail avoidance is switched off in every ATAG configuration
# (operations_contrails_start_year = 2101), matching the reports' own scope.
CONTRAIL_DISABLED_NOTE = (
    "Contrail avoidance is disabled in all scenarios "
    "(operations_contrails_start_year = 2101), matching the reports' scope."
)


def temperature_columns(group):
    """Climate-output column names carrying the temperature of one family."""
    return [f"temperature_increase_from_{m}_from_aviation" for m in MECHANISM_GROUPS[group][1]]


def erf_columns(group):
    """Climate-output column names carrying the ERF of one family."""
    return [f"{m}_erf" for m in MECHANISM_GROUPS[group][1]]


def all_temperature_columns():
    """Every temperature column the five families need, deduplicated."""
    return [column for group in MECHANISM_GROUPS for column in temperature_columns(group)]


def all_erf_columns():
    """Every ERF column the five families need, deduplicated."""
    return [column for group in MECHANISM_GROUPS for column in erf_columns(group)]


def group_temperature(df_climate, years, group):
    """Aviation-attributable temperature for one mechanism family [K]."""
    return df_climate.loc[years, temperature_columns(group)].sum(axis=1)


def group_erf(df_climate, years, group):
    """Effective radiative forcing for one mechanism family [W/m2]."""
    return df_climate.loc[years, erf_columns(group)].sum(axis=1)
