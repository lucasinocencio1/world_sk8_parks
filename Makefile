.PHONY: help server install setup mcp mcp-stdio mcp-http

SHELL := /bin/bash

.DEFAULT_GOAL := help

help:
	@echo "Skateparks API - available targets:"
	@echo ""
	@echo "  make setup     - Create .venv if it doesn't exist"
	@echo "  make install  - Install dependencies (runs setup first)"
	@echo "  make server   - Run the backend (runs install first)"
	@echo "  make mcp      - Run MCP server: stdio + HTTP on :8010 (Cursor + terminal)"
	@echo "  make mcp-stdio - MCP stdio only (for Cursor)"
	@echo "  make mcp-http  - MCP HTTP only on :8010 (for curl/other terminal)"
	@echo "  make help     - Show this help"
	@echo ""

setup:
	@if [ ! -d .venv ]; then python3 -m venv .venv; echo "Created .venv"; else echo ".venv already exists"; fi

install: setup
	.venv/bin/python -m pip install -r requirements.txt

server: install
	. .venv/bin/activate && uvicorn app.main:app --reload

mcp: install
	.venv/bin/python mcp_server.py
mcp-stdio: install
	.venv/bin/python mcp_server.py --stdio
mcp-http: install
	.venv/bin/python mcp_server.py --http
