# TaskPulse Benchmark Lab

TaskPulse is a fullstack sample project designed to benchmark and compare `make`, `just`, and `please` on the exact same workflow.

See [instructions.md](instructions.md) for full setup, benchmark methodology, and troubleshooting.

Quickstart:

```bash
git clone https://github.com/himudigonda/please-hands-on.git
cd please-hands-on
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

## Committed Benchmark Artifacts

This repo commits reproducible benchmark and command-output artifacts under `benchmark/`:

- `benchmark.csv`
- `benchmark.txt`
- `make_ouptut.txt` (intentional typo kept for compatibility)
- `make_output.txt`
- `just_output.txt`
- `please_output.txt`
- `system_info.txt`
- `tool_versions.txt`
- `artifact_manifest.txt`

To regenerate all output artifacts in one command:

```bash
./scripts/capture_outputs.sh
```
