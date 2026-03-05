# TaskPulse Benchmark Lab

TaskPulse is a fullstack sample project designed to benchmark and compare `make`, `just`, and `please` on the exact same workflow.

See [instructions.md](instructions.md) for full setup, benchmark methodology, and troubleshooting.
Additional docs:
- [docs/setup-and-run.md](docs/setup-and-run.md)
- [docs/benchmark-methodology.md](docs/benchmark-methodology.md)

## Install Please (recommended)

Latest release (default):

```bash
curl -fsSL https://raw.githubusercontent.com/himudigonda/Please/main/install.sh | bash
```

Stable-only channel:

```bash
curl -fsSL https://raw.githubusercontent.com/himudigonda/Please/main/install.sh | PLEASE_CHANNEL=stable bash
```

Pinned RC:

```bash
curl -fsSL https://raw.githubusercontent.com/himudigonda/Please/main/install.sh | PLEASE_VERSION=v0.4.0-rc.1 bash
```

Quickstart:

```bash
git clone https://github.com/himudigonda/please-hands-on.git
cd please-hands-on
please --workspace . run setup
please --workspace . run ci --explain
please --workspace . run bench
```

Alternative runner parity:

```bash
make setup && make ci && make bench
just setup && just ci && just bench
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

This repository uses `pleasefile` schema `0.4`.

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
