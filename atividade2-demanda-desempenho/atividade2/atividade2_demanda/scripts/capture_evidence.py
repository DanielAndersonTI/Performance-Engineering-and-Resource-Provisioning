"""Capture the provisioning evidence for one scenario, run from the HOST.

Each scenario in the study is a different VirtualBox configuration (vCPUs and
RAM). The measurement files record what the application and the guest did, but
nothing in them records what the guest was *given*. This script captures that
missing half, so every scenario carries its own record of the resources it ran
with, taken from VirtualBox itself rather than retyped by hand.

For one scenario it writes:

    <out>/<scenario>-config.txt     the full VirtualBox machine description
    <out>/<scenario>-console.png    a screenshot of the guest console

The text file is the precise record: it is the machine-readable truth about
vCPUs, memory and port forwarding, and it cannot drift from what actually ran.
The screenshot is the human-readable companion the assignment's roteiro asks
for. Both are captured from the running machine, never composed afterwards.

    python scripts/capture_evidence.py --scenario C1

Requires VBoxManage on the host. It reads the machine while it runs, so call it
after the guest is up and before or during the measurement.
"""

import argparse
import subprocess
import sys
from pathlib import Path


DEFAULT_VBOXMANAGE = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
DEFAULT_VM = "Po-2026.2"

# Properties worth having on their own, so the report does not depend on the
# reader parsing the full machine description to find the provisioning.
SUMMARY_KEYS = ("name", "cpus", "memory", "VMState", "ostype")


def run_vboxmanage(executable, *arguments):
    result = subprocess.run(
        [executable, *arguments],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"VBoxManage {' '.join(arguments)} failed:\n{result.stderr.strip()}"
        )
    return result.stdout


def summarize(configuration):
    """Pull the provisioning values out of the machine description."""
    wanted = {}
    for line in configuration.splitlines():
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key in SUMMARY_KEYS:
            wanted[key] = value.strip('"')
    return wanted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, help="e.g. C1")
    parser.add_argument("--vm", default=DEFAULT_VM, help="VirtualBox machine name")
    parser.add_argument("--vboxmanage", default=DEFAULT_VBOXMANAGE)
    parser.add_argument("--out", default="evidencias", help="output directory")
    parser.add_argument(
        "--note",
        default="",
        help="free text recorded in the configuration file, e.g. the demand levels used",
    )
    args = parser.parse_args()

    executable = Path(args.vboxmanage)
    if not executable.exists():
        raise SystemExit(
            f"VBoxManage not found at {executable}. Pass --vboxmanage with the "
            "correct path for this host."
        )

    destination = Path(args.out)
    destination.mkdir(parents=True, exist_ok=True)

    configuration = run_vboxmanage(executable, "showvminfo", args.vm, "--machinereadable")
    values = summarize(configuration)

    config_path = destination / f"{args.scenario}-config.txt"
    with config_path.open("w", encoding="utf-8") as handle:
        handle.write(f"Scenario: {args.scenario}\n")
        handle.write(f"Captured from: VirtualBox machine {args.vm!r}\n")
        if args.note:
            handle.write(f"Note: {args.note}\n")
        handle.write("\n")
        handle.write("Provisioning\n")
        handle.write("------------\n")
        for key in SUMMARY_KEYS:
            if key in values:
                handle.write(f"{key}: {values[key]}\n")
        handle.write("\n")
        handle.write("Full machine description (VBoxManage showvminfo --machinereadable)\n")
        handle.write("-" * 68 + "\n")
        handle.write(configuration)
    print(f"wrote {config_path}  (cpus={values.get('cpus')}, memory={values.get('memory')} MB)")

    screenshot_path = destination / f"{args.scenario}-console.png"
    run_vboxmanage(executable, "controlvm", args.vm, "screenshotpng", str(screenshot_path))
    print(f"wrote {screenshot_path}")

    if "cpus" not in values or "memory" not in values:
        print(
            "Warning: the machine description did not include cpus/memory. The "
            "machine may not exist under that name.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
