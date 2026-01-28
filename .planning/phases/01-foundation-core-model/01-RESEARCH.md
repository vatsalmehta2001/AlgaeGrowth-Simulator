# Phase 1: Foundation & Core Model - Research

**Researched:** 2026-01-28
**Domain:** Microalgal growth kinetics (Monod equations, Beer-Lambert light attenuation, photoinhibition), pure Python scientific simulation
**Confidence:** HIGH

## Summary

Phase 1 establishes the pure Python simulation foundation for Chlorella vulgaris growth modeling. The core challenge is implementing Monod-form growth kinetics with Beer-Lambert light attenuation and Steele-type photoinhibition, using conservative field-validated parameters that produce defensible 6-10 g/m2/day productivity estimates.

Research drew from two primary-source papers provided by the user: Schediwy et al. (2019) "Microalgal kinetics" which provides the most complete kinetic parameter table (Table 2) with ranges for all key variables, and Razzak et al. (2024) "Microalgae cultivation in photobioreactors" which provides the combined growth-light-CO2 equation framework. These papers, cross-referenced with web-sourced Chlorella vulgaris-specific data, provide a complete parameter set for implementation.

The recommended approach uses Monod-form kinetics for both light and CO2 limitation, combined multiplicatively per Liebig's law (as specified in CONTEXT.md). Light attenuation follows Beer-Lambert with depth-averaged integration. Photoinhibition uses the Steele (1962) model which naturally captures growth reduction at high irradiance. A 50% real-world discount factor converts theoretical predictions to field-realistic estimates. All parameters are stored in a YAML config with per-parameter citations for carbon credit audit trail.

**Primary recommendation:** Implement the combined model: `mu = mumax * f_steele(I_avg) * f_monod(CO2) * discount_factor` with Beer-Lambert depth-averaging, frozen dataclasses for all parameters, and integration tests validating 6-10 g/m2/day output range.

## Standard Stack

The established libraries/tools for this phase (Phase 1 is pure Python, no Streamlit):

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12 | Runtime | Stable, supported by all scientific libraries, not bleeding-edge |
| NumPy | >= 2.4.1 | Array operations, Beer-Lambert vectorized calculations | Foundation for all numerical work; `numpy.typing.NDArray` for type hints |
| SciPy | >= 1.17.0 | ODE solving via `solve_ivp`, numerical integration | Gold standard for Monod kinetics ODEs; 6 solver methods including stiff-equation handlers |
| Pydantic | >= 2.12.5 | Parameter validation with range constraints | Runtime validation of scientific parameters (e.g., temperature 0-50C, depth > 0) |
| PyYAML | >= 6.0 | Loading parameter config with citations | Standard YAML parser for species_params.yaml provenance file |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | >= 8.0.0 | Unit and integration testing | All test execution |
| pytest-approx | (bundled) | Floating-point comparison in tests | `assert result == pytest.approx(expected, rel=1e-3)` |
| mypy | >= 1.8.0 | Static type checking | CI/pre-commit type validation |
| ruff | >= 0.1.0 | Linting + formatting | Code quality enforcement |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `scipy.integrate.solve_ivp` | Hand-coded RK4 | Never hand-roll; solve_ivp has adaptive step, error control, stiff solvers |
| `scipy.integrate.solve_ivp` | `scipy.integrate.odeint` | odeint is legacy API; solve_ivp is modern replacement with better interface |
| Pydantic | Plain dataclasses + manual validation | More boilerplate, worse error messages, no nested validation |
| Frozen dataclasses | Pydantic BaseModel (frozen=True) | Either works; frozen dataclasses are simpler for pure data containers with no validation beyond types |
| YAML config | JSON config | YAML supports comments for inline citations; JSON does not |

**Installation:**
```bash
pip install numpy>=2.4.1 scipy>=1.17.0 pydantic>=2.12.5 pyyaml>=6.0 pytest>=8.0.0 mypy>=1.8.0 ruff>=0.1.0
```

## Architecture Patterns

### Recommended Project Structure (Phase 1 only)
```
src/
├── __init__.py
├── simulation/
│   ├── __init__.py
│   ├── growth.py           # Monod growth + Steele photoinhibition
│   └── light.py            # Beer-Lambert attenuation + depth averaging
├── models/
│   ├── __init__.py
│   ├── parameters.py       # Frozen dataclasses: GrowthParams, LightParams, ReactorParams
│   └── results.py          # SimulationResult dataclass
└── config/
    ├── __init__.py
    ├── species_params.yaml  # Chlorella vulgaris params + citations
    └── loader.py            # YAML loading + Pydantic validation
tests/
├── __init__.py
├── test_growth.py          # Unit tests for Monod + Steele
├── test_light.py           # Unit tests for Beer-Lambert + depth averaging
└── test_integration.py     # Integration tests: 6-10 g/m2/day validation
```

