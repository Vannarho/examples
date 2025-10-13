# VRE Python Module

We provide easy access to VRE via a pre-compiled Python module, updated with each release.
The Python module provides the same functionality as the VRE command line executable and more.

Some example scripts using this VRE module are provided in this VREPython directory.

Prerequisite: Python 3.9+

If you are developing locally, install the module into your environment rather than tweaking `PYTHONPATH`.
From `VREPython/`, run: `python -m pip install -e .`.

Otherwise install the pre-built Python module as follows:

Create a virtual environment: <code> python -m venv env1 </code>

Activate the virtual environment
- on Windows: <code> .\env1\Scripts\activate.bat </code>
- on macOS or Linux: <code> source env1/bin/activate </code>

Then install VRE: <code> pip install vannarho-risk-engine </code>

Try the Python examples
- Re-run the Swap exposure of the first Exposure example: <code> python vre.py </code>
- Show how to access and post-process VRE in-memory results without reading files: <code> python vre2.py </code>
- Demonstrate lower-level access to the QuantLib and QuantExt libraries: <code> python commodityforward.py </code>
- Then try any of the Jupyter notebooks, in directories VREPython/Notebooks/Example_*;
  install juypter: <code> python -m pip install jupyterlab </code>
  start juypter: <code> python -m jupyterlab & </code>
  and open any of the notebooks
