#!/usr/bin/env python

import glob
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.chdir(HERE)

sys.path.append('../')
from vre_examples_helper import VreExample

# Ensure output folders exist for each run
for p in [
    Path("Output/8_1"),
    Path("Output/8_2"),
    Path("Output/8_3/pnl"),
    Path("Output/8_3/explain"),
]:
    p.mkdir(parents=True, exist_ok=True)

vreex = VreExample(sys.argv[1] if len(sys.argv) > 1 else False)


print("+-----------------------------------------------------+")
print("| Scenario (8_1)                                      |")
print("+-----------------------------------------------------+")
vreex.run("Input/8_1/vre.xml")

print("+-----------------------------------------------------+")
print("| Historical Sim Var (8_2)                            |")
print("+-----------------------------------------------------+")
vreex.run("Input/8_2/vre.xml")

print("+-----------------------------------------------------+")
print("| P&L (8_3)                                           |")
print("+-----------------------------------------------------+")
vreex.run("Input/8_3/vre_pnl.xml")

print("+-----------------------------------------------------+")
print("| P&L Explain (8_3)                                   |")
print("+-----------------------------------------------------+")
vreex.run("Input/8_3/vre_explain.xml")
