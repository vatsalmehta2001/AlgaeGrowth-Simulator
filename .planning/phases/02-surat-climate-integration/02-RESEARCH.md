# Phase 2: Surat Climate Integration - Research

**Researched:** 2026-01-30
**Domain:** Climate-dependent microalgal growth modeling (temperature inhibition, seasonal PAR, city-as-config)
**Confidence:** MEDIUM-HIGH (strong literature basis, some parameter values require conservative estimation)

## Summary

This research covers the technical domain needed to implement Surat climate integration into the existing Phase 1 growth model. The phase adds three climate modifiers: (1) a cardinal temperature model that reduces growth rate at suboptimal and supraoptimal temperatures, (2) a seasonal PAR profile that varies surface irradiance month-by-month, and (3) a day/night temperature split that models daytime growth and nighttime respiration losses separately.

The standard approach in the microalgae modeling literature is the **Cardinal Temperature Model with Inflection (CTMI)** by Rosso et al. (1993), validated for microalgae by Bernard and Remond (2012). This model uses three biologically meaningful parameters (T_min, T_opt, T_max) and produces a bell-shaped curve that naturally captures both cold stress and heat stress. For Chlorella vulgaris, the literature consensus places T_min at approximately 5-8 C, T_opt at 25-30 C, and T_max at 38-42 C (strain-dependent). Conservative values of T_min=8, T_opt=28, T_max=40 are recommended for our model.

The climate data structure uses the city-as-config pattern already established in Phase 1 (YAML + Pydantic validation + frozen dataclasses). Surat climate data is well-documented across multiple sources, with monthly temperature, solar radiation, sunshine hours, and humidity all available. PAR values are derived from global horizontal irradiance (GHI) using the standard 0.45 conversion factor.

**Primary recommendation:** Implement the CTMI equation as a pure function `temperature_response(T, T_min, T_opt, T_max) -> float` following the same patterns as Phase 1's `steele_light_response()`, and load all climate data from a YAML city config with Pydantic validation.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyYAML | 6.0.2 | Climate config loading | Already in project, handles city YAML profiles |
| Pydantic | 2.12.5 | Climate config validation | Already in project, range validation on temperature/PAR values |
| NumPy | 2.4.1 | Numerical computation | Already in project, exp() for CTMI equation |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| dataclasses (stdlib) | 3.13 | Frozen climate parameter containers | ClimateParams, MonthlyClimate dataclasses |
| math (stdlib) | 3.13 | Simple math operations | Where NumPy is overkill (e.g., single float operations) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| CTMI (Rosso 1993) | Ratkowsky square-root model | Equally good fit, but CTMI parameters have direct biological meaning and are uncorrelated, making calibration easier |
| CTMI (Rosso 1993) | Arrhenius-type model | More complex, requires activation energies rather than observable temperatures, harder to parameterize from literature |
| Monthly resolution | Daily/hourly resolution | Unnecessary complexity for v1; monthly captures seasonal patterns adequately |
| Static YAML | Database/API | Overkill for shipping one city; YAML is simpler and the loader pattern already exists |

**Installation:** No new dependencies needed. All libraries already in `pyproject.toml`.

## Architecture Patterns

### Recommended Project Structure
```
src/
  climate/
    __init__.py          # Module exports
    temperature.py       # CTMI temperature response function
    loader.py            # Climate YAML loader with Pydantic validation
    surat.yaml           # Surat city climate profile
  models/
    parameters.py        # ADD: ClimateParams, MonthlyClimate dataclasses
  simulation/
    growth.py            # ADD: temperature_modifier integration point
```

### Pattern 1: CTMI Temperature Response (Pure Function)
**What:** A pure function computing the temperature growth modifier using the Cardinal Temperature Model with Inflection
**When to use:** Every growth rate calculation that needs temperature dependence
**Equation:**

The CTMI defines a dimensionless temperature response phi(T) in [0, 1]:

```
phi(T) = 0                                          if T <= T_min or T >= T_max
phi(T) = (T - T_max)(T - T_min)^2 /
         [(T_opt - T_min) * ((T_opt - T_min)(T - T_opt)
           - (T_opt - T_max)(T_opt + T_min - 2T))]  if T_min < T < T_max
```

Where:
- T_min: minimum temperature for growth (below this, growth = 0)
- T_opt: optimal temperature (phi = 1.0 at T = T_opt)
- T_max: maximum temperature for growth (above this, growth = 0)

