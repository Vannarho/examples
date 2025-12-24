This example mirrors Example_8 style but demonstrates:
- SA-CCR (BIS Example 1 Aggregation)
- SA-CVA (BA-CVA reduced + SA-CVA classic)
- FRTB-SA (SBM and Simplified)

Prerequisites (wheel-first):
- Python 3.9–3.13
- Install the packaged wheel (bundles native deps): `pip install --upgrade vannarho-risk-engine` or point pip at a local `.whl` under wheelhouse/ or build/wheel/.
- No repo-built binaries or PYTHONPATH tweaks are required; the wheel includes QuantLib/QuantExt/VRE libraries.

Usage:
- The notebook begins with a wheel bootstrap/validation cell that ensures `import VRE` comes from a site-packages wheel (and not a build tree). Run the top cells first, then proceed with the analytics sections.
- It loads the corresponding XML master configs under Examples/* and runs them via VRE.Parameters + VRE.VREApp.
