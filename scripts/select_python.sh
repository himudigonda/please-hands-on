#!/usr/bin/env bash
set -euo pipefail

for candidate in python3.13 python3.12 python3.11 python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    echo "$candidate"
    exit 0
  fi
done

echo "python3"
