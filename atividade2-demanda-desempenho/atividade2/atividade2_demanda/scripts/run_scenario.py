"""Drive one provisioning scenario end to end, from the HOST.

Runs every demand level of one scenario back to back, appends the results to
results/measurements.csv, and records the UTC window of each level in
results/run_log.csv. Those windows are what let the analysis attribute the
VM-side samples in results/resources.csv to the right demand level.

Workflow for one scenario:

  1. In VirtualBox, set the vCPU and RAM for this scenario, then start the VM.
  2. In the guest, start the application, then start the monitor for roughly the
     number of seconds this script prints.
  3. On the host, run this script.

Example:
    python scripts/run_scenario.py --scenario C1 --size 60000 \
        --levels 1,2,4,8 --duration 30 --warmup 5

Reconfigure the VM once per scenario, not once per level: this is why the whole
level sweep lives in a single command.

A warm-up run precedes each level and is not recorded. It fills the page cache
and lets the JIT-free Python process reach steady state, so the first level is
not penalised for being first.
"""

import argparse
import csv
import datetime
import json
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import urlopen

import load_test


RUN_LOG_FIELDNAMES = [
    "scenario",
    "level",
    "run_id",
    "start_utc",
    "end_utc",
    "concurrency",
    "duration_s",
    "warmup_s",
    "work_url",
    "profile",
    "status",
]


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def parse_levels(text):
    levels = []
    for piece in text.split(","):
        piece = piece.strip()
        if not piece:
            continue
        try:
            level = int(piece)
        except ValueError:
            raise SystemExit(f"--levels must be a comma-separated list of integers, got {piece!r}")
        if level < 1:
            raise SystemExit(f"--levels entries must be at least 1, got {level}")
        levels.append(level)
    if not levels:
        raise SystemExit("--levels must contain at least one level")
    return sorted(set(levels))


def health_url_for(work_url):
    parts = urlsplit(work_url)
    return urlunsplit((parts.scheme, parts.netloc, "/health", "", ""))


def check_health(work_url, expect_profile, timeout=10.0):
    """Confirm the target is reachable and, when asked, that it is the right app."""
    url = health_url_for(work_url)
    try:
        with urlopen(url, timeout=timeout) as response:
            body = json.load(response)
    except (OSError, URLError, HTTPError) as error:
        raise SystemExit(
            f"Could not reach {url}: {error}\n"
            "Check that the application is running in the guest and that the VM's "
            "network is set up so the host can reach the forwarded port."
        )

    profile = body.get("profile", "")
    if expect_profile and profile != expect_profile:
        raise SystemExit(
            f"{url} reports profile {profile!r} but --expect-profile is "
            f"{expect_profile!r}. You are probably load-testing the wrong "
            "application."
        )
    return profile


