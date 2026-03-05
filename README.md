# TaskPulse Benchmark Lab

TaskPulse is a fullstack sample project designed to benchmark and compare `make`, `just`, and `please` on the exact same workflow.

See [instructions.md](instructions.md) for full setup, benchmark methodology, and troubleshooting.

Quickstart:

```bash
cd ~/Desktop/test
make setup
make ci
python3 scripts/benchmark.py
```

If your installed `please` is older than the `pleasefile` schema, set:

```bash
export PLEASE_BIN=/absolute/path/to/please
export PLEASE="$PLEASE_BIN"
```

Then use:

```bash
$PLEASE --workspace . run ci --explain
```
