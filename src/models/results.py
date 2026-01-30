"""Simulation result dataclass for downstream consumption.

Uses tuple (not list) for all sequence fields to maintain hashability,
enabling Streamlit caching of complete simulation results.
"""

from dataclasses import dataclass

from src.models.parameters import SpeciesParams


@dataclass(frozen=True)
class SimulationResult:
    """Immutable container for a complete simulation run output.

    All sequence fields use tuple for hashability. The parameters_used
    field provides a full audit trail back to the input configuration.
    """

    time_days: tuple[float, ...]
    """Time points of the simulation [days]."""

    biomass_concentration: tuple[float, ...]
    """Biomass concentration at each time point [g/L]."""

    productivity_areal: tuple[float, ...]
    """Areal productivity at each time point [g/m2/day]."""

    co2_captured_cumulative: tuple[float, ...]
    """Cumulative CO2 captured per unit area at each time point [g/m2]."""

    warnings: tuple[str, ...]
    """Any warnings generated during the simulation
    (e.g., 'Productivity exceeds 10 g/m2/day — verify parameters')."""

    parameters_used: SpeciesParams
    """The species parameters used for this simulation run (audit trail)."""

    # -- Phase 3 additions: daily tracking --

    co2_captured_daily: tuple[float, ...]
    """Daily CO2 captured [kg]. One value per simulation day."""

    growth_rate_daily: tuple[float, ...]
    """Net daily specific growth rate [1/d]. One value per simulation day."""

    harvest_days: tuple[int, ...]
    """Day indices (0-based) on which harvest events occurred."""

    # -- Phase 3 additions: summary statistics --

    total_co2_captured_kg: float
    """Total CO2 captured over the simulation [kg]."""

    total_co2_captured_tco2e: float
    """Total CO2 captured [tonnes CO2 equivalent]. Equal to total_co2_captured_kg / 1000."""

    total_biomass_harvested_kg: float
    """Total biomass removed by harvest events [kg]."""

    harvest_count: int
    """Number of harvest events during the simulation."""

    avg_daily_productivity: float
    """Average daily areal productivity [g/m2/day] over the simulation."""

    duration_days: int
    """Simulation duration [days]."""

    start_month: int
    """Starting calendar month [1-12]."""

    # -- Phase 3 additions: seasonal breakdown --

    seasonal_co2: tuple[float, ...]
    """CO2 captured per season [kg]. Ordered: (dry, hot, monsoon)."""

    seasonal_productivity: tuple[float, ...]
    """Average daily productivity per season [g/m2/day]. Ordered: (dry, hot, monsoon)."""

    @property
    def peak_productivity(self) -> float:
        """Return the maximum areal productivity [g/m2/day] from this run."""
        if not self.productivity_areal:
            return 0.0
        return max(self.productivity_areal)
