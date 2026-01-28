# Project Research Summary

**Project:** AlgaeGrowth Simulator (Photobioreactor CO2 Capture)
**Domain:** Scientific simulation web application (carbon credit verification)
**Researched:** 2026-01-27
**Confidence:** HIGH

## Executive Summary

This is a Python/Streamlit web app for simulating algae growth in photobioreactors with CO2 capture quantification, specifically targeting the India carbon credit market in Surat's tropical monsoon climate. Expert practice for scientific simulation apps centers on **separating physics from UI**: implement growth models (Monod kinetics, Beer-Lambert light attenuation) in pure Python modules with SciPy ODE solvers, then wrap with Streamlit UI using aggressive caching to handle re-execution.

The recommended approach uses **Python 3.12 + Streamlit 1.53+ for UI, NumPy/SciPy for numerical simulation, Plotly for interactive visualization, and Pydantic for parameter validation**. Critical architecture pattern: multipage app with cached simulation engine (`@st.cache_data`) to avoid re-running expensive ODE solves on every user interaction. Deploy to free Streamlit Cloud with 1GB memory constraint driving conservative design choices.

The primary risk is **credibility loss through overestimation**: lab-based models routinely overestimate field productivity by 3-6x, and Surat's extreme temperatures (40-44C March-June, monsoon June-September) will crash algae cultures if not explicitly modeled. Mitigation requires conservative productivity baselines (6-10 g/m2/day, not lab's 15-25 g/m2/day), temperature-dependent growth inhibition, and clear disclaimers that simulation outputs support verification workflows but are not verified carbon credits. India's new CCTS system (launching 2026) requires third-party verification regardless of simulation accuracy.

## Key Findings

### Recommended Stack

Python 3.12 with Streamlit 1.53+ provides the foundation. All core scientific libraries (NumPy 2.4.1, SciPy 1.17.0, Pandas 3.0.0) require Python >= 3.11, making 3.12 the sweet spot for stability without bleeding-edge risk. Streamlit Cloud's 1GB memory limit and free tier make it ideal for MVP deployment.

**Core technologies:**
- **SciPy 1.17+**: ODE solving via `solve_ivp` — gold standard for Monod kinetics differential equations, supports 6 solver methods including stiff-equation handlers
- **NumPy 2.4+**: Array operations for Beer-Lambert calculations — foundation for all numerical work, version 2.x has improved typing support
- **Plotly 6.5+**: Interactive visualization — native Streamlit integration, critical for time-series exploration (zoom, hover, pan)
- **Pydantic 2.12+**: Input validation — scientific simulations need rigorous parameter bounds (temperature 0-50C, not negative depths)
- **Streamlit 1.53+**: Web framework — user-specified constraint, free cloud deployment, Python-only (no HTML/CSS/JS needed)

**Key architectural constraint:** Streamlit's re-execution model (entire script runs top-to-bottom on every interaction) requires caching strategy. Use `@st.cache_data` for expensive simulation runs, forms for batch input, and frozen dataclasses for hashable parameters.

### Expected Features

Expert analysis of carbon credit verification requirements, India CCTS regulations, and algae simulation tools reveals clear feature priorities.

**Must have (table stakes):**
- Climate parameter inputs (temperature, humidity, solar radiation, rainfall) with Surat defaults pre-loaded — algae growth is climate-dependent
- Farm setup parameters (pond size, depth, algae species, cultivation method) — buyers need to model specific operations
- Biomass growth visualization (time-series chart) — core output users validate against
- CO2 capture calculation (kg biomass to tCO2e) — the primary deliverable for carbon credit context, must show methodology
- GEI-compatible output — India CCTS requires `(GEI Target - GEI Achieved) x Production Volume` format
- CSV/JSON export — users need data for external reporting to verification bodies
- Parameter transparency — show all model assumptions, equations, and sources for credibility
- Scientific model foundation — Monod equations cited to literature; carbon credit buyers require defensible methodology

