# HousingPricer
## Quickstart
To properly use the project, run the following in the root directory:
```
    make venv
    make install
```
this sets up a virtual environment and installs the project dependencies as per instructions in the `pyproject.toml`.

## Components
* Fetch historical final prices: `historical_scraping`
* Fetch data for listed housing: `listing_scraping`
* Supplemental data (such as location, traveling times, in-cluster comparison): ...
* Database interactions: ...
* Final price predictions: ...


## For developers
This projects uses
* `poetry` as build tool;
* `make` as interface and
* `venv` as dependency control.

See `Makefile` for specifics, but use of the following is recommended:
* `make dev`
and use of
* `make lint`
* `make test`

is _REQUIRED_ before pushing commits (CI/CD to be added).