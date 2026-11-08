# Benchmark Methodology

TaskPulse compares `make`, `just`, and `broski` with a stable-vs-candidate Broski split.

## Runner versions

- baseline Broski: `v0.5.1`
- candidate Broski: current local build (`v0.6.0-candidate` label in reports)

## Scenario groups

Core:

1. `cold_ci`
2. `warm_ci`
3. `touch_no_content_backend`
4. `content_change_backend`
5. `content_change_frontend`

Cache flags (Broski):

1. `cache_explain_hit`
2. `cache_bypass_no_cache`
3. `cache_bypass_force`
4. `dry_run_ci`

Mode mix (Broski):

1. `passthrough_path`
2. `interactive_smoke`

## Iterations

- warmup runs: default `1` (configurable via `WARMUP_RUNS`)
- measured runs: default `7` (configurable via `REPETITIONS`)

## Fairness controls

- serial execution on one machine
- per-scenario cleanup before measured loops
- baseline and candidate use dedicated `broskifile` variants:
  - `broskifile.v051` for `v0.5.1`
  - `broskifile.v060` for candidate

## Outputs

- `benchmark/benchmark.csv`
- `benchmark/benchmark.txt`
- `benchmark/comparison.md`

CSV columns:

- `timestamp`
- `runner_version`
- `tool`
- `scenario`
- `scenario_group`
- `iteration`
- `duration_sec`
- `exit_code`
- `ok`
- `error`

## Stability metrics

Each scenario reports:

- `mean`
- `median`
- `p95`
- `stddev`
- `failures/attempts`

## Candidate budget checks

- `cold_ci <= 6s`
- `content_change_frontend <= 3s`
- `warm_ci <= 0.05s`

## Re-run command

```bash
COMPARE_MODE=both python3 scripts/benchmark.py
```
