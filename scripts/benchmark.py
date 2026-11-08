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
BIN_DIR = BENCH_DIR / "bin"
CSV_PATH = BENCH_DIR / "benchmark.csv"
TXT_PATH = BENCH_DIR / "benchmark.txt"
CMP_PATH = BENCH_DIR / "comparison.md"

REPETITIONS = int(os.environ.get("REPETITIONS", "7"))
WARMUP_RUNS = int(os.environ.get("WARMUP_RUNS", "1"))
FILTER_TOOLS = os.environ.get("TOOL_FILTER", "").strip()
COMPARE_MODE = os.environ.get("COMPARE_MODE", "both").strip().lower()

RUNNER_SCENARIOS: dict[str, list[tuple[str, str]]] = {
    "core": [
        ("cold_ci", "core"),
        ("warm_ci", "core"),
        ("touch_no_content_backend", "core"),
        ("content_change_backend", "core"),
        ("content_change_frontend", "core"),
    ],
    "cache_flags": [
        ("cache_explain_hit", "cache_flags"),
        ("cache_bypass_no_cache", "cache_flags"),
        ("cache_bypass_force", "cache_flags"),
        ("dry_run_ci", "cache_flags"),
    ],
    "mode_mix": [
        ("passthrough_path", "mode_mix"),
        ("interactive_smoke", "mode_mix"),
    ],
}


class BenchmarkError(RuntimeError):
    pass


def run_command(
    command: list[str], label: str, timeout_s: int | None = None
) -> tuple[float, int]:
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        raise BenchmarkError(
            f"{label} timed out after {timeout_s}s\\ncommand: {' '.join(command)}"
        ) from exc

    duration = time.perf_counter() - started
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-12:])
        raise BenchmarkError(
            f"{label} failed (exit={proc.returncode})\\n"
            f"command: {' '.join(command)}\\n"
            f"stderr tail:\\n{tail}"
        )
    return duration, proc.returncode


def resolve_candidate_broski_binary() -> str:
    candidates: list[str] = []
    for env_key in ["BROSKI_CANDIDATE_BIN", "BROSKI_BIN"]:
        value = os.environ.get(env_key)
        if value:
            candidates.append(value)

    path_candidate = shutil.which("broski")
    if path_candidate:
        candidates.append(path_candidate)

    dev_candidate = (
        Path.home()
        / "Documents"
        / "Projects"
        / "BroSki"
        / "target"
        / "debug"
        / "broski"
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
        "No compatible candidate Broski binary found. "
        "Set BROSKI_CANDIDATE_BIN to an explicit path."
    )


def resolve_baseline_broski_binary() -> str:
    env_candidate = os.environ.get("BROSKI_BASELINE_BIN")
    if env_candidate:
        if not Path(env_candidate).exists():
            raise BenchmarkError(f"BROSKI_BASELINE_BIN does not exist: {env_candidate}")
        return env_candidate

    candidate = BIN_DIR / "broski-v051"
    if candidate.exists():
        return str(candidate)

    raise BenchmarkError(
        "No baseline Broski binary found. Build v0.5.1 and set BROSKI_BASELINE_BIN, "
        "or place it at benchmark/bin/broski-v051"
    )


def command_output(command: list[str]) -> str:
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        return "unavailable"
    return (proc.stdout.strip() or proc.stderr.strip()).splitlines()[0]


def touch(path: Path) -> None:
    now = time.time()
    os.utime(path, (now, now))


def mutate_file(path: Path, marker: str) -> str:
    original = path.read_text(encoding="utf-8")
    path.write_text(original + f"\n{marker}\n", encoding="utf-8")
    return original


def restore_file(path: Path, original: str) -> None:
    path.write_text(original, encoding="utf-8")


def clear_broski_state() -> None:
    for path in [
        ROOT / ".broski" / "cache",
        ROOT / ".broski" / "tx",
        ROOT / ".broski" / "stamps",
    ]:
        if path.exists():
            shutil.rmtree(path)


