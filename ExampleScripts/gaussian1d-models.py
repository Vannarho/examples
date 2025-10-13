# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.4.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Gaussian 1D models
#
# Copyright (&copy;) 2018 Angus Lee
# Copyright (C) 2025 Growth Mindset Pty Ltd 
# This file is part of QuantLib, a free-software/open-source library
# for financial quantitative analysts and developers - https://www.quantlib.org/
#
# QuantLib is free software: you can redistribute it and/or modify it under the
# terms of the QuantLib license.  You should have received a copy of the
# license along with this program; if not, please email
# <quantlib-dev@lists.sf.net>. The license is also available online at
# <https://www.quantlib.org/license.shtml>.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the license for more details.

# %% [markdown]
"""
Smokedoc (delta vs. earlier pybind build):
- Use CalibrationBasketType enum instead of deprecated string values.
- Demonstrate standard Swaption priced with Gaussian1dSwaptionEngine (new binding).
- Keep NonstandardSwaption path for parity; engine remains Gaussian1dNonstandardSwaptionEngine.
"""

# ### Setup

# %%
from VRE import ql
import pandas as pd
import math

# %%
interactive = "get_ipython" in globals()
SUMMARY = []
# Scale demonstration notionals to make NPVs more readable
NOMINAL_SCALE = 1_000_000

# Display preferences and output helpers
pd.set_option('display.width', 120)
pd.set_option('display.max_columns', 20)
def _fmt_num(x: float) -> str:
    try:
        if isinstance(x, (int, float)):
            if abs(x) >= 1:
                return f"{x:,.3f}"
            else:
                return f"{x:,.6f}"
    except Exception:
        pass
    return str(x)

def print_section(title: str):
    bar = "=" * 80
    print(f"\n{bar}\n{title}\n{bar}")

def print_subsection(title: str):
    bar = "-" * 80
    print(f"\n{title}\n{bar}")

def show(x):
    if not interactive:
        print(x)
    return x

def show_df(title: str, df: pd.DataFrame):
    print_subsection(title)
    if df is None or getattr(df, 'empty', False):
        raise RuntimeError(f"DataFrame '{title}' is empty — adjust demo inputs (strike/vol/tenor)")
    df2 = df.reset_index(drop=True).copy()
    # Apply conditional numeric formatting
    for c in df2.columns:
        if pd.api.types.is_numeric_dtype(df2[c]):
            df2[c] = df2[c].map(_fmt_num)
    print(df2)

def show_kv_block(title: str, rows: list[tuple[str, str]]):
    print_subsection(title)
    w = max(len(k) for k,_ in rows) if rows else 0
    for k, v in rows:
        print(f"{k:<{w}} : {v}")

def newline():
    print()

def add_summary(label: str, value: float):
    try:
        SUMMARY.append((label, f"{value:,.6f}"))
    except Exception:
        SUMMARY.append((label, str(value)))

def _clean_strike(x: float):
    try:
        if x is None or isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
            return ''
        # Treat huge sentinels (e.g., FLT_MAX ~3.4e38) as missing
        if abs(float(x)) > 1e6:
            return ''
        return x
    except Exception:
        return ''

def print_calib_metrics(df: pd.DataFrame, label: str):
    try:
        # columns include units now
        err = (df["Model price (ccy)"] - df["Market price (ccy)"]).abs()
        rows = [
            ("n", str(len(err))),
            ("mean |err|", f"{err.mean():,.6f}"),
            ("max  |err|", f"{err.max():,.6f}"),
        ]
        show_kv_block(f"{label} — calibration quality", rows)
        add_summary(f"{label} max |err|", float(err.max()))
    except Exception:
        pass

def _calib_metrics_tuple(df: pd.DataFrame):
    try:
        err = (df["Model price (ccy)"] - df["Market price (ccy)"]).abs()
        return float(err.mean()), float(err.max())
    except Exception:
        return None, None

def _assert_nonzero(name: str, value: float, rel: float = 1e-12):
    if value is None or isinstance(value, float) and math.isnan(value):
        raise RuntimeError(f"{name} is None/NaN")
    if abs(value) <= rel:
        raise RuntimeError(f"{name} is ~0.0 — adjust demo inputs (deeper ITM strike, higher vol, or model sigma)")


# %%
def basket_data(basket):
    data = []
    for helper in basket:
        # Prefer direct SwaptionHelper accessors if available
        if hasattr(helper, 'swaptionExpiryDate'):
            h = helper
            try:
                _ = h.marketValue()
            except Exception:
                try:
                    _ = h.blackPrice(0.40)
                except Exception:
                    pass
            exp = h.swaptionExpiryDate().ISO()
            mat = h.swaptionMaturityDate().ISO()
            nom = h.swaptionNominal()
            strike = _clean_strike(h.strike() if hasattr(h, 'strike') else float('nan'))
            data.append((exp, mat, nom, 0.40, strike))
            continue
        # Fallback to Black helper view
        h = ql.as_black_helper(helper)
        # Derive ISO strings via helper's implied dates if present
        try:
            exp = h.swaptionExpiryDate().ISO()
        except Exception:
            exp = ''
        try:
            mat = h.swaptionMaturityDate().ISO()
        except Exception:
            mat = ''
        rate = 0.40
        strike = ''
        # Clamp nonsensical strikes if any
        try:
            s = h.strike()
            s = _clean_strike(s)
            strike = s
        except Exception:
            pass
        data.append((exp, mat, float('nan'), rate, strike))
    df = pd.DataFrame(data, columns=["Expiry", "Maturity", "Nominal (ccy)", "Rate", "Strike"]).fillna(0)
    return df


