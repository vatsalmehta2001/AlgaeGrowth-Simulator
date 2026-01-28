# Feature Landscape: Algae Growth Simulator & CO2 Capture Verification

**Domain:** Algae growth simulation + Carbon credit verification for India CCTS
**Researched:** 2026-01-27
**Target Market:** Carbon credit buyers/sellers in Surat, India (tropical/monsoon climate)

---

## Table Stakes

Features users expect. Missing = product feels incomplete or unusable for carbon credit stakeholders.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Climate Parameter Inputs** | Algae growth is temperature/light/humidity dependent; Surat has distinct monsoon seasons | Low | Temperature, humidity, solar radiation, rainfall. Pre-loaded Surat defaults critical. |
| **Farm Setup Parameters** | Buyers need to model specific operations | Low | Pond size, depth, algae species, cultivation method (open pond vs PBR) |
| **Biomass Growth Visualization** | Core output users need to see | Medium | Time-series chart showing kg biomass over time |
| **CO2 Capture Calculation** | The primary deliverable for carbon credit context | Medium | ~1.8kg CO2 per kg dry algae biomass (varies by species). Must show methodology. |
| **CO2 Accumulation Chart** | Buyers need cumulative view for credit calculations | Low | Running total over simulation period |
| **Scientific Model Foundation** | Carbon credit buyers require defensible methodology | High | Monod equations for growth kinetics; must cite sources. Credibility depends on this. |
| **GEI-Compatible Output** | India CCTS requires specific format | Medium | Output must support: `(GEI Target - GEI Achieved) x Production Volume` calculation |
| **Export/Download Results** | Users need data for external reporting | Low | CSV/JSON export of simulation data |
| **Parameter Transparency** | Verification requires knowing all assumptions | Low | Show all model parameters, equations, sources used |
| **Baseline Scenario Support** | Carbon credits require baseline vs project comparison | Medium | "Without intervention" baseline must be calculable |

### Regulatory Table Stakes (India CCTS Specific)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Direct + Indirect Emissions Scope** | CCTS requires both | Medium | Direct (process) + Indirect (purchased electricity/heat) |
| **CO2e Unit Output** | Standard unit for carbon credits | Low | All outputs in tCO2e (tonnes CO2 equivalent) |
| **Compliance Year Alignment** | CCTS uses fiscal years | Low | Support FY 2025-26, 2026-27 with FY 2023-24 baseline |
| **Production Volume Tracking** | Required for GEI formula | Low | kg/tonnes of product output over period |

---

## Differentiators

Features that set product apart. Not expected, but create competitive advantage.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Surat-Specific Climate Pre-sets** | Zero-config for target market | Low | Monthly averages pre-loaded: 27C annual avg, 1269mm rainfall, 61% humidity avg, monsoon June-Sept |
| **Monsoon Season Modeling** | Critical for Surat accuracy | Medium | Distinct wet (June-Sept, 80%+ annual rainfall) vs dry season modeling. Humidity 42-86% range. |
| **Real-Time Parameter Adjustment** | Instant feedback encourages exploration | Medium | Sliders/inputs update charts live without page reload |
| **Scenario Comparison** | Critical for credit verification use case | Medium | Side-by-side baseline vs project scenario |
| **Verification Checklist Output** | Directly supports buyer workflow | Medium | Auto-generate what VVBs (Validation/Verification Bodies) need to see |
| **Additionality Documentation Helper** | Key carbon credit requirement | High | Generate narrative: "Without this project, X tonnes would not be captured" |
| **Uncertainty/Confidence Bounds** | Higher credibility for serious buyers | High | Show conservative estimates alongside primary. Follows VCS "conservatively estimated" principle. |
| **Multi-Species Comparison** | Optimize for CO2 capture | Medium | Chlorella vs Spirulina vs others - different growth rates, CO2 fixation |
| **Temperature Stress Modeling** | Surat hits 40C+ in summer | Medium | Model growth inhibition at extreme temps (>35C degrades many species) |
| **Light Saturation Curves** | Scientific accuracy | High | Monod-type saturation model for illumination vs growth rate relationship |
| **PDF Verification Report** | Professional output for auditors | Medium | Formatted report with methodology, parameters, results, timestamp |
| **Audit Trail / Version History** | Verification requires traceability | Medium | Log all parameter changes, who ran what when |

### Market Differentiation

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **India CCTS Alignment Badge** | Trust signal for Indian market | Low | Visual indicator that outputs align with CCTS requirements |
| **Methodology Documentation** | Transparency = credibility | Medium | Embedded documentation of Monod equations, CO2 stoichiometry, data sources |
| **Free Tier Positioning** | SME Climate Hub / Normative model | Low | Core simulation free, attracts users who later need advanced features |

---

## Anti-Features

