.PHONY: help server install setup

SHELL := /bin/bash

.DEFAULT_GOAL := help

help:
	@echo "Skateparks API - available targets:"
	@echo ""
	@echo "  make setup   - Create .venv if it doesn't exist"
	@echo "  make install - Install dependencies (runs setup first)"
	@echo "  make server  - Run the backend (runs install first)"
	@echo "  make help    - Show this help"
	@echo ""

setup:
	@if [ ! -d .venv ]; then python3 -m venv .venv; echo "Created .venv"; else echo ".venv already exists"; fi

install: setup
	.venv/bin/python -m pip install -r requirements.txt

server: install
	. .venv/bin/activate && uvicorn app.main:app --reload