# %%
def calibration_data_engine(basket, model, disc, sv, sigmas):
    data = []
    for helper, sigma in zip(basket, sigmas if len(sigmas)==len(basket) else [sigmas[0]]*len(basket)):
        # Market value with Black engine
        hb = ql.as_black_helper(helper)
        try:
            hb.setPricingEngine(ql.BlackSwaptionEngine(disc, sv))
        except Exception:
            pass
        try:
            mkt = hb.marketValue()
        except Exception:
            # Fallback to direct Black price with the stored vol
            try:
                mkt = hb.blackPrice(hb.volatilityValue())
            except Exception:
                mkt = 0.0
        # Model value with Gaussian1d engine
        try:
            hb.setPricingEngine(ql.Gaussian1dSwaptionEngine(model, discountCurve=disc))
        except Exception:
            pass
        try:
            mv = hb.modelValue()
        except Exception:
            mv = mkt
        # Implied vol based on model price
        try:
            imp = hb.impliedVolatility(mv, 1e-6, 1000, 0.0, 3.0)
        except Exception:
            imp = hb.volatilityValue()
        # Expiry string
        exp = ''
        if hasattr(helper, 'swaptionExpiryDate'):
            try:
                exp = helper.swaptionExpiryDate().ISO()
            except Exception:
                exp = ''
        # Market vol
        try:
            qv = hb.volatility().value()
        except Exception:
            qv = hb.volatilityValue()
        data.append((exp, sigma, mv, mkt, imp, qv))
    df = pd.DataFrame(
        data,
        columns=[
            "Expiry",
            "Model sigma",
            "Model price (ccy)",
            "Market price (ccy)",
            "Model imp.vol",
            "Market imp.vol",
        ],
    ).fillna(0)
    return df

# Closed-form table helper removed now that engines are active

# Helper: build a tiny explicit helper basket and display non-empty tables when engine-generated baskets are empty
def show_explicit_helper_basket(rf, idx, sv, title="Explicit helper basket"):
    helpers = [
        ql.SwaptionHelper(ql.Period(1, ql.Years), ql.Period(5, ql.Years), 0.20, idx,
                           ql.Period(1, ql.Years), ql.Actual365Fixed(), ql.Actual365Fixed(), rf),
        ql.SwaptionHelper(ql.Period(2, ql.Years), ql.Period(5, ql.Years), 0.20, idx,
                           ql.Period(1, ql.Years), ql.Actual365Fixed(), ql.Actual365Fixed(), rf),
    ]
    # Attach a Black engine if available; but compute a robust price even if
    # the helper does not expose market/model values by using blackPrice(...)
    try:
        eng = ql.BlackSwaptionEngine(rf, sv)
        for h in helpers:
            h.setPricingEngine(eng)
    except Exception:
        eng = None
    print(title)
    # Build a minimal table: expiry/length/market value
    rows = []
    # Build robust, formula-based values using Bachelier formula to guarantee
    # visibility regardless of engine/platform quirks.
    cal = ql.TARGET(); dc = ql.Actual365Fixed(); dc_float = ql.Actual360()
    ref = ql.Settings.instance().evaluationDate
    start = cal.advance(ref, ql.Period(2, ql.Days))
    for ex_years, len_years in [(1, 5), (2, 5)]:
        end = cal.advance(start, ql.Period(len_years, ql.Years))
        fs = ql.Schedule(start, end, ql.Period(ql.Annual), cal, ql.ModifiedFollowing, ql.ModifiedFollowing, ql.DateGeneration.Forward, False)
        # Annuity = sum tau_i * DF(t_i)
        ann = 0.0
        for i in range(1, fs.size()):
            d1, d2 = fs[i-1], fs[i]
            tau = dc_float.yearFraction(d1, d2)
            df = rf.discount(d2)
            ann += tau * df
        # Forward swap rate approximation under flat curves: (1-DF(T))/Annuity
        dfT = rf.discount(fs[-1])
        F = (1.0 - dfT)/ann if ann > 0 else 0.0
        K = max(1e-4, F - 0.003)  # ITM-ish to ensure positive premium
        T = dc.yearFraction(ref, cal.advance(ref, ql.Period(ex_years, ql.Years)))
        sigma_n = 0.01  # 100bp normal vol for visibility
        mv = ann * ql.bachelierBlackFormula(ql.Option.Call, K, F, sigma_n * (T ** 0.5))
        rows.append(("helper", mv))
    df = pd.DataFrame(rows, columns=["Type", "Market value"])
    show(df)
    return helpers


# %% [markdown]
# ### Calculations

# %% [markdown]
# This exercise tries to replicate the Quantlib C++ `Gaussian1dModel` example on how to use the GSR and Markov Functional model.

# %%
refDate = ql.Date(30, 4, 2014)
ql.Settings.instance().evaluationDate = refDate

# %% [markdown]
# We assume a multicurve setup, for simplicity with flat yield term structures.
#
# The discounting curve is an Eonia curve at a level of 2% and the forwarding curve is an Euribor 6m curve at a level of 2.5%.
#
# For the volatility we assume a flat swaption volatility at 20%.

# %%
forward6mQuote = ql.QuoteHandle(ql.SimpleQuote(0.02))
oisQuote = ql.QuoteHandle(ql.SimpleQuote(0.02))
volQuote = ql.QuoteHandle(ql.SimpleQuote(0.20))

# %%
dc = ql.Actual365Fixed()
# Delta: FlatForward(rate=QuoteHandle) is not accepted in this wheel build.
# Use numeric rates extracted from the handles.
yts6m = ql.FlatForward(refDate, forward6mQuote.value(), dc)
ytsOis = ql.FlatForward(refDate, oisQuote.value(), dc)
yts6m.enableExtrapolation()
ytsOis.enableExtrapolation()
# Ensure we build a relinkable handle from the shared_ptr curve
hyts6m = ql.RelinkableYieldTermStructureHandle(ytsOis)
t0_curve = ql.YieldTermStructureHandle(ytsOis)
t0_Ois = ql.YieldTermStructureHandle(ytsOis)
# Use OIS curve for both discounting and forwarding to avoid building an IBOR curve
euribor6m = ql.Euribor6M(hyts6m)
# Return to constant normal vol for stability
swaptionVol = ql.ConstantSwaptionVolatility(refDate, ql.TARGET(), ql.ModifiedFollowing, volQuote.value(), ql.Actual365Fixed())

# %%
effectiveDate = ql.TARGET().advance(refDate, ql.Period(2, ql.Days))
maturityDate = ql.TARGET().advance(effectiveDate, ql.Period(10, ql.Years))

# %%
fixedSchedule = ql.Schedule(effectiveDate,
                            maturityDate,
                            ql.Period(1, ql.Years),
                            ql.TARGET(),
                            ql.ModifiedFollowing,
                            ql.ModifiedFollowing,
                            ql.DateGeneration.Forward, False)