**Should have (competitive):**
- Surat-specific climate presets (27C annual avg, monsoon June-Sept 1269mm rainfall, 61% humidity) — zero-config for target market
- Monsoon season modeling — distinct wet (80%+ rainfall) vs dry season, critical for Surat accuracy
- Real-time parameter adjustment — sliders update charts without page reload, encourages exploration
- Scenario comparison — side-by-side baseline vs project, critical for additionality verification
- Multi-species comparison (Chlorella vs Spirulina) — optimize for CO2 capture rate
- Temperature stress modeling — Surat hits 40C+ in summer, most algae species fail above 35C
- Uncertainty bounds — conservative estimates alongside primary, follows VCS principles

**Defer (v2+):**
- PDF verification reports — nice-to-have, not blocking; add after auditor feedback
- User authentication — no validated need for MVP; add when usage patterns demand saved simulations
- Real-time satellite integration — expensive DMRV systems cost millions; use validated climate data APIs instead
- Verification checklist output — requires deep VVB (Validation/Verification Body) workflow knowledge; defer until real verification attempts

**Anti-features (do NOT build):**
- Automatic carbon credit issuance — only accredited registries (Verra, Gold Standard, ACR) can issue credits; creating fake "credits" destroys credibility
- "Guaranteed" CO2 capture claims — all models have uncertainty; promising exact numbers invites liability
- Blockchain-based credit tracking — India CCTS uses regulated exchanges (CERC), not blockchain; adds complexity without value

### Architecture Approach

Scientific simulation apps built with Streamlit follow **separation of concerns**: UI layer (Streamlit pages), simulation engine (pure Python/NumPy with zero Streamlit imports), and data layer (climate inputs, configuration). The key challenge is managing Streamlit's re-execution model where the entire script runs top-to-bottom on every user interaction, requiring aggressive caching and modular design.

**Major components:**
1. **Multipage UI (`pages/01_inputs.py`, `02_simulation.py`, `03_analysis.py`)** — organized user flow: Setup → Run → Analyze; uses forms for batch input to prevent re-runs on every keystroke
2. **Simulation engine (`src/simulation/`)** — pure Python modules for Monod growth, Beer-Lambert light attenuation, CO2 calculations; fully testable without Streamlit, uses `scipy.integrate.solve_ivp` for ODE solving
3. **Climate module (`src/climate/`)** — dataclasses for climate parameters, hardcoded Surat seasonal defaults, user override handling
4. **Data models (`src/models/`)** — frozen dataclasses for all parameters (SimulationParameters, ClimateParameters, ReactorParameters) to enable `@st.cache_data` hashing

**Critical patterns:**
- Cached simulation with TTL: `@st.cache_data(ttl=3600, max_entries=10)` prevents re-running ODE solver on every interaction
- Dataclass parameters: frozen dataclasses are hashable for cache keys and prevent accidental mutation
- Forms for batch input: group related inputs in `st.form()` to submit all together, avoid keystroke-triggered re-runs

**Build order:** Foundation (dataclasses, pure Python equations, tests) → Climate module → Simulation engine → Basic UI → Visualization. This enables testing physics before building UI.

### Critical Pitfalls

Research identified 7 critical pitfalls; top 5 for roadmap consideration:

1. **Lab-to-field yield gap overestimation** — Simulation produces productivity 3-6x higher than real-world operations (models predict 15-25 g/m2/day, field averages 6 g/m2/day). Models trained on lab data don't capture seasonal variability, operational challenges, or time-dependent photoinhibition. **Prevention:** Use conservative 6-10 g/m2/day baseline from long-term field data, apply 40-60% real-world discount factor, cite validated large-scale operations. **Phase:** Core model development — build conservatism in from day one, cannot retrofit without losing credibility.

2. **Surat temperature extremes not modeled** — Using annual average (27C) masks March-June temperatures of 40-44C that exceed algae thermal tolerance (most species max at 35C), causing culture collapse. Photobioreactor temperatures can exceed ambient by 10-15C under high irradiance. **Prevention:** Model monthly temperature profiles with min/max extremes, include high-temperature growth inhibition (Weibull model), consider thermotolerant strains (Picochlorum sp. tolerates 40C peaks), build culture-crash warnings for >35C. **Phase:** Climate integration — Surat's extreme pre-monsoon heat is defining characteristic.

