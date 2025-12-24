#!/usr/bin/env python

import sys
sys.path.append('../')
from vre_examples_helper import VreExample

vreex = VreExample(sys.argv[1] if len(sys.argv) > 1 else False)

print("+-----------------------------------------------------+")
print("| XVA Risk: SA-CVA    - AAD (CG) 2 Trade EQ COM      |")
print("+-----------------------------------------------------+")

vreex.print_headline("Run SA-CVA with CG/AAD CVA Sensitivities (FD EQ/COM inputs)")
vreex.run("Input/vre_sacva_fd_aad_eqcom.xml")
