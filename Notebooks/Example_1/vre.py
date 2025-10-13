'''
 Copyright (C) 2022 Quaternion Risk Management Ltd
 Copyright (C) 2025 Growth Mindset Pty Ltd
 All rights reserved
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
