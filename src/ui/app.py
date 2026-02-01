# AlgaeGrowth Simulator -- Streamlit entry point
# Run with: streamlit run src/ui/app.py

import streamlit as st

# st.set_page_config MUST be the very first Streamlit command.
st.set_page_config(
    page_title="AlgaeGrowth Simulator",
    page_icon=":material/eco:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# All other imports come AFTER set_page_config to avoid StreamlitAPIException.
from src.climate.loader import load_city_climate  # noqa: E402
from src.config.loader import load_species_params  # noqa: E402
from src.models.parameters import CityClimate, GrowthParams, SimulationConfig, SpeciesParams  # noqa: E402
from src.simulation.engine import run_simulation  # noqa: E402
from src.ui.results import display_results  # noqa: E402
from src.ui.sidebar import render_sidebar  # noqa: E402


# ---------------------------------------------------------------------------
# Cached simulation wrapper
# ---------------------------------------------------------------------------
# Uses hash_funcs for frozen dataclasses so Streamlit can hash the inputs.
# show_spinner=False because we wrap the call in our own st.spinner.

@st.cache_data(
    hash_funcs={
        SimulationConfig: hash,
        SpeciesParams: hash,
        CityClimate: hash,
    },
    show_spinner=False,
)
def cached_simulation(
    config: SimulationConfig,
    species: SpeciesParams,
    climate: CityClimate,
):
    """Run simulation with Streamlit caching.

    Frozen dataclasses are hashable, so identical inputs return cached
    results instantly without re-computation.
    """
    return run_simulation(config, species, climate)


# ---------------------------------------------------------------------------
# Main application flow
# ---------------------------------------------------------------------------

# 1. Load default species and climate (file-based, fast)
species = load_species_params()
default_climate = load_city_climate()

# 2. Render sidebar and collect user inputs
inputs = render_sidebar(default_climate, species)

# 3. Rebuild species from sidebar inputs (frozen dataclass, must reconstruct)
species = SpeciesParams(
    name=species.name,
    growth=GrowthParams(
        mu_max=inputs["mu_max"],
        Ks_co2=inputs["ks_co2"],
        I_opt=inputs["i_opt"],
        r_maintenance=species.growth.r_maintenance,
        discount_factor=species.growth.discount_factor,
    ),
    light=species.light,
    carbon_content=species.carbon_content,
    co2_to_biomass_ratio=species.co2_to_biomass_ratio,
)

# 4. Build SimulationConfig from sidebar inputs
config = SimulationConfig(
    duration_days=inputs["duration_days"],
    start_month=inputs["start_month"],
    initial_biomass=inputs["initial_biomass"],
    harvest_threshold=inputs["harvest_threshold"],
    co2_concentration=inputs["co2_concentration"],
    depth=inputs["depth"],
    surface_area=inputs["surface_area"],
)

# 5. Determine climate source (default Surat or user override)
climate = inputs["override_climate"] if inputs["climate_overridden"] else default_climate

# 6. Page header
st.title("AlgaeGrowth Simulator")
st.caption(
    "Estimate CO2 capture from open-pond microalgae cultivation. "
    "Adjust parameters in the sidebar and click **Run Simulation**."
)

# 7. Track user interaction via session state
if inputs["run_clicked"]:
    st.session_state["has_run"] = True

# 8. Always run simulation (pre-loaded default on first visit, cached thereafter)
#    Validation errors block the Run button but NOT the default pre-load.
with st.spinner("Running simulation..."):
    result = cached_simulation(config, species, climate)

display_results(result, climate, config)