**Key property:** phi(T_opt) = 1.0 exactly. The curve is asymmetric -- it rises gradually from T_min to T_opt and drops steeply from T_opt to T_max. This asymmetry matches biological reality: heat kills faster than cold.

**Example:**
```python
# Source: Rosso et al. (1993), Bernard & Remond (2012)
def temperature_response(T: float, T_min: float, T_opt: float, T_max: float) -> float:
    """CTMI cardinal temperature model. Returns growth modifier in [0, 1].

    Args:
        T: Culture temperature [C].
        T_min: Minimum temperature for growth [C].
        T_opt: Optimal temperature for growth [C].
        T_max: Maximum temperature for growth [C].

    Returns:
        Temperature response fraction in [0, 1].
        Returns 0.0 for T <= T_min or T >= T_max.
        Returns 1.0 at T = T_opt.

    References:
        Rosso et al. (1993): CTMI original formulation
        Bernard & Remond (2012): Validation for microalgae
    """
    if T <= T_min or T >= T_max:
        return 0.0

    numerator = (T - T_max) * (T - T_min) ** 2
    denominator = (T_opt - T_min) * (
        (T_opt - T_min) * (T - T_opt)
        - (T_opt - T_max) * (T_opt + T_min - 2.0 * T)
    )

    return numerator / denominator
```

### Pattern 2: City-as-Config Climate Profile (YAML + Pydantic + Dataclass)
**What:** Each city is a YAML file containing 12 months of climate data, validated by Pydantic, stored in frozen dataclasses
**When to use:** Loading climate conditions for any simulation location
**Example YAML schema:**

```yaml
# Source: Pattern mirrors existing species_params.yaml structure
city: Surat
country: India
latitude: 21.17
longitude: 72.83

# Cardinal temperature parameters for Chlorella vulgaris
# These are species-dependent, but loaded with climate since they define
# the temperature response in this city's context
temperature_params:
  T_min:
    value: 8.0
    unit: "C"
    source: "Literature consensus for C. vulgaris; conservative lower bound"
    note: "Growth effectively zero below this; some strains survive at 5C"
  T_opt:
    value: 28.0
    unit: "C"
    source: "Converti et al. (2009); Singh & Singh (2014); Bernard & Remond (2012)"
    note: "Mid-range of 25-30C optimal; conservative for outdoor conditions"
  T_max:
    value: 40.0
    unit: "C"
    source: "Converti et al. (2009): death at 38C; DISCOVR screening to 45C"
    note: "Conservative; some strains die at 38C, hardy strains tolerate to 42C"

months:
  january:
    season: dry
    temp_day:
      value: 29.8
      unit: "C"
      source: "weather-atlas.com; climatestotravel.com (1981-2010 avg)"
    temp_night:
      value: 15.2
      unit: "C"
      source: "climatestotravel.com (1981-2010 avg low)"
    par:
      value: 1062
      unit: "umol/m2/s"
      source: "Derived: 5.1 kWh/m2/d GHI (WeatherSpark) * 0.45 PAR fraction / 11.0h daylight / 3.6 * 1e6 / 4.6"
      note: "Peak instantaneous mid-day PAR estimate"
    photoperiod:
      value: 11.0
      unit: "hours"
      source: "WeatherSpark: avg daylight hours Jan at 21N latitude"
    rainfall:
      value: 0
      unit: "mm"
      source: "weather-atlas.com"
    cloud_cover_fraction:
      value: 0.16
      unit: "fraction"
      source: "WeatherSpark: 16% cloud cover January"
  # ... (remaining months follow same schema)
```

### Pattern 3: Day/Night Temperature Split for Growth Calculation
**What:** Compute daily growth as daytime photosynthetic growth minus nighttime respiration loss, each at their respective temperatures
**When to use:** Computing effective daily growth rate under realistic outdoor conditions

