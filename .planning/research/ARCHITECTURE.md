# Architecture Patterns: Algae Growth Simulation Web App

**Domain:** Scientific simulation web application (photobioreactor modeling)
**Researched:** 2026-01-27
**Overall Confidence:** HIGH (verified with Streamlit official documentation)

## Executive Summary

Scientific simulation web apps built with Streamlit follow a **separation of concerns** pattern: UI layer (Streamlit pages), simulation engine (pure Python/NumPy), and data layer (climate inputs, configuration). The key architectural challenge is managing Streamlit's **re-execution model** where the entire script runs top-to-bottom on every user interaction.

For an algae growth simulation with Monod equations and Beer-Lambert light attenuation, the recommended architecture uses:
- **Multipage app** with `st.navigation` for organized user flow
- **Cached simulation engine** using `@st.cache_data` to avoid re-running expensive ODE solves
- **Modular Python packages** separating simulation logic from UI code
- **Dataclass-based configuration** for type-safe parameter passing

---

## Recommended Architecture

```
pbr-simulator/
├── streamlit_app.py          # Entry point + router
├── pages/
│   ├── 01_inputs.py          # Climate + farm setup page
│   ├── 02_simulation.py      # Run simulation + view results
│   └── 03_analysis.py        # Charts, exports, CO2 estimates
├── src/
│   ├── __init__.py
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── engine.py         # Main simulation orchestrator
│   │   ├── growth.py         # Monod equations
│   │   ├── light.py          # Beer-Lambert attenuation
│   │   └── co2.py            # CO2 capture calculations
│   ├── climate/
│   │   ├── __init__.py
│   │   ├── data.py           # Climate data structures
│   │   ├── surat_defaults.py # Built-in Surat climate data
│   │   └── loader.py         # User override handling
│   └── models/
│       ├── __init__.py
│       ├── parameters.py     # Dataclasses for all parameters
│       └── results.py        # Simulation result structures
├── data/
│   └── surat_climate.json    # Default climate dataset
├── tests/
│   ├── test_growth.py
│   ├── test_light.py
│   └── test_engine.py
└── requirements.txt
```

---

## Component Boundaries

| Component | Responsibility | Communicates With | Cacheable |
|-----------|---------------|-------------------|-----------|
| **streamlit_app.py** | Router, global config, session state init | All pages | No |
| **pages/01_inputs.py** | Collect user inputs, validate, store in session | session_state, climate module | No |
| **pages/02_simulation.py** | Trigger simulation, display progress, cache results | simulation engine, session_state | Yes (results) |
| **pages/03_analysis.py** | Render charts, calculate summaries, export data | cached results, Plotly | No |
| **src/simulation/engine.py** | Orchestrate full simulation run | growth, light, co2 modules | Yes |
| **src/simulation/growth.py** | Monod equation implementation, ODE solving | scipy.integrate | Yes |
| **src/simulation/light.py** | Beer-Lambert calculations per depth layer | NumPy | Yes |
| **src/simulation/co2.py** | CO2 fixation from biomass growth | growth results | Yes |
| **src/climate/data.py** | Climate parameter dataclasses | None (pure data) | N/A |
| **src/climate/surat_defaults.py** | Hardcoded Surat seasonal data | climate/data.py | N/A |
| **src/models/parameters.py** | Input parameter dataclasses | None (pure data) | N/A |
| **src/models/results.py** | Result container dataclasses | None (pure data) | N/A |

---

## Data Flow

### User Input Flow
```
User Input (widgets)
    ↓
pages/01_inputs.py validates → stores in st.session_state
    ↓
SimulationParameters dataclass created
    ↓
Passed to simulation engine
```

### Simulation Flow
```
SimulationParameters
    ↓
engine.py orchestrates:
    1. climate.loader → ClimateData (hourly T, solar, etc.)
    2. For each time step:
       a. light.py → I(depth) via Beer-Lambert
       b. growth.py → μ(I, nutrients) via Monod
       c. ODE solver → biomass at t+dt
       d. co2.py → CO2 captured
    ↓
SimulationResults dataclass
    ↓
Cached with @st.cache_data
    ↓
Stored in st.session_state for pages to access
```

### Visualization Flow
```
SimulationResults (from cache or session_state)
    ↓
pages/03_analysis.py:
    - Plotly figures (growth curves, CO2 capture)
    - Summary statistics
    - Export buttons (CSV, JSON)
```

---

## Patterns to Follow

### Pattern 1: Separation of Simulation from UI
**What:** Keep all simulation logic in `src/simulation/` with zero Streamlit imports. The simulation engine should be callable from tests, notebooks, or CLI without Streamlit.

