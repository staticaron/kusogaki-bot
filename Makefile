.PHONY: check format

check:
	poetry run ruff format --check .

format:
	poetry run ruff format .
