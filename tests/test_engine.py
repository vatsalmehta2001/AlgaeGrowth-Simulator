"""Unit tests for the simulation engine (run_simulation).

Tests cover basic execution, harvest mechanics, CO2 accounting,
seasonal breakdown, and edge cases. Uses real Chlorella vulgaris
species parameters and Surat climate data.

TDD RED phase: all tests fail because run_simulation() and the
expanded SimulationResult fields do not yet exist.
"""

import dataclasses

import pytest

from src.climate.loader import load_city_climate
from src.config.loader import load_species_params
from src.models.parameters import SimulationConfig
from src.models.results import SimulationResult
from src.simulation.engine import run_simulation


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def species():
    """Load real Chlorella vulgaris species parameters."""
    return load_species_params()


@pytest.fixture
def climate():
    """Load real Surat climate profile."""
    return load_city_climate()


@pytest.fixture
def default_config():
    """Standard 365-day simulation starting in January."""
    return SimulationConfig(
        duration_days=365,
        start_month=1,
        initial_biomass=0.5,
        harvest_threshold=2.0,
        co2_concentration=5.0,
        depth=0.3,
        surface_area=100.0,
    )


@pytest.fixture
def short_config():
    """Short 30-day simulation for quick tests."""
    return SimulationConfig(
        duration_days=30,
        start_month=1,
        initial_biomass=0.5,
        harvest_threshold=2.0,
        co2_concentration=5.0,
        depth=0.3,
        surface_area=100.0,
    )


# ---------------------------------------------------------------------------
# TestSimulationBasicExecution
# ---------------------------------------------------------------------------


class TestSimulationBasicExecution:
    """Verify that run_simulation returns correct types and dimensions."""

    def test_returns_simulation_result(self, short_config, species, climate):
        """run_simulation() returns a SimulationResult instance."""
        result = run_simulation(short_config, species, climate)
        assert isinstance(result, SimulationResult)

    def test_result_is_frozen(self, short_config, species, climate):
        """SimulationResult is immutable (frozen dataclass)."""
        result = run_simulation(short_config, species, climate)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.duration_days = 999  # type: ignore[misc]

    def test_time_series_length_matches_duration(
        self, short_config, species, climate
    ):
        """Time series length equals configured duration_days."""
        result = run_simulation(short_config, species, climate)
        assert len(result.time_days) == 30
        assert len(result.biomass_concentration) == 30
        assert len(result.co2_captured_daily) == 30
        assert len(result.growth_rate_daily) == 30

    def test_biomass_starts_at_initial(self, short_config, species, climate):
        """First biomass value approximately equals initial_biomass.

        The first recorded value is after day 0's Euler step, so it may
        differ slightly from initial_biomass due to growth. We check that
        it is within a reasonable range (not wildly off).
        """
        result = run_simulation(short_config, species, climate)
        # Day 0 starts at 0.5 g/L; after one Euler step it should be close
        assert result.biomass_concentration[0] == pytest.approx(
            short_config.initial_biomass, abs=0.1
        )


# ---------------------------------------------------------------------------
# TestHarvestMechanics
# ---------------------------------------------------------------------------


class TestHarvestMechanics:
    """Verify harvest events reset biomass and accumulate harvested mass."""

    def test_harvest_resets_to_initial_biomass(
        self, default_config, species, climate
    ):
        """After harvest, biomass resets to initial_biomass.

        Over a full year with Surat climate, at least one harvest should
        occur. On any harvest day, the recorded biomass should be near
        initial_biomass (post-reset).
        """
        result = run_simulation(default_config, species, climate)
        assert result.harvest_count >= 1
        # On harvest days, the recorded biomass should be initial_biomass
        for day_idx in result.harvest_days:
            assert result.biomass_concentration[day_idx] == pytest.approx(
                default_config.initial_biomass, abs=1e-9
            )

    def test_harvest_days_tracked(self, default_config, species, climate):
        """harvest_days is a tuple of ints with length == harvest_count."""
        result = run_simulation(default_config, species, climate)
        assert isinstance(result.harvest_days, tuple)
        if result.harvest_count > 0:
            assert len(result.harvest_days) == result.harvest_count
            # All entries should be valid day indices
            for day_idx in result.harvest_days:
                assert 0 <= day_idx < default_config.duration_days

    def test_total_harvested_biomass_positive(
        self, default_config, species, climate
    ):
        """Total harvested biomass is positive for a full-year simulation."""
        result = run_simulation(default_config, species, climate)
        assert result.total_biomass_harvested_kg > 0.0


# ---------------------------------------------------------------------------
# TestCO2Accounting
# ---------------------------------------------------------------------------


class TestCO2Accounting:
    """Verify CO2 capture calculations use species conversion factor."""

    def test_co2_uses_species_conversion_factor(
        self, default_config, species, climate
    ):
        """CO2 is computed using species.co2_to_biomass_ratio (1.83).

        Total CO2 captured should be positive for a full year.
        """
        result = run_simulation(default_config, species, climate)
        assert result.total_co2_captured_kg > 0.0

    def test_co2_tco2e_is_kg_divided_by_1000(
        self, default_config, species, climate
    ):
        """tCO2e is simply total_co2_captured_kg / 1000."""
        result = run_simulation(default_config, species, climate)
        assert result.total_co2_captured_tco2e == pytest.approx(
            result.total_co2_captured_kg / 1000.0
        )

    def test_daily_co2_sums_to_total(self, default_config, species, climate):
        """Sum of daily CO2 captured equals total_co2_captured_kg."""
        result = run_simulation(default_config, species, climate)
        assert sum(result.co2_captured_daily) == pytest.approx(
            result.total_co2_captured_kg, rel=1e-9
        )


# ---------------------------------------------------------------------------
# TestSeasonalBreakdown
# ---------------------------------------------------------------------------


class TestSeasonalBreakdown:
    """Verify seasonal CO2 and productivity breakdown."""

    def test_seasonal_co2_sums_to_total(
        self, default_config, species, climate
    ):
        """Sum of seasonal CO2 equals total for a full year starting Jan."""
        result = run_simulation(default_config, species, climate)
        assert sum(result.seasonal_co2) == pytest.approx(
            result.total_co2_captured_kg, rel=1e-6
        )

    def test_seasonal_productivity_tuple_length(
        self, default_config, species, climate
    ):
        """Seasonal productivity has 3 entries: dry, hot, monsoon."""
        result = run_simulation(default_config, species, climate)
        assert len(result.seasonal_productivity) == 3
        assert len(result.seasonal_co2) == 3


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge case handling for extreme configurations."""

    def test_one_day_simulation(self, species, climate):
        """A 1-day simulation produces valid results."""
        config = SimulationConfig(
            duration_days=1,
            start_month=7,
            initial_biomass=0.5,
            harvest_threshold=2.0,
            co2_concentration=5.0,
            depth=0.3,
            surface_area=100.0,
        )
        result = run_simulation(config, species, climate)
        assert len(result.time_days) == 1
        assert len(result.biomass_concentration) == 1
        assert result.duration_days == 1

    def test_biomass_never_negative(self, default_config, species, climate):
        """Biomass concentration never drops below zero."""
        result = run_simulation(default_config, species, climate)
        assert all(b >= 0 for b in result.biomass_concentration)
