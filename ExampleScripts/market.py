
# Copyright (C) 2018 Quaternion Risk Manaement Ltd
# Copyright (C) 2025 Growth Mindset Pty Ltd 

# All rights reserved.

from VRE import *
import os, tempfile

# Delta: Build a minimal Parameters XML on-the-fly and create a TodaysMarket
_here = os.path.abspath(os.path.dirname(__file__))
_repo = os.path.abspath(os.path.join(_here, os.pardir, os.pardir))
_input = os.path.join(_repo, "Input")

params_xml = f"""
<Parameters>
  <Setup>
    <Parameter name="asofDate">2016-02-05</Parameter>
    <Parameter name="curveConfigFile">curveconfig.xml</Parameter>
    <Parameter name="marketConfigFile">todaysmarket.xml</Parameter>
    <Parameter name="marketDataFile">market_20160205.txt</Parameter>
    <Parameter name="fixingDataFile">fixings_20160205.txt</Parameter>
    <Parameter name="conventionsFile">conventions.xml</Parameter>
    <Parameter name="implyTodaysFixings">Y</Parameter>
  </Setup>
</Parameters>
""".strip()

with tempfile.NamedTemporaryFile("w", suffix=".xml", dir=_input, delete=False) as tf:
    tf.write(params_xml)
    tf.flush()
    vrexml = tf.name

print("Run VRE using", vrexml)
market = make_example_market(vrexml)

asof = market.asofDate();
print ("Market asof date", asof)

ccy = "EUR"
index = "EUR-EURIBOR-6M"
print ("Get term structures for ccy ", ccy, "and index", index);

discountCurve = market.discountCurve(ccy)
print ("   discount curve is of type", type(discountCurve))

iborIndex = market.iborIndex(index)
print ("   ibor index is of type", type(iborIndex))

forwardCurve = iborIndex.forwardingTermStructure()
print ("   forward curve is of type", type(forwardCurve))

print ("Evaluate term structures");
date = asof + 10*Years;
zeroRateDcName = "ACT/365"
discount = discountCurve.discount(date)
zero = discountCurve.zeroRate(date, zeroRateDcName, "Continuous")
fwdDiscount = forwardCurve.discount(date)
fwdZero = forwardCurve.zeroRate(date, zeroRateDcName, "Continuous")
print ("   10y discount factor (discount curve) is", discount)
print ("   10y discout factor (forward curve) is", fwdDiscount)
print ("   10y zero rate (discount curve) is", zero)
print ("   10y zero rate (forward curve) is", fwdZero)

print("Done")
