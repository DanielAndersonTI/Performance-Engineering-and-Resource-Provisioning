"""Build the comparative figures and the summary table from collected data.

Everything here is derived from measurements that were actually recorded. If a
file is missing the corresponding figure is skipped and reported, never
fabricated.

    python scripts/plot_results.py

Inputs (written by the experiment scripts):
    results/measurements.csv  application metrics, one row per load level
    results/run_log.csv       UTC window of each level
    results/resources.csv     VM-side samples

Outputs:
    results/graphs/*.png      figures for the report
    results/summary.csv       one row per scenario and level, app + VM metrics

Why the run log matters: resources.csv holds a continuous stream of samples
across the whole scenario, so averaging it per scenario would blend every demand
level into one number and hide the effect being studied. The run log gives each
level a UTC window, and the samples are attributed through those windows
instead.
"""

import csv
import datetime
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


MEASUREMENTS = Path("results/measurements.csv")
RUN_LOG = Path("results/run_log.csv")
RESOURCES = Path("results/resources.csv")
GRAPH_DIR = Path("results/graphs")
SUMMARY = Path("results/summary.csv")

RAMP_DOWN_NOTE = (
    "Vazão calculada sobre o tempo total da execução, incluindo a conclusão "
    "das últimas requisições em voo."
)

SUMMARY_FIELDS = [
    "scenario",
    "level",
    "repeats",
    "successes",
    "attempts",
    "errors",
    "error_rate",
    "success_throughput_rps",
    "throughput_rps",
    "mean_ms",
    "p50_ms",
    "p95_ms",
    "p99_ms",
    "cpu_percent",
    "memory_used_mb",
    "swap_used_mb",
    "vm_samples",
]


def read_csv(path):
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_utc(text):
    if not text:
        return None
    try:
        return datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def mean_of(rows, field):
    values = []
    for row in rows:
        raw = row.get(field)
        if raw in (None, ""):
            continue
        try:
            values.append(float(raw))
        except ValueError:
            continue
    return statistics.fmean(values) if values else None


def aggregate_measurements(rows):
    """Collapse repeats into one point per (scenario, level)."""
    grouped = defaultdict(list)
    for row in rows:
        level = row.get("level")
        if level in (None, ""):
            continue
        grouped[(row["scenario"], int(level))].append(row)

    aggregated = {}
    for key, group in grouped.items():
        aggregated[key] = {
            field: mean_of(group, field)
            for field in (
                "successes",
                "attempts",
                "errors",
                "error_rate",
                "success_throughput_rps",
                "throughput_rps",
                "mean_ms",
                "p50_ms",
                "p95_ms",
                "p99_ms",
            )
        }
        aggregated[key]["repeats"] = len(group)
    return aggregated


def resources_by_level(run_log_rows, resource_rows):
    """Attribute VM samples to a level through that level's UTC window."""
    by_scenario = defaultdict(list)
    for row in resource_rows:
        by_scenario[row.get("scenario", "")].append(row)

    attributed = {}
    for entry in run_log_rows:
        if entry.get("status") != "ok":
            continue
        start = parse_utc(entry.get("start_utc"))
        end = parse_utc(entry.get("end_utc"))
        if start is None or end is None:
            continue

        inside = []
        for row in by_scenario.get(entry["scenario"], []):
            stamp = parse_utc(row.get("date_utc"))
            if stamp is not None and start <= stamp <= end:
                inside.append(row)

        attributed[(entry["scenario"], int(entry["level"]))] = {
            "vm_samples": len(inside),
            "cpu_percent": mean_of(inside, "cpu_percent"),
            "memory_used_mb": mean_of(inside, "memory_used_mb"),
            "swap_used_mb": mean_of(inside, "swap_used_mb"),
        }
    return attributed


def levels_of(series):
    return sorted({level for _, level in series})


def plot_metric(series, destination, title, ylabel, footnote=None):
    """One line per scenario, demand on the x axis.

    `series` maps (scenario, level) to a value or None.
    """
    by_scenario = defaultdict(dict)
    for (scenario, level), value in series.items():
        by_scenario[scenario][level] = value

    figure, axes = plt.subplots(figsize=(9, 5.5))
    for scenario in sorted(by_scenario):
        points = sorted(by_scenario[scenario].items())
        xs = [level for level, value in points if value is not None]
        ys = [value for level, value in points if value is not None]
        if xs:
            axes.plot(xs, ys, marker="o", label=scenario)

    ticks = levels_of(series)
    if ticks:
        axes.set_xticks(ticks)

    axes.set_xlabel("Demanda (clientes simultâneos)")
    axes.set_ylabel(ylabel)
    axes.set_title(title)
    axes.grid(alpha=0.3)
    if by_scenario:
        axes.legend(title="Cenário")

    if footnote:
        figure.text(0.01, 0.01, footnote, fontsize=7, color="#555555")

    figure.tight_layout(rect=(0, 0.04 if footnote else 0, 1, 1))
    figure.savefig(destination, dpi=150)
    plt.close(figure)
    print(f"  wrote {destination}")