Features to explicitly NOT build. Common mistakes in this domain.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Automatic Carbon Credit Issuance** | Only accredited registries (Verra, Gold Standard, ACR) can issue credits. Creating fake "credits" destroys credibility. | Output data that supports verification by actual registries |
| **"Guaranteed" CO2 Capture Claims** | All models have uncertainty. Promising exact numbers invites legal liability and buyer distrust. | Always show ranges, confidence levels, and methodology limitations |
| **Real-Time Satellite Integration** | Expensive, complex, overkill for simulation MVP. DMRV systems cost millions. | Use validated climate data APIs or manual input |
| **Blockchain-Based Credit Tracking** | Adds complexity without value for simulation tool. India CCTS uses regulated exchanges (CERC), not blockchain. | Focus on data export that feeds into existing registries |
| **Multi-Region Support (v1)** | Dilutes Surat expertise, increases complexity | Surat-only, nail one market before expanding |
| **User Authentication (v1)** | Adds complexity without validated need | Public tool first, accounts when usage patterns demand |
| **Complex CFD Modeling** | Computational fluid dynamics is research-grade, not needed for business users | Simplified Monod-based models sufficient for credit verification |
| **Proprietary Methodology** | Carbon market requires recognized, peer-reviewed methods. Custom methods aren't accepted. | Use published Monod equations, cite papers, align with VCS principles |
| **Over-Precise Outputs** | Showing 8 decimal places implies false accuracy | Round appropriately, show significant figures only |
| **Regulatory Compliance Guarantees** | Legal liability; regulations change | Disclaim: "Supports compliance workflow, not legal advice" |

---

## Feature Dependencies

```
                    +------------------+
                    | Climate Inputs   |
                    | (Surat defaults) |
                    +--------+---------+
                             |
                             v
+------------------+    +----+---------------+
| Farm Parameters  +--->| Growth Model Core |<---+ Scientific
| (pond, species)  |    | (Monod equations) |    | Foundation
+------------------+    +--------+----------+    +-------------+
                                 |
              +------------------+------------------+
              |                  |                  |
              v                  v                  v
     +--------+-------+  +-------+--------+  +-----+------+
     | Biomass Output |  | CO2 Capture    |  | Parameter  |
     | Visualization  |  | Calculation    |  | Transparency|
     +--------+-------+  +-------+--------+  +------------+
              |                  |
              v                  v
     +--------+------------------+--------+
     |     GEI-Compatible Output         |
     |     (tCO2e, production volume)    |
     +----------------+------------------+
                      |
     +----------------+------------------+
     |                |                  |
     v                v                  v
+----+-----+   +------+------+   +------+------+
| CSV/JSON |   | Scenario    |   | PDF Report  |
| Export   |   | Comparison  |   | (v2)        |
+----------+   +-------------+   +-------------+
                      |
                      v
              +-------+--------+
              | Verification   |
              | Checklist (v2) |
              +----------------+
```

**Critical Path:**
1. Climate + Farm Inputs --> Growth Model --> Biomass/CO2 Output --> Export
2. Everything else builds on this foundation

**Parallel Development Possible:**
- Visualizations (once model exists)
- Export formats (once output calculated)
- Documentation/transparency features

---

## MVP Recommendation

### Must Have for MVP (v1)

Based on carbon credit buyer requirements and India CCTS alignment:

1. **Climate Parameter Inputs** with Surat defaults
   - Temperature (monthly averages: 22-35C range)
   - Humidity (42-86% seasonal range)
   - Solar radiation
   - Rainfall (distinguishing monsoon vs dry)

2. **Farm Setup Parameters**
   - Pond surface area (m2)
   - Depth (m)
   - Algae species (start with Chlorella - best documented)
   - Cultivation type (open raceway default)

3. **Scientific Growth Model**
   - Monod equation implementation
   - Temperature-dependent growth rate
   - Light-limited growth factor
   - Documented assumptions

4. **Core Outputs**
   - Biomass accumulation over time (kg)
   - CO2 captured over time (tCO2e)
   - Final totals for simulation period
   - Parameter summary showing all inputs

5. **Basic Visualization**
   - Biomass growth curve
   - CO2 capture accumulation curve

6. **Data Export**
   - CSV download of time-series data
   - Clear column headers for external use

7. **Methodology Documentation**
   - In-app explanation of model
   - Citations to source papers
   - Key assumptions listed

### Defer to Post-MVP (v2)

| Feature | Reason to Defer | When to Add |
|---------|-----------------|-------------|
| Scenario Comparison | Adds UI complexity | After validating core model is accurate |
| Uncertainty Bounds | Requires validation of error margins | After user feedback on precision needs |
| PDF Reports | Nice-to-have, not blocking verification | After auditor feedback |
| Multi-species | Chlorella sufficient for MVP | After proving single-species value |
| Verification Checklist | Requires deep VVB workflow knowledge | After real verification attempts |
| User Accounts | No validated need | When users want to save simulations |
| API Access | Enterprise feature | When paid tier is ready |
| Temperature Stress Modeling | Refinement, not core | After basic model validated |

---

## Competitive Landscape

### Existing Tools (Partial Competitors)

| Tool | Focus | Gap for Our Use Case |
|------|-------|---------------------|
| **ADA (Algal Data Analyser)** | Lab PBR data analysis | Not simulation, not climate-aware |
| **Raceway Simulation Tools** | Academic PBR design | Not carbon credit focused, complex |
| **Persefoni, Sweep** | Enterprise carbon accounting | Not algae-specific, expensive |
| **Normative** | SMB carbon calculator | General, not biofuel/algae |
| **Sentra CCTS Calculator** | India CCTS compliance | Industrial focus, not algae simulation |

