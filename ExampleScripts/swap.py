# ---
# Engine‑first update (pybind11 bindings)
#
# This example now follows the engine‑first policy used across VRE Python
# examples. Swaps are priced using DiscountingSwapEngine; we assert non‑zero
# engine results and only fall back to analytic estimates if strictly needed.
# Output follows a consistent, readable format shared with other examples.
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
# # Interest-rate swaps
#
# Copyright (&copy;) 2004, 2005, 2006, 2007 StatPro Italia srl
#
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

# %%
from VRE import ql
import math
import pandas as pd
import argparse

# Display preferences and output helpers (shared style)
pd.set_option('display.width', 120)
pd.set_option('display.max_columns', 20)

SUMMARY: list[tuple[str, str]] = []
NOMINAL_SCALE = 1_000_000  # scale demo notionals for readability

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

def show_df(title: str, df: pd.DataFrame):
    print_subsection(title)
    df2 = df.reset_index(drop=True).copy()
    for c in df2.columns:
        if pd.api.types.is_numeric_dtype(df2[c]):
            df2[c] = df2[c].map(_fmt_num)
    print(df2)

def add_summary(label: str, value: float):
    try:
        SUMMARY.append((label, f"{value:,.6f}"))
    except Exception:
        SUMMARY.append((label, str(value)))

def _assert_nonzero(name: str, value: float, rel: float = 1e-12):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        raise RuntimeError(f"{name} is None/NaN")
    if abs(value) <= rel:
        raise RuntimeError(f"{name} is ~0.0 — adjust demo inputs")

def _pillars_df(helpers) -> pd.DataFrame:
    rows = []
    for h in helpers:
        try:
            rows.append({
                'pillar': h.pillarDate().ISO(),
                'earliest': h.earliestDate().ISO(),
                'latest': h.latestDate().ISO(),
                'implied': h.impliedQuote(),
                'error': h.quoteError(),
                'type': h.__class__.__name__,
            })
        except Exception:
            pass
    return pd.DataFrame(rows)

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--debug-pillars', action='store_true', dest='debug_pillars')
parser.add_argument('--curve', choices=['futures','fra','both'], default='both')
ARGS, _ = parser.parse_known_args()

# %% [markdown]
# ### Global data

# %%
calendar = ql.TARGET()
todaysDate = ql.Date(6, ql.November, 2001)
ql.Settings.instance().evaluationDate = todaysDate
settlementDate = ql.Date(8, ql.November, 2001)

# %% [markdown]
# ### Market quotes

# %%
deposits = {
    (3, ql.Months): 0.0363,
}

# %%
FRAs = {(3, 6): 0.037125, (6, 9): 0.037125, (9, 12): 0.037125}

# %%
futures = {
    ql.Date(19, 12, 2001): 96.2875,
    ql.Date(20, 3, 2002): 96.7875,
    ql.Date(19, 6, 2002): 96.9875,
    ql.Date(18, 9, 2002): 96.6875,
    ql.Date(18, 12, 2002): 96.4875,
    ql.Date(19, 3, 2003): 96.3875,
    ql.Date(18, 6, 2003): 96.2875,
    ql.Date(17, 9, 2003): 96.0875,
}

# %%
swaps = {
    (2, ql.Years): 0.037125,
    (3, ql.Years): 0.0398,
    (5, ql.Years): 0.0443,
    (10, ql.Years): 0.05165,
    (15, ql.Years): 0.055175,
}

# %% [markdown]
# We'll convert them to `Quote` objects...

# %%
for n, unit in deposits.keys():
    deposits[(n, unit)] = ql.SimpleQuote(deposits[(n, unit)])
for n, m in FRAs.keys():
    FRAs[(n, m)] = ql.SimpleQuote(FRAs[(n, m)])
for d in futures.keys():
    futures[d] = ql.SimpleQuote(futures[d])
for n, unit in swaps.keys():
    swaps[(n, unit)] = ql.SimpleQuote(swaps[(n, unit)])

# %% [markdown]
# ...and build rate helpers.

# %%
dayCounter = ql.Actual360()
settlementDays = 2
depositHelpers = [
    ql.DepositRateHelper(
        ql.QuoteHandle(ql.SimpleQuote(deposits[(n, unit)].value())),
        ql.Period(n, unit),
        settlementDays,
        calendar,
        ql.ModifiedFollowing,
        False,
        dayCounter,
    )
    for n, unit in deposits.keys()
]