def plot_latency_panels(series_by_percentile, destination):
    """p50, p95 and p99 side by side, so degradation shape is visible."""
    figure, panels = plt.subplots(1, 3, figsize=(15, 5), sharex=True)
    for panel, (label, series) in zip(panels, series_by_percentile.items()):
        by_scenario = defaultdict(dict)
        for (scenario, level), value in series.items():
            by_scenario[scenario][level] = value
        for scenario in sorted(by_scenario):
            points = sorted(by_scenario[scenario].items())
            xs = [level for level, value in points if value is not None]
            ys = [value for level, value in points if value is not None]
            if xs:
                panel.plot(xs, ys, marker="o", label=scenario)
        ticks = levels_of(series)
        if ticks:
            panel.set_xticks(ticks)
        panel.set_title(label)
        panel.set_xlabel("Demanda (clientes simultâneos)")
        panel.grid(alpha=0.3)
    panels[0].set_ylabel("Latência (ms)")
    panels[-1].legend(title="Cenário")

    figure.suptitle("Latência por demanda e provisionamento")
    figure.tight_layout()
    figure.savefig(destination, dpi=150)
    plt.close(figure)
    print(f"  wrote {destination}")


def write_summary(measurements, resources):
    with SUMMARY.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        for key in sorted(measurements):
            scenario, level = key
            app = measurements[key]
            vm = resources.get(key, {})
            row = {"scenario": scenario, "level": level}
            for field in SUMMARY_FIELDS:
                if field in row:
                    continue
                if field in app:
                    value = app[field]
                else:
                    value = vm.get(field)
                row[field] = "" if value is None else round(value, 4) if isinstance(value, float) else value
            writer.writerow(row)
    print(f"  wrote {SUMMARY}")


def main():
    if not MEASUREMENTS.exists():
        raise SystemExit(
            f"{MEASUREMENTS} not found. Run the load experiments first "
            "(scripts/run_scenario.py or scripts/load_test.py)."
        )

    measurements = aggregate_measurements(read_csv(MEASUREMENTS))
    if not measurements:
        raise SystemExit(f"{MEASUREMENTS} has no usable rows.")

    resource_rows = read_csv(RESOURCES) if RESOURCES.exists() else []
    run_log_rows = read_csv(RUN_LOG) if RUN_LOG.exists() else []

    if resource_rows and not run_log_rows:
        print(
            "Warning: results/resources.csv exists but results/run_log.csv does "
            "not, so VM samples cannot be attributed to a demand level. The "
            "resource figures will be skipped. Use scripts/run_scenario.py to "
            "record the run log.",
            file=sys.stderr,
        )
        resource_rows = []

    resources = resources_by_level(run_log_rows, resource_rows) if resource_rows else {}

    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    scenarios = sorted({scenario for scenario, _ in measurements})
    print(f"Scenarios: {', '.join(scenarios)}")
    print(f"Levels: {', '.join(str(level) for level in levels_of(measurements))}")

    plot_latency_panels(
        {
            "p50": {(s, l): v["p50_ms"] for (s, l), v in measurements.items()},
            "p95": {(s, l): v["p95_ms"] for (s, l), v in measurements.items()},
            "p99": {(s, l): v["p99_ms"] for (s, l), v in measurements.items()},
        },
        GRAPH_DIR / "latencia_vs_demanda.png",
    )

    plot_metric(
        {(s, l): v["success_throughput_rps"] for (s, l), v in measurements.items()},
        GRAPH_DIR / "vazao_vs_demanda.png",
        "Vazão por demanda e provisionamento",
        "Requisições bem-sucedidas por segundo",
        footnote=RAMP_DOWN_NOTE,
    )

    plot_metric(
        {(s, l): v["error_rate"] for (s, l), v in measurements.items()},
        GRAPH_DIR / "erros_vs_demanda.png",
        "Taxa de falha por demanda e provisionamento",
        "Falhas / requisições",
        footnote="Inclui HTTP 503 devolvido quando todos os postos de trabalho estão ocupados.",
    )

    if resources:
        plot_metric(
            {(s, l): v["cpu_percent"] for (s, l), v in resources.items()},
            GRAPH_DIR / "cpu_vs_demanda.png",
            "Utilização de CPU da VM por demanda e provisionamento",
            "CPU (%)",
            footnote="Média das amostras do monitor dentro da janela de cada nível.",
        )
        plot_metric(
            {(s, l): v["memory_used_mb"] for (s, l), v in resources.items()},
            GRAPH_DIR / "memoria_vs_demanda.png",
            "Memória utilizada na VM por demanda e provisionamento",
            "Memória usada (MiB)",
            footnote="Média das amostras do monitor dentro da janela de cada nível.",
        )
        used_swap = any(v.get("swap_used_mb") for v in resources.values())
        if used_swap:
            plot_metric(
                {(s, l): v["swap_used_mb"] for (s, l), v in resources.items()},
                GRAPH_DIR / "swap_vs_demanda.png",
                "Uso de swap na VM por demanda e provisionamento",
                "Swap usada (MiB)",
                footnote="Uso de swap indica que a RAM provisionada ficou abaixo da demanda.",
            )
    else:
        print("No VM resource samples attributed; resource figures skipped.")

    write_summary(measurements, resources)
    print(f"\nFigures are in {GRAPH_DIR}")


if __name__ == "__main__":
    main()
