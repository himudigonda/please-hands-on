# TaskPulse Instructions

Related docs:
- `docs/setup-and-run.md`
- `docs/benchmark-methodology.md`

## 1. Prerequisites

Required tools:
- `python3` (3.11+; 3.13/3.12 preferred if multiple are installed)
- `node` + `npm` (Node 20+ recommended)
- `make`
- `just`
- `please`
- Optional for Docker mode: `docker`, `docker compose`

Install `please` quickly:

```bash
# latest release channel (default)
curl -fsSL https://raw.githubusercontent.com/himudigonda/Please/main/install.sh | bash

# stable-only channel
curl -fsSL https://raw.githubusercontent.com/himudigonda/Please/main/install.sh | PLEASE_CHANNEL=stable bash

# pinned release candidate
curl -fsSL https://raw.githubusercontent.com/himudigonda/Please/main/install.sh | PLEASE_VERSION=v0.4.0-rc.1 bash
```

Quick checks:

```bash
python3 --version
python3.13 --version  # optional if installed
node --version
npm --version
make --version
just --version
please --version
```

Python interpreter selection in this repo:
- `setup` auto-selects in this order: `python3.13`, `python3.12`, `python3.11`, `python3`.

Please binary selection:
- The benchmark harness auto-detects a compatible `please` binary for this `pleasefile` schema.
- This project uses `pleasefile` schema `0.4`, so use `please >= 0.4.0-rc.1`.
- If your PATH `please` is older, set:
  ```bash
  export PLEASE_BIN=/absolute/path/to/please
  export PLEASE="${PLEASE_BIN}"
  ```
  Then run commands with `$PLEASE` instead of `please`.

## 2. One-command Setup Per Runner

All three commands do the same setup:

```bash
cd please-hands-on

make setup
just setup
please --workspace . run setup
# or, if PATH please is older:
$PLEASE --workspace . run setup
```

Notes:
- Setup creates `backend/.venv` and installs Python dependencies.
- Setup installs frontend dependencies in `frontend/node_modules`.

## 3. Run the Project Locally (UI + API)

Backend:

```bash
make run_backend
# or: just run_backend
# or: please --workspace . run run_backend
```

Frontend (separate terminal):

```bash
make run_frontend
# or: just run_frontend
# or: please --workspace . run run_frontend
```

Open UI at: [http://127.0.0.1:5173](http://127.0.0.1:5173)

Backend API at: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

Smoke check while both are running:

```bash
python3 scripts/smoke.py
```

## 4. Optional Docker Mode

```bash
docker compose up --build
```

Then open:
- UI: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- API health: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

This mode is for demonstration only and is not timed in benchmarks.
If endpoints do not respond immediately, wait 10-30 seconds for first startup.

## 5. Benchmark Execution

Run benchmark harness:

```bash
python3 scripts/benchmark.py
```

Or via runner task:

```bash
make bench
just bench
please --workspace . run bench
# or:
$PLEASE --workspace . run bench
```

Artifacts produced:
- `benchmark/benchmark.csv`
- `benchmark/benchmark.txt`

## 6. Reproduce Captured Outputs

Generate full runner command outputs and benchmark artifacts:

```bash
./scripts/capture_outputs.sh
```

This command captures deterministic logs for:
- `make`: `clean setup db_reset backend_test frontend_build ci bench`
- `just`: `clean setup db_reset backend_test frontend_build ci bench`
- `please`: `clean setup db_reset backend_test frontend_build ci bench` (with `--explain`)

The script writes section headers with command, timestamp, exit code, and elapsed seconds.

## 7. Where to Find Logs and Reports

All committed artifacts are in `benchmark/`:
- `benchmark.csv`
- `benchmark.txt`
- `make_ouptut.txt` (intentional typo retained)
- `make_output.txt`
- `just_output.txt`
- `please_output.txt`
- `system_info.txt`
- `tool_versions.txt`
- `artifact_manifest.txt`

## 8. What Benchmark Scenarios Mean

Scenarios measured per tool (`make`, `just`, `please`):
- `cold_ci`: clean outputs and run full `ci`.
- `warm_ci`: run `ci` twice; second run measured.
- `touch_no_content_backend`: touch backend file without changing content.
- `content_change_backend`: mutate backend source and run `ci`.
- `content_change_frontend`: mutate frontend source and run `ci`.

Each scenario runs:
- 1 warmup iteration
- 7 measured iterations

Interpretation guidance:
- Expect `please` to be strongest on warm reruns and touch-without-content runs because it can skip unchanged tasks via content hashing.
- Cold runs and true content-change runs can be slower in this lab because Please stages execution and validates task contracts.
- Use `please --workspace . run ci --explain` to verify exactly why a task reran.

## 9. Realtime Demo Commands

Run each runner CI path:

```bash
make ci
just ci
please --workspace . run ci --explain
# or:
$PLEASE --workspace . run ci --explain
```

Touch-without-content behavior:

```bash
touch backend/app/main.py
make ci
just ci
please --workspace . run ci --explain
# or:
$PLEASE --workspace . run ci --explain
```

The `--explain` output should show whether Please reused cache or why it rebuilt.

## 10. Troubleshooting

### Port already in use
- Kill existing servers on `8000` or `5173`.
- macOS helper:
  ```bash
  lsof -i :8000
  lsof -i :5173
  ```

### Missing tool on PATH
- Install missing tool and re-run setup.
- Verify with `command -v <tool>`.
- If `please` on PATH is older than 0.4:
  ```bash
  export PLEASE_BIN=/absolute/path/to/please
  export PLEASE="${PLEASE_BIN}"
  ```

### Stale cache/artifacts
- Clean project artifacts:
  ```bash
  make clean
  # or just clean
  # or please --workspace . run clean
  ```

### SQLite permission/reset issues
- Ensure `backend/data/` is writable.
- Reset DB:
  ```bash
  make db_reset
  # or just db_reset
  # or please --workspace . run db_reset
  ```

## 11. Task Surface (Parity)

All three runners expose the same semantic tasks:
- `setup`
- `db_reset`
- `backend_test`
- `frontend_build`
- `ci`
- `run_backend`
- `run_frontend`
- `clean`
- `bench`