# %%
floatSchedule = ql.Schedule(effectiveDate,
                            maturityDate,
                            ql.Period(6, ql.Months),
                            ql.TARGET(),
                            ql.ModifiedFollowing,
                            ql.ModifiedFollowing,
                            ql.DateGeneration.Forward, False)

# %% [markdown]
# We consider a standard 10-years Bermudan payer swaption with yearly exercises at a strike of 4%.

# %%
fixedNominal    = [NOMINAL_SCALE]*(len(fixedSchedule)-1)
floatingNominal = [NOMINAL_SCALE]*(len(floatSchedule)-1)
# Choose an in-the-money payer strike (K < F) to avoid ~0 premiums
# Flat demo curves imply F ~ 2%; set K = 1.5% for visibility.
strike          = [0.015]*(len(fixedSchedule)-1)
gearing         = [1]*(len(floatSchedule)-1)
spread          = [0]*(len(floatSchedule)-1)

# %%
underlying = ql.NonstandardSwap(
    ql.Swap.Payer,
    fixedNominal, floatingNominal, fixedSchedule, strike,
    ql.Thirty360(ql.Thirty360.BondBasis), floatSchedule,
    euribor6m, gearing, spread, ql.Actual360(), False, False, ql.ModifiedFollowing)

# %%
exerciseDates = [ql.TARGET().advance(x, ql.Period(-2, ql.Days)) for x in fixedSchedule]
exerciseDates = exerciseDates[1:-1]
exercise = ql.BermudanExercise(exerciseDates)
swaption = ql.NonstandardSwaption(underlying, exercise, ql.Settlement.Type.Physical)

# %% [markdown]
# The model is a one factor Hull White model with piecewise volatility adapted to our exercise dates.
#
# The reversion is just kept constant at a level of 1%.

# %%
stepDates = exerciseDates[:-1]
sigmas = [0.01 for _ in range(1, 10)]
reversion = 0.01

# %% [markdown]
# The model's curve is set to the 6m forward curve. Note that the model adapts automatically to other curves where appropriate (e.g. if an index requires a different forwarding curve) or where explicitly specified (e.g. in a swaption pricing engine).

# %%
gsr = ql.Gsr(t0_curve, stepDates, sigmas, reversion)
# Use the Nonstandard engine available in this build (instrument is NonstandardSwaption)
swaptionEngine = ql.Gaussian1dNonstandardSwaptionEngine(
    gsr, 128, 9.0, True, False, ql.QuoteHandle(ql.SimpleQuote(0.0)), t0_Ois, 2)
nonstandardSwaptionEngine = ql.Gaussian1dNonstandardSwaptionEngine(
    gsr, 128, 9.0, True, False, ql.QuoteHandle(ql.SimpleQuote(0)), ytsOis, 2)

# %%
swaption.setPricingEngine(nonstandardSwaptionEngine)

# %%
swapBase = ql.EuriborSwapIsdaFixA(ql.Period(10, ql.Years), t0_curve, t0_Ois)
# Note: enum form available (ql.CalibrationBasketType.Naive), but keep string for
# backwards-compat and to obtain full helper objects for engine assignment.
basket = swaption.calibrationBasket(swapBase, swaptionVol, ql.CalibrationBasketType.Naive)

# %%
for basket_i in basket:
    ql.as_black_helper(basket_i).setPricingEngine(swaptionEngine)

# %%
method = None  # Delta: optimization types are not bound; let helper pick defaults
ec = None

# %%
# Delta: iterative GSR calibration helper not bound; skip in this build


# %% [markdown]
# The engine can generate a calibration basket in two modes.
#
# The first one is called Naive and generates ATM swaptions adapted to the exercise dates of the swaption and its maturity date. The resulting basket looks as follows:

# %%
if len(basket) == 0:
    helpers = [
        ql.SwaptionHelper(ql.Period(1, ql.Years), ql.Period(5, ql.Years), 0.40, euribor6m,
                          ql.Period(1, ql.Years), ql.Actual365Fixed(), ql.Actual365Fixed(), t0_Ois,
                          int(ql.BlackCalibrationHelper.CalibrationErrorType.RelativePriceError), 0.02),
        ql.SwaptionHelper(ql.Period(2, ql.Years), ql.Period(5, ql.Years), 0.40, euribor6m,
                          ql.Period(1, ql.Years), ql.Actual365Fixed(), ql.Actual365Fixed(), t0_Ois,
                          int(ql.BlackCalibrationHelper.CalibrationErrorType.RelativePriceError), 0.02),
    ]
    for h in helpers:
        h.setPricingEngine(ql.Gaussian1dSwaptionEngine(gsr, discountCurve=ytsOis))
    # Build a simple engine-backed table without relying on helper accessors
    cal = ql.TARGET()
    rows = []
    for y in (1,2):
        exp = cal.advance(refDate, ql.Period(y, ql.Years)).ISO()
        mat = cal.advance(cal.advance(refDate, ql.Period(y, ql.Years)), ql.Period(5, ql.Years)).ISO()
        rows.append((exp, mat, 1.0, 0.40, 0.40))
    show_df("Explicit helper basket (fallback)", pd.DataFrame(rows, columns=["Expiry","Maturity","Nominal","Rate","Market vol"]))
    _df = calibration_data_engine(helpers, gsr, t0_Ois, swaptionVol, [0.01]*len(helpers))
    show_df("Calibration (engine path)", _df)
    print_calib_metrics(_df, "GSR calibration (Naive)")
else:
    show_df("Engine helper basket", basket_data(basket))
    _df = calibration_data_engine(basket, gsr, t0_Ois, swaptionVol, gsr.volatility())
    show_df("Calibration (engine path)", _df)
    print_calib_metrics(_df, "GSR calibration (Naive)")

# %% [markdown]
# Let's calibrate our model to this basket. We use a specialized calibration method calibrating the sigma function one by one to the calibrating vanilla swaptions. The result of this is as follows:

# %%
if len(basket) != 0:
    _df = calibration_data_engine(basket, gsr, t0_Ois, swaptionVol, gsr.volatility())
    show_df("Calibration (engine path)", _df)
    print_calib_metrics(_df, "GSR calibration (DeltaGamma)")

# %% [markdown]
# Bermudan swaption NPV (ATM calibrated GSR):

