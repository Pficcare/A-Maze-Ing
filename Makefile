SYS_PYTHON := python3

VENV       := .venv
PYTHON     := $(VENV)/bin/python
PIP     := $(VENV)/bin/pip

CONFIG     := config.txt

MYPY_FLAGS := --warn-return-any --warn-unused-ignores \
              --ignore-missing-imports --disallow-untyped-defs \
              --check-untyped-defs

.PHONY: help install run build debug clean fclean lint lint-strict

help:
	@echo "make install      create venv/ and install the dev tools"
	@echo "make run          generate and display a maze"
	@echo "make build        build the wheel file"
	@echo "make debug        same, under the pdb debugger"
	@echo "make lint         flake8 + mypy with the required flags"
	@echo "make lint-strict  flake8 + mypy --strict"
	@echo "make clean        remove caches"
	@echo "make fclean       remove caches and venv"


install: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements.txt
	@printf 'Creating venv...\n'
	$(SYS_PYTHON) -m venv $(VENV)
	@printf 'Installing dependencies...\n'
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@printf '\n\033[32mActivate venv with \033[34msource $(VENV)/bin/activate\033[0m\n'

run: install
	$(PYTHON) a_maze_ing.py $(CONFIG)

build: install
	$(PYTHON) -m build --wheel --outdir .

debug: install
	$(PYTHON) -m pdb a_maze_ing.py $(CONFIG)

clean:
	find . \( -name "__pycache__" -o -name ".mypy_cache" -o -name "*.egg-info" -o -name ".pytest_cache" \) -type d -exec rm -rf {} +
	rm -rf build/ dist/
	rm -f maze.txt

fclean: clean
	rm -rf $(VENV)

lint: install
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . $(MYPY_FLAGS)

lint-strict: install
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --strict
