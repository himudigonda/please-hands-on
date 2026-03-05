#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCH_DIR="$ROOT/benchmark"
TMP_DIR="$(mktemp -d)"
LIVE_DIR="$BENCH_DIR/live"
trap 'rm -rf "$TMP_DIR"' EXIT

mkdir -p "$BENCH_DIR"
mkdir -p "$LIVE_DIR"

check_please_compatible() {
  local bin="$1"
  python3 - "$bin" <<'PY'
import re
import subprocess
import sys

bin_path = sys.argv[1]
try:
    out = subprocess.check_output([bin_path, "--version"], text=True).strip()
except Exception:
    sys.exit(1)

version_token = out.split()[-1]
m = re.search(r"(\d+)\.(\d+)\.(\d+)", version_token)
if not m:
    sys.exit(1)
major, minor, patch = map(int, m.groups())
sys.exit(0 if (major, minor, patch) >= (0, 3, 0) else 1)
PY
}

resolve_please_bin() {
  if [[ -n "${PLEASE_BIN:-}" ]] && check_please_compatible "$PLEASE_BIN"; then
    printf '%s\n' "$PLEASE_BIN"
    return
  fi

  if command -v please >/dev/null 2>&1; then
    local path_bin
    path_bin="$(command -v please)"
    if check_please_compatible "$path_bin"; then
      printf '%s\n' "$path_bin"
      return
    fi
  fi

  local dev_bin
  dev_bin="$HOME/Documents/Projects/Please/target/debug/please"
  if [[ -x "$dev_bin" ]] && check_please_compatible "$dev_bin"; then
    printf '%s\n' "$dev_bin"
    return
  fi

  echo "No compatible please binary found (need >= 0.3.0). Set PLEASE_BIN explicitly." >&2
  exit 1
}

write_section() {
  local log_file="$1"
  local title="$2"
  shift 2

  local start_ts
  start_ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  local start_epoch
  start_epoch="$(python3 - <<'PY'
import time
print(f"{time.time():.6f}")
PY
)"

  {
    echo "============================================================"
    echo "COMMAND: $title"
    echo "START_UTC: $start_ts"
    echo "PWD: $ROOT"
    echo "------------------------------------------------------------"
  } >>"$log_file"

  set +e
  "$@" >>"$log_file" 2>&1
  local exit_code=$?
  set -e

  local end_ts
  end_ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  local end_epoch
  end_epoch="$(python3 - <<'PY'
import time
print(f"{time.time():.6f}")
PY
)"
  local elapsed
  elapsed="$(python3 - "$start_epoch" "$end_epoch" <<'PY'
import sys
start = float(sys.argv[1])
end = float(sys.argv[2])
print(f"{end - start:.3f}")
PY
)"

  {
    echo "------------------------------------------------------------"
    echo "END_UTC: $end_ts"
    echo "EXIT_CODE: $exit_code"
    echo "ELAPSED_SEC: $elapsed"
    echo
  } >>"$log_file"

  echo "[$(date -u +"%H:%M:%S")] $title (exit=$exit_code, elapsed=${elapsed}s)"

  if [[ "$exit_code" -ne 0 ]]; then
    echo "Failed command: $title" >&2
    exit "$exit_code"
  fi
}

write_system_info() {
  {
    echo "generated_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo "uname=$(uname -a)"

    if command -v sw_vers >/dev/null 2>&1; then
      echo "sw_vers_product_name=$(sw_vers -productName)"
      echo "sw_vers_product_version=$(sw_vers -productVersion)"
      echo "sw_vers_build_version=$(sw_vers -buildVersion)"
    fi

    if command -v sysctl >/dev/null 2>&1; then
      echo "cpu_brand=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || true)"
      echo "cpu_cores=$(sysctl -n hw.ncpu 2>/dev/null || true)"
      echo "mem_bytes=$(sysctl -n hw.memsize 2>/dev/null || true)"
    fi

    if command -v lscpu >/dev/null 2>&1; then
      echo "lscpu=$(lscpu | tr '\n' ';')"
    fi

    if command -v free >/dev/null 2>&1; then
      echo "free=$(free -h | tr '\n' ';')"
    fi
  } >"$BENCH_DIR/system_info.txt"
}

