import platform
import subprocess
import shutil
import os
import glob
import re

import matplotlib
import sys

matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.ticker
import pandas as pd
from datetime import datetime
from math import log

skip_examples = [
    "Example_54",
    "Example_56",
    "Example_68",
    "Example_70"    
    ]

def get_list_of_examples():
    return get_list_of_new_examples()

def get_list_of_legacy_examples():
    legacy = sorted([e for e in os.listdir(os.path.join(os.getcwd(),"Legacy"))
                     if e[:8] == 'Example_'], key=lambda e: int(e.split('_')[1]))
#                     if e == 'Example_1'])
    return [ os.path.join("Legacy", e) for e in legacy if e not in skip_examples ]

def get_list_of_new_examples():
    return ["AmericanMonteCarlo",
            "CreditRisk",
            "CurveBuilding",
            "Exposure",
            "ExposureWithCollateral",
            "InitialMargin",
            "MarketRisk",
            "MinimalSetup",
            "VRE-API",
            "VREPython",
            "Performance",
            "Products",
            "ScriptedTrade",
            "XvaRisk"
            ]

def get_list_vre_academy():
    return ["Academy/FC003_Reporting_Currency",
            "Academy/TA001_Equity_Option",
            "Academy/TA002_IR_Swap"
            ]

def print_on_console(line):
    print(line)
    sys.stdout.flush()


