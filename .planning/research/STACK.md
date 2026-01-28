# Technology Stack

**Project:** AlgaeGrowth Simulator (Photobioreactor CO2 Capture)
**Researched:** 2026-01-27
**Research Mode:** Ecosystem (Stack dimension)

## Executive Summary

For a Python-based Streamlit web app simulating algae growth with Monod kinetics and Beer-Lambert light attenuation, the recommended stack centers on **SciPy for ODE solving**, **NumPy for numerical operations**, **Plotly for interactive visualization**, and **Pydantic for parameter validation**. All versions verified current as of January 2026.

**Key constraint:** Streamlit Cloud's 1GB memory limit and Python version requirements dictate careful library selection. NumPy 2.x and SciPy 1.17+ require Python >= 3.11, which is fully supported.

---

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | 3.12 | Runtime | Sweet spot: supported by all libraries, not bleeding-edge 3.14. Streamlit Cloud supports released Python versions with security updates. | HIGH |
| Streamlit | >= 1.53.1 | Web framework | User-specified constraint. Free Streamlit Cloud deployment. Released Jan 22, 2026. Requires Python >= 3.10. | HIGH |

**Rationale for Python 3.12:**
- NumPy 2.4.1 requires Python >= 3.11
- SciPy 1.17.0 requires Python >= 3.11
- Pandas 3.0.0 requires Python >= 3.11
- Streamlit 1.53.1 supports 3.10-3.14
- 3.12 is stable, widely supported, avoids 3.14's potential edge cases

### Numerical & Scientific Computing

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| NumPy | >= 2.4.1 | Array operations, Beer-Lambert calculations | Foundation for all numerical work. Version 2.x has improved typing support (`numpy.typing.NDArray`). Released Jan 10, 2026. | HIGH |
| SciPy | >= 1.17.0 | ODE solving (Monod kinetics), integration | `scipy.integrate.solve_ivp` is the standard for solving differential equations. Supports 6 methods including stiff-equation solvers (Radau, BDF, LSODA). Released Jan 10, 2026. | HIGH |
| Pandas | >= 3.0.0 | Time series data, climate data handling | Standard for tabular data manipulation. New 3.0 release (Jan 21, 2026) with improved performance. | HIGH |

**ODE Solver Choice:**

For Monod kinetics growth models, use `scipy.integrate.solve_ivp` with:
- **Default method:** `RK45` (5th order Runge-Kutta) for most simulations
- **Stiff problems:** Switch to `Radau`, `BDF`, or `LSODA` if simulation shows numerical instability

```python
from scipy.integrate import solve_ivp

# Example: Monod growth with light limitation
solution = solve_ivp(
    fun=monod_growth_model,
    t_span=(0, simulation_days),
    y0=[initial_biomass, initial_substrate],
    method='RK45',  # or 'LSODA' for auto-stiffness detection
    t_eval=time_points,
    dense_output=True
)
```

### Data Visualization

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Plotly | >= 6.5.2 | Interactive charts | Native Streamlit integration via `st.plotly_chart()`. 40+ chart types including scientific visualizations. Interactive zoom/pan essential for time-series simulation data. Released Jan 14, 2026. | HIGH |

**Why Plotly over Matplotlib:**
- **Interactive:** Users can zoom into specific time periods, hover for exact values
- **Native integration:** `st.plotly_chart()` is simpler than `st.pyplot()`
- **Publication quality:** Suitable for reports and presentations
- **Animation support:** Can animate growth over time if needed

**Do NOT use:**
- `matplotlib` alone: Static plots less useful for simulation exploration
- `Altair`: Good for declarative viz, but Plotly better for scientific time-series
- `Bokeh`: Overkill for this use case, adds complexity

### Data Validation

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Pydantic | >= 2.12.5 | Parameter validation | Validate user inputs (temperature ranges, pond dimensions, growth parameters). Type hints + runtime validation. Rust-based core = fast. Released Nov 26, 2025. | HIGH |

**Why Pydantic:**
- Scientific simulations need rigorous input validation (e.g., temperature 0-50C, not negative)
- Clear error messages for users when inputs are invalid
- Type hints improve code maintainability
- Works seamlessly with Streamlit forms

```python
from pydantic import BaseModel, Field, field_validator

class SimulationParameters(BaseModel):
    temperature_celsius: float = Field(ge=0, le=50, description="Water temperature")
    pond_depth_meters: float = Field(gt=0, le=2.0, description="Pond depth")
    light_intensity: float = Field(ge=0, description="PAR in umol/m2/s")

    @field_validator('temperature_celsius')
    @classmethod
    def validate_algae_survival(cls, v):
        if v > 45:
            raise ValueError("Most algae species cannot survive above 45C")
        return v
```

