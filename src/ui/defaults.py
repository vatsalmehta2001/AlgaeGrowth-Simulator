"""Default values, validation helpers, and climate override builder for the UI.

This module contains pure Python logic only -- no Streamlit imports -- making
it fully testable without a running Streamlit server.
"""

from src.models.parameters import CityClimate, ClimateParams, MonthlyClimate


# ---------------------------------------------------------------------------
# Default simulation parameter values (matching SimulationConfig / CONTEXT.md)
# ---------------------------------------------------------------------------

DEFAULT_SURFACE_AREA: float = 100.0
"""Default pond surface area [m2]. Typical Surat raceway."""

DEFAULT_DEPTH: float = 0.3
"""Default pond depth [m]. Typical raceway depth."""

DEFAULT_INITIAL_BIOMASS: float = 0.5
"""Default initial biomass concentration [g/L]. Typical inoculation density."""

DEFAULT_HARVEST_THRESHOLD: float = 2.0
"""Default harvest threshold [g/L]. Biomass concentration triggering harvest."""

DEFAULT_CO2_CONCENTRATION: float = 5.0
"""Default dissolved CO2 concentration [mg/L]. Continuous injection."""

DEFAULT_DURATION_DAYS: int = 365
"""Default simulation duration [days]."""

DEFAULT_START_MONTH: int = 1
"""Default starting month (January = 1)."""


# ---------------------------------------------------------------------------
# Duration presets for the sidebar dropdown
# ---------------------------------------------------------------------------

DURATION_PRESETS: dict[str, int | None] = {
    "Custom (days)": None,
    "1 month": 30,
    "3 months": 90,
    "6 months": 180,
    "1 year": 365,
}
"""Mapping from preset label to day count. None means user enters custom value."""


# ---------------------------------------------------------------------------
# Month names for the start-month dropdown
# ---------------------------------------------------------------------------

MONTH_NAMES: list[str] = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]
"""1-indexed month names (MONTH_NAMES[0] = January)."""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def collect_validation_errors(
    surface_area: float,
    depth: float,
    initial_biomass: float,
    co2_concentration: float,
) -> list[str]:
    """Collect hard validation errors that block simulation.

    Returns a list of human-readable error messages. An empty list means
    all inputs are valid and the Run button can be enabled.

    Args:
        surface_area: Pond surface area [m2].
        depth: Pond depth [m].
        initial_biomass: Initial biomass concentration [g/L].
        co2_concentration: Dissolved CO2 concentration [mg/L].

    Returns:
        List of error message strings (empty if all valid).
    """
    errors: list[str] = []
    if surface_area <= 0:
        errors.append("Surface area must be positive")
    if depth <= 0:
        errors.append("Depth must be positive")
    if initial_biomass <= 0:
        errors.append("Initial biomass must be positive")
    if co2_concentration < 0:
        errors.append("CO2 concentration cannot be negative")
    return errors


# ---------------------------------------------------------------------------
# Climate override builder
# ---------------------------------------------------------------------------

def build_overridden_climate(
    base_climate: CityClimate,
    temp_day: float,
    temp_night: float,
    par: float,
    photoperiod: float,
) -> CityClimate:
    """Build a CityClimate with uniform monthly values from user overrides.

    Creates 12 identical MonthlyClimate entries using the user's override
    values. Seasonal variation is removed (all months are "custom" season).
    City metadata and climate_params are preserved from the base profile.

    Args:
        base_climate: The original Surat climate profile to preserve metadata from.
        temp_day: User-specified daytime temperature [C].
        temp_night: User-specified nighttime temperature [C].
        par: User-specified PAR [umol/m2/s].
        photoperiod: User-specified photoperiod [hours].

    Returns:
        A new frozen CityClimate with 12 identical override months.
    """
    uniform_month = MonthlyClimate(
        season="custom",
        temp_day=temp_day,
        temp_night=temp_night,
        par=par,
        photoperiod=photoperiod,
        rainfall=0.0,
        cloud_cover_fraction=0.0,
    )
    return CityClimate(
        city=base_climate.city,
        country=base_climate.country,
        latitude=base_climate.latitude,
        longitude=base_climate.longitude,
        climate_params=base_climate.climate_params,
        months=tuple([uniform_month] * 12),
    )
