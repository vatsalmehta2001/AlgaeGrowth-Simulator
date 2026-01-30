from src.simulation.growth import (
    check_productivity_warnings,
    compute_areal_productivity,
    depth_averaged_growth_rate,
    monod_co2_response,
    specific_growth_rate,
    steele_light_response,
)
from src.simulation.light import beer_lambert, depth_averaged_irradiance

__all__ = [
    "beer_lambert",
    "check_productivity_warnings",
    "compute_areal_productivity",
    "depth_averaged_growth_rate",
    "depth_averaged_irradiance",
    "monod_co2_response",
    "run_simulation",
    "specific_growth_rate",
    "steele_light_response",
]


def __getattr__(name: str):
    """Lazy import for run_simulation to avoid circular dependency.

    engine.py imports from src.climate.growth_modifier which imports
    from src.simulation.growth -- creating a circular chain if engine
    is eagerly imported at package level.
    """
    if name == "run_simulation":
        from src.simulation.engine import run_simulation

        return run_simulation
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