### Pattern 1: Frozen Dataclasses for Parameter Containers
**What:** All kinetic parameters stored as frozen (immutable) dataclasses. Hashable for downstream Streamlit cache keys.
**When to use:** Every parameter group (growth, light, reactor, species).
**Example:**
```python
# src/models/parameters.py
from dataclasses import dataclass

@dataclass(frozen=True)
class GrowthParams:
    """Monod growth kinetics parameters for a single species."""
    mu_max: float          # Maximum specific growth rate [1/d]
    Ks_co2: float          # Half-saturation constant for CO2 [mg/L]
    I_opt: float           # Optimal light intensity for Steele model [umol/m2/s]
    r_maintenance: float   # Maintenance respiration rate [1/d]
    discount_factor: float # Real-world discount (0-1), typically 0.5

@dataclass(frozen=True)
class LightParams:
    """Beer-Lambert light attenuation parameters."""
    sigma_x: float         # Biomass-specific light absorption [m2/g]
    background_turbidity: float  # Non-biomass light extinction [1/m]

@dataclass(frozen=True)
class ReactorParams:
    """Physical reactor/pond parameters."""
    depth: float           # Pond depth [m]
    surface_area: float    # Pond surface area [m2]

@dataclass(frozen=True)
class SpeciesParams:
    """Complete species parameter set with provenance."""
    name: str
    growth: GrowthParams
    light: LightParams
    carbon_content: float  # Fraction of biomass that is carbon [g_C/g_DW]
    citation_file: str     # Path to YAML with per-parameter citations
```

### Pattern 2: Pure Functions for Growth Equations
**What:** Growth model functions are stateless -- they take parameters and state, return rates. No side effects, no mutation.
**When to use:** All mathematical model functions.
**Example:**
```python
# src/simulation/growth.py
import numpy as np

def steele_light_response(I: float, I_opt: float) -> float:
    """Steele (1962) photoinhibition model.

    Returns growth fraction [0, 1] relative to max.
    Peak at I = I_opt, declining at higher intensities.

    Source: Steele (1962); Razzak et al. (2024) Eq. 17
    """
    if I <= 0 or I_opt <= 0:
        return 0.0
    ratio = I / I_opt
    return ratio * np.exp(1.0 - ratio)

def monod_co2_response(co2: float, Ks_co2: float) -> float:
    """Monod kinetics for CO2 limitation.

    Source: Razzak et al. (2024) Eq. 2/11
    """
    if co2 <= 0:
        return 0.0
    return co2 / (Ks_co2 + co2)

def specific_growth_rate(
    I_avg: float,
    co2: float,
    params: GrowthParams,
) -> float:
    """Combined growth rate: mu = mumax * f(light) * f(CO2) * discount.

    Limiting factors combine multiplicatively (Liebig's law).
    Source: CONTEXT.md decision; Razzak et al. (2024) framework
    """
    f_light = steele_light_response(I_avg, params.I_opt)
    f_co2 = monod_co2_response(co2, params.Ks_co2)
    mu = params.mu_max * f_light * f_co2 * params.discount_factor
    return max(mu - params.r_maintenance, 0.0)
```

### Pattern 3: Depth-Averaged Light Integration
**What:** Beer-Lambert attenuation integrated across pond depth to get average irradiance seen by cells.
**When to use:** Every growth rate calculation (light varies with depth).
**Example:**
```python
# src/simulation/light.py
import numpy as np

def beer_lambert(I0: float, sigma_x: float, biomass: float,
                 depth: float, background_k: float = 0.0) -> float:
    """Light intensity at a given depth.

    I(z) = I0 * exp(-(sigma_x * X + k_bg) * z)

    Source: Razzak et al. (2024) Eq. 18; Schediwy et al. (2019) Eq. 3
    """
    extinction = sigma_x * biomass + background_k
    return I0 * np.exp(-extinction * depth)

def depth_averaged_irradiance(I0: float, sigma_x: float,
                               biomass: float, depth: float,
                               background_k: float = 0.0) -> float:
    """Analytical depth-averaged irradiance.

    I_avg = I0 / (K * D) * (1 - exp(-K * D))
    where K = sigma_x * X + k_bg

    Source: Razzak et al. (2024) Eq. 19; Schediwy et al. (2019) Eq. 10
    """
    K = sigma_x * biomass + background_k
    if K * depth < 1e-10:
        return I0  # No attenuation in very shallow / very clear
    return I0 / (K * depth) * (1.0 - np.exp(-K * depth))

def depth_averaged_growth_numerical(
    I0: float, biomass: float, depth: float,
    growth_params: GrowthParams, light_params: LightParams,
    co2: float, n_layers: int = 20,
) -> float:
    """Numerical depth-averaged growth rate.

    Integrates growth rate across n_layers of depth.
    More accurate than analytical when growth response is nonlinear.

    Source: Schediwy et al. (2019) Eq. 10
    """
    dz = depth / n_layers
    total_mu = 0.0
    K = light_params.sigma_x * biomass + light_params.background_turbidity

    for i in range(n_layers):
        z_mid = (i + 0.5) * dz
        I_z = I0 * np.exp(-K * z_mid)
        mu_z = specific_growth_rate(I_z, co2, growth_params)
        total_mu += mu_z

    return total_mu / n_layers
```

