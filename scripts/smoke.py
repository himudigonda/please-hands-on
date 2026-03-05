#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BACKEND = "http://127.0.0.1:8000"
FRONTEND = "http://127.0.0.1:5173"


def fetch_json(url: str, method: str = "GET", payload: dict | None = None) -> dict:
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, method=method, data=body, headers=headers)
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.read().decode("utf-8")


def main() -> int:
    try:
        health = fetch_json(f"{BACKEND}/api/health")
        if health.get("status") != "ok":
            raise RuntimeError(f"unexpected health payload: {health}")

        created = fetch_json(
            f"{BACKEND}/api/tasks", method="POST", payload={"title": "smoke task"}
        )
        toggled = fetch_json(f"{BACKEND}/api/tasks/{created['id']}", method="PATCH")
        if toggled.get("completed") is not True:
            raise RuntimeError("toggle endpoint did not mark task as completed")

        html = fetch_text(FRONTEND)
        if "TaskPulse" not in html:
            raise RuntimeError("frontend index does not contain TaskPulse marker")

        print("Smoke check passed: backend + db + frontend are reachable")
        return 0
    except urllib.error.URLError as exc:
        print(f"Smoke check failed: network error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Smoke check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
