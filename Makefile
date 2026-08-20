#> ===================================================================
#> HOW A MAKEFILE WORKS  (notes to myself, safe to delete)
#>
#> A rule reads:   target: prerequisites
#>                 <TAB>recipe line
#> The recipe MUST start with a real tab, never spaces. A space there
#> is the classic "missing separator" error.
#>
#> Run one rule with:  make <target>
#> Running plain `make` runs the FIRST target of the file, which is
#> why `help` sits at the top here.
#>
#> := assigns once, when the file is read.  = would re-evaluate the
#> variable every single time it is used.
#> $(NAME) reads a variable back.
#>
#> .PHONY lists targets that are NOT file names. Without it, a file
#> called "clean" sitting in the folder would make `make clean` say
#> "nothing to be done": make would think the target is already built.
#> ===================================================================

#> Interpreter used to CREATE the virtualenv (the system one).
SYS_PYTHON := python3

#> Folder holding the virtualenv, and the interpreter inside it.
#> Everything else runs through it, so the tools are the pinned ones.
VENV       := venv
PYTHON     := $(VENV)/bin/python

#> Config file passed to the program. Override it from the command
#> line without editing this file:  make run CONFIG=other.txt
CONFIG     := config.txt

#> mypy flags the subject imposes for the `lint` rule.
MYPY_FLAGS := --warn-return-any --warn-unused-ignores \
              --ignore-missing-imports --disallow-untyped-defs \
              --check-untyped-defs

.PHONY: help install run debug clean lint lint-strict

#> Lists the available rules. First target, so it is what plain
#> `make` runs.
help:
	@echo "make install      create venv/ and install the dev tools"
	@echo "make run          generate and display a maze"
	@echo "make debug        same, under the pdb debugger"
	@echo "make lint         flake8 + mypy with the required flags"
	@echo "make lint-strict  flake8 + mypy --strict"
	@echo "make clean        remove caches"

#> Creates the virtualenv if missing, then installs the dev tools in
#> it. A venv is needed because this system marks its Python as
#> externally managed (PEP 668), so a global pip install is refused.
#> `test -d ... ||` means "unless the folder is already there".
install:
	test -d $(VENV) || $(SYS_PYTHON) -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

#> Runs the program on the config file.
run:
	$(PYTHON) a_maze_ing.py $(CONFIG)

#> Same, under the built-in debugger. pdb stops on the first line and
#> waits: `n` steps, `c` continues, `q` quits, `b 42` breaks on a line.
debug:
	$(PYTHON) -m pdb a_maze_ing.py $(CONFIG)

#> Deletes what the interpreter and mypy cache. Never touches venv/
#> nor any source file.
clean:
	rm -rf __pycache__ .mypy_cache
	rm -f .coverage

#> The two checks the subject requires. flake8 reads its exclusions
#> from setup.cfg, which is why plain `.` is enough here.
lint:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . $(MYPY_FLAGS)

#> Same, with every optional strictness turned on.
lint-strict:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --strict
