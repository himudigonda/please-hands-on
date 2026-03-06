#!/usr/bin/env python3
from __future__ import annotations

import csv
import datetime as dt
import os
import platform
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH_DIR = ROOT / "benchmark"
CSV_PATH = BENCH_DIR / "benchmark.csv"
TXT_PATH = BENCH_DIR / "benchmark.txt"

REPETITIONS = 7
WARMUP_RUNS = 1

SCENARIOS = [
    "cold_ci",
    "warm_ci",
    "touch_no_content_backend",
    "content_change_backend",
    "content_change_frontend",
]


class BenchmarkError(RuntimeError):
    pass


def resolve_broski_binary() -> str:
    candidates: list[str] = []
    env_candidate = os.environ.get("BROSKI_BIN")
    if env_candidate:
        candidates.append(env_candidate)

    path_candidate = shutil.which("broski")
    if path_candidate:
        candidates.append(path_candidate)

    dev_candidate = (
        Path.home() / "Documents" / "Projects" / "Please" / "target" / "debug" / "broski"
    )
    if dev_candidate.exists():
        candidates.append(str(dev_candidate))

    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            proc = subprocess.run(
                [candidate, "--workspace", ".", "list"],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
        except OSError:
            continue
        if proc.returncode == 0:
            return candidate

    raise BenchmarkError(
        "No compatible broski binary found for this broskifile schema. "
        "Set BROSKI_BIN to an explicit compatible binary path."
    )


def build_tools(broski_bin: str) -> dict[str, dict[str, list[str]]]:
    return {
        "make": {
            "setup": ["make", "setup"],
            "clean": ["make", "clean"],
            "ci": ["make", "ci"],
        },
        "just": {
            "setup": ["just", "setup"],
            "clean": ["just", "clean"],
            "ci": ["just", "ci"],
        },
        "broski": {
            "setup": [broski_bin, "--workspace", ".", "run", "setup"],
            "clean": [broski_bin, "--workspace", ".", "run", "clean"],
            "ci": [broski_bin, "--workspace", ".", "run", "ci"],
        },
    }


def run_command(command: list[str], label: str) -> tuple[float, int]:
    started = time.perf_counter()
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    duration = time.perf_counter() - started
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-12:])
        raise BenchmarkError(
            f"{label} failed (exit={proc.returncode})\n"
            f"command: {' '.join(command)}\n"
            f"stderr tail:\n{tail}"
        )
    return duration, proc.returncode


def touch(path: Path) -> None:
    now = time.time()
    os.utime(path, (now, now))


def mutate_file(path: Path, marker: str) -> str:
    original = path.read_text(encoding="utf-8")
    path.write_text(original + f"\n{marker}\n", encoding="utf-8")
    return original


def restore_file(path: Path, original: str) -> None:
    path.write_text(original, encoding="utf-8")


def run_scenario(
    tools: dict[str, dict[str, list[str]]],
    tool: str,
    scenario: str,
    iteration: int,
    warmup: bool,
) -> tuple[float, int]:
    cmd_ci = tools[tool]["ci"]
    cmd_clean = tools[tool]["clean"]
    backend_main = ROOT / "backend" / "app" / "main.py"
    frontend_app = ROOT / "frontend" / "src" / "App.tsx"

    if scenario == "cold_ci":
        # Keep cold runs truly cold for Broski across warmup + measured iterations.
        if tool == "broski":
            clear_broski_state()
        run_command(cmd_clean, f"{tool}:{scenario}:clean")
        return run_command(cmd_ci, f"{tool}:{scenario}:ci")

    if scenario == "warm_ci":
        run_command(cmd_ci, f"{tool}:{scenario}:prime")
        return run_command(cmd_ci, f"{tool}:{scenario}:measure")

    if scenario == "touch_no_content_backend":
        run_command(cmd_ci, f"{tool}:{scenario}:prime")
        touch(backend_main)
        return run_command(cmd_ci, f"{tool}:{scenario}:measure")

    if scenario == "content_change_backend":
        run_command(cmd_ci, f"{tool}:{scenario}:prime")
        original = mutate_file(
            backend_main,
            f"# BENCHMARK_MUTATION_{tool}_{iteration}_{'WARMUP' if warmup else 'RUN'}",
        )
        try:
            return run_command(cmd_ci, f"{tool}:{scenario}:measure")
        finally:
            restore_file(backend_main, original)

    if scenario == "content_change_frontend":
        run_command(cmd_ci, f"{tool}:{scenario}:prime")
        original = mutate_file(
            frontend_app,
            f"// BENCHMARK_MUTATION_{tool}_{iteration}_{'WARMUP' if warmup else 'RUN'}",
        )
        try:
            return run_command(cmd_ci, f"{tool}:{scenario}:measure")
        finally:
            restore_file(frontend_app, original)

    raise ValueError(f"unknown scenario: {scenario}")


