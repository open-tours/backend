SHELL := /bin/sh

PROJECT := config
PROJECT_DIR := $(abspath $(shell pwd))

test:
	python manage.py test

pre_commit_all:
	pre-commit install
	pre-commit run --all-files