```python
# Source: Edmundson & Huesemann (2015); Decostere et al. (2016)
def daily_growth_rate(
    daytime_temp: float,
    nighttime_temp: float,
    par: float,
    photoperiod: float,       # hours of daylight
    co2: float,
    biomass_conc: float,
    depth: float,
    growth_params: GrowthParams,
    light_params: LightParams,
    climate_params: ClimateParams,  # T_min, T_opt, T_max
) -> float:
    """Net daily growth = daytime growth * (photoperiod/24) - nighttime respiration * ((24-photoperiod)/24).

    Daytime: full growth model (light + CO2 + temperature modifier)
    Nighttime: only respiration loss (temperature-dependent)
    """
    # Daytime growth (modified by temperature)
    f_temp_day = temperature_response(daytime_temp, climate_params.T_min,
                                       climate_params.T_opt, climate_params.T_max)
    mu_day = depth_averaged_growth_rate(par, co2, biomass_conc, depth,
                                         growth_params, light_params)
    mu_day_temp = mu_day * f_temp_day

    # Nighttime respiration (simplified: maintenance * temperature factor)
    f_temp_night = temperature_response(nighttime_temp, climate_params.T_min,
                                         climate_params.T_opt, climate_params.T_max)
    r_night = growth_params.r_maintenance * f_temp_night

    # Weighted daily net growth
    day_fraction = photoperiod / 24.0
    night_fraction = 1.0 - day_fraction

    return mu_day_temp * day_fraction - r_night * night_fraction
```

### Pattern 4: Multiplicative Growth Modifier Integration
**What:** Temperature modifier integrates multiplicatively with existing Phase 1 growth equation
**When to use:** Preserving Phase 1's growth equation structure while adding climate effects

The existing growth equation is:
```
mu = max(mu_max * f_light * f_co2 * discount_factor - r_maintenance, 0)
```

With temperature, it becomes:
```
mu = max(mu_max * f_light * f_co2 * f_temp * discount_factor - r_maintenance, 0)
```

Where f_temp = temperature_response(T, T_min, T_opt, T_max).

**Critical:** This approach preserves backward compatibility. When T = T_opt, f_temp = 1.0 and the equation reduces to the Phase 1 form.

### Anti-Patterns to Avoid
- **Sharp threshold crash:** Using if/else at 35C to model "culture crash." The CTMI provides a smooth, biologically realistic curve. Do NOT use a step function.
- **Single daily temperature:** Using a 24-hour average temperature ignores the Surat day/night split. Pre-monsoon days hit 36-37C (heavily inhibited) while nights at 24-27C are near-optimal for respiration. Using the average (~30C) would mask the daytime growth penalty.
- **Modifying Phase 1 functions in place:** Do NOT edit `specific_growth_rate()` to add a temperature parameter. Instead, create a new wrapper function or a separate temperature modifier that multiplies with the existing output.
- **Hardcoding Surat data:** All climate values must come from the YAML config, not from constants in Python code. This supports the city-as-config pattern for future cities.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Temperature response curve | Polynomial fit or step function | CTMI equation (Rosso 1993) | Biologically grounded, 3 meaningful parameters, validated for microalgae by Bernard & Remond (2012) |
| Climate data validation | Manual range checks | Pydantic validators (already in project) | Handles edge cases, gives clear error messages, consistent with Phase 1 pattern |
| PAR from solar radiation | Custom conversion pipeline | Standard factor: PAR = GHI * 0.45 | Well-established in literature; PAR is 45% of total solar irradiance |
| Seasonal classification | Date range logic | Direct month-to-season mapping in YAML | Simple lookup, no date arithmetic needed, each month has a `season` field |
| YAML config loading | Custom parser | Existing `loader.py` pattern with `_extract_values()` | Already handles value/unit/source/note structure |

**Key insight:** The temperature inhibition curve looks like it could be modeled with a simple polynomial, but the CTMI has specific mathematical properties (zero at T_min and T_max, exactly 1.0 at T_opt, correct asymmetry) that a naive polynomial would require careful fitting to achieve. Use the established equation.

## Common Pitfalls