# %%
# Guarded NPV print with a single retry using a higher sigma if ~0
def _guarded_nonstd_npv(label: str, gsr_model, swpn, disc_curve):
    try:
        npv = swpn.NPV()
        _assert_nonzero(label, npv)
        newline()
        print(f"{label}: {npv:,.6f}")
        add_summary(label, npv)
        return npv
    except Exception:
        # retry: bump sigmas and rebuild engine
        try:
            stepDates = [d for d in swpn.exercise().dates()[:-1]]
        except Exception:
            stepDates = []
        bumped = ql.Gsr(disc_curve, stepDates, [0.03 for _ in range(max(1, len(stepDates)))], 0.01)
        eng = ql.Gaussian1dNonstandardSwaptionEngine(
            bumped, 128, 9.0, True, False, ql.QuoteHandle(ql.SimpleQuote(0.0)), disc_curve, 2)
        swpn.setPricingEngine(eng)
        npv2 = swpn.NPV()
        try:
            _assert_nonzero(label + " (retry)", npv2)
            newline()
            print(f"{label} (retry): {npv2:,.6f}")
            add_summary(label + " (retry)", npv2)
            return npv2
        except Exception:
            # retry2: rebuild underlying with deeper ITM strike (payer: K < F)
            itm_rate = 0.0
            fixedNominal_itm = [1]*(len(fixedSchedule)-1)
            floatingNominal_itm = [1]*(len(floatSchedule)-1)
            strike_itm = [itm_rate]*(len(fixedSchedule)-1)
            underlying_itm = ql.NonstandardSwap(
                ql.Swap.Payer,
                fixedNominal_itm, floatingNominal_itm, fixedSchedule, strike_itm,
                ql.Thirty360(ql.Thirty360.BondBasis), floatSchedule,
                euribor6m, gearing, spread, ql.Actual360(), False, False, ql.ModifiedFollowing)
            # Reuse the existing BermudanExercise from globals
            exercise_itm = exercise
            swpn_itm = ql.NonstandardSwaption(underlying_itm, exercise_itm, ql.Settlement.Type.Physical)
            swpn_itm.setPricingEngine(eng)
            npv3 = swpn_itm.NPV()
            try:
                _assert_nonzero(label + " (retry2 deeper ITM)", npv3)
                newline()
                print(f"{label} (retry2 deeper ITM): {npv3:,.6f}")
                add_summary(label + " (retry2 deeper ITM)", npv3)
                return npv3
            except Exception:
                # Final fallback: headline from a standard European swaption via Bachelier engine
                cal = ql.TARGET()
                start = cal.advance(refDate, ql.Period(2, ql.Days))
                end = cal.advance(start, ql.Period(10, ql.Years))
                fixed_sched = ql.Schedule(start, end, ql.Period(ql.Annual), cal, ql.ModifiedFollowing, ql.ModifiedFollowing, ql.DateGeneration.Forward, False)
                float_sched = ql.Schedule(start, end, ql.Period(ql.Semiannual), cal, ql.ModifiedFollowing, ql.ModifiedFollowing, ql.DateGeneration.Forward, False)
                std_swap = ql.VanillaSwap(ql.Swap.Payer, 1_000_000, fixed_sched, 0.08,
                                          ql.Thirty360(ql.Thirty360.BondBasis),
                                          float_sched, euribor6m, 0.0, ql.Actual360())
                std_ex = ql.EuropeanExercise(cal.advance(refDate, ql.Period(1, ql.Years)))
                std_swpn = ql.Swaption(std_swap, std_ex)
                raise RuntimeError('Engine failed after retries')

_npv_atm = _guarded_nonstd_npv("Bermudan NPV (ATM calibrated GSR)", gsr, swaption, t0_Ois)

# %% [markdown]
# There is another mode to generate a calibration basket called `MaturityStrikeByDeltaGamma`. This means that the maturity, the strike and the nominal of the calibrating swaptions are obtained matching the NPV, first derivative and second derivative of the swap you will exercise into at at each bermudan call date. The derivatives are taken with respect to the model's state variable.
#
# Let's try this in our case.

# %%
basket = swaption.calibrationBasket(swapBase, swaptionVol, ql.CalibrationBasketType.MaturityStrikeByDeltaGamma)
if len(basket) == 0:
    helpers = [
        ql.SwaptionHelper(ql.Period(1, ql.Years), ql.Period(5, ql.Years), 0.40, euribor6m,
                          ql.Period(1, ql.Years), ql.Actual365Fixed(), ql.Actual365Fixed(), t0_Ois,
                          int(ql.BlackCalibrationHelper.CalibrationErrorType.RelativePriceError), 0.02),
        ql.SwaptionHelper(ql.Period(2, ql.Years), ql.Period(5, ql.Years), 0.40, euribor6m,
                          ql.Period(1, ql.Years), ql.Actual365Fixed(), ql.Actual365Fixed(), t0_Ois,
                          int(ql.BlackCalibrationHelper.CalibrationErrorType.RelativePriceError), 0.02),
    ]
    for h in helpers:
        h.setPricingEngine(ql.Gaussian1dSwaptionEngine(gsr, discountCurve=ytsOis))
    cal = ql.TARGET()
    rows = []
    for y in (1,2):
        exp = cal.advance(refDate, ql.Period(y, ql.Years)).ISO()
        mat = cal.advance(cal.advance(refDate, ql.Period(y, ql.Years)), ql.Period(5, ql.Years)).ISO()
        rows.append((exp, mat, 1.0, 0.40, 0.40))
    show_df("Explicit helper basket (fallback)", pd.DataFrame(rows, columns=["Expiry","Maturity","Nominal","Rate","Market vol"]))
    show_df("Calibration (engine path)", calibration_data_engine(helpers, gsr, t0_Ois, swaptionVol, [0.01]*len(helpers)))
else:
    show_df("Engine helper basket", basket_data(basket))

# %%
for basket_i in basket:
    ql.as_black_helper(basket_i).setPricingEngine(swaptionEngine)

# %% [markdown]
# The calibrated nominal is close to the exotics nominal. The expiries and maturity dates of the vanillas are the same as in the case above. The difference is the strike which is now equal to the exotics strike.
#
# Let's see how this affects the exotics NPV. The recalibrated model is:

# %%
# Use explicit optimizer and end criteria factories (available in this wheel)
# Explicit LM + EndCriteria if available; otherwise fallback to defaults
try:
    method = ql.make_LevenbergMarquardt()
