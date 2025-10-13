#!/usr/bin/env python

import sys
sys.path.append('../')
from vre_examples_helper import VreExample

vreex = VreExample(sys.argv[1] if len(sys.argv)>1 else False)

vrexmls = [
	("Input/vre_SIMM2.4_10D.xml", "2.4", "10"),
	("Input/vre_SIMM2.4_1D.xml", "2.4", "1"),
	("Input/vre_SIMM2.6_10D.xml", "2.6", "10"),
	("Input/vre_SIMM2.6_1D.xml", "2.6", "1")
]
for vrexml in vrexmls:
	vreex.print_headline(f"Run VRE SIMM; version={vrexml[1]}; MPOR days={vrexml[2]}")
	vreex.run(vrexml[0])