write_tool_versions() {
  {
    echo "generated_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo "git=$({ git --version 2>/dev/null || true; } | head -n 1)"
    echo "make=$({ make --version 2>/dev/null || true; } | head -n 1)"
    echo "just=$({ just --version 2>/dev/null || true; } | head -n 1)"
    echo "please=$({ "$PLEASE_BIN" --version 2>/dev/null || true; } | head -n 1)"
    echo "python3=$({ python3 --version 2>/dev/null || true; } | head -n 1)"
    echo "node=$({ node --version 2>/dev/null || true; } | head -n 1)"
    echo "npm=$({ npm --version 2>/dev/null || true; } | head -n 1)"
    echo "docker=$({ docker --version 2>/dev/null || true; } | head -n 1)"
  } >"$BENCH_DIR/tool_versions.txt"
}

write_artifact_manifest() {
  python3 - "$BENCH_DIR" <<'PY' >"$BENCH_DIR/artifact_manifest.txt"
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

bench = Path(sys.argv[1])
files = sorted(
    p for p in bench.glob("*")
    if p.is_file() and p.name != "artifact_manifest.txt" and p.suffix in {".txt", ".csv"}
)

print("generated_utc=" + datetime.now(timezone.utc).isoformat(timespec="seconds"))
print("file\tsize_bytes\tsha256")
for path in files:
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"{path.name}\t{path.stat().st_size}\t{h}")
PY
}

run_for_tool() {
  local tool="$1"
  local log_file="$2"
  : >"$log_file"
  echo "[$(date -u +"%H:%M:%S")] starting tool=$tool, log=$log_file"

  case "$tool" in
    make)
      write_section "$log_file" "make clean" make clean
      write_section "$log_file" "make setup" make setup
      write_section "$log_file" "make db_reset" make db_reset
      write_section "$log_file" "make backend_test" make backend_test
      write_section "$log_file" "make frontend_build" make frontend_build
      write_section "$log_file" "make ci" make ci
      write_section "$log_file" "make bench" make bench
      ;;
    just)
      write_section "$log_file" "just clean" just clean
      write_section "$log_file" "just setup" just setup
      write_section "$log_file" "just db_reset" just db_reset
      write_section "$log_file" "just backend_test" just backend_test
      write_section "$log_file" "just frontend_build" just frontend_build
      write_section "$log_file" "just ci" just ci
      write_section "$log_file" "just bench" just bench
      ;;
    please)
      write_section "$log_file" "please run clean --explain" "$PLEASE_BIN" --workspace . run clean --explain
      write_section "$log_file" "please run setup --explain" "$PLEASE_BIN" --workspace . run setup --explain
      write_section "$log_file" "please run db_reset --explain" "$PLEASE_BIN" --workspace . run db_reset --explain
      write_section "$log_file" "please run backend_test --explain" "$PLEASE_BIN" --workspace . run backend_test --explain
      write_section "$log_file" "please run frontend_build --explain" "$PLEASE_BIN" --workspace . run frontend_build --explain
      write_section "$log_file" "please run ci --explain" "$PLEASE_BIN" --workspace . run ci --explain
      write_section "$log_file" "please run bench --explain" "$PLEASE_BIN" --workspace . run bench --explain
      ;;
    *)
      echo "Unknown tool: $tool" >&2
      exit 1
      ;;
  esac
}

cd "$ROOT"
PLEASE_BIN="$(resolve_please_bin)"
export PLEASE_BIN

echo "Using please binary: $PLEASE_BIN"

TOOLS="${TOOL_FILTER:-make just please}"
for tool in $TOOLS; do
  run_for_tool "$tool" "$LIVE_DIR/$tool.log"
done

for tool in make just please; do
  if [[ ! -f "$LIVE_DIR/$tool.log" ]]; then
    echo "Missing log file for tool '$tool' at $LIVE_DIR/$tool.log" >&2
    exit 1
  fi
done

cp "$LIVE_DIR/make.log" "$BENCH_DIR/make_ouptut.txt"
cp "$LIVE_DIR/make.log" "$BENCH_DIR/make_output.txt"
cp "$LIVE_DIR/just.log" "$BENCH_DIR/just_output.txt"
cp "$LIVE_DIR/please.log" "$BENCH_DIR/please_output.txt"

write_system_info
write_tool_versions
write_artifact_manifest

echo "Wrote outputs to $BENCH_DIR"
