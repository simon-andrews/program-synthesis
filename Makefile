all: format test typecheck

format:
	isort program_translation/**/*.py
	black --line-length 120 program_translation/**/*.py

test:
	pytest --cov=program_translation program_translation/tests --cov-report term-missing

typecheck:
	mypy program_translation

.PHONY: format test typecheck
