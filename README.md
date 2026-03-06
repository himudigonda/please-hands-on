# TaskPulse Benchmark Lab

TaskPulse is a fullstack sample project designed to benchmark and compare `make`, `just`, and `broski` on the exact same workflow.

See [instructions.md](instructions.md) for full setup, benchmark methodology, and troubleshooting.
Additional docs:
- [docs/setup-and-run.md](docs/setup-and-run.md)
- [docs/benchmark-methodology.md](docs/benchmark-methodology.md)

## Install Broski (recommended)

Latest release (default):

```bash
curl -fsSL https://raw.githubusercontent.com/himudigonda/Broski/main/install.sh | bash
```

Stable-only channel:

```bash
curl -fsSL https://raw.githubusercontent.com/himudigonda/Broski/main/install.sh | BROSKI_CHANNEL=stable bash
```

Pinned RC:

```bash
curl -fsSL https://raw.githubusercontent.com/himudigonda/Broski/main/install.sh | BROSKI_VERSION=v0.5.0 bash
```

Quickstart:

```bash
git clone https://github.com/himudigonda/broski-hands-on.git
cd broski-hands-on
broski --workspace . run setup
broski --workspace . run ci --explain
broski --workspace . run bench
```

Alternative runner parity:

```bash
make setup && make ci && make bench
just setup && just ci && just bench
```

If your installed `broski` is older than the `broskifile` schema, set:

```bash
export BROSKI_BIN=/absolute/path/to/broski
export PLEASE="$BROSKI_BIN"
```

Then use:

```bash
$PLEASE --workspace . run ci --explain
```

This repository uses `broskifile` schema `0.5`.

## Committed Benchmark Artifacts

This repo commits reproducible benchmark and command-output artifacts under `benchmark/`:

- `benchmark.csv`
- `benchmark.txt`
- `make_ouptut.txt` (intentional typo kept for compatibility)
- `make_output.txt`
- `just_output.txt`
- `system_info.txt`
- `tool_versions.txt`
- `artifact_manifest.txt`

To regenerate all output artifacts in one command:

```bash
./scripts/capture_outputs.sh
```