**Why:**
- Testability: Unit test growth equations without mocking Streamlit
- Reusability: Same engine could power a FastAPI backend later
- Maintainability: Physics changes don't touch UI code

**Example:**
```python
# src/simulation/growth.py - NO Streamlit imports
from dataclasses import dataclass
import numpy as np
from scipy.integrate import solve_ivp

@dataclass
class MonodParameters:
    mu_max: float      # Maximum specific growth rate (1/day)
    Ks: float          # Half-saturation constant (g/L)
    Y_xs: float        # Biomass yield coefficient

def monod_growth_rate(S: float, params: MonodParameters) -> float:
    """Calculate specific growth rate using Monod kinetics."""
    return params.mu_max * S / (params.Ks + S)

def simulate_growth(
    X0: float,
    S0: float,
    params: MonodParameters,
    t_span: tuple[float, float],
    light_intensity: callable
) -> np.ndarray:
    """Solve growth ODE. Returns (t, X, S) arrays."""
    def ode_system(t, y):
        X, S = y
        I = light_intensity(t)
        mu = monod_growth_rate(S, params) * light_factor(I)
        dX_dt = mu * X
        dS_dt = -mu * X / params.Y_xs
        return [dX_dt, dS_dt]

    sol = solve_ivp(ode_system, t_span, [X0, S0], dense_output=True)
    return sol
```

```python
# pages/02_simulation.py - UI layer only
import streamlit as st
from src.simulation.engine import run_simulation
from src.models.parameters import SimulationParameters

@st.cache_data
def cached_simulation(params: SimulationParameters):
    """Cache expensive simulation results."""
    return run_simulation(params)

# ... UI code that calls cached_simulation
```

### Pattern 2: Dataclass Parameters for Cache Hashing
**What:** Use frozen dataclasses for all simulation parameters. Streamlit can hash these for caching.

**Why:**
- `@st.cache_data` needs hashable inputs
- Dataclasses provide clear API contracts
- Frozen prevents accidental mutation

**Example:**
```python
# src/models/parameters.py
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ClimateParameters:
    location: str
    temperature_avg: float      # Celsius
    solar_radiation: float      # W/m2
    day_length: float          # hours
    season: str

@dataclass(frozen=True)
class ReactorParameters:
    depth: float               # meters
    surface_area: float        # m2
    initial_biomass: float     # g/L

@dataclass(frozen=True)
class SimulationParameters:
    climate: ClimateParameters
    reactor: ReactorParameters
    duration_days: int
    time_step_hours: float = 1.0
```

### Pattern 3: Cached Simulation with TTL
**What:** Cache simulation results with appropriate TTL and max_entries to prevent memory bloat.

**Why:**
- Simulations can take seconds to minutes
- Users iterate on parameters frequently
- Memory limits on Streamlit Cloud

**Example:**
```python
@st.cache_data(
    ttl=3600,           # Cache for 1 hour
    max_entries=10,     # Keep last 10 simulations
    show_spinner="Running simulation..."
)
def run_cached_simulation(params: SimulationParameters) -> SimulationResults:
    return run_simulation(params)
```

### Pattern 4: Forms for Batch Input
**What:** Group related inputs in `st.form()` to prevent re-runs on each keystroke.

**Why:**
- Typing in a number field causes re-run without forms
- Forms submit all inputs together
- Better UX for parameter entry

**Example:**
```python
with st.form("simulation_params"):
    col1, col2 = st.columns(2)
    with col1:
        depth = st.number_input("Reactor Depth (m)", 0.1, 1.0, 0.3)
        area = st.number_input("Surface Area (m2)", 1.0, 100.0, 10.0)
    with col2:
        duration = st.slider("Duration (days)", 1, 365, 30)

    submitted = st.form_submit_button("Run Simulation")
    if submitted:
        params = build_parameters(depth, area, duration)
        st.session_state.params = params
```

### Pattern 5: Router Pattern for Multipage
**What:** Use `st.navigation` in entry point as a router, with common elements (header, state init) in the frame.

**Why:**
- Consistent navigation across pages
- Global state initialization happens once
- Common styling/branding in one place