def build_tools(
    broski_bin: str, include_reference: bool
) -> dict[str, dict[str, list[str]]]:
    tools: dict[str, dict[str, list[str]]] = {
        "broski": {
            "setup": [broski_bin, "--workspace", ".", "run", "setup"],
            "clean": [broski_bin, "--workspace", ".", "run", "clean"],
            "ci": [broski_bin, "--workspace", ".", "run", "ci"],
            "ci_explain": [broski_bin, "--workspace", ".", "run", "ci", "--explain"],
            "ci_no_cache": [broski_bin, "--workspace", ".", "run", "ci", "--no-cache"],
            "ci_force": [broski_bin, "--workspace", ".", "run", "ci", "--force"],
            "ci_dry_run": [broski_bin, "--workspace", ".", "run", "ci", "--dry-run"],
            "passthrough": [
                broski_bin,
                "--workspace",
                ".",
                "run",
                "bench_passthrough",
                "--",
                "bench-payload",
            ],
            "interactive": [broski_bin, "--workspace", ".", "run", "interactive_smoke"],
        }
    }

    if include_reference:
        tools["make"] = {
            "setup": ["make", "setup"],
            "clean": ["make", "clean"],
            "ci": ["make", "ci"],
        }
        tools["just"] = {
            "setup": ["just", "setup"],
            "clean": ["just", "clean"],
            "ci": ["just", "ci"],
        }

    if not FILTER_TOOLS:
        return tools

    requested = {name.strip() for name in FILTER_TOOLS.split(",") if name.strip()}
    supported = set(tools)
    unknown = requested - supported
    if unknown:
        raise BenchmarkError(
            "Unknown TOOL_FILTER values: "
            + ", ".join(sorted(unknown))
            + f". Expected: {', '.join(sorted(supported))}"
        )

    return {name: tools[name] for name in tools if name in requested}


def reset_tool_state(
    tools: dict[str, dict[str, list[str]]], tool: str, scenario: str
) -> None:
    run_command(tools[tool]["clean"], f"{tool}:{scenario}:preclean")
    if tool == "broski":
        clear_broski_state()