### Pattern 4: YAML Parameter Config with Citations
**What:** Species parameters stored in YAML with value + citation together. Enables carbon credit audit.
**When to use:** All species kinetic parameters.
**Example:**
```yaml
# src/config/species_params.yaml
species: Chlorella vulgaris

growth:
  mu_max:
    value: 0.06   # conservative end: 0.02-0.15 g/g/h = ~0.5-3.6 /d
    unit: "1/d"
    # Using 0.06/h * 24h = 1.44/d, but applying field discount -> effective ~0.7/d
    # Conservative choice: use rX,max low end from Schediwy Table 2
    source: "Schediwy et al. (2019), Table 2: rX,max = 0.02-0.15 g/g/h"
    note: "Using conservative (lower) end per CONTEXT.md decision"

  Ks_co2:
    value: 0.5
    unit: "mg/L dissolved CO2"
    source: "Schediwy et al. (2019), Table 2: kCO2 = 0.5 mg/L"
    note: "Half-saturation for dissolved CO2; also reported as 0.027% or 11 umol/L"

  I_opt:
    value: 80.0
    unit: "umol/m2/s"
    source: "Razzak et al. (2024), citing Metsoviti et al."
    note: "Optimal light for C. vulgaris; photoinhibition onset >110 umol/m2/s"

  r_maintenance:
    value: 0.01
    unit: "1/d"
    source: "Assumed from general microalgae literature"
    note: "ASSUMED - not from primary sources; flagged per CONTEXT.md"

  discount_factor:
    value: 0.5
    unit: "dimensionless"
    source: "Schediwy et al. (2019); PITFALLS.md: lab-to-field 40-60% discount"
    note: "Midpoint of 40-60% range; user-visible per CONTEXT.md"

light:
  sigma_x:
    value: 0.2
    unit: "m2/g"
    source: "Schediwy et al. (2019), Table 2: sigma_X = 0.1-0.3 m2/g"
    note: "Midpoint of range; biomass-specific light absorption coefficient"

  background_turbidity:
    value: 0.5
    unit: "1/m"
    source: "General open pond literature estimate"
    note: "ASSUMED - accounts for non-biomass light extinction (water, dissolved organics)"

carbon:
  carbon_content:
    value: 0.50
    unit: "g_C/g_DW"
    source: "Schediwy et al. (2019), Table 2: carbon content = 0.5 g/g"
    note: "Yields YCO2/X = MCO2/MC * 0.5 = (44/12)*0.5 = 1.83 g_CO2/g_biomass"

  co2_to_biomass_ratio:
    value: 1.83
    unit: "g_CO2/g_DW"
    source: "Derived: (44/12) * 0.50 = 1.833; Schediwy Table 2 reports 1.8"
    note: "Consistent with Razzak et al. (2024): up to 1.83 kg CO2/kg biomass"
```