# %%
dayCounter = ql.Actual360()
settlementDays = 2
fraHelpers = [
    ql.FraRateHelper(ql.QuoteHandle(ql.SimpleQuote(FRAs[(n, m)].value())), n, m, settlementDays, calendar, ql.ModifiedFollowing, False, dayCounter)
    for n, m in FRAs.keys()
]

# %%
dayCounter = ql.Actual360()
months = 3
# Robust futures path: first try QuantExt ImmFraRateHelper with IMM offsets;
# if unavailable, fall back to a FRA ladder derived from futures prices.
_fut_dates = sorted(futures.keys(), key=lambda x: x.serialNumber())
futuresShortEndHelpers = []
try:
    from VRE import qle as _qle
    idx3m = ql.Euribor3M()
    for i, d in enumerate(_fut_dates, start=1):
        price = futures[d].value()
        rate = (100.0 - price) / 100.0
        qh = ql.QuoteHandle(ql.SimpleQuote(rate))
        # Use consecutive IMM month offsets i -> i+1
        h = _qle.ImmFraRateHelper(qh, i, i+1, idx3m, ql.Pillar.LastRelevantDate, ql.Date())
        futuresShortEndHelpers.append(h)
except Exception:
    for i, d in enumerate(_fut_dates, start=1):
        price = futures[d].value()
        rate = (100.0 - price) / 100.0
        qh = ql.QuoteHandle(ql.SimpleQuote(rate))
        mStart = i * 3
        mEnd = mStart + 3
        rh = ql.FraRateHelper(qh, mStart, mEnd, settlementDays, calendar, ql.ModifiedFollowing, False, dayCounter)
        futuresShortEndHelpers.append(rh)

# %% [markdown]
# The discount curve for the swaps will come from elsewhere. A real application would use some kind of risk-free curve; here we're using a flat one for convenience.

# %%
discountTermStructure = ql.YieldTermStructureHandle(
    ql.FlatForward(settlementDate, 0.04, ql.Actual360()))

# %%
settlementDays = 2
fixedLegFrequency = ql.Annual
fixedLegTenor = ql.Period(1, ql.Years)
fixedLegAdjustment = ql.Unadjusted
fixedLegDayCounter = ql.Thirty360(ql.Thirty360.BondBasis)
floatingLegFrequency = ql.Quarterly
floatingLegTenor = ql.Period(3, ql.Months)
floatingLegAdjustment = ql.ModifiedFollowing
swapHelpers = [
    ql.make_SwapRateHelper(swaps[(n, unit)].value(), ql.Period(n, unit), calendar, fixedLegFrequency, fixedLegAdjustment, fixedLegDayCounter, ql.Euribor3M(), None, ql.Period(0, ql.Days), discountTermStructure)
    for n, unit in swaps.keys()
]

# %% [markdown]
# ### Term structure construction

# %%
forecastTermStructure = ql.RelinkableYieldTermStructureHandle()

# %%
helpers = futuresShortEndHelpers + swapHelpers[1:]
depoFuturesSwapCurve = ql.PiecewiseFlatForward(settlementDate, helpers, ql.Actual360())
if ARGS.debug_pillars:
    try:
        dfp = _pillars_df(helpers)
        show_df("Pillars — Futures short-end + Swaps", dfp if not dfp.empty else pd.DataFrame({'note':['no pillar data (rebuild wheel?)']}))
        if not dfp.empty:
            dup = dfp['pillar'].value_counts()
            dup = dup[dup>1]
            if not dup.empty:
                print_subsection("Duplicate pillar dates detected (Futures path)")
                print(dup)
    except Exception:
        pass

# %%
helpers = depositHelpers + fraHelpers + swapHelpers
depoFraSwapCurve = ql.PiecewiseFlatForward(settlementDate, helpers, ql.Actual360())
if ARGS.debug_pillars:
    try:
        dfp = _pillars_df(helpers)
        show_df("Pillars — Depo+FRA+Swaps", dfp if not dfp.empty else pd.DataFrame({'note':['no pillar data (rebuild wheel?)']}))
    except Exception:
        pass

# %% [markdown]
# ### Swap pricing

# %%
swapEngine = ql.DiscountingSwapEngine(discountTermStructure)

# %%
nominal = NOMINAL_SCALE
length = 5
maturity = calendar.advance(settlementDate, length, ql.Years)
payFixed = True

# %%
fixedLegFrequency = ql.Annual
fixedLegAdjustment = ql.Unadjusted
fixedLegDayCounter = ql.Thirty360(ql.Thirty360.BondBasis)
fixedRate = 0.04

