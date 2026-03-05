SHELL := /bin/bash
PYTHON_BOOTSTRAP := $(shell ./scripts/select_python.sh)

PYTHON := backend/.venv/bin/python
PIP := backend/.venv/bin/pip
PYTEST := backend/.venv/bin/pytest
UVICORN := backend/.venv/bin/uvicorn

.PHONY: setup db_reset backend_test frontend_build ci run_backend run_frontend clean bench

setup:
	$(PYTHON_BOOTSTRAP) -m venv --clear backend/.venv
	$(PIP) install -r backend/requirements-dev.txt
	cd frontend && npm install

db_reset:
	PYTHONPATH=backend $(PYTHON) backend/scripts/reset_db.py

backend_test:
	PYTHONPATH=backend $(PYTEST) backend/tests -q

frontend_build:
	cd frontend && npm run test -- --run
	cd frontend && npm run build

ci: db_reset backend_test frontend_build

run_backend:
	PYTHONPATH=backend $(UVICORN) app.main:app --host 127.0.0.1 --port 8000 --reload

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