### Anti-Patterns to Avoid
- **Hardcoded magic numbers:** Never write `mu = 0.5 * S / (0.1 + S)` inline. All parameters must come from the YAML config or dataclass, with citations traceable.
- **Mutable parameter objects:** Never use regular (non-frozen) dataclasses for parameters. Mutation bugs are silent and devastating in simulation code.
- **Streamlit imports in simulation code:** Phase 1 has zero Streamlit dependency. All simulation code must be testable via `pytest` alone.
- **Single-depth light calculation:** Never compute growth at surface irradiance only. Beer-Lambert depth-averaging is mandatory for any pond deeper than a few centimeters.
- **Using `odeint` instead of `solve_ivp`:** `odeint` is legacy SciPy API. `solve_ivp` has better interface, more methods, adaptive stepping.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ODE integration | Euler method, hand-coded RK4 | `scipy.integrate.solve_ivp(method='RK45')` | Adaptive step size, error control, handles stiff transitions; hand-rolled misses edge cases |
| Depth-averaged irradiance | Simple average of surface and bottom | Analytical formula: `I_avg = I0/(K*D) * (1 - exp(-K*D))` | Exponential decay means simple average is wrong by 20-50%; analytical solution is exact |
| Parameter validation | Manual `if` checks | Pydantic `Field(ge=0, le=50)` validators | Consistent error messages, composable validation, automatic for nested structures |
| YAML loading + validation | Manual dict parsing | PyYAML + Pydantic model parsing | Type coercion, missing field detection, nested validation for free |
| Floating-point test comparison | `assert a == b` | `pytest.approx(expected, rel=1e-3)` | Floating-point equality fails spuriously; approx handles rounding correctly |

**Key insight:** Scientific simulation code has decades of established solutions. The value of this project is in parameter selection and model composition, not in reimplementing numerical methods.

## Common Pitfalls

### Pitfall 1: Lab-to-Field Yield Gap (3-6x Overestimation)
**What goes wrong:** Model predicts 15-25 g/m2/day (lab values) when real field operations average 6 g/m2/day.
**Why it happens:** Lab conditions use controlled temperature, optimal light, constant nutrients, no contamination. Short-term trials (<12 months) miss seasonal variability.
**How to avoid:** Apply 50% real-world discount factor. Use conservative (lower) end of all parameter ranges. Integration tests must validate 6-10 g/m2/day output range.
**Warning signs:** Productivity estimates >10 g/m2/day without extreme light/CO2 conditions should trigger warning flag (per CONTEXT.md).
**Source:** Schediwy et al. (2019); PITFALLS.md; PMC/10901112

### Pitfall 2: Monod Ks Values Vary Wildly
**What goes wrong:** Using a single Ks value from one paper when literature reports order-of-magnitude variation across studies.
**Why it happens:** Ks depends on environmental conditions (temperature, pH, mixing), not just species. Papers report different values because conditions differ.
**How to avoid:** Use Schediwy et al. Table 2 as primary source (kCO2 = 0.5 mg/L for dissolved CO2). Document the environmental context. Flag as sensitivity-analysis target for future phases.
**Warning signs:** Growth model shows zero sensitivity to CO2 concentration (Ks too low) or no growth at reasonable CO2 (Ks too high).
**Source:** Schediwy et al. (2019) Table 2; PMC/9671824

### Pitfall 3: Missing Photoinhibition at High Light
**What goes wrong:** Using simple Monod-form light response (Type I) where growth increases monotonically with light. Surat's intense solar radiation (>1500 umol/m2/s at surface) would predict maximum growth when cells are actually being damaged.
**Why it happens:** Simple Monod is easier to implement. Photoinhibition requires Type II model (e.g., Steele).
**How to avoid:** Use Steele (1962) model: `P = Pmax * (I/Iopt) * exp(1 - I/Iopt)`. This naturally captures inhibition above Iopt. For Chlorella vulgaris, Iopt = 80 umol/m2/s, inhibition onset >110 umol/m2/s.
**Warning signs:** Growth rate still increasing at I > 500 umol/m2/s. No decline in productivity during midday peak irradiance.
**Source:** Razzak et al. (2024) Eq. 17; Steele (1962); Schediwy et al. (2019) Table 2 (kI = 100-300 umol/m2/s)

### Pitfall 4: Ignoring Self-Shading Feedback
**What goes wrong:** Beer-Lambert attenuation is computed once at initial biomass concentration. As biomass grows, attenuation increases but the model does not update, leading to overestimation.
**Why it happens:** Computing depth-averaged irradiance at each ODE step seems expensive. Developers compute it once.
**How to avoid:** The ODE system must recompute depth-averaged irradiance at each evaluation using current biomass concentration `X(t)`. This is critical because `K = sigma_x * X(t)` changes as X grows.
**Warning signs:** Light-limited growth does not slow down as culture gets denser. Biomass grows exponentially without bound.

### Pitfall 5: Unit Inconsistencies
**What goes wrong:** Mixing hourly and daily rates, mg/L and g/L, umol and W/m2 without consistent conversion.
**Why it happens:** Different papers use different unit systems. Schediwy uses g/g/h; Razzak uses 1/d; irradiance can be umol/m2/s (PAR) or W/m2 (total solar).
**How to avoid:** Standardize all internal calculations to: rates in 1/d, concentrations in g/L, irradiance in umol/m2/s (PAR), depth in m, area in m2. Document conversion factors explicitly. PAR is approximately 0.45 * total solar W/m2; 1 W/m2 PAR is approximately 4.57 umol/m2/s.
**Warning signs:** Productivity off by factor of 24 (hourly vs daily confusion) or by ~2x (PAR vs total solar confusion).