def reset_tool_state(tools: dict[str, dict[str, list[str]]], tool: str, scenario: str) -> None:
    run_command(tools[tool]["clean"], f"{tool}:{scenario}:preclean")
    if tool != "broski":
        return

    clear_broski_state()


def clear_broski_state() -> None:
    # Fully reset Broski cache metadata/artifacts without deleting the active
    # stage directory that the running process may rely on.
    for path in [
        ROOT / ".broski" / "cache",
        ROOT / ".broski" / "tx",
        ROOT / ".broski" / "stamps",
    ]:
        if path.exists():
            shutil.rmtree(path)


def stats(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    p95_index = max(0, int(round(0.95 * (len(ordered) - 1))))
    return {
        "mean": statistics.mean(ordered),
        "median": statistics.median(ordered),
        "p95": ordered[p95_index],
        "stddev": statistics.pstdev(ordered),
    }


def command_output(command: list[str]) -> str:
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        return "unavailable"
    return (proc.stdout.strip() or proc.stderr.strip()).splitlines()[0]


def write_summary(rows: list[dict[str, str]], tools: dict[str, dict[str, list[str]]]) -> None:
    durations: dict[tuple[str, str], list[float]] = {}
    for row in rows:
        if int(row["exit_code"]) != 0:
            continue
        key = (row["tool"], row["scenario"])
        durations.setdefault(key, []).append(float(row["duration_sec"]))

    lines: list[str] = []
    lines.append("TaskPulse Benchmark Report")
    lines.append(f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("System")
    lines.append(f"- platform: {platform.platform()}")
    lines.append(f"- python: {platform.python_version()}")
    lines.append(f"- make: {command_output(['make', '--version'])}")
    lines.append(f"- just: {command_output(['just', '--version'])}")
    lines.append(f"- broski: {command_output([tools['broski']['ci'][0], '--version'])}")
    lines.append("")

    lines.append("Scenario Statistics (seconds)")
    for scenario in SCENARIOS:
        lines.append("")
        lines.append(f"## {scenario}")
        scenario_table: list[tuple[str, dict[str, float]]] = []
        for tool in tools:
            key = (tool, scenario)
            values = durations.get(key, [])
            if not values:
                continue
            scenario_table.append((tool, stats(values)))

        scenario_table.sort(key=lambda item: item[1]["mean"])
        for tool, numbers in scenario_table:
            lines.append(
                f"- {tool}: mean={numbers['mean']:.4f} median={numbers['median']:.4f} "
                f"p95={numbers['p95']:.4f} stddev={numbers['stddev']:.4f}"
            )

        broski_stats = dict(scenario_table).get("broski") if scenario_table else None
        if broski_stats is not None:
            lines.append("- speedup ratios vs broski (mean):")
            for tool, numbers in scenario_table:
                ratio = (
                    numbers["mean"] / broski_stats["mean"]
                    if broski_stats["mean"] > 0
                    else float("inf")
                )
                lines.append(f"  - {tool}: {ratio:.2f}x")

    TXT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    BENCH_DIR.mkdir(parents=True, exist_ok=True)

    broski_bin = resolve_broski_binary()
    tools = build_tools(broski_bin)

    for tool in tools:
        if tool == "broski":
            continue
        if shutil.which(tool) is None:
            print(f"Missing required tool on PATH: {tool}", file=sys.stderr)
            return 1

    print(f"Using broski binary: {broski_bin}", flush=True)
    print("Running setup once per tool...", flush=True)
    for tool in tools:
        run_command(tools[tool]["setup"], f"{tool}:setup")

    rows: list[dict[str, str]] = []

    for scenario in SCENARIOS:
        for tool in tools:
            print(f"Scenario={scenario} Tool={tool}", flush=True)
            reset_tool_state(tools, tool, scenario)

            for warmup in range(WARMUP_RUNS):
                run_scenario(tools, tool, scenario, warmup + 1, warmup=True)

            for iteration in range(1, REPETITIONS + 1):
                duration, exit_code = run_scenario(
                    tools, tool, scenario, iteration, warmup=False
                )
                rows.append(
                    {
                        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
                        "tool": tool,
                        "scenario": scenario,
                        "iteration": str(iteration),
                        "duration_sec": f"{duration:.6f}",
                        "exit_code": str(exit_code),
                    }
                )

    with CSV_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "timestamp",
                "tool",
                "scenario",
                "iteration",
                "duration_sec",
                "exit_code",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    write_summary(rows, tools)
    print(f"Wrote {CSV_PATH}", flush=True)
    print(f"Wrote {TXT_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BenchmarkError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