3. **Monsoon season model failure** — Model doesn't account for Surat's intense monsoon (June-September): 359mm rainfall in July alone, reduced sunlight from cloud cover, humidity spikes (85%+), dilution in open ponds. **Prevention:** Model distinct seasons (Dry Oct-Feb, Hot Mar-May, Monsoon Jun-Sep), reduce light availability during monsoon (cloud cover factor), model pond dilution/overflow for open systems, flag monsoon period as high uncertainty. **Phase:** Climate integration — monsoon is Surat's defining climate feature.

4. **CO2 capture quantification without direct measurement basis** — Claiming "1 kg biomass = 1.88 kg CO2" as universal constant when actual capture varies 40-50% by species and growth conditions. This rough assumption undermines credibility with verifiers. **Prevention:** Use species-specific carbon content percentages with citations, document autotrophic vs mixotrophic growth, show calculation methodology explicitly in UI, present ranges not single values (1.6-2.0 kg CO2/kg), cite sources. **Phase:** CO2 calculation module — core value proposition.

5. **Carbon credit additionality blind spot** — Tool produces CO2 capture numbers but users don't understand additionality requirements (carbon credits require proving counterfactual: what would have happened WITHOUT the project). **Prevention:** Clear disclaimer: "This tool estimates CO2 capture, not carbon credit eligibility", show baseline comparison (with vs. without algae cultivation), educate on additionality, link to ACVA (Accredited Carbon Verifier and Auditor) resources, do NOT imply simulation = verified credits. **Phase:** UI/UX design — frame tool correctly from start to avoid misuse and liability.

## Implications for Roadmap

Based on research, suggested phase structure organized by dependencies and risk mitigation:

### Phase 1: Foundation & Core Model
**Rationale:** Pure Python simulation engine with conservative parameters must come first. Cannot build UI on top of flawed physics. Testability requires zero Streamlit dependencies at this layer.

**Delivers:**
- Python 3.12 environment with requirements.txt (Streamlit, NumPy, SciPy, Pandas, Plotly, Pydantic)
- Dataclass models for all parameters (SimulationParameters, ClimateParameters, ReactorParameters, MonodParameters)
- Monod growth equation implementation with conservative field-validated parameters (6-10 g/m2/day baseline)
- Beer-Lambert light attenuation calculations
- Unit tests for growth and light modules

**Addresses features:**
- Scientific model foundation (table stakes)
- Parameter transparency (table stakes)

**Avoids pitfalls:**
- Lab-to-field overestimation — build in 40-60% real-world discount from day one
- Monod parameter issues — require citations for all kinetics parameters

**Research flag:** SKIP RESEARCH — Monod/Beer-Lambert are well-documented patterns, use established SciPy methods.

### Phase 2: Surat Climate Integration
**Rationale:** Climate is the primary input variable and Surat's extreme conditions (40-44C pre-monsoon, 359mm monsoon rainfall) are make-or-break for model credibility. Must come before UI so defaults are correct.

**Delivers:**
- Hardcoded Surat climate data (monthly temperature ranges 7.6-44C, humidity 42-86%, rainfall 0-359mm/month)
- Three-season model: Dry (Oct-Feb), Hot (Mar-May), Monsoon (Jun-Sep)
- Temperature-dependent growth rate modifier with high-temp inhibition (>35C crash warning)
- Monsoon cloud cover factor reducing PAR availability
- Climate dataclasses and loader module

**Addresses features:**
- Climate parameter inputs with Surat defaults (table stakes)
- Surat-specific climate presets (differentiator)
- Monsoon season modeling (differentiator)
- Temperature stress modeling (differentiator)

**Avoids pitfalls:**
- Surat temperature extremes — explicit March-June productivity crash modeling
- Monsoon season failure — June-September gets reduced light, dilution effects
- Light oversimplification — diurnal and seasonal PAR variation

