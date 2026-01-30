"""Day-by-day Euler simulation engine with harvest cycling and CO2 accounting.

Orchestrates Phase 1 growth equations and Phase 2 climate integration into
a complete time-stepping simulation. Takes frozen configuration dataclasses
and returns a frozen SimulationResult with daily time-series, harvest
tracking, and seasonal CO2 breakdown.

The engine is a pure function: no side effects, no state mutation, no
file I/O. All inputs are immutable dataclasses; the output is an
immutable dataclass. This enables deterministic results and safe
Streamlit caching.

Simulation loop:
    For each day d in [0, duration_days):
        1. Look up monthly climate for this calendar day
        2. Compute net daily growth rate via daily_growth_rate() (Phase 2)
        3. Euler step: X(d+1) = X(d) + mu_net * X(d) * dt  (dt = 1 day)
        4. Guard: biomass >= 0 (prevent negative from numerical edge cases)
        5. Harvest check: if biomass >= threshold, reset to initial and
           accumulate harvested mass

CO2 accounting:
    Daily CO2 = mu_net * X * V * co2_to_biomass_ratio / 1000  [kg]
    Only positive growth days contribute (mu_net > 0).
    Total CO2 = sum of daily CO2.
    tCO2e = total_co2_kg / 1000.

References:
    PMC8238767: Forward Euler validated for daily microalgae stepping.
    Schediwy et al. (2019): CO2/biomass ratio = 1.83 (species_params.yaml).
    Phase 1 growth.py: Monod + Steele growth model.
    Phase 2 growth_modifier.py: CTMI temperature + photoperiod integration.
"""

import calendar

from src.climate.growth_modifier import daily_growth_rate
from src.models.parameters import CityClimate, SimulationConfig, SpeciesParams
from src.models.results import SimulationResult
from src.simulation.growth import check_productivity_warnings


def _build_day_to_month_map(
    start_month: int, duration_days: int
) -> tuple[int, ...]:
    """Map each simulation day (0-based) to a month index (0-11).

    Walks through calendar months from start_month (1-based), using
    calendar.monthrange(2023, month) for days per month (non-leap year).
    Handles year wrapping: December (12) -> January (1).

    Args:
        start_month: Starting calendar month [1-12]. January=1, December=12.
        duration_days: Total number of simulation days.

    Returns:
        Tuple of length duration_days where each element is a month index
        (0 for January, 11 for December) for CityClimate.months lookup.
    """
    day_to_month: list[int] = []
    month = start_month  # 1-based (1=Jan, 12=Dec)
    day_in_month = 0
    days_in_current = calendar.monthrange(2023, month)[1]  # non-leap year

    for _ in range(duration_days):
        day_to_month.append(month - 1)  # convert to 0-indexed
        day_in_month += 1
        if day_in_month >= days_in_current:
            day_in_month = 0
            month = (month % 12) + 1
            days_in_current = calendar.monthrange(2023, month)[1]

    return tuple(day_to_month)


