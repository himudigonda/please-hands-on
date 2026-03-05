set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

default:
    @just --list

setup:
    PY=$(./scripts/select_python.sh); $PY -m venv --clear backend/.venv
    backend/.venv/bin/pip install -r backend/requirements-dev.txt
    cd frontend && npm install

db_reset:
    PYTHONPATH=backend backend/.venv/bin/python backend/scripts/reset_db.py

backend_test:
    PYTHONPATH=backend backend/.venv/bin/pytest backend/tests -q

frontend_build:
    cd frontend && npm run test -- --run
    cd frontend && npm run build

ci: db_reset backend_test frontend_build

run_backend:
    PYTHONPATH=backend backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

run_frontend:
    cd frontend && npm run dev

clean:
    rm -rf backend/.pytest_cache
    rm -f backend/data/app.db
    rm -rf frontend/dist frontend/.vite
    rm -rf .please
    rm -f benchmark/benchmark.csv benchmark/benchmark.txt

bench:
    python3 scripts/benchmark.py