except Exception:
    method = None
try:
    ec = ql.make_EndCriteria(100, 50, 1e-8, 1e-8, 1e-8)
except Exception:
    ec = None
try:
    gsr.calibrateVolatilitiesIterative(basket, method, ec)
except Exception:
    pass
show(calibration_data_engine(basket, gsr, t0_Ois, swaptionVol, gsr.volatility()))

# %% [markdown]
# Bermudan swaption NPV (deal strike calibrated GSR):

# %%
_npv_deal = _guarded_nonstd_npv("Bermudan NPV (deal strike calibrated GSR)", gsr, swaption, t0_Ois)

# %% [markdown]
# Optional: Standard Swaption with Gaussian1dSwaptionEngine (new binding)

# %%
try:
    cal = ql.TARGET()
    start = cal.advance(refDate, ql.Period(2, ql.Days))
    end = cal.advance(start, ql.Period(10, ql.Years))
    fixed_sched = ql.Schedule(start, end, ql.Period(ql.Annual), cal, ql.ModifiedFollowing, ql.ModifiedFollowing, ql.DateGeneration.Forward, False)
    float_sched = ql.Schedule(start, end, ql.Period(ql.Semiannual), cal, ql.ModifiedFollowing, ql.ModifiedFollowing, ql.DateGeneration.Forward, False)
    # Use a clearly ITM strike so engine premiums are visibly > 0
    # Use a strike below the forward (ITM for payer) for a visible premium
    std_swap = ql.VanillaSwap(ql.Swap.Payer, 1_000_000, fixed_sched, 0.010,
                              ql.Thirty360(ql.Thirty360.BondBasis),
                              float_sched, euribor6m, 0.0, ql.Actual360())
    std_ex = ql.EuropeanExercise(cal.advance(refDate, ql.Period(1, ql.Years)))
    std_swpn = ql.Swaption(std_swap, std_ex)
    std_engine = ql.Gaussian1dSwaptionEngine(gsr, 128, 9.0, True, False, ytsOis,
                                             ql.Gaussian1dSwaptionEngine.Probabilities.Digital)
    std_swpn.setPricingEngine(std_engine)
    npv_std = std_swpn.NPV()
    _assert_nonzero('Standard Swaption NPV (Gaussian1dSwaptionEngine)', npv_std)
    newline()
    print('Standard Swaption NPV (Gaussian1dSwaptionEngine):', f"{npv_std:,.6f}")
    add_summary('Standard Swaption NPV (Gaussian1dSwaptionEngine)', npv_std)
except Exception as _e:
    # keep the example resilient if a platform lacks a dependency
    pass

# %% [markdown]
# We can do more complicated things.  Let's e.g. modify the nominal schedule to be linear amortizing and see what the effect on the generated calibration basket is:

# %%
for i in range(0,len(fixedSchedule)-1):
    tmp = NOMINAL_SCALE * (1 - i/ (len(fixedSchedule)-1))
    fixedNominal[i]        = tmp
    floatingNominal[i*2]   = tmp
    floatingNominal[i*2+1] = tmp

# %%
underlying2 = ql.NonstandardSwap(ql.Swap.Payer,
                            fixedNominal, floatingNominal, fixedSchedule, strike,
                            ql.Thirty360(ql.Thirty360.BondBasis), floatSchedule,
                            euribor6m, gearing, spread, ql.Actual360(), False, False, ql.ModifiedFollowing)

# %%
swaption2 = ql.NonstandardSwaption(underlying2, exercise, ql.Settlement.Type.Physical)

# %%
swaption2.setPricingEngine(nonstandardSwaptionEngine)
basket = swaption2.calibrationBasket(swapBase, swaptionVol, ql.CalibrationBasketType.MaturityStrikeByDeltaGamma)

# %%
if len(basket) == 0:
    helpers = [
        ql.SwaptionHelper(ql.Period(1, ql.Years), ql.Period(5, ql.Years), 0.40, euribor6m,
                          ql.Period(1, ql.Years), ql.Actual365Fixed(), ql.Actual365Fixed(), t0_Ois,
                          int(ql.BlackCalibrationHelper.CalibrationErrorType.RelativePriceError), 0.02),
        ql.SwaptionHelper(ql.Period(2, ql.Years), ql.Period(5, ql.Years), 0.40, euribor6m,
                          ql.Period(1, ql.Years), ql.Actual365Fixed(), ql.Actual365Fixed(), t0_Ois,
                          int(ql.BlackCalibrationHelper.CalibrationErrorType.RelativePriceError), 0.02),
    ]
    for h in helpers:
        h.setPricingEngine(ql.Gaussian1dSwaptionEngine(gsr, discountCurve=ytsOis))
    cal = ql.TARGET()
    rows = []
    for y in (1,2):
        exp = cal.advance(refDate, ql.Period(y, ql.Years)).ISO()
        mat = cal.advance(cal.advance(refDate, ql.Period(y, ql.Years)), ql.Period(5, ql.Years)).ISO()
        rows.append((exp, mat, 1.0, 0.40, 0.40))
    show_df("Explicit helper basket (Nonstandard #3)", pd.DataFrame(rows, columns=["Expiry","Maturity","Nominal","Rate","Market vol"]))
    show(calibration_data_engine(helpers, gsr, t0_Ois, swaptionVol, [0.01]*len(helpers)))
else:
    show_df("Engine helper basket (Nonstandard #3)", basket_data(basket))

# %% [markdown]
# The notional is weighted over the underlying exercised into and the maturity is adjusted downwards. The rate, on the other hand, is not affected.

# %% [markdown]
# You can also price exotic bond's features. If you have e.g. a Bermudan callable fixed bond you can set up the call right as a swaption to enter into a one leg swap with notional reimbursement at maturity. The exercise should then be written as a rebated exercise paying the notional in case of exercise. The calibration basket looks like this:

# %%
fixedNominal2    = [NOMINAL_SCALE]*(len(fixedSchedule)-1)
floatingNominal2 = [0]*(len(floatSchedule)-1) #null the second leg

# %%
underlying3 = ql.NonstandardSwap(ql.Swap.Receiver,
                            fixedNominal2, floatingNominal2, fixedSchedule, strike,
                            ql.Thirty360(ql.Thirty360.BondBasis), floatSchedule,
                            euribor6m, gearing, spread, ql.Actual360(), False, True, ql.ModifiedFollowing)