**Example:**
```python
# streamlit_app.py
import streamlit as st

st.set_page_config(
    page_title="PBR Simulator",
    page_icon="🌿",
    layout="wide"
)

# Initialize session state once
if "simulation_results" not in st.session_state:
    st.session_state.simulation_results = None

# Define pages
pages = [
    st.Page("pages/01_inputs.py", title="Setup", icon="⚙️"),
    st.Page("pages/02_simulation.py", title="Simulate", icon="▶️"),
    st.Page("pages/03_analysis.py", title="Results", icon="📊"),
]

# Router
pg = st.navigation(pages)
pg.run()
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Simulation Logic in UI Code
**What:** Putting ODE equations directly in Streamlit page files.

**Why Bad:**
- Cannot unit test physics without Streamlit
- Mixing concerns makes debugging hard
- Cannot reuse simulation logic elsewhere

**Instead:** Keep all math in `src/simulation/`, import into pages.

### Anti-Pattern 2: Uncached Heavy Computations
**What:** Running ODE solver without `@st.cache_data`.

**Why Bad:**
- Every widget interaction re-runs simulation
- Multi-second delays on every click
- Poor user experience

**Instead:** Cache simulation results keyed by parameters.

### Anti-Pattern 3: Mutable Session State for Parameters
**What:** Storing simulation parameters as mutable dicts in session_state.

**Why Bad:**
- Cannot use as cache key (unhashable)
- Accidental mutation bugs
- No type safety

**Instead:** Use frozen dataclasses, store in session_state.

### Anti-Pattern 4: Single Monolithic Page
**What:** All inputs, simulation, and results on one scrolling page.

**Why Bad:**
- Confusing user flow
- Hard to maintain
- Poor mobile experience

**Instead:** Logical multipage structure: Setup → Run → Analyze.

### Anti-Pattern 5: Loading Large Data Without Caching
**What:** Reading climate CSV on every page load.

**Why Bad:**
- Unnecessary I/O on each interaction
- Slows down responsiveness

**Instead:**
```python
@st.cache_data
def load_climate_data():
    return pd.read_csv("data/surat_climate.csv")
```

### Anti-Pattern 6: Button-Only State Changes
**What:** Using button clicks as the only way to trigger actions, without storing state.

**Why Bad:**
- Button value resets to False on next rerun
- Logic conditioned on button won't persist
- Leads to "nothing happens" bugs

**Instead:** Store action results in session_state, use button to trigger state change.

---

## Simulation Engine Architecture

### Core Equations

**Monod Growth Model:**
```
μ = μmax * S / (Ks + S)
dX/dt = μ * X
dS/dt = -μ * X / Yxs
```

Where:
- μ: specific growth rate (1/day)
- μmax: maximum growth rate
- S: limiting substrate concentration
- Ks: half-saturation constant
- X: biomass concentration
- Yxs: yield coefficient

**Beer-Lambert Light Attenuation:**
```
I(d) = I0 * exp(-k * C * d)
```

Where:
- I(d): light intensity at depth d
- I0: incident light at surface
- k: extinction coefficient (includes biomass + water)
- C: biomass concentration
- d: depth in reactor

**Light-Limited Growth Integration:**
For photobioreactors, light varies with depth. Integrate growth across depth layers:

```python
def calculate_average_growth_rate(I0, biomass_conc, depth, k, monod_params):
    """Calculate depth-averaged growth rate."""
    n_layers = 10
    dz = depth / n_layers
    total_mu = 0

    for i in range(n_layers):
        z = (i + 0.5) * dz  # midpoint
        I = I0 * np.exp(-k * biomass_conc * z)
        mu = light_response(I) * monod_growth_rate(S, monod_params)
        total_mu += mu

    return total_mu / n_layers
```

### ODE Solver Selection

**Recommendation:** Use `scipy.integrate.solve_ivp` with method='RK45' (default).

**Rationale:**
- RK45 is adaptive, handles stiff transitions well
- Well-tested FORTRAN implementation
- Appropriate for multi-day simulations

**Configuration:**
```python
from scipy.integrate import solve_ivp

solution = solve_ivp(
    ode_system,
    t_span=(0, duration_days),
    y0=[X0, S0],
    method='RK45',
    t_eval=np.arange(0, duration_days, dt),
    rtol=1e-6,
    atol=1e-9
)
```

---

## Climate Data Module Structure

### Data Structure for Surat Climate
```python
@dataclass
class HourlyClimate:
    hour: int
    temperature: float      # Celsius
    solar_radiation: float  # W/m2
    humidity: float         # %

@dataclass
class DailyClimate:
    date: str
    hours: list[HourlyClimate]
    sunrise: float          # hour (e.g., 6.5)
    sunset: float           # hour (e.g., 18.5)

@dataclass
class SeasonalPattern:
    season: str             # "monsoon", "winter", "summer"
    months: list[int]
    avg_temperature: float
    avg_solar_radiation: float
    cloud_cover_factor: float
