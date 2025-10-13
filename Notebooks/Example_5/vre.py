# Copyright (C) 2018 Quaternion Risk Manaement Ltd
# All rights reserved.

from VRE import *

print ("Loading parameters...")
params = Parameters()
print ("   params is of type", type(params))
params.fromFile("Input/vre.xml")
print ("   setup/asofdate = " + params.get("setup","asofDate"))

print ("Building VRE App...")
vre = VREApp(params)
print ("   vre is of type", type(vre))

print ("Running VRE process...");
# Run it all 
vre.run()

print("Done")