### Climate/Weather Data

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Open-Meteo API | N/A (API) | Historical climate data | Free, no API key needed for non-commercial use. 80+ years of hourly data. 10km resolution. Ideal for Surat historical averages. | MEDIUM |
| requests | >= 2.31.0 | HTTP client | Standard Python HTTP library for API calls | HIGH |

**Alternative options (if Open-Meteo insufficient):**
- **OpenWeatherMap:** Solar radiation API available, requires API key, has free tier
- **Visual Crossing:** Comprehensive solar data, free tier up to 1000 records/day
- **Static data:** For MVP, embed monthly Surat averages directly (simplest)

**Recommendation for v1:** Embed static monthly Surat climate averages in code. Add API integration in v2 for dynamic/custom dates.

### Type Hints

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| numpy.typing | (bundled with NumPy) | Array type hints | `NDArray[np.float64]` for precise typing. NumPy 2.1+ has full shape typing. | HIGH |

```python
from numpy.typing import NDArray
import numpy as np

def calculate_light_profile(
    I0: float,
    Ka: float,
    biomass: float,
    depths: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Beer-Lambert light attenuation."""
    return I0 * np.exp(-Ka * biomass * depths)
```

---

## Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dateutil | >= 2.8.2 | Date parsing | If handling user-input date ranges |
| pytz | >= 2024.1 | Timezone handling | For Surat IST timezone conversions |

---

## Development Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| pytest | >= 8.0.0 | Testing |
| mypy | >= 1.8.0 | Static type checking |
| ruff | >= 0.1.0 | Linting + formatting |

---

## Alternatives Considered

### Web Framework Alternatives

| Recommended | Alternative | Why Not Alternative |
|-------------|-------------|---------------------|
| Streamlit | Dash | User specified Streamlit. Dash requires callbacks + HTML knowledge. More complex for rapid prototyping. |
| Streamlit | Panel | Steeper learning curve. Better for complex multi-page apps, overkill for MVP simulator. |
| Streamlit | Gradio | Designed for ML demos, not scientific simulations. Limited charting options. |

**Verdict:** Streamlit is correct for this use case - simple deployment, good scientific viz support, free cloud hosting.

### ODE Solver Alternatives

| Recommended | Alternative | Why Not Alternative |
|-------------|-------------|---------------------|
| scipy.integrate.solve_ivp | diffeqpy | Requires Julia installation. Overkill for Monod kinetics. Adds deployment complexity. |
| scipy.integrate.solve_ivp | scipy.integrate.odeint | Legacy API. solve_ivp is the modern replacement with better interface and more methods. |
| scipy.integrate.solve_ivp | Hand-coded Euler/RK4 | Reinventing the wheel. Less accurate, more bugs, no stiff-equation handling. |

**Verdict:** `solve_ivp` is the standard. No reason to deviate.

### Visualization Alternatives

| Recommended | Alternative | Why Not Alternative |
|-------------|-------------|---------------------|
| Plotly | Matplotlib | Static only. Interactive exploration critical for simulations. |
| Plotly | Altair | Declarative grammar good for exploration, but Plotly better for scientific plots and has more chart types. |
| Plotly | Bokeh | More complex API. Plotly's Streamlit integration is simpler. |

**Verdict:** Plotly's interactivity + native Streamlit support makes it the clear choice.

### Validation Alternatives

| Recommended | Alternative | Why Not Alternative |
|-------------|-------------|---------------------|
| Pydantic | dataclasses + manual validation | More boilerplate, less robust error messages, no nested validation. |
| Pydantic | attrs | Good library, but Pydantic has better FastAPI/Streamlit ecosystem, better docs. |
| Pydantic | cerberus | Schema-based, not type-hint based. Less Pythonic, more verbose. |

**Verdict:** Pydantic is the Python ecosystem standard for validation.

---

## Streamlit Cloud Constraints

**Critical limitations affecting stack choices:**

| Constraint | Impact | Mitigation |
|------------|--------|------------|
| 1GB memory limit | Cannot load huge datasets or run massive Monte Carlo | Use efficient NumPy operations; pre-compute Surat climate data |
| Debian 11 base | Some native libraries may have version constraints | Stick to pure-Python or wheel-available packages |
| US hosting only | Latency for India users | Acceptable for MVP; consider edge deployment later |
| 3 app limit (free) | Only one deployment slot for this project | Fine for single MVP |
| Python version | Must use released versions with security updates | Python 3.12 is safe choice |

