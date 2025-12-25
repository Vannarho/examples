# Example 11 — FD vs CG/AAD SA-CVA Parity (Tutorial)

This tutorial walks through building a **parity pair** between a finite-difference (FD) SA-CVA run and a computation-graph (CG) AAD run, with all inputs bundled locally. It is aimed at newcomers who want to understand how the configuration files fit together and how we optimise performance (AAD, JIT, SIMD) while keeping pricing/sensitivities accurate across ScriptedTrade payoffs (EQ, COM, FX, IR combos).

## Performance philosophy
- **AAD + JIT + SIMD:** The CG path uses automatic differentiation on a computation graph with just-in-time kernels and SIMD where available, giving fast, path-wise sensitivities without bumping. The same framework prices scripted payoffs spanning EQ (spots/vols), COM (price curves/vols), FX, and IR legs.
- **Deterministic knobs:** Measure flags (domestic vs legacy), midpoint sampling, compact per-step solves, and drift gates are driven by config (not env) to keep runs reproducible.

## Configuration map (what points to what)
- **Master driver XMLs** (copied locally):
  - `Input/vre_sacva_cg_ad_eqcom.xml` → uses CG/AAD stack under `Input/sacva_cg_eqcom/`
  - `Input/vre_sacva_fd_aad_eqcom.xml` → uses FD + AAD stack under `Input/sacva_fd_eqcom/`
- **Common building blocks** (one per stack):
  - `curveconfig.xml` — defines discount/forecast/hazard curves
  - `todaysmarket.xml` — binds curve IDs to market data files (quotes/fixings/dividends)
  - `pricingengine_amccg.xml` — ScriptedTrade CG model/engine parameters
  - `simulation.xml` — grid, samples, time steps per year
  - `sensimarket.xml` — simulated term structures for sensitivities (tenors, vols)
  - `xvasensiconfig.xml` / `sensitivity.xml` — shift sizes/tenors per risk factor
  - `portfolio_sacva_eqcom.xml`, `netting.xml`, `collateralbalances.xml`, `counterparty.xml`

Everything above lives in `Input/sacva_cg_eqcom` and `Input/sacva_fd_eqcom` for this example.

## Key files and why they matter

### 1) curveconfig.xml (shared structure in CG/FD trees)
Defines discount/forecast curves for EUR/USD etc., plus hazard/default curves. Keep CCY coverage identical so CAM (CG) and FD bumps see the same pillars.

```xml
<DiscountCurve id="EUR-EONIA">
  <DayCounter>A365</DayCounter>
  <Currency>EUR</Currency>
  <Segments>
    <Simple>...</Simple>
  </Segments>
</DiscountCurve>
<!-- Similar blocks for USD, and default curves for CPTY_A with 6M/1Y/5Y tenors -->
```

**Why:** SA-CVA needs consistent discounting and hazard grids. Align hazard tenors (6M/1Y/5Y) with sensi tenors to avoid interpolation mismatches between CG recalibration and FD bumping.

### 2) todaysmarket.xml
Binds curve IDs to data files (market_20160205.txt, fixings_20160205.txt, dividends.csv).

```xml
<Configuration id="default">
  <DiscountCurve currency="EUR">EUR-EONIA</DiscountCurve>
  <DiscountCurve currency="USD">USD-FED</DiscountCurve>
  <DefaultCurve name="CPTY_A">CPTY_A_DEFAULT</DefaultCurve>
  <EquityCurve name="SP5">EQ-SP5</EquityCurve>
  <CommodityCurve name="NYMEX:CL">COM-NYMEX-CL</CommodityCurve>
</Configuration>
```

**Why:** Keeps both runs on the exact same quotes/fixings/dividends, removing data skew as a source of differences.

### 3) pricingengine_amccg.xml (ScriptedTrade model/engine knobs)
Config-driven CG settings (no env). Key parameters:

```xml
<ModelParameters>
  <Parameter name="EquityCgUseDomesticMeasure">true</Parameter>
  <Parameter name="EquityCgUseMidpoint">true</Parameter>
  <Parameter name="CommodityCgUseDomesticMeasure">true</Parameter>
  <Parameter name="EquityCgUseCompact">true</Parameter>
  <Parameter name="EquityCgLambdaSweep">1e-10,5e-10,1e-9,5e-9,1e-8,1e-7,1e-6</Parameter>
  <Parameter name="EquityCgDisableFxEqDrift">false</Parameter>
</ModelParameters>
```

- Domestic measure + midpoint: better quanto drift/variance matching.
- Compact solve: analytic per-step EQ/FX loadings; set to false to use LM sweep with the given lambdas.
- Drift gate: leave false unless A/B testing.

Align these between CG and FD comparisons so measure/scheme differences don’t show up as risk gaps.

### 4) simulation.xml
Sets samples, time steps per year, valuation/simulation dates. Keep identical values in CG and FD folders. Example:

```xml
<Simulation>
  <Parameter name="Samples">8192</Parameter>
  <Parameter name="TimeStepsPerYear">24</Parameter>
  <Grid>
    <Dates>2016-02-05,2016-08-05,2017-02-05</Dates>
  </Grid>
</Simulation>
```

**Why:** MC variance and discretisation differences shrink when sim grids match.

### 5) sensimarket.xml
Defines simulated curves/surfaces for sensitivities. Critical to align tenors with `xvasensiconfig.xml` (IR 1Y/5Y; credit 6M/1Y/5Y) and include vol surfaces for EQ/COM/FX so CG AAD vegas exist.

```xml
<InterestRateVolatility>
  <Volatility structure="SwaptionVolatility" ...>
    <Tenors>1Y,5Y</Tenors>
  </Volatility>
</InterestRateVolatility>
<EquityVolatility>
  <Name>SP5</Name>
  <Expiries>1Y,2Y</Expiries>
  <Strikes>ATM</Strikes>
</EquityVolatility>
<CommodityVolatility>...</CommodityVolatility>
<FXVolatility>
  <CurrencyPair>EURUSD</CurrencyPair>
  <Expiries>6M,1Y</Expiries>
  <Strikes>ATM</Strikes>
</FXVolatility>
```

**Why:** Missing vol surfaces → zero vegas on CG. Matching tenors → clean deltas.

### 6) xvasensiconfig.xml / sensitivity.xml
Shift sizes and tenors per risk factor. Align these across CG/FD.

```xml
<InterestRates>
  <Tenors>1Y,5Y</Tenors>
  <ShiftSizes>0.0001</ShiftSizes>
</InterestRates>
<Credit>
  <Tenors>6M,1Y,5Y</Tenors>
  <ShiftSizes>0.0001</ShiftSizes>
</Credit>
<EquitySpot shiftType="Relative" shiftSize="0.0001"/>
<EquityVol shiftType="Relative" shiftSize="0.01"/>
<FXSpot shiftType="Relative" shiftSize="0.0001"/>
<FXVol shiftType="Relative" shiftSize="0.01"/>
<CommoditySpot .../>
<CommodityVol .../>
```

**Why:** Ensures FD bumps and CG AAD gradients are evaluated on the same grid/eps. FactorMapper now tolerates FX zero shift.

### 7) Portfolio and static data
`portfolio_sacva_eqcom.xml` (EQ + COM trades), `netting.xml`, `collateralbalances.xml`, `counterparty.xml` should be identical across runs.

## Running and comparing
- Use the notebook (`vre.ipynb`) to run all three cases from this folder. Outputs land under:
  - `Output/sacva_cg_aad_eqcom` (CG/AAD)
  - `Output/sacva_fd_aad_eqcom` (FD inputs + CG sensitivities)
  - `Output/sacva_fd_eqcom` (classic FD bump)
- Compare `sacva.csv` and `sacva_sensitivities.csv`; the notebook reports max/mean absolute differences and highlights the largest entries.

## Interpreting residual differences
- **Hazard skew:** CAM recalibration vs FD bumping on hazard grids may leave small credit gaps.
- **MC variance:** increase samples/time steps if needed.
- **Discretisation:** midpoint Euler vs analytic drift/vol; compact vs LM solve can move quanto loadings slightly.
- **FX spot reporting:** FX spot delta may be ~0; enable write-all or lower eps if you need explicit rows.
