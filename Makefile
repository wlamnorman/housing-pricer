SOURCES=housing_pricer tests
MAX_LINE_LENGTH=100

venv:
	python3.10 -m venv .venv

install:
	poetry lock && poetry build && poetry install

dev:
	poetry run -m pip install -e .

lint:
	poetry run isort $(SOURCES) --skip .venv
	poetry run black --line-length $(MAX_LINE_LENGTH) --exclude .venv $(SOURCES)
	poetry run pylint $(SOURCES) --max-line-length=$(MAX_LINE_LENGTH) --ignore=.venv,tests --rcfile=pylintrc

test:
	poetry run pytest