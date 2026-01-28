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

    @property
    def peak_productivity(self) -> float:
        """Return the maximum areal productivity [g/m2/day] from this run."""
        if not self.productivity_areal:
            return 0.0
        return max(self.productivity_areal)
