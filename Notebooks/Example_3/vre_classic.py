'''
 Copyright (C) 2018-2023 Quaternion Risk Management Ltd

 This file is part of VRE, a free-software/open-source library
 for transparent pricing and risk analysis - http://opensourcerisk.org
 VRE is free software: you can redistribute it and/or modify it
 under the terms of the Modified BSD License.  You should have received a
 copy of the license along with this program.
 The license is also available online at <http://opensourcerisk.org>
 This program is distributed on the basis that it will form a useful
 contribution to risk analytics and model standardisation, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 FITNESS FOR A PARTICULAR PURPOSE. See the license for more details.
'''

import sys, time
from VRE import *

print ("Loading parameters...")
params = Parameters()
params.fromFile("Input/vre_classic.xml")

print ("Creating VREApp...")
vre = VREApp(params, True)

print ("Running VRE process...")
vre.run()

print ("VRE process done")
