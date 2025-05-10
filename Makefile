# Makefile for the DomainSale library

.PHONY: help install test lint clean build dist

help:
	@echo "Available commands:"
	@echo "  make install    - Install the package in development mode"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linting"
	@echo "  make clean      - Clean up build artifacts"
	@echo "  make build      - Build the package"
	@echo "  make dist       - Create distribution packages"

install:
	pip install -e .

test:
	python -m unittest discover -s domainsale/tests

lint:
	flake8 domainsale
	pylint domainsale

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

build: clean
	python setup.py build

dist: clean
	python setup.py sdist bdist_wheel