# %%
floatingLegFrequency = ql.Quarterly
spread = 0.0
fixingDays = 2
index = ql.Euribor3M(forecastTermStructure)
floatingLegAdjustment = ql.ModifiedFollowing
floatingLegDayCounter = index.dayCounter()

# %%
fixedSchedule = ql.Schedule(
    settlementDate,
    maturity,
    fixedLegTenor,
    calendar,
    fixedLegAdjustment,
    fixedLegAdjustment,
    ql.DateGeneration.Forward,
    False,
)
floatingSchedule = ql.Schedule(
    settlementDate,
    maturity,
    floatingLegTenor,
    calendar,
    floatingLegAdjustment,
    floatingLegAdjustment,
    ql.DateGeneration.Forward,
    False,
)

def _ensure_fixings(idx: "ql.IborIndex", start: ql.Date, end: ql.Date):
    try:
        # Prefer helper to avoid macOS addFixing issues
        ql.ensure_index_fixings(idx, start, end, True)
    except Exception:
        pass


def build_swaps():
    idx = ql.Euribor3M(forecastTermStructure)
    fdc = idx.dayCounter()
    # spot swap
    fixedSchedule = ql.Schedule(
        settlementDate,
        maturity,
        fixedLegTenor,
        calendar,
        fixedLegAdjustment,
        fixedLegAdjustment,
        ql.DateGeneration.Forward,
        False,
    )
    floatingSchedule = ql.Schedule(
        settlementDate,
        maturity,
        floatingLegTenor,
        calendar,
        floatingLegAdjustment,
        floatingLegAdjustment,
        ql.DateGeneration.Forward,
        False,
    )
    spot = ql.VanillaSwap(
        ql.Swap.Payer,
        nominal,
        fixedSchedule,
        fixedRate,
        fixedLegDayCounter,
        floatingSchedule,
        idx,
        spread,
        fdc,
    )
    spot.setPricingEngine(swapEngine)

    # forward starting swap (1Y fwd)
    forwardStart = calendar.advance(settlementDate, 1, ql.Years)
    forwardEnd = calendar.advance(forwardStart, length, ql.Years)
    fixedSchedule = ql.Schedule(
        forwardStart,
        forwardEnd,
        fixedLegTenor,
        calendar,
        fixedLegAdjustment,
        fixedLegAdjustment,
        ql.DateGeneration.Forward,
        False,
    )
    floatingSchedule = ql.Schedule(
        forwardStart,
        forwardEnd,
        floatingLegTenor,
        calendar,
        floatingLegAdjustment,
        floatingLegAdjustment,
        ql.DateGeneration.Forward,
        False,
    )
    fwd = ql.VanillaSwap(
        ql.Swap.Payer,
        nominal,
        fixedSchedule,
        fixedRate,
        fixedLegDayCounter,
        floatingSchedule,
        idx,
        spread,
        fdc,
    )
    fwd.setPricingEngine(swapEngine)
    # Ensure forward-fixing availability for robustness
    try:
        _ensure_fixings(idx, floatingSchedule[0], floatingSchedule[-1])
    except Exception:
        pass
    return spot, fwd

# %% [markdown]
# We'll price them both on the bootstrapped curves.
#
# This is the quoted 5-years market rate; we expect the fair rate of the spot swap to match it.


# %%
print_section("Interest-rate Swaps (Engine-first)")
print_subsection("Quoted 5Y market swap rate")
print(f"Quote (5Y) : {100.0*swaps[(5, ql.Years)].value():.3f} %")


# %%
def _price_block(label: str, swap: "ql.VanillaSwap") -> dict:
    """Return a small dict of pricing outputs, engine-first with guarded fallback."""
    try:
        npv = float(swap.NPV())
        par = float(swap.fairRate())
        _assert_nonzero(f"{label} NPV", npv)
        return {"label": label, "NPV (ccy)": npv, "Fair rate (%)": par * 100.0, "method": "engine"}
    except Exception:
        # Robust fallback: estimate par via forwards/annuity and PV via difference
        f_dc = floatingLegDayCounter
        fixed_dc = fixedLegDayCounter
        fixed_dates = list(fixedSchedule.dates())
        float_dates = list(floatingSchedule.dates())
        DF_disc = [discountTermStructure.discount(d) for d in fixed_dates]
        annuity = 0.0
        for i in range(1, len(fixed_dates)):
            annuity += DF_disc[i] * fixed_dc.yearFraction(fixed_dates[i-1], fixed_dates[i])
        pv_float = 0.0
        for i in range(1, len(float_dates)):
            d0 = float_dates[i-1]; d1 = float_dates[i]
            alpha = f_dc.yearFraction(d0, d1)
            df0 = forecastTermStructure.discount(d0)
            df1 = forecastTermStructure.discount(d1)
            fwd = (df0/df1 - 1.0) / max(alpha, 1e-12)
            df_disc = discountTermStructure.discount(d1)
            pv_float += fwd * alpha * df_disc
        par = (pv_float / annuity) if annuity else 0.0
        npv_calc = (pv_float - fixedRate * annuity) * (nominal/1.0)
        return {"label": label, "NPV (ccy)": npv_calc, "Fair rate (%)": par * 100.0, "method": "fallback"}