def append_run_log(path, row):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    has_content = target.exists() and target.stat().st_size > 0

    if has_content:
        with target.open(encoding="utf-8", newline="") as handle:
            header = handle.readline().strip().split(",")
        if header != RUN_LOG_FIELDNAMES:
            raise SystemExit(
                f"{target} was written with a different set of columns; "
                "move or delete it before recording new runs."
            )

    with target.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RUN_LOG_FIELDNAMES)
        if not has_content:
            writer.writeheader()
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, help="e.g. C1")
    parser.add_argument(
        "--work-url",
        default="http://127.0.0.1:8080/work",
        help="base work URL in the guest; --size is appended as a query",
    )
    parser.add_argument(
        "--size",
        default=None,
        help="workload size passed to the application; omit to use its default",
    )
    parser.add_argument("--levels", default="1,2,4,8", help="concurrencies to sweep")
    parser.add_argument("--duration", type=float, default=30.0, help="seconds per level")
    parser.add_argument("--warmup", type=float, default=5.0, help="seconds before each level")
    parser.add_argument("--timeout", type=float, default=60.0, help="per-request timeout")
    parser.add_argument(
        "--start-delay",
        type=float,
        default=15.0,
        help="seconds to wait so you can start the guest monitor first",
    )
    parser.add_argument(
        "--expect-profile",
        default="",
        help="abort unless /health reports this profile, e.g. cpu",
    )
    parser.add_argument("--out-measurements", default="results/measurements.csv")
    parser.add_argument("--out-runlog", default="results/run_log.csv")
    args = parser.parse_args()

    levels = parse_levels(args.levels)
    work_url = args.work_url if args.size is None else f"{args.work_url}?size={args.size}"

    profile = check_health(work_url, args.expect_profile)

    measuring_seconds = len(levels) * (args.warmup + args.duration)
    monitor_seconds = int(args.start_delay + measuring_seconds + 30)

    print("=" * 68)
    print(f"Scenario        : {args.scenario}")
    print(f"Application     : {profile or 'unknown profile'}")
    print(f"Work URL        : {work_url}")
    print(f"Demand levels   : {', '.join(str(level) for level in levels)}")
    print(f"Per level       : {args.warmup:g}s warm-up + {args.duration:g}s measured")
    print(f"Measuring total : {measuring_seconds / 60:.1f} min")
    print("=" * 68)
    print("\nIn the guest, while this script waits, run:\n")
    print(f"    python scripts/monitor.py --scenario {args.scenario} --seconds {monitor_seconds}\n")
    print(f"Starting the sweep in {args.start_delay:g}s... (Ctrl+C to abort)\n")

    run_log_rows = []
    measured_rows = []
    try:
        time.sleep(args.start_delay)

        for level in levels:
            run_id = f"{args.scenario}-L{level}"

            if args.warmup > 0:
                print(f"[{run_id}] warm-up {args.warmup:g}s at concurrency {level}...", flush=True)
                load_test.measure(
                    work_url, level, args.timeout, duration=args.warmup
                )

            print(f"[{run_id}] measuring {args.duration:g}s...", flush=True)
            start = utc_now()
            samples, elapsed, mode = load_test.measure(
                work_url, level, args.timeout, duration=args.duration
            )
            end = utc_now()

            row = load_test.build_row(
                run_id=run_id,
                scenario=args.scenario,
                level=level,
                url=work_url,
                concurrency=level,
                mode=mode,
                requests_target=None,
                duration_target=args.duration,
                samples=samples,
                elapsed=elapsed,
            )
            load_test.write_row(args.out_measurements, row)
            measured_rows.append(row)

            run_log_rows.append(
                {
                    "scenario": args.scenario,
                    "level": level,
                    "run_id": run_id,
                    "start_utc": start.isoformat(timespec="seconds"),
                    "end_utc": end.isoformat(timespec="seconds"),
                    "concurrency": level,
                    "duration_s": args.duration,
                    "warmup_s": args.warmup,
                    "work_url": work_url,
                    "profile": profile,
                    "status": "ok",
                }
            )

            print(
                f"[{run_id}] {row['successes']}/{row['attempts']} ok  "
                f"{row['success_throughput_rps']} rps  "
                f"p50={row['p50_ms']}ms  p95={row['p95_ms']}ms  "
                f"errors={row['errors_by_kind'] or 'none'}\n",
                flush=True,
            )
    except KeyboardInterrupt:
        print("\nAborted; the levels already finished are kept.", file=sys.stderr)
    finally:
        for row in run_log_rows:
            append_run_log(args.out_runlog, row)

    if run_log_rows:
        print(f"Level summary for {args.scenario}")
        print(f"  {'level':>5} {'ok/attempts':>13} {'rps':>9} {'p50 ms':>9} {'p95 ms':>9}")
        for row in measured_rows:
            print(
                f"  {row['level']:>5} "
                f"{str(row['successes']) + '/' + str(row['attempts']):>13} "
                f"{row['success_throughput_rps']:>9} "
                f"{row['p50_ms']:>9} "
                f"{row['p95_ms']:>9}"
            )
        print(
            f"\nWrote {len(run_log_rows)} level windows to {args.out_runlog} "
            f"and the measurements to {args.out_measurements}."
        )
    else:
        print("No levels were recorded.")


if __name__ == "__main__":
    main()
