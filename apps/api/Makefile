PYTHON ?= python

.PHONY: dev lint typecheck test coverage build

dev:
	$(PYTHON) -m uvicorn app.main:app --reload --port 8000

lint:
	$(PYTHON) -m compileall -q app

typecheck:
	$(PYTHON) -m compileall -q app

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py" -v

coverage:
	$(PYTHON) -m coverage run --rcfile=.coveragerc -m unittest discover -s tests -p "test_*.py" -v
	$(PYTHON) -m coverage report --rcfile=.coveragerc

build:
	$(PYTHON) -m compileall -q app