class VreExample(object):
    def __init__(self, dry=False):
        self.vre_exe = ""
        self._qle_core_exe = None
        self.headlinecounter = 0
        self.dry = dry
        self.ax = None
        self.plot_name = ""
        if 'VRE_EXAMPLES_USE_PYTHON' in os.environ.keys():
            self.use_python = os.environ['VRE_EXAMPLES_USE_PYTHON']=="1"
            self.vre_exe = ""
        else:
            self.use_python = False
            self._locate_vre_exe()

    def _locate_vre_exe(self):
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

        # Allow users to override the executable location explicitly. If
        # VRE_EXECUTABLE is set and points to a valid file it is used directly
        # without any additional lookup logic.
        env_vre = os.environ.get("VRE_EXECUTABLE")
        if env_vre and os.path.isfile(env_vre):
            self.vre_exe = env_vre
            print_on_console("Using VRE executable " + os.path.abspath(self.vre_exe))
            return

        # Attempt to determine the build directory from an explicit CMake
        # preset.  The preset name can be supplied via the VRE_CMAKE_PRESET
        # environment variable or via CMAKE_BUILD_PRESET/CMAKE_PRESET which are
        # understood by CMake itself.  If a preset is provided and the
        # corresponding executable exists it is preferred over the legacy search
        # paths below.
        preset_name = (
            os.environ.get("VRE_CMAKE_PRESET")
            or os.environ.get("CMAKE_BUILD_PRESET")
            or os.environ.get("CMAKE_PRESET")
        )
        preset_file = os.path.join(repo_root, "CMakePresets.json")
        if preset_name and os.path.isfile(preset_file):
            try:
                import json

                with open(preset_file, "r") as fh:
                    presets = json.load(fh)
                binary_dir = None
                for p in presets.get("configurePresets", []):
                    if p.get("name") == preset_name:
                        binary_dir = p.get("binaryDir")
                        break
                if binary_dir:
                    binary_dir = binary_dir.replace("${sourceDir}", repo_root)
                    candidate = os.path.join(
                        binary_dir,
                        "App",
                        "vre.exe" if os.name == "nt" else "vre",
                    )
                    if os.path.isfile(candidate):
                        self.vre_exe = os.path.relpath(candidate)
                        print_on_console(
                            "Using VRE executable " + os.path.abspath(self.vre_exe)
                        )
                        return
            except Exception:
                pass

        # If no preset is provided, search common build directories.  This
        # allows the examples to run without explicitly specifying a preset
        # once the project has been configured via CMake presets.
        build_root = os.path.join(repo_root, "build")
        if not self.vre_exe and os.path.isdir(build_root):
            exe_name = "vre.exe" if os.name == "nt" else "vre"
            try:
                for sub in sorted(os.listdir(build_root)):
                    subdir = os.path.join(build_root, sub)
                    if not os.path.isdir(subdir):
                        continue
                    candidate = os.path.join(subdir, "App", exe_name)
                    if os.path.isfile(candidate):
                        self.vre_exe = os.path.relpath(candidate)
                        print_on_console(
                            "Using VRE executable " + os.path.abspath(self.vre_exe)
                        )
                        return
            except Exception:
                pass

        # Fall back to the old heuristics if the preset search failed
        if os.name == 'nt':
            if platform.machine()[-2:] == "64":
                if os.path.isfile(r"..\..\App\bin\x64\Release\vre.exe"):
                    self.vre_exe = r"..\..\App\bin\x64\Release\vre.exe"
                elif os.path.isfile(r"..\..\..\App\bin\x64\Release\vre.exe"):
                    self.vre_exe = r"..\..\..\App\bin\x64\Release\vre.exe"
                elif os.path.isfile(r"..\..\build\App\vre.exe"):
                    self.vre_exe = r"..\..\build\App\vre.exe"
                elif os.path.isfile(r"..\..\..\build\App\vre.exe"):
                    self.vre_exe = r"..\..\..\build\App\vre.exe"
                elif os.path.isfile(r"..\..\..\build\vre\App\vre.exe"):
                    self.vre_exe = r"..\..\..\build\vre\App\vre.exe"
                elif os.path.isfile(r"..\..\..\..\build\vre\App\vre.exe"):
                    self.vre_exe = r"..\..\..\..\build\vre\App\vre.exe"
                elif os.path.isfile(r"..\..\..\build\vre\App\RelWithDebInfo\vre.exe"):
                    self.vre_exe = r"..\..\..\build\vre\App\RelWithDebInfo\vre.exe"
                elif os.path.isfile(r"..\..\..\..\build\vre\App\RelWithDebInfo\vre.exe"):
                    self.vre_exe = r"..\..\..\..\build\vre\App\RelWithDebInfo\vre.exe"
                elif os.path.isfile(r"..\..\build\App\Release\vre.exe"):
                    self.vre_exe = r"..\..\build\App\Release\vre.exe"
                elif os.path.isfile(r"..\..\..\build\App\Release\vre.exe"):
                    self.vre_exe = r"..\..\..\build\App\Release\vre.exe"
                else:
                    print_on_console("VRE executable not found.")
                    quit()
            else:
                if os.path.isfile(r"..\..\App\bin\Win32\Release\vre.exe"):
                    self.vre_exe = r"..\..\App\bin\Win32\Release\vre.exe"
                elif os.path.isfile(r"..\..\..\App\bin\Win32\Release\vre.exe"):
                    self.vre_exe = r"..\..\..\App\bin\Win32\Release\vre.exe"
                elif os.path.isfile(r"..\..\build\App\vre.exe"):
                    self.vre_exe = r"..\..\build\App\vre.exe"
                elif os.path.isfile(r"..\..\..\build\App\vre.exe"):
                    self.vre_exe = r"..\..\..\build\App\vre.exe"
                else:
                    print_on_console("VRE executable not found.")
                    quit()
        else:
            if os.path.isfile("../../App/build/vre"):
                self.vre_exe = "../../App/build/vre"
            elif os.path.isfile("../../../App/build/vre"):
                self.vre_exe = "../../../App/build/vre"
            elif os.path.isfile("../../build/App/vre"):
                self.vre_exe = "../../build/App/vre"
            elif os.path.isfile("../../../build/App/vre"):
                self.vre_exe = "../../../build/App/vre"
            elif os.path.isfile("../../../build/App/vre"):
                self.vre_exe = "../../../build/App/vre"
            elif os.path.isfile("../../../../build/App/vre"):
                self.vre_exe = "../../../../build/App/vre"
            elif os.path.isfile("../../App/vre"):
                self.vre_exe = "../../App/vre"
            elif os.path.isfile("../../../App/vre"):
                self.vre_exe = "../../../App/vre"
            elif os.path.isfile("../../../build/vre/App/vre"):
                self.vre_exe = "../../../build/vre/App/vre"
            elif os.path.isfile("../../../../build/vre/App/vre"):
                self.vre_exe = "../../../../build/vre/App/vre"
            else:
                print_on_console("VRE executable not found.")
                quit()
        print_on_console("Using VRE executable " + (os.path.abspath(self.vre_exe)))

        # Set the DYLD_LIBRARY_PATH environment variable. The standard build
        # layout places the libraries next to the executable, but on macOS the
        # libraries often reside in build subdirectories.  Determine all
        # relevant directories dynamically and append them to the environment
        # variable so that the executables can locate their dependencies.

        exe_abs = os.path.abspath(self.vre_exe)
        exe_dir = os.path.dirname(exe_abs)
        # VRE libraries sit one level above the App directory
        library_root = os.path.abspath(os.path.join(exe_dir, os.pardir))
        search_paths = [exe_dir, library_root]

        # Search subdirectories for folders that actually contain the core
        # VRE libraries.  This keeps the environment setup flexible with
        # different build directory layouts.
        # for root, dirs, files in os.walk(library_root):
        #     if (
        #         "libVREData.dylib" in files
        #         or "libVREAnalytics.dylib" in files
        #         or "libQuantExt.dylib" in files
        #         or any(f.startswith("libQuantLib") and f.endswith(".dylib") for f in files)
        #         or "libVREData.so" in files
        #         or "libVREAnalytics.so" in files
        #         or "libQuantExt.so" in files
        #         or any(f.startswith("libQuantLib") and f.endswith(".so") for f in files)
        #     ):
        #         search_paths.append(root)

        current = os.environ.get("DYLD_LIBRARY_PATH", "")
        if current:
            search_paths.extend([p for p in current.split(":") if p])

        # # De-duplicate while preserving order
        dyld_paths = []
        seen = set()
        for p in search_paths:
            if p not in seen:
                dyld_paths.append(p)
                seen.add(p)

        os.environ["DYLD_LIBRARY_PATH"] = ":".join(dyld_paths)
        print_on_console("Set DYLD_LIBRARY_PATH to " + os.environ["DYLD_LIBRARY_PATH"])

        # # Warn if none of the core libraries are found
        # expected_libs = []
        # for lib in ["libVREData", "libVREAnalytics", "libQuantExt", "libQuantLib"]:
        #     expected_libs.extend([os.path.join(p, lib + suffix) for p in dyld_paths for suffix in (".dylib", ".so")])

        # if not any(os.path.isfile(l) for l in expected_libs):
        #     print_on_console(
        #         "Warning: required VRE libraries not found under {}.".format(library_root)
        #         + "\nVRE might not run correctly. Please build the project or set"
        #         " DYLD_LIBRARY_PATH accordingly."
        #     )

    def _locate_qle_core_exe(self):
        if self._qle_core_exe and os.path.isfile(self._qle_core_exe):
            return self._qle_core_exe

        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        candidates = []

        build_root = os.path.join(repo_root, "build")
        if os.path.isdir(build_root):
            patterns = [
                os.path.join(build_root, "**", "QuantExt", "test", "qle-core"),
                os.path.join(build_root, "**", "QuantExt", "test", "qle-core.exe"),
            ]
            for pattern in patterns:
                candidates.extend(glob.glob(pattern, recursive=True))

        legacy_patterns = [
            os.path.join(repo_root, "QuantExt", "test", "qle-core"),
            os.path.join(repo_root, "QuantExt", "test", "qle-core.exe"),
            os.path.join(repo_root, "..", "QuantExt", "test", "qle-core"),
        ]
        for lp in legacy_patterns:
            if os.path.isfile(lp):
                candidates.append(lp)

        for candidate in candidates:
            if os.path.isfile(candidate):
                self._qle_core_exe = os.path.abspath(candidate)
                return self._qle_core_exe

        return None

    def print_headline(self, headline):
        self.headlinecounter += 1
        print_on_console('')
        print_on_console(str(self.headlinecounter) + ") " + headline)

    def get_times(self, output):
        print_on_console("Get times from the log file:")
        logfile = open(output)
        for line in logfile.readlines():
            if "ValuationEngine completed" in line:
                times = line.split(":")[-1].strip().split(",")
                for time in times:
                    print_on_console("\t" + time.split()[0] + ": " + time.split()[1])

    def get_output_data_from_column(self, csv_name, colidx, offset=1, filter='', filterCol=0):
        f = open(os.path.join(os.path.join(os.getcwd(), "Output"), csv_name))
        data = []
        count = 0
        for line in f:
            tokens = line.split(',')
            if colidx < len(tokens):
                if (filter == '' or (filter in tokens[filterCol]) or count == 0):
                    data.append(tokens[colidx])
            else:
                data.append("Error")
            count = count + 1
        return [float(i) for i in data[offset:]]

    def save_output_to_subdir(self, subdir, files):
        if not os.path.exists(os.path.join("Output", subdir)):
            os.makedirs(os.path.join("Output", subdir))
        for file in files:
            shutil.copy(os.path.join("Output", file), os.path.join("Output", subdir))

    def plot(self, filename, colIdxTime, colIdxVal, color, label, offset=1, marker='', linestyle='-', filter='', filterCol=0):
        self.ax.plot(self.get_output_data_from_column(filename, colIdxTime, offset, filter, filterCol),
                     self.get_output_data_from_column(filename, colIdxVal, offset, filter, filterCol),
                     linewidth=2,
                     linestyle=linestyle,
                     color=color,
                     label=label,
                     marker=marker)

    def plotScaled(self, filename, colIdxTime, colIdxVal, color, label, offset=1, marker='', linestyle='-', title='', xlabel='', ylabel='', rescale=False, zoom=1, legendLocation='upper right', xScale=1.0, yScale=1.0, exponent=1.0):
        xTmp = self.get_output_data_from_column(filename, colIdxTime, offset)
        yTmp = self.get_output_data_from_column(filename, colIdxVal, offset)
        x = []
        y = []
        yMax = pow(float(yTmp[0]), exponent) / yScale
        yMin = pow(float(yTmp[0]), exponent) / yScale
        for i in range(0, len(xTmp)-1):
            try :
                tmp = pow(float(yTmp[i]), exponent) / yScale;
                y.append(tmp)
                yMax = max(tmp, yMax)
                yMin = min(tmp, yMin)
                x.append(float(xTmp[i]) / xScale)
            except TypeError:
                pass
        if (yMax != 0.0):
            yn = [ u / yMax for u in y ]
        self.ax.plot(x,
                     y,
                     linewidth=2,
                     linestyle=linestyle,
                     color=color,
                     label=label,
                     marker=marker)
        if rescale:            
            self.ax.set_ylim([yMin/zoom, yMax/zoom])
        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.legend(loc=legendLocation, shadow=True)        

    def plotSq(self, filename, colIdxTime, colIdxVal, color, label, offset=1, marker='', linestyle='-', title='',
               xlabel='', ylabel='', rescale=False, zoom=1):
        xTmp = self.get_output_data_from_column(filename, colIdxTime, offset)
        yTmp = self.get_output_data_from_column(filename, colIdxVal, offset)
        x = []
        y2 = []
        yMax = 0.0
        for i in range(0, len(xTmp) - 1):
            try:
                tmp = float(yTmp[i]) * float(yTmp[i])
                y2.append(tmp)
                yMax = max(tmp, yMax)
                x.append(float(xTmp[i]))
            except TypeError:
                pass
        y2n = [u / yMax for u in y2]
        self.ax.plot(x,
                     y2,
                     linewidth=2,
                     linestyle=linestyle,
                     color=color,
                     label=label,
                     marker=marker)
        if rescale:
            self.ax.set_ylim([0, yMax / zoom])
        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.legend(loc="upper right", shadow=True)
        self.ax.get_yaxis().set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, p: '{:1.2e}'.format(float(x))))

    def plot_npv(self, filename, colIdx, color, label, marker='', offset=1, filter='', filterCol=0):
        data = self.get_output_data_from_column(filename, colIdx, offset, filter, filterCol)
        self.ax.plot(range(1, len(data) + 1),
                     data,
                     color=color,
                     label=label,
                     linewidth=2,
                     marker=marker)

    def plot_zeroratedist(self, filename, colIdxTime, colIdxVal, maturity, color, label,
                          title='Zero Rate Distribution'):
        f = open(os.path.join(os.path.join(os.getcwd(), "Output"), filename))
        xdata = []
        ydata = []
        for line in f:
            try:
                xtmp = datetime.strptime(line.split(',')[colIdxTime], '%Y-%m-%d')
                ytmp = -log(float(line.split(',')[colIdxVal])) / float(maturity)
                xdata.append(xtmp)
                ydata.append(ytmp)
            except ValueError:
                pass
            except TypeError:
                pass
        d = pd.DataFrame({'x': xdata, 'y': ydata})
        grouped = d.groupby('x')
        mdata = grouped.mean()['y']
        sdata = grouped.std()['y']
        self.ax.plot(list(mdata.index.values),
                     list(mdata),
                     linewidth=3,
                     linestyle='-',
                     color=color,
                     label=label + ' (mean)')
        self.ax.plot(list(mdata.index.values),
                     list(mdata - sdata),
                     linewidth=1,
                     linestyle='-',
                     color=color,
                     label=label + ' (mean +/- std)')
        self.ax.plot(list(mdata.index.values),
                     list(mdata + sdata),
                     linewidth=1,
                     linestyle='-',
                     color=color,
                     label='')
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Zero Rate")
        self.ax.get_yaxis().set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, p: '{:1.4f}'.format(float(x))))
        self.ax.legend(loc="upper left", shadow=True)
        self.ax.set_title(title)

    def decorate_plot(self, title, ylabel="Exposure", xlabel="Time / Years", legend_loc="upper right", y_format_as_int = True, display_grid = False):
        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.legend(loc=legend_loc, shadow=True)
        if y_format_as_int:
            self.ax.get_yaxis().set_major_formatter(
                matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
        if display_grid:
            self.ax.grid()

    def plot_line(self, xvals, yvals, color, label):
        self.ax.plot(xvals, yvals, color=color, label=label, linewidth=2)

    def plot_line_marker(self, xvals, yvals, color, label, marker = ''):
        self.ax.plot(xvals, yvals, color=color, label=label, marker=marker, linewidth=2)

    def plot_hline(self, yval, color, label):
        plt.axhline(yval, xmin=0, xmax=1, color=color, label=label, linewidth=2)

    def setup_plot(self, filename):
        self.fig = plt.figure(figsize=plt.figaspect(0.4))
        self.ax = self.fig.add_subplot(111)
        self.plot_name = "mpl_" + filename

    def save_plot_to_file(self, subdir="Output"):
        file = os.path.join(subdir, self.plot_name + ".pdf")
        plt.savefig(file)
        print_on_console("Saving plot...." + file)
        plt.close()

    def run(self, xml):
        if not self.dry:
            if(self.use_python):
                if(os.path.isfile(os.path.join(os.pardir, "vre_wrapper.py"))):
                    res = subprocess.call([sys.executable, os.path.join(os.pardir, "vre_wrapper.py"), xml])
                elif(os.path.isfile(os.path.join(os.pardir, "..", "vre_wrapper.py"))):
                    res = subprocess.call([sys.executable, os.path.join(os.pardir, "..", "vre_wrapper.py"), xml])
            else:
                res = subprocess.call([self.vre_exe, xml])
            if res != 0:
                raise Exception("Return Code was not Null.")

    # --- GPU helper: detect device and patch XMLs in-place (with auto-restore) ---
    def _detect_external_device(self):
        import platform, subprocess, os
        override = os.getenv("EXTERNAL_COMPUTE_DEVICE")
        if override:
            return override
        system = platform.system()

        def _devices_from_compute_environment():
            try:
                return self._detect_compute_environment_devices()
            except Exception:
                return []

        def _nvidia_name():
            try:
                out = subprocess.check_output([
                    "nvidia-smi","--query-gpu=name","--format=csv,noheader"
                ], stderr=subprocess.DEVNULL, text=True, timeout=2)
                names = [l.strip() for l in out.splitlines() if l.strip()]
                return names[0] if names else None
            except Exception:
                return None

        if system == "Linux":
            name = _nvidia_name()
            if not name:
                raise RuntimeError("No NVIDIA GPU detected via nvidia-smi and no EXTERNAL_COMPUTE_DEVICE override set")
            return f"CUDA/NVIDIA/{name}"

        # macOS – prefer pyopencl if available, otherwise fall back to a simple SoC heuristic
        if system == "Darwin":
            devices = _devices_from_compute_environment()
            for preferred_prefix in ("Metal/", "OpenCL/"):
                for dev in devices:
                    if dev.startswith(preferred_prefix):
                        return dev
            try:
                import pyopencl as cl  # type: ignore
                for p in cl.get_platforms():
                    if "Apple" in (p.name or "") or "Apple" in (p.vendor or ""):
                        gpus = [d for d in p.get_devices() if d.type & cl.device_type.GPU]
                        if gpus:
                            return f"OpenCL/Apple/{gpus[0].name}"
            except Exception:
                pass
            try:
                brand = subprocess.check_output(["sysctl","-n","machdep.cpu.brand_string"], text=True).strip()
                if "M4" in brand and "Max" in brand:
                    return "OpenCL/Apple/Apple M4 Max"
                if "M3" in brand and "Ultra" in brand:
                    return "OpenCL/Apple/Apple M3 Ultra"
            except Exception:
                pass
            raise RuntimeError("No Apple OpenCL GPU detected and no EXTERNAL_COMPUTE_DEVICE override set")

        raise RuntimeError(f"Unsupported platform for GPU detection: {system}")

    def _detect_compute_environment_devices(self):
        exe = self._locate_qle_core_exe()
        if not exe or not os.path.isfile(exe):
            return []

        cmd = [exe, "--run_test=@qle.computeenvironment.testEnvironmentInit", "-l", "message", "-r", "confirm"]
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=20)
        except Exception:
            return []

        ansi_re = re.compile(r"\x1b\[[0-9;]*m")
        plain = ansi_re.sub("", out)
        pattern = re.compile(r"device '([^']+)'")
        devices = []
        for match in pattern.finditer(plain):
            name = match.group(1)
            if name not in devices:
                devices.append(name)
        return devices

    def _patch_external_device_param(self, xml_path, device_str):
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_path)
        root = tree.getroot()
        changed_any = False
        # Patch both pricing-engine and xva-cg parameter names
        names = {"ExternalComputeDevice", "xvaCgExternalComputeDevice"}
        for p in root.iter("Parameter"):
            if p.get("name") in names:
                p.text = device_str
                changed_any = True
        if not changed_any:
            params = root.find(".//Parameters") or root
            for n in names:
                ET.SubElement(params, "Parameter", name=n).text = device_str
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)

    def run_gpu_dynamic(self, main_xml, extra_xmls=None):
        """
        Detect the active GPU and patch the ExternalComputeDevice parameter
        into main_xml and any extra_xmls, in-place with automatic restore.
        Returns False (without raising) if no GPU is detected.
        """
        try:
            device = self._detect_external_device()
        except RuntimeError as err:
            print_on_console(f"[gpu] Skipping dynamic run: {err}")
            return False
        print_on_console(f"[gpu] ExternalComputeDevice = {device}")

        # Prepare list of XMLs to patch (relative to current example dir)
        xmls = [main_xml] + (extra_xmls or [])
        backups = []
        try:
            for rel in xmls:
                if not rel:
                    continue
                if not os.path.isfile(rel):
                    # tolerate missing extras
                    continue
                bak = rel + ".bak_gpu_patch"
                if os.path.exists(bak):
                    os.remove(bak)
                shutil.copy2(rel, bak)
                backups.append((rel, bak))
                self._patch_external_device_param(rel, device)

            # Run with patched main XML
            self.run(main_xml)
        finally:
            # Restore originals
            for rel, bak in backups:
                try:
                    if os.path.isfile(bak):
                        shutil.move(bak, rel)
                except Exception:
                    pass
        return True


def run_example(example):
    current_dir = os.getcwd()
    print_on_console("Running: " + example)
    try:
        os.chdir(os.path.join(os.getcwd(), example))
        filename = "run.py"
        sys.argv = [filename, 0]
        exit_code = subprocess.call([sys.executable, filename])
        os.chdir(os.path.dirname(os.getcwd()))
        print_on_console('-' * 50)
        print_on_console('')
    except:
        print_on_console("Error running " + example)
    finally:
        os.chdir(current_dir)
    return exit_code


if __name__ == "__main__":
    for example in (get_list_of_examples() + get_list_vre_academy()):
        run_example(example)
