# TaskPulse Benchmark Lab

TaskPulse is a fullstack sample project used to benchmark `make`, `just`, and `broski`.

This lab now supports direct Broski comparison:
- baseline: `v0.5.1`
- candidate: current `v0.6` branch build

See [instructions.md](instructions.md) for full step-by-step setup and runbook.

Quick benchmark command:

```bash
cd /Users/himudigonda/Desktop/test
BROSKI_BASELINE_BIN=benchmark/bin/broski-v051 \
BROSKI_CANDIDATE_BIN=benchmark/bin/broski-v060 \
COMPARE_MODE=both \
python3 scripts/benchmark.py
```

Outputs:
- `benchmark/benchmark.csv`
- `benchmark/benchmark.txt`
- `benchmark/comparison.md`