```

### User Override Strategy
```python
def get_climate_data(
    location: str = "surat",
    user_override: Optional[pd.DataFrame] = None
) -> ClimateData:
    """
    Returns climate data, preferring user upload over defaults.
    """
    if user_override is not None:
        return parse_user_climate(user_override)

    if location == "surat":
        return load_surat_defaults()

    raise ValueError(f"Unknown location: {location}")
```

---

## Suggested Build Order

Based on component dependencies:

### Phase 1: Foundation (No UI)
1. **src/models/parameters.py** - Define all dataclasses first
2. **src/models/results.py** - Result containers
3. **src/simulation/growth.py** - Monod equations (testable in isolation)
4. **src/simulation/light.py** - Beer-Lambert (testable in isolation)
5. **tests/test_growth.py, tests/test_light.py** - Verify math

**Rationale:** Pure Python, no Streamlit dependency. Can verify equations match literature.

### Phase 2: Climate Module
6. **src/climate/data.py** - Climate dataclasses
7. **src/climate/surat_defaults.py** - Hardcoded defaults
8. **src/climate/loader.py** - User override logic

**Rationale:** Climate inputs are needed before full simulation can run.

### Phase 3: Simulation Engine
9. **src/simulation/co2.py** - CO2 calculations
10. **src/simulation/engine.py** - Orchestrate full run
11. **tests/test_engine.py** - Integration test

**Rationale:** Engine depends on growth, light, and climate modules.

### Phase 4: Basic UI
12. **streamlit_app.py** - Router setup
13. **pages/01_inputs.py** - Parameter entry forms
14. **pages/02_simulation.py** - Run button + basic output

**Rationale:** Minimal viable interface to run simulations.

### Phase 5: Visualization & Polish
15. **pages/03_analysis.py** - Plotly charts
16. Add export functionality (CSV, JSON)
17. Improve styling, add help text

**Rationale:** Visualization depends on simulation results being available.

---

## Scalability Considerations

| Concern | 1-10 Users (Dev) | 100 Users (Launch) | 1000+ Users |
|---------|------------------|-------------------|-------------|
| **Compute** | Single process OK | Streamlit Cloud handles | Consider FastAPI backend |
| **Caching** | In-memory fine | Use disk cache + TTL | Redis or external cache |
| **State** | session_state OK | session_state OK | Database for persistence |
| **Simulation Time** | <10s OK | Cache aggressively | Pre-compute common scenarios |

**Streamlit Cloud Limits:**
- 1GB memory per app
- No persistent storage (cache resets on restart)
- Suitable for interactive exploration, not batch processing

---

## Sources

### Official Documentation (HIGH Confidence)
- [Streamlit Architecture - Execution Model](https://docs.streamlit.io/develop/concepts/architecture)
- [Streamlit Design Concepts](https://docs.streamlit.io/develop/concepts/design)
- [st.cache_data API Reference](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data)
- [Multipage Apps with st.navigation](https://docs.streamlit.io/develop/concepts/multipage-apps/page-and-navigation)
- [Button Behavior and Examples](https://docs.streamlit.io/develop/concepts/design/buttons)

### Scientific Modeling (MEDIUM-HIGH Confidence)
- [Monod Equation Overview - ScienceDirect](https://www.sciencedirect.com/topics/engineering/monod-equation)
- [Light Attenuation in Photobioreactors - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S2211926417309992)
- [Beer-Lambert Calculation in PBRs - Springer](https://link.springer.com/article/10.1007/BF02931920)
- [Python ODE Solvers - Berkeley](https://pythonnumericalmethods.berkeley.edu/notebooks/chapter22.06-Python-ODE-Solvers.html)

### Community Patterns (MEDIUM Confidence)
- [Project Structure for Large Streamlit Apps - Streamlit Forum](https://discuss.streamlit.io/t/project-structure-for-medium-and-large-apps-full-example-ui-and-logic-splitted/59967)
- [Streamlit Best Practices - Streamlit Forum](https://discuss.streamlit.io/t/streamlit-best-practices/57921)
- [Clean Architecture with Streamlit - Streamlit Forum](https://discuss.streamlit.io/t/clean-architecture-with-streamlit/15262)
- [SimService: Simulation Services in Python - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10809901/)

### Climate/Weather Data (MEDIUM Confidence)
- [pvlib-python for Solar Radiation](https://pvlib-python.readthedocs.io/en/v0.4.0/forecasts.html)
- [Meteostat Python Library](https://dev.meteostat.net/python)