**Research flag:** SKIP RESEARCH — climate data sources verified (Weather Spark, Climate-Data.org), implementation is data integration not new patterns.

### Phase 3: Simulation Engine & CO2 Calculation
**Rationale:** Orchestrates growth + light + climate into full time-series simulation. CO2 calculation is the core value proposition for carbon credit use case.

**Delivers:**
- ODE solver integration (scipy.integrate.solve_ivp with RK45 method)
- Time-stepped simulation (daily resolution over user-specified duration)
- CO2 capture calculation with species-specific carbon content (40-50% range, cited)
- SimulationResults dataclass with biomass time series, CO2 accumulation, summary statistics
- Integration tests verifying realistic output ranges

**Addresses features:**
- Biomass growth visualization data (table stakes)
- CO2 capture calculation (table stakes)
- CO2 accumulation chart data (table stakes)

**Avoids pitfalls:**
- CO2 quantification without basis — species-specific conversion factors with citations, ranges not point estimates
- Light oversimplification — depth-averaged growth rate across layers

**Research flag:** SKIP RESEARCH — SciPy solve_ivp is standard tool, implementation follows established patterns.

### Phase 4: Streamlit UI (Inputs & Simulation Page)
**Rationale:** With validated physics engine, build minimal UI for parameter entry and simulation triggering. Forms prevent keystroke re-runs, caching prevents redundant solves.

**Delivers:**
- Multipage app router (streamlit_app.py with st.navigation)
- Input page (pages/01_inputs.py) with forms for climate + farm parameters, Surat preset buttons
- Simulation page (pages/02_simulation.py) with cached run function, progress indicator, basic results display
- Session state management for parameters and results
- Pydantic validation with clear error messages

**Addresses features:**
- Climate parameter inputs (table stakes)
- Farm setup parameters (table stakes)
- Surat-specific presets (differentiator)
- Real-time parameter adjustment via sliders (differentiator)

**Avoids pitfalls:**
- Uncached heavy computations — @st.cache_data on simulation function
- Button-only state changes — store results in session_state
- No warning about extreme inputs — Pydantic validators with helpful error messages

**Research flag:** SKIP RESEARCH — Streamlit patterns well-documented in official docs, form/caching patterns verified.

### Phase 5: Visualization & Export
**Rationale:** With working simulation, add interactive charts and data export for carbon credit reporting workflows.

**Delivers:**
- Analysis page (pages/03_analysis.py) with Plotly charts: biomass growth curve, CO2 accumulation curve
- GEI-compatible output display (tCO2e format)
- CSV export of time-series data
- JSON export of full simulation parameters + results
- Methodology documentation panel showing equations, assumptions, parameter sources

**Addresses features:**
- Biomass growth visualization (table stakes)
- CO2 capture calculation display (table stakes)
- CO2 accumulation chart (table stakes)
- GEI-compatible output (table stakes)
- CSV/JSON export (table stakes)
- Parameter transparency (table stakes)

**Avoids pitfalls:**
- Showing only final CO2 number — display intermediate values for validation
- No explanation of assumptions — expandable "How this works" section with citations
- Precision theater — round appropriately, show significant figures only

**Research flag:** SKIP RESEARCH — Plotly Streamlit integration well-documented, CSV export is standard Python.

### Phase 6: Carbon Credit Context & Disclaimers
**Rationale:** Frame tool correctly to avoid liability and user confusion about verification requirements.

**Delivers:**
- Clear disclaimers: "This tool estimates CO2 capture for verification support, not verified carbon credits"
- Additionality education: "Carbon credits require proving counterfactual (what would happen without project)"
- Baseline scenario support (optional "without algae" comparison for additionality narrative)
- Link to India ACVA (Accredited Carbon Verifier and Auditor) resources
- India CCTS context (voluntary market vs. compliance market distinction)
- Confidence level indicators showing model uncertainty

**Addresses features:**
- Baseline scenario support (table stakes)
- Scenario comparison (differentiator)