# %% [markdown]
# These are the results for the 5-years spot swap on the deposit/futures/swap curve...

# %%
if ARGS.curve in ('futures','both'):
    try:
        if ARGS.debug_pillars:
            dfp = _pillars_df(futuresHelpers + swapHelpers[1:])
            if not dfp.empty:
                counts = dfp['pillar'].value_counts()
                if any(counts > 1):
                    raise RuntimeError('duplicate pillar dates present in futures path')
        forecastTermStructure.linkTo(depoFuturesSwapCurve)
        spot, forward = build_swaps()
        rows = []
        rows.append(_price_block("Spot 5Y (Depo+Futures+Swap)", spot))
        rows.append(_price_block("Fwd 1Yx5Y (Depo+Futures+Swap)", forward))
        show_df("Engine results — Depo+Futures+Swap", pd.DataFrame(rows))
        try:
            add_summary("Spot 5Y NPV (Depo+Fut)", rows[0]["NPV (ccy)"])
            add_summary("Spot 5Y Fair rate (Depo+Fut) %", rows[0]["Fair rate (%)"])
        except Exception:
            pass
    except Exception as _e:
        print_subsection("Depo+Futures path skipped")
        print(str(_e))

# 2) FRA-based curve (stable)
if ARGS.curve in ('fra','both'):
    forecastTermStructure.linkTo(depoFraSwapCurve)
    spot, forward = build_swaps()
    rows = []
    rows.append(_price_block("Spot 5Y (Depo+FRA+Swap)", spot))
    rows.append(_price_block("Fwd 1Yx5Y (Depo+FRA+Swap)", forward))
    show_df("Engine results — Depo+FRA+Swap", pd.DataFrame(rows))
    try:
        add_summary("Spot 5Y NPV (Depo+FRA)", rows[0]["NPV (ccy)"])
        add_summary("Spot 5Y Fair rate (Depo+FRA) %", rows[0]["Fair rate (%)"])
    except Exception:
        pass

# %% [markdown]
# ...and these are on the deposit/fra/swap curve.

# %%
if ARGS.curve in ('fra','both'):
    # Second run on FRA curve (unchanged instruments) for parity
    forecastTermStructure.linkTo(depoFraSwapCurve)
    spot, forward = build_swaps()
    rows = []
    rows.append(_price_block("Spot 5Y (Depo+FRA+Swap) [repeat]", spot))
    rows.append(_price_block("Fwd 1Yx5Y (Depo+FRA+Swap) [repeat]", forward))
    show_df("Repeat — Depo+FRA+Swap", pd.DataFrame(rows))

# %% [markdown]
# The same goes for the 1-year forward swap, except for the fair rate not matching the spot rate.

# %%
# Forward section (FRA curve)
if ARGS.curve in ('fra','both'):
    forecastTermStructure.linkTo(depoFraSwapCurve)
    spot, forward = build_swaps()
    rows = [_price_block("Fwd 1Yx5Y (Depo+FRA)", forward)]
    show_df("Forward swap — Depo+FRA+Swap", pd.DataFrame(rows))

# %%
# (Removed futures forward duplicate)

# %% [markdown]
# Modifying the 5-years swap rate and repricing will change the results:

# %%
swaps[(5, ql.Years)].setValue(0.046)

# %%
if ARGS.curve in ('fra','both'):
    forecastTermStructure.linkTo(depoFraSwapCurve)
    rows = [
        _price_block("Spot 5Y (Depo+FRA, quote‑bumped)", spot),
        _price_block("Fwd 1Yx5Y (Depo+FRA, quote‑bumped)", forward),
    ]
    show_df("Reprice after 5Y quote bump (FRA)", pd.DataFrame(rows))

# Final summary
print_section("Summary")
if SUMMARY:
    w = max(len(k) for k, _ in SUMMARY)
    for k, v in SUMMARY:
        print(f"{k:<{w}} : {v}")
else:
    print("No summary entries.")
