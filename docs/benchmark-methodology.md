# Benchmark Methodology

TaskPulse compares `make`, `just`, and `broski` on equivalent workflows.

## Scenarios

The benchmark script measures:

1. `cold_ci`
2. `warm_ci`
3. `touch_no_content_backend`
4. `content_change_backend`
5. `content_change_frontend`

## Iterations

- warmup runs: `1`
- measured runs: `7` per scenario/tool

## Fairness controls

- same machine, serial benchmark execution
- dependency caches retained
- per-scenario cleanup before measured loop

## Outputs

- `benchmark/benchmark.csv`
- `benchmark/benchmark.txt`

CSV columns:

- `timestamp`
- `tool`
- `scenario`
- `iteration`
- `duration_sec`
- `exit_code`

## Interpretation notes

- `broski` should dominate warm/no-content-change paths due to content-hash skipping.
- `make` can rerun on timestamp-only touches.
- `just` runs recipes unless explicit skip logic is encoded in the recipe itself.

## Re-run command

```bash
python3 scripts/benchmark.py
```
