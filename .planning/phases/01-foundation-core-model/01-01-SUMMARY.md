---
phase: 01-foundation-core-model
plan: 01
subsystem: core-data-model
tags: [python, dataclasses, pydantic, yaml, parameters, config]
completed: 2026-01-28
duration: ~4 minutes
requires: []
provides:
  - frozen-parameter-dataclasses
  - yaml-species-config
  - validated-config-loader
  - python-package-structure
affects:
  - 01-02 (growth.py consumes GrowthParams, LightParams)
  - 01-03 (ODE engine consumes SpeciesParams, produces SimulationResult)
  - phase-04 (Streamlit caching relies on hashable frozen dataclasses)
tech-stack:
  added: [numpy-2.4.1, scipy-1.17.0, pydantic-2.12.5, pyyaml-6.0, pytest-8.0, mypy-1.14, ruff-0.13]
  patterns: [frozen-dataclasses, pydantic-validation, yaml-config-with-citations]
key-files:
  created:
    - pyproject.toml
    - src/__init__.py
    - src/simulation/__init__.py
    - src/models/__init__.py
    - src/models/parameters.py
    - src/models/results.py
    - src/config/__init__.py
    - src/config/loader.py
    - src/config/species_params.yaml
    - tests/__init__.py
    - tests/test_parameters.py
  modified: []
decisions:
  - id: D-0101-01
    decision: "Use setuptools.build_meta as build backend (not legacy backend)"
    rationale: "Legacy setuptools backend not available in installed version"
  - id: D-0101-02
    decision: "Python >=3.12 requirement, running on 3.13.5"
    rationale: "Plan specified >=3.12; 3.13 is the available runtime"
metrics:
  tasks-completed: 3
  tasks-total: 3
  tests-passing: 24
  test-time: 0.37s
---

# Phase 01 Plan 01: Project Foundation & Parameter Data Model Summary

**One-liner:** Frozen parameter dataclasses with YAML-cited Chlorella vulgaris config and Pydantic-validated loader

## What Was Built

### Task 1: Project Scaffolding
- Created `pyproject.toml` with algaegrowth-simulator package metadata
- Dependencies: numpy>=2.4.1, scipy>=1.17.0, pydantic>=2.12.5, pyyaml>=6.0
- Dev dependencies: pytest>=8.0.0, mypy>=1.8.0, ruff>=0.1.0
- Package installed in editable mode via `pip install -e ".[dev]"`
- All subpackages importable: `src.simulation`, `src.models`, `src.config`

### Task 2: Frozen Parameter Dataclasses
- **GrowthParams**: mu_max, Ks_co2, I_opt, r_maintenance, discount_factor
- **LightParams**: sigma_x, background_turbidity
- **ReactorParams**: depth, surface_area
- **SpeciesParams**: name, growth, light, carbon_content, co2_to_biomass_ratio
- **SimulationResult**: time_days, biomass_concentration, productivity_areal, co2_captured_cumulative, warnings, parameters_used (all tuple fields for hashability)
- All dataclasses are `frozen=True` -- mutation raises `FrozenInstanceError`, all are hashable

### Task 3: YAML Config & Validated Loader
- **species_params.yaml**: Complete Chlorella vulgaris parameter set with per-parameter citations (value + unit + source + note)
- **loader.py**: `load_species_params()` loads YAML, validates ranges via Pydantic, returns frozen `SpeciesParams`
- **loader.py**: `get_parameter_citations()` returns raw YAML for transparency display
- ASSUMED parameters (r_maintenance, background_turbidity) flagged with "ASSUMED" in note field
- Pydantic validation ranges enforce physical plausibility (e.g., mu_max 0.1-5.0, carbon_content 0.3-0.7)

## Key Parameter Values (Chlorella vulgaris)

| Parameter | Value | Unit | Source |
|-----------|-------|------|--------|
| mu_max | 1.0 | 1/d | Schediwy et al. (2019), Table 2 |
| Ks_co2 | 0.5 | mg/L | Schediwy et al. (2019), Table 2 |
| I_opt | 80.0 | umol/m2/s | Razzak et al. (2024) |
| r_maintenance | 0.01 | 1/d | ASSUMED |
| discount_factor | 0.5 | dimensionless | Schediwy et al. (2019) |
| sigma_x | 0.2 | m2/g | Schediwy et al. (2019), Table 2 |
| background_turbidity | 0.5 | 1/m | ASSUMED |
| carbon_content | 0.50 | g_C/g_DW | Schediwy et al. (2019), Table 2 |
| co2_to_biomass_ratio | 1.83 | g_CO2/g_DW | Derived: (44/12)*0.50 |

## Decisions Made

1. **D-0101-01**: Used `setuptools.build_meta` as build backend instead of the legacy `setuptools.backends._legacy:_Backend` which was not available. Standard modern Python packaging approach.

2. **D-0101-02**: Python >=3.12 requirement satisfied by Python 3.13.5 runtime. No compatibility issues encountered.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed setuptools build backend**
- **Found during:** Task 1
- **Issue:** `setuptools.backends._legacy:_Backend` does not exist in the installed setuptools version
- **Fix:** Changed to `setuptools.build_meta` which is the standard modern build backend
- **Files modified:** pyproject.toml
- **Commit:** ad0e82e

## Test Results

24 tests passing in 0.37s:
- 2 default parameter loading tests
- 5 frozen/immutability tests
- 6 hashability tests
- 5 validation rejection tests
- 2 citation accessibility tests
- 2 ASSUMED parameter flagging tests
- 2 SimulationResult tests

## Commits

| Task | Commit | Type | Description |
|------|--------|------|-------------|
| 1 | ad0e82e | chore | Project scaffolding and dependencies |
| 2 | 5fc9854 | feat | Frozen parameter dataclasses and results model |
| 3 | f4f51a1 | feat | YAML species config with citations and validated loader |

## Next Phase Readiness

Plan 01-01 establishes the complete data contract for all downstream plans:
- **01-02** (growth.py, light.py): Will import GrowthParams, LightParams, SpeciesParams
- **01-03** (ODE engine): Will import SpeciesParams, produce SimulationResult
- **Phase 4** (Streamlit): Hashable frozen dataclasses ready for `@st.cache_data`

No blockers or concerns for subsequent plans.
