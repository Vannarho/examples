import platform
import subprocess
import shutil
import os
import re
import tomllib

import matplotlib
import sys
from pathlib import Path

matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.ticker
import pandas as pd
from datetime import datetime
from math import log

from _wheel_runtime import _import_installed_vre

skip_examples = [
    "Example_54",
    "Example_56",
    "Example_68",
    "Example_70"    
    ]

def get_list_of_examples():
    return get_list_of_new_examples()

def get_list_of_legacy_examples():
    legacy = sorted([e for e in os.listdir(os.path.join(os.getcwd(),"legacy"))
                     if e[:8] == 'Example_'], key=lambda e: int(e.split('_')[1]))
#                     if e == 'Example_1'])
    return [ os.path.join("legacy", e) for e in legacy if e not in skip_examples ]

def get_list_of_new_examples():
    return ["credit_risk",
            "curve_building",
            "exposure",
            "initial_margin",
            "market_risk",
            "getting_started",
            "vre_python",
            "performance",
            "products",
            "xva_risk"
            ]

def get_list_vre_academy():
    return ["academy/fc003_reporting_currency",
            "academy/ta001_equity_option",
            "academy/ta002_ir_swap"
            ]

def print_on_console(line):
    print(line)
    sys.stdout.flush()


class VreExample(object):
    def __init__(self, dry=False):
        self.vre_exe = ""
        self._qle_core_exe = None
        self._vre_module = None
        self.headlinecounter = 0
        self.dry = dry
        self.ax = None
        self.plot_name = ""
        self.use_python = True
        self.vre_exe = ""
        self._vre_module = _import_installed_vre()
        print_on_console(
            "Using installed VRE wheel for notebook examples "
            + str(Path(getattr(self._vre_module, "__file__", "")).resolve())
        )

    def _locate_vre_exe(self):
        raise RuntimeError("Notebook examples are wheel-only; direct VRE executable discovery is disabled.")

    def _locate_qle_core_exe(self):
        if self._qle_core_exe and os.path.isfile(self._qle_core_exe):
            return self._qle_core_exe

        override = os.environ.get("VRE_QLE_CORE_EXE", "").strip()
        candidates = [override] if override else []

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
            VRE = self._vre_module or _import_installed_vre()
            params_cls = getattr(VRE, "Parameters", None)
            app_cls = getattr(VRE, "VREApp", None)
            if params_cls is None or app_cls is None:
                if hasattr(VRE, "vrea"):
                    params_cls = getattr(VRE.vrea, "Parameters", None)
                    app_cls = getattr(VRE.vrea, "VREApp", None)
            if params_cls is None or app_cls is None:
                raise RuntimeError("Installed VRE wheel does not expose Parameters/VREApp for notebook execution.")
            params = params_cls()
            params.fromFile(xml)
            app = app_cls(params, True)
            app.run()

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
        path = Path(xml_path)
        if path.suffix.lower() != ".xml":
            text = path.read_text(encoding="utf-8")
            patterns = (
                (r'(?m)^(\s*ExternalComputeDevice\s*=\s*").*(".*)$', r"\1" + device_str + r"\2"),
                (r'(?m)^(\s*xvaCgExternalComputeDevice\s*=\s*").*(".*)$', r"\1" + device_str + r"\2"),
                (r'(?m)^(\s*ExternalComputeDevice\s*:\s*).*$' , r"\1" + device_str),
                (r'(?m)^(\s*xvaCgExternalComputeDevice\s*:\s*).*$' , r"\1" + device_str),
                (r'("ExternalComputeDevice"\s*:\s*")[^"]*(")', r"\1" + device_str + r"\2"),
                (r'("xvaCgExternalComputeDevice"\s*:\s*")[^"]*(")', r"\1" + device_str + r"\2"),
            )
            changed_any = False
            for pattern, replacement in patterns:
                text, count = re.subn(pattern, replacement, text)
                changed_any = changed_any or count > 0
            if changed_any:
                path.write_text(text, encoding="utf-8")
            return

        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_path)
        root = tree.getroot()
        changed_any = False
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

    def _gpu_patch_targets(self, main_config, extra_configs=None):
        targets = [Path(main_config)]
        for extra in extra_configs or []:
            if extra:
                targets.append(Path(extra))

        main_path = Path(main_config)
        if main_path.suffix.lower() == ".toml" and main_path.is_file():
            bundle = tomllib.loads(main_path.read_text(encoding="utf-8"))
            input_path = bundle.get("setup", {}).get("inputPath")
            if isinstance(input_path, str) and input_path:
                bundle_root = (main_path.parent / input_path).resolve()
                if bundle_root.is_dir():
                    for candidate in bundle_root.rglob("*"):
                        if candidate.suffix.lower() not in {".toml", ".json", ".yaml", ".yml", ".xml"}:
                            continue
                        if not candidate.is_file():
                            continue
                        try:
                            text = candidate.read_text(encoding="utf-8")
                        except Exception:
                            continue
                        if "ExternalComputeDevice" in text or "xvaCgExternalComputeDevice" in text:
                            targets.append(candidate)

        unique_targets = []
        seen = set()
        for target in targets:
            resolved = target.resolve() if target.exists() else Path(os.path.abspath(str(target)))
            if resolved in seen:
                continue
            seen.add(resolved)
            unique_targets.append(target)
        return unique_targets

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

        backups = []
        try:
            for target in self._gpu_patch_targets(main_xml, extra_xmls):
                rel = str(target)
                if not os.path.isfile(rel):
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
