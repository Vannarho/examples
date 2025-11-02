'''
 Copyright (C) 2022 Quaternion Risk Management Ltd
 Copyright (C) 2025 Growth Mindset Pty Ltd
 All rights reserved.

 This file is part of VRE, a free-software/open-source library
 for transparent pricing and risk analysis

 VRE is free software: you can redistribute it and/or modify it
 under the terms of the Modified BSD License.  You should have received a
 copy of the license along with this program.

 This program is distributed on the basis that it will form a useful
 contribution to risk analytics and model standardisation, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 FITNESS FOR A PARTICULAR PURPOSE. See the license for more details.
'''

import sys, time
from VRE import *

print ("Loading parameters...")
params = Parameters()
params.fromFile("Input/vre.xml")

print ("Creating VREApp...")
vre = VREApp(params)

print ("Running VRE process...")
vre.run()

print("Run time: %.6f sec" % vre.getRunTime())

print ("VRE process done")
