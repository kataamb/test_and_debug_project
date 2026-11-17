#!/bin/bash


poetry run mypy --check-untyped-defs --namespace-packages --explicit-package-bases .
echo ""

poetry run ruff check .
echo ""


#poetry run pytest --random-order --alluredir=./allure-results
#echo ""

poetry run pytest --random-order --cov=. --cov-report=term-missing


#poetry run allure serve ./allure-results

#poetry run pytest -n 8 -v

#poetry run pytest --random-order --cov=. --cov-report=term-missing

allure generate ./allure-results -o ./allure-report --clean
#then
allure serve ./allure-results

