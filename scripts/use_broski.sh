#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="$ROOT/benchmark/bin"
LINK_PATH="$BIN_DIR/broski-current"
TARGET="${1:-}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 baseline|candidate|show"
  exit 1
fi

mkdir -p "$BIN_DIR"

case "$TARGET" in
  baseline)
    SRC="$BIN_DIR/broski-v051"
    ;;
  candidate)
    SRC="$BIN_DIR/broski-v060"
    ;;
  show)
    if [[ -L "$LINK_PATH" ]]; then
      echo "current -> $(readlink "$LINK_PATH")"
      "$LINK_PATH" --version || true
      exit 0
    fi
    echo "no current broski symlink at $LINK_PATH"
    exit 0
    ;;
  *)
    echo "Usage: $0 baseline|candidate|show"
    exit 1
    ;;
esac

if [[ ! -x "$SRC" ]]; then
  echo "missing executable: $SRC"
  exit 1
fi

ln -sfn "$SRC" "$LINK_PATH"
echo "updated: $LINK_PATH -> $SRC"
"$LINK_PATH" --version || true
