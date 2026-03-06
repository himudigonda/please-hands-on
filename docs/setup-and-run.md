# Setup and Run Guide

## Install Broski

```bash
curl -fsSL https://raw.githubusercontent.com/himudigonda/Broski/main/install.sh | bash
```

## Project setup

```bash
broski --workspace . run setup
```

## Run backend

```bash
broski --workspace . run run_backend
```

Backend health endpoint:

- `http://127.0.0.1:8000/api/health`

## Run frontend

Open a second terminal:

```bash
broski --workspace . run run_frontend
```

Frontend URL:

- `http://127.0.0.1:5173`

## Local smoke test

With backend and frontend running:

```bash
python3 scripts/smoke.py
```