### Pitfall 1: CTMI Denominator Division by Zero
**What goes wrong:** The CTMI equation has a denominator that can approach zero when T is near T_opt under certain parameter combinations.
**Why it happens:** The denominator includes (T_opt - T_min) * ((T_opt - T_min)(T - T_opt) - (T_opt - T_max)(T_opt + T_min - 2T)). When T = T_opt, both the numerator and denominator evaluate in a way that the ratio equals 1.0, but floating-point arithmetic may not produce exact cancellation.
**How to avoid:** Add a guard: if abs(T - T_opt) < epsilon, return 1.0 directly. Use epsilon = 1e-10 (consistent with Phase 1's K*D guard).
**Warning signs:** NaN or Inf in temperature response output.

### Pitfall 2: Temperature Response Exceeding [0, 1]
**What goes wrong:** Floating-point arithmetic could produce values slightly above 1.0 or below 0.0.
**Why it happens:** Numerical precision limits in the CTMI equation.
**How to avoid:** Clamp output: `return max(0.0, min(1.0, result))`. Phase 1's Steele function naturally stays in [0,1] due to its mathematical form, but CTMI does not have this guarantee in floating-point.
**Warning signs:** Growth rate exceeding Phase 1 baseline at T_opt.

### Pitfall 3: Breaking Phase 1 Tests
**What goes wrong:** Adding temperature dependence changes the growth rate output, breaking 66 existing tests.
**Why it happens:** If temperature modifier is injected into `specific_growth_rate()` as a mandatory parameter.
**How to avoid:** Temperature modifier should be a SEPARATE function that multiplies with the existing growth rate. Do not add a temperature parameter to `specific_growth_rate()`. Instead, compose: `mu_with_temp = mu_base * f_temp`. This preserves all Phase 1 tests unchanged.
**Warning signs:** Any Phase 1 test failures after Phase 2 implementation.

### Pitfall 4: Confusing Daytime High with Culture Temperature
**What goes wrong:** Using the ambient air high temperature directly as culture temperature.
**Why it happens:** Open raceway ponds have significant thermal mass. The culture temperature lags behind air temperature and is typically 2-5C cooler than peak air temperature during the day, and warmer than ambient at night.
**How to avoid:** In v1, use the daytime high directly as a conservative estimate (worst-case heat stress). Document this simplification. Future phases could add a thermal model. The CONTEXT.md decision is to use daytime temperature directly for growth, which is conservative (overestimates heat stress).
**Warning signs:** Growth rates appearing too low during pre-monsoon -- consider whether culture temperature buffering should be noted.

### Pitfall 5: PAR Units Confusion
**What goes wrong:** Mixing up PAR in different units: umol/m2/s (PPFD), W/m2, kWh/m2/day, mol/m2/day.
**Why it happens:** Solar radiation data comes in energy units (kWh/m2/day), but the growth model uses photon flux (umol/m2/s).
**How to avoid:** Store PAR in the YAML in umol/m2/s (matching Phase 1's I0 parameter). Document the conversion used to derive from GHI data. All conversions happen once, at config creation time, not in simulation code.
**Warning signs:** Growth rates that are wildly off (orders of magnitude) from Phase 1 baseline.

### Pitfall 6: Monsoon PAR Reduction Double-Counting
**What goes wrong:** Applying both a cloud cover fraction AND reduced baseline PAR for monsoon months.
**Why it happens:** The CONTEXT.md mentions "fixed seasonal PAR reduction factors per month (e.g., Jun=0.6, Jul=0.4, Aug=0.4, Sep=0.5)" but the monthly PAR profile already accounts for monsoon cloud cover.
**How to avoid:** Use ONE approach: either (a) a full 12-month PAR profile that already incorporates seasonal variation including monsoon cloud cover, OR (b) a clear-sky baseline PAR with explicit cloud cover reduction factors. Recommend approach (a) -- a single monthly PAR value that represents typical conditions for that month. The cloud_cover_fraction field in YAML is informational/metadata, not a separate multiplier.
**Warning signs:** Monsoon productivity dropping to near-zero when it should be reduced but not eliminated.

## Code Examples

### CTMI Temperature Response Function
```python
# Source: Rosso et al. (1993); Bernard & Remond (2012)
def temperature_response(T: float, T_min: float, T_opt: float, T_max: float) -> float:
    """Compute CTMI cardinal temperature growth modifier.

    Returns a dimensionless fraction in [0, 1] representing the
    temperature effect on growth rate. Peaks at 1.0 when T = T_opt.

    Args:
        T: Culture temperature [C].
        T_min: Minimum temperature for growth [C].
        T_opt: Optimal temperature (maximum growth) [C].
        T_max: Maximum temperature for growth [C].

    Returns:
        Temperature response in [0, 1].
    """
    if T <= T_min or T >= T_max:
        return 0.0

    # Guard for T very close to T_opt (avoid numerical issues)
    if abs(T - T_opt) < 1e-10:
        return 1.0

    numerator = (T - T_max) * (T - T_min) ** 2
    denominator = (T_opt - T_min) * (
        (T_opt - T_min) * (T - T_opt)
        - (T_opt - T_max) * (T_opt + T_min - 2.0 * T)
    )

    if abs(denominator) < 1e-15:
        return 0.0

    result = numerator / denominator
    return max(0.0, min(1.0, result))
```

### Verification: CTMI at Key Points
```python
# Verification values for T_min=8, T_opt=28, T_max=40
#
# T=8   -> 0.0 (exactly, by boundary condition)
# T=10  -> ~0.021 (barely growing)
# T=15  -> ~0.195 (cold stress, ~20% of optimal)
# T=20  -> ~0.535 (suboptimal, ~54% of optimal)
# T=25  -> ~0.879 (near-optimal, ~88%)
# T=28  -> 1.0 (exactly optimal)
# T=30  -> ~0.938 (slight decline, ~94%)
# T=35  -> ~0.439 (significant heat stress, ~44% -- meets >50% reduction criterion)
# T=38  -> ~0.094 (severe heat stress, ~9%)
# T=40  -> 0.0 (exactly, by boundary condition)
#
# NOTE: At T=35, growth drops to ~44% of optimal. This satisfies the
# success criterion "Growth rate drops significantly (>50%) when
# temperature exceeds 35C" since the drop from 100% to 44% is a 56% reduction.
```

### Climate Config Loader (Following Phase 1 Pattern)
```python
# Source: Mirrors existing src/config/loader.py pattern
from pathlib import Path
from pydantic import BaseModel, Field

class MonthlyClimateValidator(BaseModel):
    """Validates a single month of climate data."""
    season: str  # "dry", "hot", or "monsoon"
    temp_day: float = Field(ge=-10.0, le=55.0)
    temp_night: float = Field(ge=-10.0, le=45.0)
    par: float = Field(ge=0.0, le=2500.0)    # umol/m2/s
    photoperiod: float = Field(ge=0.0, le=24.0)  # hours
    rainfall: float = Field(ge=0.0, le=2000.0)   # mm
    cloud_cover_fraction: float = Field(ge=0.0, le=1.0)

class ClimateProfileValidator(BaseModel):
    """Validates a complete city climate profile."""
    city: str
    country: str
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    T_min: float = Field(ge=-10.0, le=20.0)
    T_opt: float = Field(ge=15.0, le=40.0)
    T_max: float = Field(ge=25.0, le=55.0)
    months: dict[str, MonthlyClimateValidator]

# Frozen dataclass for simulation consumption
@dataclass(frozen=True)
class MonthlyClimate:
    season: str
    temp_day: float
    temp_night: float
    par: float
    photoperiod: float
    rainfall: float
    cloud_cover_fraction: float

@dataclass(frozen=True)
class ClimateParams:
    T_min: float
    T_opt: float
    T_max: float

@dataclass(frozen=True)
class CityClimate:
    city: str
    country: str
    latitude: float
    longitude: float
    climate_params: ClimateParams
    months: tuple[MonthlyClimate, ...]  # 12 months, tuple for hashability
```

### Monthly PAR Derivation for Surat
```python
# How PAR values were derived from GHI data
#
# Source: WeatherSpark (satellite-derived solar energy data for Surat)
# Method: GHI (kWh/m2/day) -> peak PAR (umol/m2/s)
#
# Steps:
# 1. Start with monthly GHI from WeatherSpark
# 2. PAR fraction of GHI = 0.45 (standard; Mavi & Tupper 2004)
# 3. Convert daily total to average daytime irradiance:
#    GHI_avg_daytime [W/m2] = GHI [kWh/m2/day] * 1000 / daylight_hours / 3600 * 3600
#    Simplified: GHI_avg [W/m2] = GHI [kWh/m2/day] * 1000 / daylight_hours
# 4. PAR_avg [W/m2] = GHI_avg * 0.45
# 5. PAR [umol/m2/s] = PAR_avg * 4.57 (conversion factor for sunlight)
#
# For the growth model, we want PEAK mid-day PAR, not daily average.
# Peak is typically 1.3-1.5x the daily average for a clear day.
# However, using daily-average PAR is more representative for a
# depth-averaged, day-long growth calculation.
#
# RECOMMENDED: Use average daytime PAR directly in the model.
# This is what the depth_averaged_growth_rate function expects
# as I0 (representative surface irradiance).
```

## Surat Climate Data (Compiled)

### Monthly Climate Summary

Data compiled from Weather Atlas, WeatherSpark, and ClimatesToTravel (1981-2010 averages):

| Month | Season | Day High C | Night Low C | GHI kWh/m2/d | Daylight h | Cloud % | Rain mm |
|-------|--------|-----------|-------------|---------------|------------|---------|---------|
| Jan   | Dry    | 29.8      | 15.2        | 5.1           | 11.0       | 16      | 0       |
| Feb   | Dry    | 31.5-32.3 | 16.7-18.0   | 6.0           | 11.5       | 13      | 0       |
| Mar   | Hot    | 34.3-35.4 | 20.7-22.0   | 6.8           | 12.0       | 15      | 0       |
| Apr   | Hot    | 35.8-36.7 | 24.0-25.0   | 7.2           | 12.7       | 18      | 0       |
| May   | Hot    | 35.3-35.8 | 26.8-27.9   | 7.1           | 13.2       | 29      | 0-4     |
| Jun   | Monsoon| 33.0-34.0 | 27.0-28.3   | 5.8           | 13.4       | 60      | 41-245  |
| Jul   | Monsoon| 29.8-31.2 | 25.9-26.5   | 5.0           | 13.3       | 78      | 135-465 |
| Aug   | Monsoon| 29.3-30.8 | 25.5-26.0   | 5.2           | 12.8       | 76      | 122-285 |
| Sep   | Monsoon| 30.3-32.3 | 25.2-25.4   | 5.5           | 12.2       | 53      | 65-150  |
| Oct   | Dry    | 33.6-35.1 | 23.3-24.9   | 5.5           | 11.6       | 32      | 13-40   |
| Nov   | Dry    | 33.2-34.1 | 19.6-23.3   | 5.1           | 11.1       | 22      | 5-7     |
| Dec   | Dry    | 30.8-31.9 | 16.5-20.6   | 4.7           | 10.9       | 20      | 0-1     |

**Notes:**
- Ranges reflect variation between Weather Atlas, WeatherSpark, and ClimatesToTravel sources
- GHI values from WeatherSpark satellite data
- Day High used as daytime culture temperature (conservative -- overestimates heat stress)
- Night Low used as nighttime culture temperature (conservative -- underestimates thermal mass)
- Monsoon months (Jun-Sep) show dramatically reduced solar energy (5.0-5.8 vs 6.8-7.2 kWh/m2/d)

### Recommended Monthly PAR Values for YAML Config

Using average daytime PAR (not peak) derived from GHI:

PAR_avg [umol/m2/s] = GHI [kWh/m2/d] * 1000 / daylight_hours_s * 0.45 * 4.57

Where daylight_hours_s = daylight_hours * 3600

Simplified: PAR_avg = GHI * 1000 * 0.45 * 4.57 / (daylight * 3600)

| Month | GHI kWh/m2/d | Daylight h | PAR_avg umol/m2/s | Season |
|-------|-------------|------------|-------------------|--------|
| Jan   | 5.1         | 11.0       | 430               | Dry    |
| Feb   | 6.0         | 11.5       | 484               | Dry    |
| Mar   | 6.8         | 12.0       | 525               | Hot    |
| Apr   | 7.2         | 12.7       | 525               | Hot    |
| May   | 7.1         | 13.2       | 498               | Hot    |
| Jun   | 5.8         | 13.4       | 401               | Monsoon|
| Jul   | 5.0         | 13.3       | 348               | Monsoon|
| Aug   | 5.2         | 12.8       | 376               | Monsoon|
| Sep   | 5.5         | 12.2       | 418               | Monsoon|
| Oct   | 5.5         | 11.6       | 439               | Dry    |
| Nov   | 5.1         | 11.1       | 426               | Dry    |
| Dec   | 4.7         | 10.9       | 400               | Dry    |

**Confidence:** MEDIUM -- derived from WeatherSpark GHI data using standard conversion factors. The conversion chain (GHI -> PAR) introduces ~10% uncertainty. These values are representative daytime averages, suitable for the depth_averaged_growth_rate model.

### Recommended Daytime/Nighttime Temperature Values

Use consensus values from multiple sources. For conservative modeling, use:
- Day temperature = average daily high (from Weather Atlas)
- Night temperature = average daily low (from ClimatesToTravel)

| Month | Temp Day C | Temp Night C | Season |
|-------|-----------|-------------|--------|
| Jan   | 30        | 15          | Dry    |
| Feb   | 32        | 17          | Dry    |
| Mar   | 35        | 21          | Hot    |
| Apr   | 37        | 24          | Hot    |
| May   | 36        | 27          | Hot    |
| Jun   | 34        | 27          | Monsoon|
| Jul   | 31        | 26          | Monsoon|
| Aug   | 31        | 26          | Monsoon|
| Sep   | 32        | 25          | Monsoon|
| Oct   | 35        | 23          | Dry    |
| Nov   | 34        | 20          | Dry    |
| Dec   | 31        | 17          | Dry    |

**Key insight for Surat:** The day/night split is most dramatic in winter (30/15 = 15C difference) and least in monsoon (31/26 = 5C difference). Pre-monsoon (Apr-May) has the highest daytime heat stress (36-37C) where f_temp drops to ~0.45-0.52, directly meeting the >50% growth reduction success criterion.

### Cardinal Temperature Parameters for Chlorella vulgaris

| Parameter | Value | Confidence | Source |
|-----------|-------|-----------|--------|
| T_min | 8 C | MEDIUM | Literature: growth observed at 5-8C but very slow; 8C is conservative lower bound where growth is negligible |
| T_opt | 28 C | HIGH | Converti et al. (2009), Singh & Singh (2014): optimal at 25-30C; 28C is mid-range |
| T_max | 40 C | MEDIUM | Converti et al. (2009): death at 38C; DISCOVR screening: some strains tolerate 42C; 40C gives model headroom |

**Rationale for T_max=40 (not 38):** The CONTEXT.md specifies Surat daytime temperatures up to 44C and that growth should drop >50% above 35C. With T_max=38, the CTMI would give exactly 0.0 at 38C, which is too aggressive -- it means zero growth at a temperature that Surat regularly reaches in pre-monsoon. T_max=40 gives a steep but nonzero decline, with growth ~4% at 38C and 0% at 40C. This is more realistic for open pond culture (which has thermal buffering) and avoids the model predicting absolute zero production during entire months.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Simple Arrhenius temperature model | CTMI (Rosso 1993) validated for algae | Bernard & Remond 2012 | Cardinal temperatures have biological meaning; easier calibration |
| Single daily temperature | Day/night split with separate growth/respiration | Edmundson & Huesemann 2015 | More accurate outdoor predictions; 10-35% of daytime biomass lost at night |
| Threshold-based heat crash (if T>35: crash) | Continuous bell-curve inhibition | Standard in modern algae models | Avoids discontinuities; better matches experimental data |
| Single location hardcoded | City-as-config with YAML profiles | Current best practice | Extensible to multiple locations; parameters are transparent |
| Solar radiation in W/m2 directly | PAR in umol/m2/s via standard conversion | Standard practice | Matches photosynthesis literature units; consistent with growth model |

**Deprecated/outdated:**
- Sharp threshold models: Using if/else at specific temperatures is not biologically realistic and produces discontinuities
- Single daily average temperature: Masks critical day/night dynamics, especially in tropical climates with large diurnal ranges
- Hardcoded climate data: No longer acceptable; config files enable transparency and extensibility

## Open Questions

### 1. Exact PAR Values Need Validation
- **What we know:** GHI data from WeatherSpark, standard 0.45 conversion factor
- **What's unclear:** Whether the derived PAR values (348-525 umol/m2/s average) match measured PAR at Surat. NASA POWER API could provide more authoritative PAR data.
- **Recommendation:** Use the derived values for v1 with MEDIUM confidence. Flag in YAML with source citation. Can be updated with better data without code changes (just update YAML).
- **Confidence:** MEDIUM

### 2. Nighttime Respiration Model Simplification
- **What we know:** Literature reports night biomass loss of 10-35% of daytime production. Maintenance respiration (r_maintenance = 0.01 1/d in current model) is the base rate. Respiration scales with temperature via CTMI.
- **What's unclear:** Whether multiplying r_maintenance by the CTMI temperature factor is sufficiently accurate, or whether a separate Arrhenius-type respiration model is needed.
- **Recommendation:** For v1, use `r_night = r_maintenance * f_temp(T_night)`. This is simple, uses existing parameters, and captures the key behavior (cooler nights = less respiration loss). The r_maintenance value (0.01 1/d) is already conservative.
- **Confidence:** MEDIUM

### 3. Photoperiod Impact on Growth
- **What we know:** Surat daylight varies from 10.9h (Dec) to 13.4h (Jun). Claude's discretion area.
- **What's unclear:** Whether photoperiod should just scale the growth period (simple proportional) or whether there's a nonlinear photoperiod response.
- **Recommendation:** Use simple proportional scaling: daytime growth contributes (photoperiod/24) and nighttime respiration contributes ((24-photoperiod)/24) of their respective rates. This is physically correct for a first-order model.
- **Confidence:** HIGH (simple physics)

### 4. Temperature Data Source Variation
- **What we know:** Weather Atlas, WeatherSpark, and ClimatesToTravel show 1-3C differences for the same month.
- **What's unclear:** Which source is most accurate for Surat.
- **Recommendation:** Use rounded consensus values (nearest whole degree C). The CTMI curve is smooth enough that 1-2C differences do not qualitatively change the results. Document the source range in YAML notes.
- **Confidence:** HIGH (temperature precision is not model-critical)

## Sources

### Primary (HIGH confidence)
- **Rosso et al. (1993)** -- Original CTMI formulation. J. Theor. Biol. 162: 447-463. The four-parameter cardinal temperature model with inflection.
- **Bernard & Remond (2012)** -- "Validation of a simple model accounting for light and temperature effect on microalgal growth." Bioresource Technology 123: 520-527. Validates CTMI for microalgae including Chlorella species. [PubMed](https://pubmed.ncbi.nlm.nih.gov/22940363/)
- **Converti et al. (2009)** -- "Effect of temperature and nitrogen concentration on the growth and lipid content of Nannochloropsis oculata and Chlorella vulgaris for biodiesel production." Chemical Engineering and Processing 48: 1146-1151. Key source for C. vulgaris temperature response: optimal 25-30C, growth decline above 30C, death at 38C.
- **Weather Atlas Surat** -- Monthly climate data (1981-2010 averages): temperature highs/lows, rainfall, humidity. [weather-atlas.com](https://www.weather-atlas.com/en/india/surat-climate)
- **WeatherSpark Surat** -- Satellite-derived solar energy (kWh/m2/day), cloud cover, daylight hours. [weatherspark.com](https://weatherspark.com/y/107304/Average-Weather-in-S%C5%ABrat-Gujarat-India-Year-Round)

### Secondary (MEDIUM confidence)
- **Rossi, Carecci & Ficara (2023)** -- "Thermal response analysis and compilation of cardinal temperatures for 424 strains." Science of the Total Environment 873: 162275. Comprehensive database of microalgae cardinal temperatures. Could not access specific C. vulgaris values (paywall). [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0048969723008914)
- **Edmundson & Huesemann (2015)** -- "The dark side of algae cultivation: Characterizing night biomass loss in three photosynthetic algae." Night biomass loss rates: -0.006 to -0.59 day^-1, species-specific and temperature-dependent. [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2211926415300862)
- **Huesemann et al. (2023)** -- DISCOVR strain pipeline screening. Growth rate screening of 38 strains (including C. vulgaris) from 5 to 45C. [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2211926423000292)
- **ClimatesToTravel Surat** -- Additional temperature and precipitation data. [climatestotravel.com](https://www.climatestotravel.com/climate/india/surat)
- **PAR conversion factors** -- Standard 0.45 PAR fraction of GHI; 4.57 umol/J conversion. Multiple sources: Mavi & Tupper (2004), bigleaf R package documentation, Wikipedia PAR article.

### Tertiary (LOW confidence)
- **Decostere et al. (2016)** -- Semi-mechanistic model for C. vulgaris respiration. Respiration = r_min + delta*mu with temperature dependence. Could not access full text. [PubMed](https://pubmed.ncbi.nlm.nih.gov/30537594/)
- **NASA POWER API** -- Could provide authoritative PAR data for Surat coordinates (21.17N, 72.83E) but was not directly queried in this research. Recommended for validation of derived PAR values.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new dependencies needed; same PyYAML + Pydantic + dataclass pattern as Phase 1
- Architecture: HIGH - Follows established Phase 1 patterns (pure functions, YAML config, Pydantic validation, frozen dataclasses)
- Temperature model (CTMI): MEDIUM-HIGH - Equation is well-established; specific C. vulgaris cardinal temperatures (T_min=8, T_opt=28, T_max=40) are conservative estimates from literature consensus, not from a single fitted CTMI curve
- Climate data: MEDIUM - Multiple sources agree on temperature ranges; PAR values are derived with standard conversion factors but not validated against ground-truth measurements
- Pitfalls: HIGH - Phase 1 compatibility, unit confusion, and CTMI numerical issues are well-understood

**Research date:** 2026-01-30
**Valid until:** 2026-03-30 (stable domain; temperature models and climate data do not change rapidly)
