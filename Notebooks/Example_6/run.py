#!/usr/bin/env python

import sys
sys.path.append('../')
from vre_examples_helper import VreExample

vreex = VreExample(sys.argv[1] if len(sys.argv)>1 else False)

vreex.print_headline("Run VRE to produce NPV cube and exposures")
vreex.run("Input/vre.xml")
vreex.get_times("Output/log.txt")

vreex.print_headline("Run VRE again to price European Swaptions")
vreex.run("Input/vre_swaption.xml")

vreex.print_headline("Plot results: Simulated exposures vs analytical swaption prices")

vreex.setup_plot("swaptions")
vreex.plot("exposure_trade_Swap_20y.csv", 2, 3, 'b', "Swap EPE")
vreex.plot("exposure_trade_Swap_20y.csv", 2, 4, 'r', "Swap ENE")
vreex.plot_npv("swaption_npv.csv", 6, 'g', "NPV Swaptions", marker='s')
vreex.decorate_plot(title="Example 1 - Simulated exposures vs analytical swaption prices")
vreex.save_plot_to_file()

