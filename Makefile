PYTHON ?= python
PIP ?= pip

.PHONY: install format lint typecheck test migrate dev

install:
	$(PIP) install -r requirements-dev.txt

format:
	black .
	ruff check . --fix

lint:
	ruff check .

typecheck:
	mypy app

test:
	pytest

migrate:
	alembic upgrade head

dev:
	uvicorn app.main:app --reload