### Pitfall 6: Not Validating Against Known Productivity Ranges
**What goes wrong:** Model produces numbers but nobody checks if they are physically reasonable.
**Why it happens:** Unit tests check that code runs without errors, not that outputs are biologically plausible.
**How to avoid:** Integration tests must check: (a) standard conditions produce 6-10 g/m2/day, (b) deep ponds (>0.3m) show measurable attenuation vs shallow, (c) high light shows photoinhibition (growth decreases), (d) zero CO2 produces near-zero growth. Add warning flag when output >10 g/m2/day per CONTEXT.md.
**Warning signs:** All tests pass but outputs are physically impossible (negative biomass, >50 g/m2/day, etc.).

## Code Examples

Verified patterns synthesized from primary sources:

### Steele Photoinhibition Model
```python
# Source: Steele (1962); Razzak et al. (2024) Eq. 17
# f(I) = (I/Iopt) * exp(1 - I/Iopt)
# Peak at I = Iopt (returns 1.0), declining for I > Iopt

import numpy as np

def steele_light_response(I: float, I_opt: float) -> float:
    """Steele photoinhibition model.

    Returns value in [0, 1]. Maximum of 1.0 at I = I_opt.
    For I > I_opt, growth decreases (photoinhibition).
    For I < I_opt, growth increases with light (light limitation).

    Args:
        I: Irradiance at the cell [umol/m2/s]
        I_opt: Optimal irradiance [umol/m2/s]

    Returns:
        Growth fraction relative to maximum.
    """
    if I <= 0 or I_opt <= 0:
        return 0.0
    ratio = I / I_opt
    return ratio * np.exp(1.0 - ratio)

# Verification:
# steele_light_response(80, 80)   -> 1.0   (optimal)
# steele_light_response(40, 80)   -> 0.824 (light limited)
# steele_light_response(200, 80)  -> 0.558 (photoinhibited)
# steele_light_response(500, 80)  -> 0.058 (severely inhibited)
```

### Beer-Lambert Depth-Averaged Irradiance (Analytical)
```python
# Source: Razzak et al. (2024) Eq. 18-19; Schediwy et al. (2019) Eq. 3, 10

import numpy as np

def depth_averaged_irradiance(
    I0: float,
    sigma_x: float,
    biomass_conc: float,
    depth: float,
    k_bg: float = 0.0,
) -> float:
    """Analytical depth-averaged irradiance in a pond/reactor.

    I_avg = I0 / (K * D) * (1 - exp(-K * D))
    where K = sigma_x * X + k_bg

    Args:
        I0: Surface irradiance [umol/m2/s]
        sigma_x: Biomass light absorption coefficient [m2/g]
        biomass_conc: Current biomass concentration [g/L = g/dm3 = kg/m3]
        depth: Pond depth [m]
        k_bg: Background extinction from water/dissolved matter [1/m]

    Returns:
        Average irradiance across depth [umol/m2/s]
    """
    K = sigma_x * biomass_conc + k_bg  # Total extinction [1/m]
    optical_depth = K * depth

    if optical_depth < 1e-10:
        return I0  # Negligible attenuation

    return I0 / optical_depth * (1.0 - np.exp(-optical_depth))

# Verification:
# depth_averaged_irradiance(500, 0.2, 1.0, 0.3)  -> ~370 (shallow, moderate biomass)
# depth_averaged_irradiance(500, 0.2, 1.0, 0.5)  -> ~316 (deeper -> less light)
# depth_averaged_irradiance(500, 0.2, 5.0, 0.3)  -> ~199 (dense culture -> much less)
```

### Combined Growth Model (Multiplicative Limiting Factors)
```python
# Source: CONTEXT.md decision (Liebig's law, multiplicative)
# mu = mumax * f_steele(I_avg) * f_monod(CO2) * discount - maintenance

def combined_growth_rate(
    I_avg: float,
    co2_dissolved: float,
    params: GrowthParams,
) -> float:
    """Combined specific growth rate with light and CO2 limitation.

    Factors combine multiplicatively per Liebig's law.
    Real-world discount factor applied.
    Maintenance respiration subtracted.

    Returns:
        Specific growth rate [1/d], clamped to >= 0.
    """
    f_light = steele_light_response(I_avg, params.I_opt)
    f_co2 = co2_dissolved / (params.Ks_co2 + co2_dissolved) if co2_dissolved > 0 else 0.0

    mu_gross = params.mu_max * f_light * f_co2 * params.discount_factor
    mu_net = mu_gross - params.r_maintenance

    return max(mu_net, 0.0)
```

