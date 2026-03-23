PYTHON ?= python

.PHONY: dev lint typecheck test build

dev:
	$(PYTHON) -m uvicorn app.main:app --reload --port 8000

lint:
	$(PYTHON) -m compileall -q app

typecheck:
	$(PYTHON) -m compileall -q app

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py" -v

build:
	$(PYTHON) -m compileall -q app
