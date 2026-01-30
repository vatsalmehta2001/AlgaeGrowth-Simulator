"""Daily growth rate integrating temperature response with Phase 1 growth model.

Computes net daily growth by combining daytime photosynthetic growth
(temperature-modified via CTMI) with nighttime respiration loss
(temperature-modified), weighted by photoperiod. This is the integration
layer that ties Phase 2 climate data and temperature response together
with Phase 1's depth-averaged growth model.

The day/night split is critical for Surat, India, where pre-monsoon
daytime highs reach 37 C (heavily inhibiting growth via CTMI) while
nighttime lows of 24-27 C have moderate respiration. Using a single
daily average (~30 C) would mask this dynamic and underestimate the
daytime growth penalty.

Design principle: Phase 1 growth functions are NOT modified. Temperature
is composed externally via multiplicative application of the CTMI modifier
to Phase 1's depth_averaged_growth_rate output.

References:
    Edmundson & Huesemann (2015): Day/night biomass loss characterization.
        Night losses of 10-35% of daytime production are species- and
        temperature-dependent.
    Rosso et al. (1993): CTMI temperature response (via temperature.py).
    Steele (1962): Photoinhibition model (via growth.py, Phase 1).
"""

from src.climate.temperature import temperature_response
from src.models.parameters import ClimateParams, GrowthParams, LightParams
from src.simulation.growth import depth_averaged_growth_rate


def daily_growth_rate(
    daytime_temp: float,
    nighttime_temp: float,
    par: float,
    photoperiod: float,
    co2: float,
    biomass_conc: float,
    depth: float,
    growth_params: GrowthParams,
    light_params: LightParams,
    climate_params: ClimateParams,
) -> float:
    """Compute net daily growth rate with day/night temperature split.

    Integrates Phase 1's depth-averaged growth model with Phase 2's CTMI
    temperature response. Daytime growth is the base growth rate scaled by
    the daytime temperature modifier. Nighttime respiration loss is the
    maintenance rate scaled by the nighttime temperature modifier. Both
    are weighted by the photoperiod fraction.

    Net daily growth:
        mu_net = mu_day * f_temp_day * (photoperiod / 24)
                 - r_maintenance * f_temp_night * ((24 - photoperiod) / 24)

    Clamped to >= 0 (biomass cannot go negative from this function).

    Args:
        daytime_temp: Average daytime high temperature [C].
        nighttime_temp: Average nighttime low temperature [C].
        par: Average daytime photosynthetically active radiation [umol/m2/s].
        photoperiod: Hours of daylight [h]. Range [0, 24].
        co2: Dissolved CO2 concentration [mg/L].
        biomass_conc: Biomass concentration [g/L].
        depth: Pond depth [m].
        growth_params: Phase 1 Monod growth kinetics parameters.
        light_params: Phase 1 Beer-Lambert light attenuation parameters.
        climate_params: Cardinal temperature parameters (T_min, T_opt, T_max).

    Returns:
        Net daily specific growth rate [1/d], always >= 0.

    References:
        Edmundson & Huesemann (2015): Day/night split approach.
        Rosso et al. (1993): CTMI temperature modifier.
        Phase 1 growth.py: depth_averaged_growth_rate (base growth).
    """
    # Edge case: no daylight means no photosynthesis, no net growth
    if photoperiod <= 0.0:
        return 0.0

    # --- Daytime growth (photosynthesis + temperature modifier) ---

    # Step 1: Daytime temperature modifier via CTMI
    f_temp_day = temperature_response(
        daytime_temp, climate_params.T_min, climate_params.T_opt, climate_params.T_max
    )

    # Step 2: Base growth rate from Phase 1 (depth-averaged, no temperature)
    mu_base = depth_averaged_growth_rate(
        par, co2, biomass_conc, depth, growth_params, light_params
    )

    # Step 3: Apply temperature modifier to daytime growth
    mu_day = mu_base * f_temp_day

    # --- Nighttime respiration loss (temperature-dependent) ---

    # Step 4: Nighttime temperature modifier via CTMI
    f_temp_night = temperature_response(
        nighttime_temp,
        climate_params.T_min,
        climate_params.T_opt,
        climate_params.T_max,
    )

    # Step 5: Nighttime respiration scaled by temperature
    r_night = growth_params.r_maintenance * f_temp_night

    # --- Photoperiod weighting ---

    # Step 6: Day/night fractions
    day_fraction = min(photoperiod, 24.0) / 24.0
    night_fraction = 1.0 - day_fraction

    # Step 7: Net daily growth
    mu_net = mu_day * day_fraction - r_night * night_fraction

    # Step 8: Clamp to non-negative
    return max(mu_net, 0.0)
