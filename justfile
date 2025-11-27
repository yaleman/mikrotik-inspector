[private]
default:
    just --list

check: lint mypy test

lint:
    uv run ruff check mikrotik_inspector tests

mypy:
    uv run mypy --strict mikrotik_inspector tests

test:
    uv run pytest

coveralls:
    uv run coverage run -m pytest
    uv run coveralls