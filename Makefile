SOURCES=housing_pricer tests
MAX_LINE_LENGTH=100
venv:
	python3.10 -m venv .venv

install:
	poetry lock && poetry build && poetry install

dev:
	@.venv/bin/python -m pip install -e .

lint:
	black --line-length $(MAX_LINE_LENGTH) --exclude .venv $(SOURCES)
	pylint $(SOURCES) --max-line-length=$(MAX_LINE_LENGTH) --ignore=.venv --init-import y --rcfile=pylintrc

test:
	@.venv/bin/python -m pytest