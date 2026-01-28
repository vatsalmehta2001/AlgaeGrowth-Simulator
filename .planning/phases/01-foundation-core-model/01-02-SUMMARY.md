---
phase: 01-foundation-core-model
plan: 02
subsystem: simulation
tags: [python, numpy, beer-lambert, light-attenuation, depth-averaged-irradiance, tdd]

# Dependency graph
requires:
  - phase: 01-01
    provides: project scaffolding, LightParams dataclass (sigma_x, background_turbidity fields)
provides:
  - beer_lambert function (irradiance at specific depth)
  - depth_averaged_irradiance function (analytical average over pond depth)
  - light attenuation module (src/simulation/light.py)
affects:
  - 01-03 (growth.py uses depth_averaged_irradiance for light-limited growth)
  - phase-02 (ODE integration calls depth_averaged_irradiance at each timestep)
  - phase-04 (Streamlit UI displays light profiles)

# Tech tracking
tech-stack:
  added: []
  patterns: [pure-functions-with-float-args, analytical-depth-averaging, guard-clauses-for-edge-cases]

key-files:
  created:
    - src/simulation/light.py
    - tests/test_light.py
  modified:
    - src/simulation/__init__.py

key-decisions:
  - "D-0102-01: Pure float arguments (no dataclass imports) for maximum testability"
  - "D-0102-02: Guard K*D < 1e-10 to avoid division by zero, returns I0"
  - "D-0102-03: Guard I0 <= 0 returns 0.0 (no negative irradiance)"

patterns-established:
  - "Pure simulation functions: take raw floats, return float, no side effects"
  - "Edge case guards at function top before main computation"
  - "Docstrings with literature citations (Razzak et al., Schediwy et al.)"

# Metrics
duration: ~3min
completed: 2026-01-28
---

# Phase 01 Plan 02: Beer-Lambert Light Attenuation Summary

**Pure Beer-Lambert attenuation and analytical depth-averaged irradiance with numpy, 11 TDD tests, edge-case guards for K*D near zero**

## Performance

- **Duration:** ~3 minutes
- **Started:** 2026-01-28T22:44:33Z
- **Completed:** 2026-01-28T22:47:20Z
- **Tasks:** 3 (RED, GREEN, REFACTOR)
- **Files created/modified:** 3

## Accomplishments

- Beer-Lambert law implementation: I(z) = I0 * exp(-(sigma_x*X + k_bg)*z)
- Analytical depth-averaged irradiance: I_avg = I0/(K*D) * (1 - exp(-K*D))
- 11 unit tests covering known values, behavioral properties, and edge cases
- Verified >0.3m depth shows measurable attenuation (6.6% from 0.1m to 0.3m)
- Pure functions with no imports beyond numpy

## Task Commits

Each TDD phase was committed atomically:

1. **RED: Failing tests** - `10d24bd` (test)
   - 11 tests for beer_lambert and depth_averaged_irradiance
   - Tests fail with ImportError (module not yet created)
2. **GREEN: Implementation** - `628541f` (feat)
   - beer_lambert() and depth_averaged_irradiance() in src/simulation/light.py
   - Exports in src/simulation/__init__.py
   - All 11 tests passing
3. **REFACTOR: No changes needed**
   - Code already clean and minimal, no refactoring required

_Note: GREEN implementation was committed in 628541f alongside 01-03 RED tests due to parallel plan execution._

## Files Created/Modified

- `src/simulation/light.py` - Beer-Lambert attenuation and depth-averaged irradiance (93 lines)
- `tests/test_light.py` - 11 unit tests for light module (143 lines)
- `src/simulation/__init__.py` - Exports beer_lambert, depth_averaged_irradiance

## Decisions Made

- **D-0102-01:** Functions take raw floats instead of dataclass objects. Keeps functions pure and avoids coupling to parameter model. Growth module will extract fields before calling.
- **D-0102-02:** K*D < 1e-10 guard returns I0 directly. Avoids division-by-zero in the analytical formula when there is no extinction (e.g., zero biomass and zero background turbidity).
- **D-0102-03:** I0 <= 0 guard returns 0.0. Prevents negative irradiance values and handles edge case of no incoming light.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- GREEN commit was absorbed into a parallel 01-03 RED commit (628541f) because both plans executed concurrently. The implementation is identical to what was written; no code was lost or changed. All 11 tests pass against the committed implementation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `beer_lambert()` and `depth_averaged_irradiance()` are ready for use by growth.py (01-03)
- Functions accept the same parameter names used in LightParams (sigma_x, background_turbidity maps to k_bg)
- No blockers for 01-03 growth kinetics implementation

---
*Phase: 01-foundation-core-model*
*Completed: 2026-01-28*