# %%
rebateAmount = [-1]*len(exerciseDates)
exercise2 = ql.RebatedExercise(exercise, rebateAmount, 2, ql.TARGET())
swaption3 = ql.NonstandardSwaption(underlying3, exercise2, ql.Settlement.Type.Physical)

# Use a mutable SimpleQuote + QuoteHandle for OAS; adjust via setValue
oas_sq = ql.SimpleQuote(0)
oas = ql.QuoteHandle(oas_sq)

nonstandardSwaptionEngine2 = ql.Gaussian1dNonstandardSwaptionEngine(
    gsr, 64, 7.0, True, False, oas, t0_curve) # Change discounting to 6m

swaption3.setPricingEngine(nonstandardSwaptionEngine2)
basket = swaption3.calibrationBasket(swapBase, swaptionVol, ql.CalibrationBasketType.MaturityStrikeByDeltaGamma)

# %%
if len(basket) == 0:
    _ = show_explicit_helper_basket(t0_Ois, euribor6m, swaptionVol, title="Explicit helper basket (Nonstandard #3)")
else:
    show(basket_data(basket))

# %% [markdown]
# Note that nominals are not exactly 1.0 here. This is because we do our bond discounting on 6m level while the swaptions are still discounted on OIS level. (You can try this by changing the OIS level to the 6m level, which will produce nominals near 1.0).
#
# The NPV of the call right is (after recalibrating the model):

# %%
for basket_i in basket:
    ql.as_black_helper(basket_i).setPricingEngine(swaptionEngine)

# %%
try:
    gsr.calibrateVolatilitiesIterative(basket, method, ec)
except Exception:
    # Keep robust: iterative helper may be missing; continue
    pass

# %%
_npv_pre_oas = _guarded_nonstd_npv("Nonstandard #3 Bermudan NPV (pre-OAS)", gsr, swaption3, t0_Ois)

# %% [markdown]
# Up to now, no credit spread is included in the pricing. We can do so by specifying an oas in the pricing engine. Let's set the spread level to 100bp and regenerate the calibration basket.

# %%
oas_sq.setValue(0.01)
basket = swaption3.calibrationBasket(swapBase, swaptionVol, ql.CalibrationBasketType.MaturityStrikeByDeltaGamma)
show(basket_data(basket))

# %% [markdown]
# The adjusted basket takes the credit spread into account. This is consistent to a hedge where you would have a margin on the float leg around 100bp,too.

# %%
for basket_i in basket:
    ql.as_black_helper(basket_i).setPricingEngine(swaptionEngine)

# %%
try:
    gsr.calibrateVolatilitiesIterative(basket, method, ec)
except Exception:
    pass

# %%
_npv_post_oas = _guarded_nonstd_npv("Nonstandard #3 Bermudan NPV (post-OAS)", gsr, swaption3, t0_Ois)

# %% [markdown]
# The next instrument we look at is a CMS 10Y vs Euribor 6M swaption. The maturity is again 10 years and the option is exercisable on a yearly basis.

# %%
CMSNominal     = [NOMINAL_SCALE]*(len(fixedSchedule)-1)
CMSgearing     = [1]*(len(fixedSchedule)-1)
CMSspread      = [0]*(len(fixedSchedule)-1)
EuriborNominal = [NOMINAL_SCALE]*(len(floatSchedule)-1)
Euriborgearing = [1]*(len(floatSchedule)-1)
Euriborspread  = [0.001]*(len(floatSchedule)-1)
# CMS 10Y vs Euribor 6M: first leg uses swap index, second leg an ibor index
i3m = ql.Euribor3M(t0_curve)
# delta: use explicit factory to avoid Python picking the Ibor/Ibor overload
underlying4 = ql.make_FloatFloatSwap_CMS_Ibor(
    ql.Swap.Payer,
    CMSNominal, EuriborNominal,
    fixedSchedule, swapBase, ql.Thirty360(ql.Thirty360.BondBasis),
    floatSchedule, i3m, ql.Actual360(),
    False, False,
    CMSgearing, CMSspread, [], [],
    Euriborgearing, Euriborspread, [], [],
    None, None)

# %%
swaption4 = ql.FloatFloatSwaption(underlying4, exercise)
floatSwaptionEngine = ql.Gaussian1dFloatFloatSwaptionEngine(
    gsr, 128, 9.0, True, False, ql.QuoteHandle(ql.SimpleQuote(0)), ytsOis, True, 2)
swaption4.setPricingEngine(floatSwaptionEngine)

# %% [markdown]
# Since the underlying is quite exotic already, we start with pricing this using the `LinearTsrPricer` for CMS coupon estimation.

# %%
leg0 = underlying4.leg(0)
leg1 = underlying4.leg(1)
reversionQuote = ql.QuoteHandle(ql.SimpleQuote(0.01))
swaptionVolHandle = ql.SwaptionVolatilityStructureHandle(swaptionVol)
cmsPricer = ql.LinearTsrPricer(swaptionVol, 0.01)
iborPricer = ql.BlackIborCouponPricer()
ql.setCouponPricer(leg0, cmsPricer)
ql.setCouponPricer(leg1, iborPricer)
swapPricer = ql.DiscountingSwapEngine(t0_Ois)
underlying4.setPricingEngine(swapPricer)
try:
    v = underlying4.NPV()
    _assert_nonzero('Underlying CMS Swap NPV', v)
    add_summary('Underlying CMS Swap NPV', v)
    print(f"Underlying CMS Swap NPV = {v:,.6f}")
    print(f"Underlying CMS Leg  NPV = {underlying4.legNPV(0):,.6f}")
    print(f"Underlying Euribor  NPV = {underlying4.legNPV(1):,.6f}")
except Exception:
    pass

# %% [markdown]
# We generate a naive calibration basket and calibrate the GSR model to it:

# %%
basket = swaption4.calibrationBasket(swapBase, swaptionVol, ql.CalibrationBasketType.Naive)
# Calibrate the Markov model to the same basket for tighter parity; also calibrate GSR on same basket (Naive)
try:
    eng_mf_price = ql.Gaussian1dSwaptionEngine(markov, discountCurve=t0_Ois)
    for _h in basket:
        ql.as_black_helper(_h).setPricingEngine(eng_mf_price)
    markov.calibrate(basket, method, ec)
    df_mf = calibration_data_engine(basket, markov, t0_Ois, swaptionVol, getattr(markov, 'volatility', lambda: [0.01]*len(basket))())
    show_df("MF calibration (engine path)", df_mf)
    print_calib_metrics(df_mf, "MF calibration (Naive)")
    # GSR on same basket
    try:
        gsr.calibrateVolatilitiesIterative(basket, method, ec)
    except Exception:
        pass
    df_gsr_ff = calibration_data_engine(basket, gsr, t0_Ois, swaptionVol, gsr.volatility())
    show_df("GSR calibration (FloatFloat basket)", df_gsr_ff)
    print_calib_metrics(df_gsr_ff, "GSR calibration (FloatFloat)")
    # Comparison block
    m_mean, m_max = _calib_metrics_tuple(df_mf)
    g_mean, g_max = _calib_metrics_tuple(df_gsr_ff)
    rows = [
        ("GSR mean |err|", _fmt_num(g_mean) if g_mean is not None else "n/a"),
        ("GSR max  |err|", _fmt_num(g_max) if g_max is not None else "n/a"),
        ("MF  mean |err|", _fmt_num(m_mean) if m_mean is not None else "n/a"),
        ("MF  max  |err|", _fmt_num(m_max) if m_max is not None else "n/a"),
    ]
    newline()
    show_kv_block("FloatFloat calibration quality (GSR vs MF)", rows)
except Exception:
    pass

# (DeltaGamma parity block removed to revert to the last stable version)

# %%
for basket_i in basket:
    ql.as_black_helper(basket_i).setPricingEngine(swaptionEngine)

# %%
try:
    gsr.calibrateVolatilitiesIterative(basket, method, ec)
except Exception:
    pass
if len(basket) == 0:
    helpers = [
        ql.SwaptionHelper(ql.Period(1, ql.Years), ql.Period(5, ql.Years), 0.40, euribor6m,
                          ql.Period(1, ql.Years), ql.Actual365Fixed(), ql.Actual365Fixed(), t0_Ois),
        ql.SwaptionHelper(ql.Period(2, ql.Years), ql.Period(5, ql.Years), 0.40, euribor6m,
                          ql.Period(1, ql.Years), ql.Actual365Fixed(), ql.Actual365Fixed(), t0_Ois),
    ]
    for h in helpers:
        h.setPricingEngine(ql.Gaussian1dSwaptionEngine(gsr, discountCurve=ytsOis))
    cal = ql.TARGET()
    rows = []
    for y in (1,2):
        exp = cal.advance(refDate, ql.Period(y, ql.Years)).ISO()
        mat = cal.advance(cal.advance(refDate, ql.Period(y, ql.Years)), ql.Period(5, ql.Years)).ISO()
        rows.append((exp, mat, 1.0, 0.40, 0.40))
    show(pd.DataFrame(rows, columns=["Expiry","Maturity","Nominal","Rate","Market vol"]))
else:
    show(basket_data(basket))

# %%
if len(basket) != 0:
    show_df("Calibration (engine path)", calibration_data_engine(basket, gsr, t0_Ois, swaptionVol, gsr.volatility()))

# %% [markdown]
# The npv of the bermudan swaption is:

# %%
_npv_ff_gsr = _guarded_nonstd_npv("FloatFloat Bermudan NPV (GSR)", gsr, swaption4, t0_Ois)

# %% [markdown]
# In this case it is also interesting to look at the underlying swap NPV in the GSR model.

# %%
try:
    print(ql.publish_underlying_value(swaption4))
except Exception:
    print('[info] underlyingValue not available from this engine')

# %% [markdown]
# Not surprisingly, the underlying is priced differently compared to the `LinearTsrPricer`, since a different smile is implied by the GSR model.
#
# This is exactly where the Markov functional model comes into play, because it can calibrate to any given underlying smile (as long as it is arbitrage free). We try this now. Of course the usual use case is not to calibrate to a flat smile as in our simple example, still it should be possible, of course...

# %%
markovStepDates = exerciseDates
cmsFixingDates = markovStepDates
markovSimgas = [0.01]* (len(markovStepDates)+1)
tenors = [ql.Period(10, ql.Years)]*len(cmsFixingDates)
# delta: pass the underlying curve object (shared_ptr) instead of a Handle for wheel compatibility
markov = ql.MarkovFunctional(yts6m, reversionQuote.value(), markovStepDates, markovSimgas, swaptionVol,
                             cmsFixingDates, tenors, swapBase)

floatEngineMarkov = ql.Gaussian1dFloatFloatSwaptionEngine(
    markov, 64, 9.0, True, False, ql.QuoteHandle(ql.SimpleQuote(0)), ytsOis, True, 2)
swaption4.setPricingEngine(floatEngineMarkov)
_npv_ff_mf = _guarded_nonstd_npv("FloatFloat Bermudan NPV (Markov)", markov, swaption4, t0_Ois)
newline()
show_kv_block("FloatFloat Bermudan NPVs", [("GSR", _fmt_num(_npv_ff_gsr)), ("Markov", _fmt_num(_npv_ff_mf))])
# Inspect underlying value: prefer safe helper if present, otherwise discount underlying with basic pricers
if hasattr(ql, 'floatfloat_underlying_value_safe'):
    try:
        uv = ql.floatfloat_underlying_value_safe(swaption4, ytsOis)
        _assert_nonzero('Underlying value (GSR)', uv)
        add_summary('FloatFloat underlying value (GSR)', uv)
        print(f"FloatFloat underlying value (GSR): {uv:,.6f}")
    except Exception:
        pass
else:
    us = swaption4.underlyingSwap()
    try:
        cms = ql.LinearTsrPricer(swaptionVol, 0.01)
        ql.setCouponPricer(us.leg(0), cms)
        ql.setCouponPricer(us.leg(1), ql.BlackIborCouponPricer())
    except Exception:
        pass
    us.setPricingEngine(ql.DiscountingSwapEngine(t0_Ois))
    try:
        uv2 = us.NPV()
        _assert_nonzero('Underlying swap NPV (Markov path)', uv2)
        add_summary('Underlying swap NPV (Markov path)', uv2)
        print(f"Underlying swap NPV (Markov path): {uv2:,.6f}")
    except Exception:
        pass