**Avoids pitfalls:**
- Carbon credit additionality blind spot — explicit disclaimer and education
- "Guaranteed" capture claims — confidence bounds, uncertainty ranges
- Regulatory compliance guarantees — disclaim "supports workflow, not legal advice"

**Research flag:** SKIP RESEARCH — India CCTS regulations verified via official sources (ICAP, IETA), disclaimer language is content not technical research.

### Phase Ordering Rationale

1. **Foundation first:** Cannot build UI on flawed physics. Pure Python simulation with tests validates equations match literature before Streamlit complexity.

2. **Climate before UI:** Surat's extreme conditions (40-44C pre-monsoon, monsoon rainfall) are defining constraints. Must be baked into defaults, not retrofitted.

3. **Engine orchestration after components:** Growth + Light + Climate modules must work independently before orchestration layer ties them together.

4. **UI after validated physics:** With tested simulation engine, Streamlit UI becomes thin wrapper. Caching strategy depends on understanding simulation cost.

5. **Visualization after data generation:** Charts require SimulationResults structure; cannot design viz without knowing data shape.

6. **Context/disclaimers last:** Once tool works, frame it correctly for carbon credit use case. Adding disclaimers early risks being ignored; adding after value is demonstrated ensures reading.

**Dependencies:**
- Phase 2 depends on Phase 1 (climate needs parameter dataclasses)
- Phase 3 depends on Phases 1 & 2 (engine needs growth + climate)
- Phase 4 depends on Phase 3 (UI needs working simulation)
- Phase 5 depends on Phase 4 (visualization needs UI framework)
- Phase 6 depends on Phase 5 (disclaimers need context of what's being disclaimed)

**Risk mitigation sequencing:**
- Lab-to-field overestimation addressed in Phase 1 (foundational)
- Temperature/monsoon extremes addressed in Phase 2 (cannot defer)
- CO2 quantification credibility addressed in Phase 3 (core value)
- Additionality confusion addressed in Phase 6 (after value proven)

### Research Flags

**Phases with standard patterns (skip research):**
- **Phase 1:** Monod/Beer-Lambert equations well-documented, SciPy solve_ivp is standard tool
- **Phase 2:** Climate data integration is well-understood, data sources verified
- **Phase 3:** ODE solver implementation follows established patterns
- **Phase 4:** Streamlit multipage + caching patterns extensively documented in official guides
- **Phase 5:** Plotly-Streamlit integration well-documented, CSV export is standard Python
- **Phase 6:** India CCTS regulations verified via official sources

**No phases require `/gsd:research-phase`** — all patterns well-established, sources verified at HIGH confidence during initial research.

**User validation needed (not research):**
- Phase 5: Which specific GEI output format do Surat carbon credit buyers expect? (User testing, not web research)
- Phase 6: What specific verification checklist items do India ACVAs require? (Interview verification bodies, not web research)

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All library versions verified on PyPI as of Jan 2026; Streamlit Cloud constraints documented in official status page; Python 3.12 compatibility confirmed across NumPy 2.4.1, SciPy 1.17.0, Pandas 3.0.0 |
| Features | MEDIUM-HIGH | Table stakes validated against carbon credit verification literature (Sylvera, Verra VCS, World Bank MRV) and India CCTS regulations (ICAP, BEE). Differentiators based on competitor gap analysis (no tool combines algae simulation + Surat climate + carbon credit output). Anti-features validated against regulatory requirements. Needs real user validation for GEI output format specifics. |
| Architecture | HIGH | Streamlit execution model, caching patterns, multipage navigation all verified in official documentation. Separation of concerns pattern for scientific apps validated across community forum examples and published simulation services (SimService, pvlib-python). Component boundaries follow established practice. |
| Pitfalls | MEDIUM | Lab-to-field gap (3-6x overestimation) verified across multiple peer-reviewed sources. Surat climate extremes confirmed via Weather Spark and Climate-Data.org. Monod parameter variability documented in PMC studies. India CCTS additionality requirements verified via ICAP and IETA business brief. Some pitfalls (monsoon dilution effects, culture crash risk) are logical inference requiring field validation. |

**Overall confidence:** HIGH

Research sources span official documentation (Streamlit, SciPy, NumPy), peer-reviewed literature (PMC, ScienceDirect, MDPI), government regulations (India BEE, ICAP), and established carbon credit standards (Verra, Sylvera). All library versions and climate data verified as current as of January 2026.

### Gaps to Address

Research was comprehensive but identified areas requiring attention during implementation:

- **Species-specific parameters:** Literature reports widely varying Monod kinetics parameters (Ks, μmax, Yxs) for Chlorella/Spirulina. Will need to select 2-3 representative parameter sets from studies with similar environmental conditions (tropical, high-temperature) and document provenance clearly. **Handle during Phase 1:** Create parameter selection matrix with citations, implement as configurable constants.

- **Exact GEI calculation methodology for algae:** India CCTS targets are sector-specific (9 industrial sectors listed). Algae cultivation may fall under multiple categories or none; likely belongs to voluntary market not compliance CCTS. **Handle during Phase 6:** Research actual ACVA verification workflow for voluntary projects, may require user interviews with verification bodies.

- **Monsoon impact quantification:** How much does 80%+ humidity and 359mm monthly rainfall affect open pond productivity? Literature discusses contamination risk and dilution but lacks quantified models. **Handle during Phase 2:** Implement conservative cloud cover factor (50% PAR reduction June-September) as placeholder, flag for user validation with real Surat operations.

- **Culture crash recovery time:** When temperature exceeds 35C and crashes culture, how long does recovery take? **Handle during Phase 2:** Model as full productivity loss during extreme temperature days, note in documentation that restart time not modeled (conservative approach).

- **Real-world discount factor validation:** Literature suggests 40-60% of theoretical max, but what's appropriate for Surat specifically? **Handle during Phase 1:** Start with 50% discount factor (midpoint), document as assumption requiring field validation, add to user-adjustable parameters in v2.

## Sources

### Primary (HIGH confidence)
- **Streamlit Official Documentation** — execution model, caching patterns (st.cache_data), multipage navigation (st.navigation), button behavior, Streamlit Cloud deployment limits
- **NumPy 2.4.1 PyPI** — version verification, Python >= 3.11 requirement
- **SciPy 1.17.0 Documentation** — solve_ivp API reference, ODE solver methods (RK45, Radau, BDF, LSODA)
- **India CCTS Regulations (ICAP, BEE)** — Carbon Credit Trading Scheme structure, GEI formula, ACVA verification requirements, 2026 launch timeline
- **Verra VCS Standard** — carbon credit validation principles, additionality requirements, conservatively estimated approach
- **Weather Spark & Climate-Data.org** — Surat monthly climate (temperature 7.6-44C, rainfall 0-359mm/month, humidity 42-86%, monsoon June-September)

### Secondary (MEDIUM confidence)
- **PMC (PubMed Central) peer-reviewed papers** — lab-to-field yield gap (3-6x overestimation), Monod parameter variability, temperature impact on algae viability, time-dependent photoinhibition causes 6x overestimation
- **ScienceDirect journals** — Chlorella miniata growth optimization, light-limited photosynthetic production modeling, Beer-Lambert application in photobioreactors
- **MDPI (Multidisciplinary Digital Publishing Institute)** — industrial CO2 capture by algae review, CFD modeling of photobioreactors, direct CO2 measurement methods
- **Streamlit Community Forum** — project structure for large apps, best practices, clean architecture patterns (community consensus, not official)
- **IETA Business Brief** — India CCTS timeline, voluntary market vs. compliance distinction, offset mechanism eligibility (trade association source)

### Tertiary (LOW confidence)
- **Sentra CCTS Calculator** — GEI target calculation examples (commercial source, not authoritative)
- **Competitor tool analysis** (ADA, Raceway Simulation Tools, Persefoni, Normative) — gap analysis for positioning (inferred from marketing materials)

---
*Research completed: 2026-01-27*
*Ready for roadmap: yes*
