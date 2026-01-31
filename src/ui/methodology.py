"""Methodology display module for the AlgaeGrowth Simulator.

Renders a collapsible explanation of the CO2 calculation methodology
including plain English summary, LaTeX equations (toggle), and a
dynamic parameter table populated from the actual simulation result.

Uses only standard KaTeX-compatible LaTeX notation per Streamlit's
built-in math rendering engine.
"""

import streamlit as st

from src.models.results import SimulationResult


def display_methodology(result: SimulationResult) -> None:
    """Render calculation methodology in a Streamlit expander.

    Displays three sections:
    1. Plain English summary of the CO2 capture calculation
    2. LaTeX equations (behind a checkbox toggle)
    3. Dynamic parameter table from result.parameters_used

    Args:
        result: Simulation result containing parameters_used for the
                dynamic parameter table.
    """
    with st.expander("Calculation Methodology", expanded=False):
        # --------------------------------------------------------------
        # Section 1: Plain English Summary
        # --------------------------------------------------------------
        st.markdown("""
**How CO2 capture is calculated:**

1. **Growth modeling**: Daily biomass growth is computed using Monod kinetics
   with light-dependent (Beer-Lambert) and temperature-dependent (CTMI) modifiers.
2. **CO2 conversion**: Biomass produced each day is converted to CO2 captured
   using the species-specific carbon content and CO2-to-biomass ratio.
3. **Conservative approach**: Only positive net growth contributes to CO2 capture.
   Maintenance respiration and a lab-to-field discount factor are applied.
4. **Harvest cycling**: When biomass exceeds the harvest threshold, it is reset
   to the initial concentration, simulating periodic harvesting.
""")

        # --------------------------------------------------------------
        # Section 2: Equations (toggle)
        # --------------------------------------------------------------
        show_equations = st.checkbox("Show equations", key="show_equations")

        if show_equations:
            st.markdown("**Monod growth with modifiers:**")
            st.latex(
                r"\mu = \mu_{max} \cdot \frac{S}{K_s + S}"
                r" \cdot f(I) \cdot f(T) \cdot \delta"
            )

            st.markdown("**Daily CO2 conversion:**")
            st.latex(
                r"CO_2 = \Delta B \cdot V \cdot r_{CO_2:bio}"
                r"\quad \text{where} \quad"
                r"r_{CO_2:bio} = \frac{44}{12} \cdot C_{content}"
            )

            st.markdown("**Total tonnes CO2 equivalent:**")
            st.latex(
                r"tCO_2e = \frac{\sum CO_{2,daily}}{1000}"
            )

        # --------------------------------------------------------------
        # Section 3: Parameters Used (dynamic from result)
        # --------------------------------------------------------------
        st.markdown("**Parameters Used**")

        sp = result.parameters_used
        table = (
            "| Parameter | Value |\n"
            "|-----------|-------|\n"
            f"| Species | {sp.name} |\n"
            f"| mu_max | {sp.growth.mu_max} 1/d |\n"
            f"| Ks_CO2 | {sp.growth.Ks_co2} mg/L |\n"
            f"| I_opt | {sp.growth.I_opt} umol/m2/s |\n"
            f"| Maintenance respiration | {sp.growth.r_maintenance} 1/d |\n"
            f"| Discount factor | {sp.growth.discount_factor} |\n"
            f"| Carbon content | {sp.carbon_content} g_C/g_DW |\n"
            f"| CO2:biomass ratio | {sp.co2_to_biomass_ratio} g_CO2/g_DW |\n"
            f"| Light absorption (sigma_x) | {sp.light.sigma_x} m2/g |\n"
            f"| Background turbidity | {sp.light.background_turbidity} 1/m |\n"
        )
        st.markdown(table)

        st.caption(
            "Parameters sourced from peer-reviewed literature. "
            "See species YAML configuration for full citations."
        )
