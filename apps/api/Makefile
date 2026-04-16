PYTHON ?= python

.PHONY: dev lint typecheck test test-coverage coverage-html build

dev:
	$(PYTHON) -m uvicorn app.main:app --reload --port 8000

lint:
	$(PYTHON) -m compileall -q app

typecheck:
	$(PYTHON) -m compileall -q app

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py" -v

test-coverage:
	$(PYTHON) -m coverage run -m unittest discover -s tests -p "test_*.py"
	$(PYTHON) -m coverage report -m

coverage-html: test-coverage
	$(PYTHON) -m coverage html

build:
	$(PYTHON) -m compileall -q app
