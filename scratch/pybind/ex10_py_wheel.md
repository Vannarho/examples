Plan to switch Example_10 notebook to use the packaged Python wheel (self-contained deps) instead of a local repo binary

- Add a short prerequisites block near the top of `Notebooks/Example_10/vre.ipynb` that mirrors other examples and instructs `pip install vannarho-risk-engine` (or install the provided wheel file) as the required step; remove any implication that a locally built binary is needed.
- Insert a small bootstrap cell to install/upgrade the wheel from PyPI or a bundled wheel path when `VRE` import fails (or when the module originates from the repo build tree). This should run before importing `VRE`.
- Add a guard/diagnostic cell that prints `VRE.__file__` and the `vannarho-risk-engine` package version, and asserts the path resolves to site-packages (not `build/.../VREPython`), so users are clearly on the wheel.
- Update `Notebooks/Example_10/README.txt` with the wheel-first setup guidance and drop references to repo binaries; point to the bootstrap cell if available.
- Keep the existing notebook logic (`VRE.vrea.Parameters`, XML inputs) unchanged; verify no remaining references to compiled artifacts or `PYTHONPATH` tweaks are required once the wheel is mandated.
