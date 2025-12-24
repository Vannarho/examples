Example 11 — FD vs CG/AAD SA-CVA parity (EQ/COM)
==================================================

Contents
--------
- Input/sacva_cg_eqcom: CG/AAD configuration (vrè_sacva_cg_ad_eqcom.xml, pricingengine_amccg with EQ/COM domestic measure, midpoint, compact solver, FX–EQ drift ON).
- Input/sacva_fd_eqcom: FD + AAD configuration (vrè_sacva_fd_aad_eqcom.xml) using the same portfolio, market, sensi grids.
- Input/vre_sacva_cg_ad_eqcom.xml and Input/vre_sacva_fd_aad_eqcom.xml: master driver XMLs copied locally so runs are self-contained.
- run_sacva_eqcom.py: runs the CG/AAD case.
- run_sacva_eqcom_fd_aad.py: runs the FD+AAD case.
- utils.py: helper functions (copied from Example 10).
- vre.ipynb: notebook that runs both cases and compares sacva.csv and sacva_sensitivities.csv.

How to run
----------
Open vre.ipynb and run all cells. It will:
1) Invoke the two run scripts from this folder (writes Output/sacva_cg_aad_eqcom and Output/sacva_fd_aad_eqcom).
2) Load sacva.csv and sacva_sensitivities.csv from both runs.
3) Summarise absolute differences to explain residual deltas/vegas.

Notes on config alignment
-------------------------
- Measure/scheme: Equity/CommodityCgUseDomesticMeasure=true, EquityCgUseMidpoint=true, EquityCgUseCompact=true, EquityCgDisableFxEqDrift=false (config-driven).
- Sensitivities: aligned IR tenors (1Y/5Y) and credit tenors (6M/1Y/5Y); FX spot/vol bumps active; EQ/COM vol bumps active.
- Simulation grids: same portfolio, market, and sensimarket/xvasensiconfig per the bundled Input sets.

Residual differences
--------------------
Small gaps can remain due to CAM hazard interpolation, MC variance, or discretisation (midpoint Euler vs analytic). See the notebook commentary for mitigation ideas.