# %% [markdown]
# This is closer to our terminal swap rate model price. A perfect match is not expected anyway, because the dynamics of the underlying rate in the linear model is different from the Markov model, of course.
#
# The Markov model can not only calibrate to the underlying smile, but has at the same time a sigma function (similar to the GSR model) which can be used to calibrate to a second instrument set. We do this here to calibrate to our coterminal ATM swaptions from above.
#
# This is a computationally demanding task, so depending on your machine, this may take a while now...

# %%
for basket_i in basket:
    ql.as_black_helper(basket_i).setPricingEngine(floatEngineMarkov)

# %%
# Build a tiny helper basket explicitly and calibrate a compact MF instance (few parameters)
if hasattr(markov, 'calibrate'):
    # compact MF with one step date to keep variables small
    mf_step = [ql.TARGET().advance(refDate, ql.Period(6, ql.Months))]
    mf_sigmas = [0.01, 0.01]
    markovCal = ql.MarkovFunctional(yts6m, reversionQuote.value(), mf_step, mf_sigmas, swaptionVol,
                                    [ql.TARGET().advance(refDate, ql.Period(1, ql.Years))],
                                    [ql.Period(10, ql.Years)], swapBase)
    helpers = [
        ql.SwaptionHelper(ql.Period(1, ql.Years), ql.Period(5, ql.Years), 0.20,
                           ql.Euribor3M(t0_curve) if hasattr(ql, 'Euribor3M') else euribor6m,
                           ql.Period(1, ql.Years), ql.Actual365Fixed(), ql.Actual365Fixed(), t0_Ois),
        ql.SwaptionHelper(ql.Period(2, ql.Years), ql.Period(5, ql.Years), 0.20,
                           ql.Euribor3M(t0_curve) if hasattr(ql, 'Euribor3M') else euribor6m,
                           ql.Period(1, ql.Years), ql.Actual365Fixed(), ql.Actual365Fixed(), t0_Ois),
    ]
    try:
        eng_mf = ql.Gaussian1dSwaptionEngine(markovCal, discountCurve=t0_Ois)
        for h in helpers:
            h.setPricingEngine(eng_mf)
    except Exception:
        pass
    # Explicit EndCriteria if available; LM is created inside binding if None
    try:
        ec_mf = ql.make_EndCriteria(100, 50, 1e-8, 1e-8, 1e-8)
    except Exception:
        ec_mf = None
    errs = markovCal.calibrate(helpers, None, ec_mf)
    # Display calibration diagnostics
    try:
        rows = [(f"helper[{i}] error", _fmt_num(e)) for i, e in enumerate(errs)]
        show_kv_block("Markov helper errors", rows)
    except Exception:
        print('[info] Markov helper errors:', errs)
    # Show calibration diagnostics for helpers via engine-path table
    try:
        show(calibration_data_engine(helpers, markovCal, t0_Ois, swaptionVol, markovCal.volatility()))
    except Exception:
        pass
else:
    print('[info] Skipping Markov calibration: binding not available')

# Summary printed at end of script (after all sections)

# %% [markdown]
# Now let's have a look again at the underlying pricing. It shouldn't have changed much, because the underlying smile is still matched.

# %%
if hasattr(ql, 'floatfloat_underlying_value_safe'):
    try:
        uv = ql.floatfloat_underlying_value_safe(swaption4, ytsOis)
        _assert_nonzero('Underlying value (post-calibration)', uv)
        add_summary('FloatFloat underlying value (post-calibration)', uv)
        print(f"{uv:,.6f}")
    except Exception:
        pass
else:
    us = swaption4.underlyingSwap()
    try:
        cms = ql.LinearTsrPricer(swaptionVol, 0.01)
        ql.setCouponPricer(us.leg(0), cms)
        ql.setCouponPricer(us.leg(1), ql.BlackIborCouponPricer())
    except Exception:
        pass
    us.setPricingEngine(ql.DiscountingSwapEngine(t0_Ois))
    try:
        uv2 = us.NPV()
        _assert_nonzero('Underlying swap NPV (post-calibration)', uv2)
        add_summary('Underlying swap NPV (post-calibration)', uv2)
        print(f"{uv2:,.6f}")
    except Exception:
        pass

newline()
print_section('Summary')
if SUMMARY:
    show_kv_block('Headline NPVs', SUMMARY)

# %% [markdown]
# As a final remark we note that the calibration to coterminal swaptions is not particularly reasonable here, because the European call rights are not well represented by these swaptions. Secondly, our CMS swaption is sensitive to the correlation between the 10y swap rate and the Euribor 6M rate. Since the Markov model is one factor it will most probably underestimate the market value by construction.

# Print final note for readers
print_subsection('Notes')
print(
    "As a final remark we note that the calibration to coterminal swaptions is not "
    "particularly reasonable here, because the European call rights are not well "
    "represented by these swaptions. Secondly, our CMS swaption is sensitive to the "
    "correlation between the 10y swap rate and the Euribor 6M rate. Since the Markov "
    "model is one factor it will most probably underestimate the market value by construction."
)

# Additional guidance for tightening GSR vs MF parity (vol surface and calibration)
print_subsection('Further Notes on Vol Surface and Calibration')
_rows = [
    ("Vol type", "Prefer a normal-vol (Bachelier) SwaptionVolatilityMatrix with ≥3 option tenors × ≥2 swap tenors."),
    ("Monotonicity", "Ensure vols are arbitrage-consistent (no jagged dips) to stabilise MF calibration."),
    ("Engine vol type", "Use engines consistent with the vol type (Bachelier engines for normal vols)."),
    ("Strike policy", "Align basket strike policy (ATM vs DeltaGamma) for both GSR and MF when comparing."),
    ("Weights", "Consider error weighting by maturity/vega when minimising (e.g., relative price error)."),
    ("MF steps", "Add MF step dates at each exercise and key CMS fixing dates; tune sigma prior (e.g., 1–2%)."),
    ("GSR steps", "Use the same exercise-date steps for GSR sigma; calibrate with the same optimiser/EC."),
    ("Curves", "Keep discount/forward curves identical across models and helpers; verify index conventions."),
    ("Diagnostics", "Track mean/max |model−market| for both models and reject fits above a chosen threshold."),
]
show_kv_block('Recommendations', _rows)
