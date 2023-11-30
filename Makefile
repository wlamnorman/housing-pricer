SOURCES="housing_pricer"
MAX_LINE_LENGTH=100
venv:
	python3.11 -m venv .venv

install:
	poetry lock && poetry build && poetry install

lint:
	black --line-length $(MAX_LINE_LENGTH) --exclude .venv .
	pylint $(SOURCES) --max-line-length=$(MAX_LINE_LENGTH) --ignore=.venv --init-import y --rcfile=pylintrc

test:
	pytest

dev:
	pip install -e .