### Unique Position
No tool currently combines:
- Algae growth simulation
- Surat/India climate specificity
- Carbon credit verification output
- Freemium accessibility

This is the gap we fill.

---

## India CCTS Feature Requirements

Based on Carbon Credit Trading Scheme regulations:

### Mandatory for CCTS Compliance Support

| Requirement | How We Address |
|-------------|----------------|
| GEI Formula Support | Output: `(GEI Target - GEI Achieved) x Production Volume` |
| tCO2e Units | All CO2 outputs in tonnes CO2 equivalent |
| Baseline Comparison | Support "without project" baseline scenario |
| Fiscal Year Alignment | Simulation periods align to Indian FY (Apr-Mar) |
| Direct + Indirect Emissions | Model includes process emissions only (Scope 1 focus for algae) |
| Production Volume | Track kg/tonnes biomass as "equivalent product" |

### CCTS Timeline Alignment

| Compliance Year | Target Stringency | Our Support |
|-----------------|-------------------|-------------|
| FY 2025-26 | Initial targets | MVP ready |
| FY 2026-27 | More stringent (3.3-7.5%+ cuts) | Scenario comparison for planning |

---

## Sources

### Carbon Credit Verification
- [Sylvera - Carbon Credit Validation 2026](https://www.sylvera.com/blog/carbon-credit-validation) - MEDIUM confidence
- [Verra VCS Standard](https://verra.org/programs/verified-carbon-standard/) - HIGH confidence
- [World Bank MRV Guide](https://www.worldbank.org/en/news/feature/2022/07/27/what-you-need-to-know-about-the-measurement-reporting-and-verification-mrv-of-carbon-credits) - HIGH confidence
- [ICVCM Core Carbon Principles](https://icvcm.org/core-carbon-principles/) - HIGH confidence

### India CCTS
- [India Bureau of Energy Efficiency CCTS](https://www.beeindia.gov.in/carbon-market.php) - HIGH confidence
- [ICAP - Indian Carbon Credit Trading Scheme](https://icapcarbonaction.com/en/ets/indian-carbon-credit-trading-scheme) - HIGH confidence
- [Sentra CCTS Calculation](https://sentra.world/blogs/ccts/carbon-credit-trading-scheme-calculation/) - MEDIUM confidence
- [GEI Target Rules 2025](https://www.sprih.com/blogs/understanding-indias-greenhouse-gases-emission-intensity-geitarget-rules-2025/) - MEDIUM confidence

### Algae Growth Models
- [ACS - Kinetic Modeling of CO2 Biofixation](https://pubs.acs.org/doi/10.1021/acssuschemeng.2c03927) - HIGH confidence
- [ScienceDirect - Chlorella miniata Growth Optimization](https://www.sciencedirect.com/science/article/abs/pii/S1878818121003352) - HIGH confidence
- [MDPI - CFD Modeling of Photobioreactors](https://www.mdpi.com/1996-1073/15/11/3966) - MEDIUM confidence
- [PMC - Real-Time CO2 Monitoring Systems](https://pmc.ncbi.nlm.nih.gov/articles/PMC7464137/) - HIGH confidence

### Climate Data
- [Climate-Data.org - Surat](https://en.climate-data.org/asia/india/gujarat/surat-959693/) - MEDIUM confidence
- [Weather Spark - Surat Year Round](https://weatherspark.com/y/107304/Average-Weather-in-S%C5%ABrat-Gujarat-India-Year-Round) - MEDIUM confidence

### Carbon Accounting Software Landscape
- [Persefoni - Best Carbon Accounting Software 2026](https://www.persefoni.com/blog/best-carbon-accounting-software) - MEDIUM confidence
- [Gartner - Carbon Accounting Software Reviews](https://www.gartner.com/reviews/market/carbon-accounting-and-management-software) - MEDIUM confidence

---

## Confidence Assessment

| Category | Confidence | Rationale |
|----------|------------|-----------|
| Table Stakes - Technical | HIGH | Based on scientific literature and established modeling practices |
| Table Stakes - Regulatory | MEDIUM | India CCTS is new (2026 launch), rules still being finalized |
| Differentiators | MEDIUM | Based on competitor gap analysis, needs user validation |
| Anti-Features | HIGH | Based on carbon market standards and legal considerations |
| MVP Priorities | MEDIUM | Logical but needs real user feedback to validate |

---

## Open Questions for Later Phases

1. **Exact GEI calculation methodology for algae** - India CCTS targets are sector-specific; algae may fall under multiple categories or none
2. **VVB acceptance criteria** - What specific documentation do Indian Accredited Carbon Verifiers need?
3. **Offset Mechanism eligibility** - Does algae CO2 capture qualify for voluntary offset credits under CCTS?
4. **Species-specific CO2 fixation rates** - Literature values vary; may need local validation
5. **Monsoon impact quantification** - How much does 80%+ humidity affect open pond productivity?