**Performance optimization:**
- Use `@st.cache_data` for expensive calculations (ODE solutions, climate data loading)
- Use `@st.cache_resource` for any ML models or heavy objects (not needed for v1)

```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def run_simulation(params: SimulationParameters) -> pd.DataFrame:
    """Cache simulation results by parameter hash."""
    ...
```

---

## Installation

### requirements.txt

```
# Core
streamlit>=1.53.1
numpy>=2.4.1
scipy>=1.17.0
pandas>=3.0.0
plotly>=6.5.2
pydantic>=2.12.5

# HTTP client (for future API integration)
requests>=2.31.0

# Date handling
python-dateutil>=2.8.2
```

### pyproject.toml (recommended)

```toml
[project]
name = "algae-growth-simulator"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "streamlit>=1.53.1",
    "numpy>=2.4.1",
    "scipy>=1.17.0",
    "pandas>=3.0.0",
    "plotly>=6.5.2",
    "pydantic>=2.12.5",
    "requests>=2.31.0",
    "python-dateutil>=2.8.2",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "mypy>=1.8.0",
    "ruff>=0.1.0",
]

[tool.mypy]
plugins = ["numpy.typing.mypy_plugin"]
```

### .python-version (for Streamlit Cloud)

```
3.12
```

---

## What NOT to Use

| Technology | Reason |
|------------|--------|
| TensorFlow/PyTorch | No ML needed for Monod kinetics. Massive overhead. Would likely exceed Streamlit Cloud memory. |
| Dask | Parallel computing overkill for single-user simulator with small datasets. |
| SQLAlchemy/databases | v1 has no persistence requirement. State is ephemeral per session. |
| FastAPI | Backend API not needed when Streamlit handles everything. |
| Docker | Streamlit Cloud handles deployment. No custom container needed. |
| Jupyter | Not a deployment platform. Use for exploration, not production. |
| diffeqpy | Julia dependency adds deployment complexity for no benefit. |

---

## Sources

### Verified via Official Documentation (HIGH confidence)

- Streamlit 1.53.1: https://pypi.org/project/streamlit/ (released Jan 22, 2026)
- NumPy 2.4.1: https://pypi.org/project/numpy/ (released Jan 10, 2026)
- SciPy 1.17.0: https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html
- Pandas 3.0.0: https://pypi.org/project/pandas/ (released Jan 21, 2026)
- Plotly 6.5.2: https://pypi.org/project/plotly/ (released Jan 14, 2026)
- Pydantic 2.12.5: https://pypi.org/project/pydantic/ (released Nov 26, 2025)
- Streamlit Cloud limits: https://docs.streamlit.io/deploy/streamlit-community-cloud/status

### Framework Comparisons (MEDIUM confidence)

- Streamlit vs Dash vs Panel: https://quansight.com/post/dash-voila-panel-streamlit-our-thoughts-on-the-big-four-dashboarding-tools/
- Panel comparison: https://panel.holoviz.org/explanation/comparisons/compare_streamlit.html

### Scientific Computing Patterns (MEDIUM confidence)

- ODE solving with SciPy: https://pythonnumericalmethods.studentorg.berkeley.edu/notebooks/chapter22.06-Python-ODE-Solvers.html
- Stiff ODE handling: https://scipython.com/books/book2/chapter-8-scipy/examples/solving-a-system-of-stiff-odes/
- Beer-Lambert in photobioreactors: https://link.springer.com/article/10.1007/BF02931920

### Climate Data APIs (MEDIUM confidence)

- Open-Meteo: https://open-meteo.com/
- OpenWeatherMap Solar API: https://openweathermap.org/api/solar-irradiance
- Visual Crossing: https://www.visualcrossing.com/weather-api/

---

## Roadmap Implications

1. **Phase 1 (Foundation):** Set up Python 3.12 + Streamlit skeleton with Pydantic parameter models
2. **Phase 2 (Core Model):** Implement Monod growth + Beer-Lambert in NumPy/SciPy
3. **Phase 3 (Climate Data):** Embed static Surat monthly averages
4. **Phase 4 (Visualization):** Plotly interactive charts for growth + CO2 curves
5. **Phase 5 (Deployment):** Streamlit Cloud deployment with caching optimization

**No deeper research needed for stack choices.** All libraries are well-established with stable APIs. Focus research effort on the growth model equations themselves (Monod kinetics parameters, Beer-Lambert coefficients for specific algae species).