def stats(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    p95_index = max(0, int(round(0.95 * (len(ordered) - 1))))
    return {
        "mean": statistics.mean(ordered),
        "median": statistics.median(ordered),
        "p95": ordered[p95_index],
        "stddev": statistics.pstdev(ordered),
    }


def run_scenario(
    tools: dict[str, dict[str, list[str]]],
    tool: str,
    scenario: str,
    iteration: int,
    warmup: bool,
) -> tuple[float, int]:
    backend_main = ROOT / "backend" / "app" / "main.py"
    frontend_app = ROOT / "frontend" / "src" / "App.tsx"

    if scenario == "cold_ci":
        if tool == "broski":
            clear_broski_state()
        run_command(tools[tool]["clean"], f"{tool}:{scenario}:clean")
        return run_command(tools[tool]["ci"], f"{tool}:{scenario}:ci")

    if scenario == "warm_ci":
        run_command(tools[tool]["ci"], f"{tool}:{scenario}:prime")
        return run_command(tools[tool]["ci"], f"{tool}:{scenario}:measure")

    if scenario == "touch_no_content_backend":
        run_command(tools[tool]["ci"], f"{tool}:{scenario}:prime")
        touch(backend_main)
        return run_command(tools[tool]["ci"], f"{tool}:{scenario}:measure")

    if scenario == "content_change_backend":
        run_command(tools[tool]["ci"], f"{tool}:{scenario}:prime")
        original = mutate_file(
            backend_main,
            f"# BENCHMARK_MUTATION_{tool}_{iteration}_{'WARMUP' if warmup else 'RUN'}",
        )
        try:
            return run_command(tools[tool]["ci"], f"{tool}:{scenario}:measure")
        finally:
            restore_file(backend_main, original)

    if scenario == "content_change_frontend":
        run_command(tools[tool]["ci"], f"{tool}:{scenario}:prime")
        original = mutate_file(
            frontend_app,
            f"// BENCHMARK_MUTATION_{tool}_{iteration}_{'WARMUP' if warmup else 'RUN'}",
        )
        try:
            return run_command(tools[tool]["ci"], f"{tool}:{scenario}:measure")
        finally:
            restore_file(frontend_app, original)

    if tool != "broski":
        raise BenchmarkError(
            f"scenario '{scenario}' is Broski-only and cannot run with {tool}"
        )

    if scenario == "cache_explain_hit":
        run_command(tools[tool]["ci"], f"{tool}:{scenario}:prime")
        return run_command(tools[tool]["ci_explain"], f"{tool}:{scenario}:measure")

    if scenario == "cache_bypass_no_cache":
        run_command(tools[tool]["ci"], f"{tool}:{scenario}:prime")
        return run_command(tools[tool]["ci_no_cache"], f"{tool}:{scenario}:measure")

    if scenario == "cache_bypass_force":
        run_command(tools[tool]["ci"], f"{tool}:{scenario}:prime")
        return run_command(tools[tool]["ci_force"], f"{tool}:{scenario}:measure")

    if scenario == "dry_run_ci":
        run_command(tools[tool]["ci"], f"{tool}:{scenario}:prime")
        return run_command(tools[tool]["ci_dry_run"], f"{tool}:{scenario}:measure")

    if scenario == "passthrough_path":
        run_command(tools[tool]["clean"], f"{tool}:{scenario}:clean")
        return run_command(tools[tool]["passthrough"], f"{tool}:{scenario}:measure")

    if scenario == "interactive_smoke":
        return run_command(
            tools[tool]["interactive"], f"{tool}:{scenario}:measure", timeout_s=20
        )

    raise BenchmarkError(f"unknown scenario: {scenario}")


def write_csv(rows: list[dict[str, str]]) -> None:
    with CSV_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "timestamp",
                "runner_version",
                "tool",
                "scenario",
                "scenario_group",
                "iteration",
                "duration_sec",
                "exit_code",
                "ok",
                "error",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def aggregate(
    rows: list[dict[str, str]],
) -> dict[tuple[str, str, str], dict[str, float | int]]:
    durations: dict[tuple[str, str, str], list[float]] = {}
    failures: dict[tuple[str, str, str], int] = {}
    attempts: dict[tuple[str, str, str], int] = {}

    for row in rows:
        key = (row["runner_version"], row["tool"], row["scenario"])
        attempts[key] = attempts.get(key, 0) + 1
        if row["ok"] == "1":
            durations.setdefault(key, []).append(float(row["duration_sec"]))
        else:
            failures[key] = failures.get(key, 0) + 1

    out: dict[tuple[str, str, str], dict[str, float | int]] = {}
    for key, values in durations.items():
        values_stats = stats(values)
        out[key] = {
            "mean": values_stats["mean"],
            "median": values_stats["median"],
            "p95": values_stats["p95"],
            "stddev": values_stats["stddev"],
            "failures": failures.get(key, 0),
            "attempts": attempts.get(key, 0),
        }

    for key, attempt_count in attempts.items():
        if key not in out:
            out[key] = {
                "mean": float("inf"),
                "median": float("inf"),
                "p95": float("inf"),
                "stddev": float("inf"),
                "failures": failures.get(key, 0),
                "attempts": attempt_count,
            }

    return out


def write_summary(
    rows: list[dict[str, str]], baseline_bin: str, candidate_bin: str
) -> None:
    agg = aggregate(rows)

    lines: list[str] = []
    lines.append("TaskPulse Benchmark Report")
    lines.append(f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("System")
    lines.append(f"- platform: {platform.platform()}")
    lines.append(f"- python: {platform.python_version()}")
    lines.append(f"- make: {command_output(['make', '--version'])}")
    lines.append(f"- just: {command_output(['just', '--version'])}")
    lines.append(f"- broski_baseline: {command_output([baseline_bin, '--version'])}")
    lines.append(f"- broski_candidate: {command_output([candidate_bin, '--version'])}")
    lines.append("")

    all_scenarios = [name for group in RUNNER_SCENARIOS.values() for name, _ in group]

    for scenario in all_scenarios:
        lines.append(f"## {scenario}")
        for runner in ["v0.5.1", "v0.6.0-candidate"]:
            key = (runner, "broski", scenario)
            stats_row = agg.get(key)
            if not stats_row:
                continue
            mean = stats_row["mean"]
            if mean == float("inf"):
                lines.append(
                    f"- {runner}/broski: all failed ({stats_row['failures']}/{stats_row['attempts']})"
                )
            else:
                lines.append(
                    f"- {runner}/broski: mean={mean:.4f} median={stats_row['median']:.4f} "
                    f"p95={stats_row['p95']:.4f} stddev={stats_row['stddev']:.4f} "
                    f"failures={stats_row['failures']}/{stats_row['attempts']}"
                )
        lines.append("")

    TXT_PATH.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def write_comparison(rows: list[dict[str, str]]) -> None:
    agg = aggregate(rows)
    scenarios = [name for group in RUNNER_SCENARIOS.values() for name, _ in group]

    lines: list[str] = []
    lines.append("# Broski Benchmark Comparison (v0.5.1 vs v0.6.0-candidate)")
    lines.append("")
    lines.append(f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Before/After (Broski)")
    lines.append("")
    lines.append(
        "| Scenario | Baseline mean (s) | Candidate mean (s) | Delta % | Baseline p95 (s) | Candidate p95 (s) | Baseline stddev | Candidate stddev | Failures (base/cand) |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |")

    for scenario in scenarios:
        base = agg.get(("v0.5.1", "broski", scenario))
        cand = agg.get(("v0.6.0-candidate", "broski", scenario))
        if not base or not cand:
            continue

        base_mean = base["mean"]
        cand_mean = cand["mean"]
        if base_mean == float("inf") or cand_mean == float("inf"):
            delta = "n/a"
            base_mean_s = "failed"
            cand_mean_s = "failed"
            base_p95 = "failed"
            cand_p95 = "failed"
            base_std = "failed"
            cand_std = "failed"
        else:
            delta_value = (
                ((cand_mean - base_mean) / base_mean) * 100 if base_mean > 0 else 0.0
            )
            delta = f"{delta_value:+.2f}%"
            base_mean_s = f"{base_mean:.4f}"
            cand_mean_s = f"{cand_mean:.4f}"
            base_p95 = f"{base['p95']:.4f}"
            cand_p95 = f"{cand['p95']:.4f}"
            base_std = f"{base['stddev']:.4f}"
            cand_std = f"{cand['stddev']:.4f}"

        lines.append(
            f"| {scenario} | {base_mean_s} | {cand_mean_s} | {delta} | "
            f"{base_p95} | {cand_p95} | {base_std} | {cand_std} | "
            f"{base['failures']}/{cand['failures']} |"
        )

    lines.append("")
    lines.append("## Candidate Budget Check")
    lines.append("")
    budgets = {
        "cold_ci": 6.0,
        "content_change_frontend": 3.0,
        "warm_ci": 0.05,
    }

    for scenario, budget in budgets.items():
        cand = agg.get(("v0.6.0-candidate", "broski", scenario))
        if not cand or cand["mean"] == float("inf"):
            lines.append(f"- FAIL: {scenario} -> no successful candidate samples")
            continue
        status = "PASS" if cand["mean"] <= budget else "FAIL"
        lines.append(
            f"- {status}: {scenario} mean={cand['mean']:.4f}s (budget <= {budget:.4f}s)"
        )

    lines.append("")
    lines.append("## Regression Warnings")
    lines.append("")
    regression_count = 0
    for scenario in scenarios:
        base = agg.get(("v0.5.1", "broski", scenario))
        cand = agg.get(("v0.6.0-candidate", "broski", scenario))
        if not base or not cand:
            continue
        if base["mean"] == float("inf") or cand["mean"] == float("inf"):
            continue
        if cand["mean"] > base["mean"] * 1.10:
            regression_count += 1
            lines.append(
                f"- WARN: {scenario} candidate mean is >10% slower ({cand['mean']:.4f}s vs {base['mean']:.4f}s)"
            )
    if regression_count == 0:
        lines.append("- None")

    CMP_PATH.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def with_broskifile(path: Path):
    class _Ctx:
        def __enter__(self):
            self.original = (ROOT / "broskifile").read_text(encoding="utf-8")
            shutil.copyfile(path, ROOT / "broskifile")
            return self

        def __exit__(self, exc_type, exc, tb):
            (ROOT / "broskifile").write_text(self.original, encoding="utf-8")
            return False

    return _Ctx()


def run_runner(
    runner_version: str,
    broski_bin: str,
    include_reference: bool,
    config_file: Path,
    rows: list[dict[str, str]],
) -> None:
    tools = build_tools(broski_bin, include_reference=include_reference)

    for tool in tools:
        if tool == "broski":
            continue
        if shutil.which(tool) is None:
            raise BenchmarkError(f"Missing required tool on PATH: {tool}")

    print(f"Runner={runner_version} Broski={broski_bin}", flush=True)
    with with_broskifile(config_file):
        print(f"Using config: {config_file.name}", flush=True)
        print("Running setup once per tool...", flush=True)
        for tool in tools:
            run_command(tools[tool]["setup"], f"{runner_version}:{tool}:setup")

        for group_name, scenario_defs in RUNNER_SCENARIOS.items():
            for scenario, scenario_group in scenario_defs:
                for tool in tools:
                    if tool != "broski" and group_name != "core":
                        continue

                    print(
                        f"Runner={runner_version} Scenario={scenario} Tool={tool}",
                        flush=True,
                    )
                    reset_tool_state(tools, tool, scenario)

                    for warmup in range(WARMUP_RUNS):
                        try:
                            run_scenario(tools, tool, scenario, warmup + 1, warmup=True)
                        except BenchmarkError:
                            pass

                    for iteration in range(1, REPETITIONS + 1):
                        timestamp = dt.datetime.now().isoformat(timespec="seconds")
                        try:
                            duration, exit_code = run_scenario(
                                tools, tool, scenario, iteration, warmup=False
                            )
                            rows.append(
                                {
                                    "timestamp": timestamp,
                                    "runner_version": runner_version,
                                    "tool": tool,
                                    "scenario": scenario,
                                    "scenario_group": scenario_group,
                                    "iteration": str(iteration),
                                    "duration_sec": f"{duration:.6f}",
                                    "exit_code": str(exit_code),
                                    "ok": "1",
                                    "error": "",
                                }
                            )
                        except BenchmarkError as exc:
                            rows.append(
                                {
                                    "timestamp": timestamp,
                                    "runner_version": runner_version,
                                    "tool": tool,
                                    "scenario": scenario,
                                    "scenario_group": scenario_group,
                                    "iteration": str(iteration),
                                    "duration_sec": "0.000000",
                                    "exit_code": "1",
                                    "ok": "0",
                                    "error": str(exc).replace("\n", " | "),
                                }
                            )


def main() -> int:
    BENCH_DIR.mkdir(parents=True, exist_ok=True)
    BIN_DIR.mkdir(parents=True, exist_ok=True)

    baseline_bin = resolve_baseline_broski_binary()
    candidate_bin = resolve_candidate_broski_binary()

    mode = COMPARE_MODE
    if mode not in {"baseline", "candidate", "both"}:
        raise BenchmarkError("COMPARE_MODE must be one of: baseline, candidate, both")

    rows: list[dict[str, str]] = []

    if mode in {"baseline", "both"}:
        run_runner(
            "v0.5.1",
            baseline_bin,
            include_reference=False,
            config_file=ROOT / "broskifile.v051",
            rows=rows,
        )

    if mode in {"candidate", "both"}:
        run_runner(
            "v0.6.0-candidate",
            candidate_bin,
            include_reference=True,
            config_file=ROOT / "broskifile.v060",
            rows=rows,
        )

    write_csv(rows)
    write_summary(rows, baseline_bin, candidate_bin)
    write_comparison(rows)

    print(f"Wrote {CSV_PATH}", flush=True)
    print(f"Wrote {TXT_PATH}", flush=True)
    print(f"Wrote {CMP_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BenchmarkError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