def run_simulation(
    config: SimulationConfig,
    species: SpeciesParams,
    climate: CityClimate,
) -> SimulationResult:
    """Run a day-by-day Euler simulation with harvest cycling and CO2 accounting.

    Pure function: takes frozen config dataclasses, returns frozen
    SimulationResult. No side effects, no state mutation.

    Args:
        config: User-configurable simulation parameters (duration, harvest
                threshold, CO2 concentration, pond geometry).
        species: Species kinetic parameters including co2_to_biomass_ratio.
        climate: City climate profile with 12 months of climate data.

    Returns:
        Frozen SimulationResult with daily time-series (biomass, growth
        rate, CO2, productivity), harvest tracking, and seasonal breakdown.
    """
    # --- Initialize tracking ---
    biomass = config.initial_biomass
    total_harvested_biomass_g = 0.0
    harvest_count = 0
    harvest_days_list: list[int] = []

    # Daily tracking lists
    time_days_list: list[float] = []
    biomass_daily: list[float] = []
    growth_rate_daily: list[float] = []
    co2_daily: list[float] = []
    productivity_daily: list[float] = []
    all_warnings: list[str] = []

    # --- Pre-compute helpers ---
    day_to_month = _build_day_to_month_map(
        config.start_month, config.duration_days
    )
    volume_liters = config.surface_area * config.depth * 1000.0  # m3 -> L

    # --- Main Euler loop ---
    for day in range(config.duration_days):
        month = climate.months[day_to_month[day]]

        # Step 1: Compute net daily growth rate (Phase 2 integration)
        mu_net = daily_growth_rate(
            daytime_temp=month.temp_day,
            nighttime_temp=month.temp_night,
            par=month.par,
            photoperiod=month.photoperiod,
            co2=config.co2_concentration,
            biomass_conc=biomass,
            depth=config.depth,
            growth_params=species.growth,
            light_params=species.light,
            climate_params=climate.climate_params,
        )

        # Step 2: Record daily values BEFORE Euler step
        # Areal productivity: mu * X * D * 1000 [g/m2/day]
        daily_areal_productivity = mu_net * biomass * config.depth * 1000.0

        # Daily CO2 capture: only from positive net growth
        if mu_net > 0.0:
            daily_co2_kg = (
                mu_net
                * biomass
                * volume_liters
                * species.co2_to_biomass_ratio
                / 1000.0  # g -> kg
            )
        else:
            daily_co2_kg = 0.0

        # Step 3: Euler step (dt = 1 day)
        biomass_new = biomass + mu_net * biomass * 1.0

        # Step 4: Guard against negative biomass
        biomass_new = max(biomass_new, 0.0)

        # Step 5: Harvest check
        if biomass_new >= config.harvest_threshold:
            harvested_g = (biomass_new - config.initial_biomass) * volume_liters
            total_harvested_biomass_g += harvested_g
            biomass_new = config.initial_biomass
            harvest_count += 1
            harvest_days_list.append(day)

        # Step 6: Record daily values
        time_days_list.append(float(day))
        biomass_daily.append(biomass_new)
        growth_rate_daily.append(mu_net)
        co2_daily.append(daily_co2_kg)
        productivity_daily.append(daily_areal_productivity)

        # Step 7: Check productivity warnings
        warnings = check_productivity_warnings(daily_areal_productivity)
        all_warnings.extend(warnings)

        # Step 8: Advance biomass for next day
        biomass = biomass_new

    # --- Post-loop summary statistics ---

    total_co2_kg = sum(co2_daily)
    total_co2_tco2e = total_co2_kg / 1000.0
    total_biomass_harvested_kg = total_harvested_biomass_g / 1000.0

    avg_productivity = (
        sum(productivity_daily) / len(productivity_daily)
        if productivity_daily
        else 0.0
    )

    # --- Cumulative CO2 array (g/m2 for backward compatibility) ---
    co2_cumulative: list[float] = []
    running_co2 = 0.0
    for daily_kg in co2_daily:
        # Convert kg total to g/m2: (kg * 1000 g/kg) / surface_area m2
        running_co2 += daily_kg * 1000.0 / config.surface_area
        co2_cumulative.append(running_co2)

    # --- Seasonal breakdown ---
    season_order = ("dry", "hot", "monsoon")
    co2_per_season: dict[str, float] = {s: 0.0 for s in season_order}
    productivity_per_season: dict[str, list[float]] = {
        s: [] for s in season_order
    }

    for day in range(config.duration_days):
        season = climate.months[day_to_month[day]].season
        co2_per_season[season] += co2_daily[day]
        productivity_per_season[season].append(productivity_daily[day])

    seasonal_co2 = tuple(co2_per_season[s] for s in season_order)
    seasonal_productivity = tuple(
        (
            sum(productivity_per_season[s]) / len(productivity_per_season[s])
            if productivity_per_season[s]
            else 0.0
        )
        for s in season_order
    )

    # --- Deduplicate warnings ---
    unique_warnings = tuple(sorted(set(all_warnings)))

    # --- Build and return frozen result ---
    return SimulationResult(
        time_days=tuple(time_days_list),
        biomass_concentration=tuple(biomass_daily),
        productivity_areal=tuple(productivity_daily),
        co2_captured_cumulative=tuple(co2_cumulative),
        warnings=unique_warnings,
        parameters_used=species,
        co2_captured_daily=tuple(co2_daily),
        growth_rate_daily=tuple(growth_rate_daily),
        harvest_days=tuple(harvest_days_list),
        total_co2_captured_kg=total_co2_kg,
        total_co2_captured_tco2e=total_co2_tco2e,
        total_biomass_harvested_kg=total_biomass_harvested_kg,
        harvest_count=harvest_count,
        avg_daily_productivity=avg_productivity,
        duration_days=config.duration_days,
        start_month=config.start_month,
        seasonal_co2=seasonal_co2,
        seasonal_productivity=seasonal_productivity,
    )