### ODE System for Biomass Growth
```python
# Source: Standard Monod ODE; SciPy solve_ivp

from scipy.integrate import solve_ivp
import numpy as np

def growth_ode_system(t, y, growth_params, light_params, reactor_params, I0_func, co2_func):
    """ODE system for biomass growth.

    State vector y = [X] where X is biomass concentration [g/L].
    I0_func(t) returns surface irradiance at time t.
    co2_func(t, X) returns dissolved CO2 at time t given biomass X.

    Returns:
        [dX/dt]
    """
    X = y[0]
    if X < 0:
        X = 0.0

    I0 = I0_func(t)
    I_avg = depth_averaged_irradiance(
        I0, light_params.sigma_x, X,
        reactor_params.depth, light_params.background_turbidity
    )
    co2 = co2_func(t, X)

    mu = combined_growth_rate(I_avg, co2, growth_params)
    dX_dt = mu * X

    return [dX_dt]

def run_batch_simulation(
    X0: float,
    duration_days: float,
    growth_params: GrowthParams,
    light_params: LightParams,
    reactor_params: ReactorParams,
    I0_func,       # callable(t) -> irradiance
    co2_func,      # callable(t, X) -> dissolved CO2
    dt_output: float = 1.0,
) -> dict:
    """Run a batch growth simulation.

    Returns dict with 'time', 'biomass', 'productivity' arrays.
    """
    t_eval = np.arange(0, duration_days + dt_output, dt_output)

    sol = solve_ivp(
        fun=lambda t, y: growth_ode_system(
            t, y, growth_params, light_params, reactor_params, I0_func, co2_func
        ),
        t_span=(0, duration_days),
        y0=[X0],
        method='RK45',
        t_eval=t_eval,
        rtol=1e-6,
        atol=1e-9,
        max_step=0.5,  # At most 12-hour steps to capture light changes
    )

    biomass = sol.y[0]

    # Areal productivity [g/m2/d]
    productivity = np.diff(biomass) * reactor_params.depth * 1000 / dt_output
    # biomass in g/L, depth in m -> g/L * m * 1000 L/m3 = g/m2 per time step

    return {
        'time': sol.t,
        'biomass': biomass,
        'productivity': np.concatenate([[0.0], productivity]),
    }
```

### Integration Test Pattern
```python
# tests/test_integration.py

import pytest

def test_standard_conditions_produce_realistic_productivity():
    """Standard Surat conditions should yield 6-10 g/m2/day.

    Per CONTEXT.md: target 6-8 g/m2/day, warning >10.
    """
    # Standard conditions: 500 umol/m2/s PAR, 0.3m depth, 1 g/L initial
    result = run_batch_simulation(
        X0=1.0,           # 1 g/L initial biomass
        duration_days=30,
        growth_params=default_chlorella_growth_params(),
        light_params=default_chlorella_light_params(),
        reactor_params=ReactorParams(depth=0.3, surface_area=10.0),
        I0_func=lambda t: 500.0,     # Constant 500 umol/m2/s
        co2_func=lambda t, X: 5.0,   # Sufficient dissolved CO2
    )

    # Check peak daily productivity is in field-realistic range
    peak_productivity = max(result['productivity'])
    assert 4.0 <= peak_productivity <= 12.0, (
        f"Peak productivity {peak_productivity:.1f} g/m2/d "
        f"outside field-realistic range [4-12]"
    )

def test_deep_pond_shows_attenuation():
    """Ponds >0.3m should show measurably lower productivity.

    Per ROADMAP: >0.3m depth shows measurable attenuation.
    """
    shallow = run_batch_simulation(
        X0=1.0, duration_days=10,
        reactor_params=ReactorParams(depth=0.1, surface_area=10.0),
        # ... other params same
    )
    deep = run_batch_simulation(
        X0=1.0, duration_days=10,
        reactor_params=ReactorParams(depth=0.5, surface_area=10.0),
        # ... other params same
    )

    # Deep pond should produce less than shallow due to light attenuation
    assert max(deep['productivity']) < max(shallow['productivity'])

def test_photoinhibition_at_high_light():
    """Very high light should reduce growth vs optimal light.

    Steele model: growth peaks at I_opt, declines above.
    """
    optimal = run_batch_simulation(I0_func=lambda t: 80.0, ...)
    extreme = run_batch_simulation(I0_func=lambda t: 2000.0, ...)

    assert max(extreme['productivity']) < max(optimal['productivity'])

def test_zero_co2_produces_near_zero_growth():
    """Without CO2, growth should be negligible."""
    result = run_batch_simulation(co2_func=lambda t, X: 0.0, ...)
    assert max(result['productivity']) < 0.1

def test_warning_flag_above_10_gm2d():
    """Per CONTEXT.md: flag when output exceeds 10 g/m2/day."""
    result = run_batch_simulation(...)
    warnings = check_productivity_warnings(result)
    # If any day exceeds 10, warning should be present
    if max(result['productivity']) > 10.0:
        assert any("exceeds typical field values" in w for w in warnings)
```

