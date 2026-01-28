# Phase 1: Foundation & Core Model - Context

**Gathered:** 2026-01-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish pure Python simulation foundation with Monod growth equations and Beer-Lambert light attenuation using conservative, field-validated parameters for Chlorella vulgaris. No UI, no Streamlit — testable simulation modules only. Temperature inhibition is Phase 2.

</domain>

<decisions>
## Implementation Decisions

### Default Species & Parameters
- Default species: Chlorella vulgaris — well-studied, high CO2 fixation
- Parameters stored as config (data structure), not hardcoded — enables species swap in v2
- Parameters visible but read-only in UI (when built in Phase 4) — transparency for credibility
- Each parameter cited individually: "mumax = 0.5 d-1 (Smith et al., 2022)" — per-parameter provenance
- Parameter provenance stored in a separate YAML/JSON config file with values + citations together

### Growth Model Limiting Factors
- Two limiting factors in Phase 1: Light (PAR) and CO2 availability
- Factors combine multiplicatively: mu = mumax x f(light) x f(CO2) — Liebig's law
- Photoinhibition included — growth reduction at very high light, important for Surat's intense solar radiation
- Daily average light used (not day/night cycles) — simplifies v1 while capturing seasonal variation

### Productivity Realism Targets
- Target output range: conservative 6-8 g/m2/day for Surat conditions
- Real-world discount factor applied and user-visible — user can see it's being applied
- Warning flag when output exceeds 10 g/m2/day: "Output exceeds typical field values"
- No hard cap — let math produce what it produces, just flag unrealistic values
- Integration tests validate output against published Chlorella field data ranges

### Parameter Sourcing
- NotebookLM "photosynthesis-growth-models" papers are primary source — use exact values from those
- When papers give a range, use the conservative (lower/safer) end — most defensible for carbon credits
- Missing parameters: use established literature values BUT flag as "assumed, not from primary sources"
- Provenance tracked in params config file: paper reference, table/figure number per parameter

### Claude's Discretion
- ODE solver choice and configuration (RK45 vs other methods)
- Dataclass structure and field naming
- Unit test framework and test structure
- Exact file/module organization

</decisions>

<specifics>
## Specific Ideas

- Monod equations and validation data are in NotebookLM "photosynthesis-growth-models" notebook — query this during research/planning for exact parameter values
- Carbon credit buyers need to audit parameter sources — the YAML/JSON config with citations is a key credibility feature
- Conservative end of all ranges: this simulator's value proposition is defensible numbers, not optimistic projections

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation-core-model*
*Context gathered: 2026-01-27*