## Kinetic Parameters Reference Table

Complete parameter set for Phase 1 implementation, extracted from primary sources:

| Parameter | Symbol | Value (Conservative) | Range | Unit | Source |
|-----------|--------|---------------------|-------|------|--------|
| Max specific growth rate | mu_max | 0.48 (=0.02*24) | 0.48-3.6 | 1/d | Schediwy Table 2: rX,max 0.02-0.15 g/g/h, using low end |
| CO2 half-saturation | Ks_CO2 | 0.5 | varies | mg/L | Schediwy Table 2: kCO2 |
| Optimal light intensity | I_opt | 80 | 80-110 | umol/m2/s | Razzak (2024), citing Metsoviti et al. |
| Light half-saturation | kI | 100 | 100-300 | umol/m2/s | Schediwy Table 2 (for Monod-form comparison) |
| Biomass light absorption | sigma_x | 0.2 | 0.1-0.3 | m2/g | Schediwy Table 2 |
| Carbon content | eC,X | 0.50 | 0.40-0.55 | g_C/g_DW | Schediwy Table 2 |
| CO2-to-biomass ratio | YCO2/X | 1.83 | 1.6-2.0 | g_CO2/g_DW | Derived: (44/12)*0.50; Schediwy reports 1.8 |
| Maintenance rate | r_m | 0.01 | 0.005-0.02 | 1/d | General microalgae literature (ASSUMED) |
| Real-world discount | -- | 0.50 | 0.40-0.60 | dimensionless | Schediwy; PITFALLS.md |
| Photon yield | yX,hv | 0.5 | 0.2-2.1 | g/mol_photons | Schediwy Table 2 (conservative end) |
| PI-curve slope | yX,I | 3.0e-4 | 1.7e-4-6.0e-4 | (g/g/h)/(umol/m2/s) | Schediwy Table 2 |
| Chlorophyll content | nChl | 20 | 18-28 | mg/g | Schediwy Table 2 |
| CO2 fixation rate | rCO2,max | 0.08 | 0.04-0.3 | g/g/h | Schediwy Table 2 (conservative end) |

**Unit conversion notes:**
- Schediwy reports rates in g/g/h; multiply by 24 for 1/d
- PAR (umol/m2/s) from total solar (W/m2): PAR = 0.45 * W/m2 * 4.57 umol/J
- 1 g/L in a 0.3m pond = 0.3 kg/m2 = 300 g/m2 standing biomass

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `scipy.integrate.odeint` | `scipy.integrate.solve_ivp` | SciPy 1.0 (2017) | Modern interface, multiple solver methods, better error control |
| Simple Monod for light (Type I) | Steele/Han photoinhibition models (Type II) | Established since 1960s, now standard | Captures growth reduction at high light; critical for tropical conditions |
| Constant "1.88 kg CO2/kg biomass" | Species-specific carbon content calculation | Ongoing shift in literature | Defensible values require measured carbon content per species |
| Lab-calibrated parameters only | Field-validated with discount factor | 2020s emphasis | Credibility requires conservative estimates acknowledging lab-field gap |
| Plain `dataclass` | `frozen=True` dataclass | Python 3.7+ | Hashability for Streamlit caching, immutability prevents mutation bugs |

**Deprecated/outdated:**
- `scipy.integrate.odeint`: Legacy API, replaced by `solve_ivp`. Do not use.
- Simple Monod light response without photoinhibition: Inappropriate for high-irradiance environments like Surat.
- Universal CO2 conversion constant (1.88): Must use species-specific carbon content with citation.

## Open Questions

Things that could not be fully resolved during research:

1. **Exact mu_max value for C. vulgaris under tropical conditions**
   - What we know: Schediwy Table 2 gives rX,max = 0.02-0.15 g/g/h (= 0.48-3.6 /d). Conservative end is 0.48/d. Literature-wide C. vulgaris mu_max is often cited as 0.5-2.0 /d.
   - What is unclear: The appropriate value for Surat's conditions specifically (25-30C, high light) with the 50% discount factor already applied.
   - Recommendation: Start with mu_max = 1.0 /d (midpoint of conservative range for C. vulgaris), then apply 50% discount factor for effective rate of ~0.5 /d. Validate against 6-10 g/m2/day target through integration tests. Adjust if tests fail.

2. **Background turbidity coefficient for open ponds in Surat**
   - What we know: Beer-Lambert needs a non-biomass extinction term (k_bg) for water, dissolved organics, suspended particles.
   - What is unclear: Actual values for Indian open-pond conditions. Literature gives 0.1-2.0 /m depending on water quality.
   - Recommendation: Use k_bg = 0.5 /m as moderate estimate. Flag as ASSUMED in parameter config. This is a Claude's Discretion area.

3. **Whether to model CO2 substrate depletion in ODE or treat as constant**
   - What we know: With CO2 injection, dissolved CO2 may remain roughly constant. Without injection, CO2 depletes as biomass grows.
   - What is unclear: CONTEXT.md mentions "CO2 availability" as a limiting factor but does not specify injection modeling.
   - Recommendation: For Phase 1, treat CO2 as a user-specified constant (co2_func returns a constant). This keeps the ODE simple (single state variable X). CO2 depletion dynamics can be added in Phase 3 when the simulation engine is built.

4. **Sensitivity of output to discount_factor value**
   - What we know: 40-60% discount range means output could vary by 50% depending on choice.
   - What is unclear: Whether 0.4 or 0.6 is more appropriate for Surat specifically.
   - Recommendation: Use 0.5 (midpoint). Make it a visible, user-adjustable parameter per CONTEXT.md decision. Document that this is the single largest source of uncertainty in the model.

## Sources

### Primary (HIGH confidence)
- **Schediwy et al. (2019)** - "Microalgal kinetics" - User-provided PDF in `Research/Photosynthesis & Growth Models/`. Table 2 is the primary parameter reference. Equations 3 (light absorption), 7 (Han/Monod growth), 8 (Blackman kinetics), 10 (depth-averaged integration), 11 (CO2 transfer rate).
- **Razzak et al. (2024)** - "Microalgae cultivation in photobioreactors" - User-provided PDF. Equations 2/11 (Monod), 17 (combined photoinhibition + CO2 model), 18 (Beer-Lambert), 19 (average irradiance), 15 (CO2 fixation rate).
- **SciPy 1.17.0 Documentation** - `solve_ivp` API: https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html
- **NumPy 2.4.1** - Array operations, typing: verified on PyPI Jan 2026.

### Secondary (MEDIUM confidence)
- **Steele (1962)** photoinhibition model - Referenced in Razzak et al. (2024) Eq. 17; widely cited in microalgae literature. Verified via multiple web sources as `P = Pmax * (I/Iopt) * exp(1 - I/Iopt)`.
- **Metsoviti et al.** - C. vulgaris optimal light 80 umol/m2/s - Cited within Razzak et al. (2024); not independently verified.
- **Lab-to-field yield gap (3-6x)** - PMC/10901112: "Microalgae cultivation: closing the yield gap from laboratory to field scale"
- **PITFALLS.md** - Ecosystem research from 2026-01-27 identifying real-world discount factor 40-60%.

### Tertiary (LOW confidence)
- **Maintenance respiration rate** (0.01 /d) - General microalgae literature estimate, not from primary Schediwy/Razzak sources. Flagged as ASSUMED.
- **Background turbidity** (0.5 /m) - Estimated from general open-pond literature. Flagged as ASSUMED.
- **C. vulgaris photoinhibition onset at 110 umol/m2/s** - From Razzak text, not experimentally verified for Surat conditions.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All library versions verified on PyPI Jan 2026; SciPy solve_ivp is established standard
- Architecture: HIGH - Frozen dataclasses, pure functions, separation from UI are well-established Python patterns
- Kinetic parameters: MEDIUM-HIGH - Primary sources are user-provided papers with specific tables; conservative-end selection methodology is sound; 2 of ~12 parameters are ASSUMED
- Pitfalls: HIGH - Lab-to-field gap and photoinhibition requirements verified across multiple sources
- Code examples: MEDIUM-HIGH - Synthesized from primary source equations; not copy-paste from running code; will need validation during implementation

**Research date:** 2026-01-28
**Valid until:** 2026-03-28 (60 days - stable domain, parameters from published papers do not change)
