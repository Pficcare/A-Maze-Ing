*This project has been created as part of the 42 curriculum by pficcare.*

# A-Maze-ing

## Description

A-Maze-ing is a maze generator written in Python, using the standard
library alone. It reads a plain-text configuration file, generates a
maze, writes it to disk in the hexadecimal format the subject defines,
and displays it in the terminal with a small interactive menu.

Two kinds of maze can be produced, depending on a single flag in the
configuration file:

- **Perfect maze** (`PERFECT=True`) — exactly one path links the entry
  to the exit. No loop anywhere. The maze is a spanning tree of the
  grid.
- **Playable board** (`PERFECT=False`, the default) — the same maze,
  with extra walls torn down so that several independent routes exist.
  This is the shape a Pac-Man-like game needs: a chased player must
  always have an alternative.

Every maze carries a visible **"42" pattern**, drawn with fully closed
cells and scaled to the grid size. It is skipped, with a message on the
console, when the grid is too small to hold it.

The generation logic lives in its own module, `mazegen.py`, with no
display code in it, so that a later project — a graphical one, for
instance — can import it and ignore everything about terminals.

## Instructions

### Requirements

Python 3.10 or later. The program itself needs **no third-party
package**: `flake8`, `mypy` and `build` are development tools only.

### Running

```bash
python3 a_maze_ing.py config.txt
```

`config.txt` is the only argument. Any other file name works.

The Makefile wraps the usual tasks:

| Command | What it does |
| --- | --- |
| `make install` | creates `venv/` and installs the development tools |
| `make run` | generates and displays a maze (`make run CONFIG=other.txt` to pick another file) |
| `make debug` | the same, under the `pdb` debugger |
| `make lint` | `flake8 .` and `mypy .` with the flags the subject requires |
| `make lint-strict` | `flake8 .` and `mypy . --strict` |
| `make clean` | removes `__pycache__` and `.mypy_cache` |

`make install` provisions a virtual environment because this system
marks its Python as externally managed (PEP 668), which makes a global
`pip install` fail.

### Using the program

Once the maze is displayed, a menu offers:

1. **Re-generate a new maze** — draws a different one from the same
   configuration (unless `SEED` is set, which pins the result).
2. **Show / Hide the shortest path** — reveals the solution one cell at
   a time, from the exit back to the entry.
3. **Rotate the wall colours** — cycles through four colour themes.
4. **Quit**.

## Configuration file format

One `KEY=VALUE` pair per line. Blank lines and lines starting with `#`
are ignored. Spaces around the key and the value are trimmed.

### Required keys

| Key | Meaning | Accepted values | Example |
| --- | --- | --- | --- |
| `WIDTH` | maze width, in cells (X axis) | integer, at least 3 | `WIDTH=38` |
| `HEIGHT` | maze height, in cells (Y axis) | integer, at least 3 | `HEIGHT=28` |
| `ENTRY` | entry cell, as `x,y` | inside the grid | `ENTRY=0,0` |
| `EXIT` | exit cell, as `x,y` | inside the grid, different from `ENTRY` | `EXIT=36,26` |
| `OUTPUT_FILE` | file the maze is written to | any writable path, not empty | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | single path, or playable board | `True`/`1`/`yes`/`on`, `False`/`0`/`no`/`off` (case-insensitive) | `PERFECT=True` |

### Optional keys

| Key | Meaning | Example |
| --- | --- | --- |
| `SEED` | random seed, for a reproducible maze. Leave it empty, or drop the line, for a different maze on every run | `SEED=42` |

A default configuration lives in `config.txt` at the root of the
repository.

### Errors

Every failure is reported with a message naming the key at fault, and
the program returns without a traceback. A missing file, a malformed
number, an unknown value for `PERFECT`, an entry equal to the exit, a
coordinate outside the grid, a grid smaller than 3×3 — all are caught
by `config_parser.py` and raised as a `ConfigError`.

### A note on coordinates

The configuration file writes coordinates as `x,y`, the form the
subject uses. Internally the grid is indexed `grid[y][x]`, rows first.
The swap happens in exactly two places: `config_parser.to_cell()` on
the way in, and `write_maze_file()` on the way out. Nowhere else.

## The generation algorithm

### Which one

**Randomized depth-first search**, also known as the *recursive
backtracker*, written iteratively with an explicit stack rather than
with recursion.

The grid starts as a rectangle of cells with all four walls closed.
From the entry cell:

1. list the neighbours that have not been visited yet;
2. if there is at least one, pick one at random, tear down the wall
   shared by the two cells, mark the neighbour visited and push it on
   the stack;
3. if there is none, pop the stack and carry on from the cell below;
4. stop when the stack is empty.

The cells forming the "42" pattern are marked as visited **before** the
walk starts. Being already visited, they are never chosen as a
neighbour, so the walk carves around them and leaves them fully closed.

When `PERFECT=False`, a second pass (`imperfection()`) walks the grid
looking for dead-ends — cells still holding three closed walls — and
opens one more wall on each. Every wall opened creates a loop, which is
what turns the single-path maze into a board with alternative routes.

### Why this one

- **It is a perfect maze by construction.** The walk only ever carves
  into a cell it has not visited, so it can never close a loop. The
  result is a spanning tree of the grid: one path between any two
  cells, exactly what `PERFECT=True` requires — with no verification
  pass needed afterwards.
- **Full connectivity is free.** The walk backtracks instead of giving
  up, so it does not stop until every reachable cell has been visited.
  An earlier prototype used a "give up after N tries" heuristic
  instead, and left unreachable cells in 198 runs out of 200. The
  backtracking version has none.
- **It needs no heavy data structure.** A stack and a `visited` flag
  per cell. Prim's and Kruskal's algorithms, the two classic
  alternatives, need a priority queue and a union-find structure
  respectively — more machinery for a result that is no better here.
- **It produces the nicest mazes to look at.** Depth-first search
  favours long winding corridors, where Prim's tends to produce short
  branches spreading out from the start. Since the maze is meant to be
  displayed, that matters.
- **The loops are added afterwards, on purpose.** Building a perfect
  maze first and then opening it up gives one algorithm serving both
  modes, and keeps the guarantee of full connectivity in both: opening
  a wall can never disconnect anything.

The solver is a separate concern: a **breadth-first search** from the
entry (`you_cannot_hide()`), then a walk back from the exit
(`solved()`). Breadth-first is what guarantees the path found is the
*shortest* one, which matters for the non-perfect board where several
routes exist.

## The reusable module

Chapter VI of the subject asks for the generation logic to be usable
from a later project. It lives in **`mazegen.py`**, which exposes a
single class, `MazeGenerator`, and contains no display code at all.

### Instantiate and use

```python
from mazegen import MazeGenerator

maze = MazeGenerator(width=10, height=6, seed=42)
maze.generate()
```

`generate()` does everything: it builds the grid, draws the "42"
pattern, carves the corridors, and opens the loops when the maze is not
a perfect one.

### Custom parameters

```python
maze = MazeGenerator(
    width=10,          # grid width, in cells
    height=6,          # grid height, in cells
    entry=(0, 0),      # entry cell, as (y, x)
    exit=(5, 9),       # exit cell, as (y, x); defaults to (height-2, width-2)
    perfect=True,      # True: one single path. False: a board with loops
    seed=42,           # any int for a reproducible maze, None for a random one
)
```

Only `width` and `height` are required. Passing the same `seed` twice
gives the very same maze, which is how reproducibility is guaranteed.

Note that `entry` and `exit` are given as `(y, x)` here, the internal
convention — not as `x,y` like in the configuration file.

`ValueError` is raised if the grid is smaller than 3×3, or if entry and
exit are equal or fall outside the grid.

### Access the structure

`maze.grid` is a `list[list[dict]]`, indexed `grid[y][x]`. Each cell is
a dictionary:

```python
>>> maze.grid[0][0]
{'wall': 11, 'visited': True, 'color': [0, 0, 0], 'logo': False, 'path': False}
```

| Field | Meaning |
| --- | --- |
| `wall` | bitmask of the closed walls: `N=1`, `E=2`, `S=4`, `W=8`. `11` is `1011`, so north, east and west are closed |
| `visited` | used by the generation walk |
| `color` | `[r, g, b]`, left to the caller to use |
| `logo` | `True` if the cell belongs to the "42" pattern |
| `path` | `True` if the caller flagged the cell as part of the solution |

Useful attributes: `maze.width`, `maze.height`, `maze.entry`,
`maze.exit`, `maze.perfect`, `maze.seed`, and `maze.logo_drawn`, which
is `False` when the pattern had to be skipped for lack of room.

`maze.to_hex()` returns the same walls as one hexadecimal digit per
cell, one string per row — the format the output file uses:

```python
>>> maze.to_hex()
['b939395513', 'aaaaac396a', 'c6c6a96aba', '95796e96aa', '855693a92a', 'c5556c6ec6']
```

### Access the solution

```python
>>> maze.solved()[:5]
[(0, 0), (1, 0), (2, 0), (2, 1), (1, 1)]

>>> maze.solution_letters
'SSENNESSENNESSSWSWWWSEEEENESENNENNENESSSSS'
```

`solved()` returns the cells of the shortest path, ordered from entry
to exit, both included, as `(y, x)` pairs. The result is cached until
the next generation. `solution_letters` is the same path spelled with
the four letters `N`, `E`, `S` and `W`, one per step.

Both raise `MazeError` if `generate()` has not been called, or if no
path links the entry to the exit.

### Packaging

The module is distributed as a `mazegen-*` package, buildable from the
sources in this repository. See `LICENSE.md` for the terms under which
it may be reused.

## Output file format

One hexadecimal digit per cell, one row per line. Each bit stands for a
closed wall: bit 0 north, bit 1 east, bit 2 south, bit 3 west. A bit set
to 1 means the wall is closed.

After a blank line come three more lines: the entry coordinates, the
exit coordinates — both written back as `x,y` — and the shortest path
spelled with `N`, `E`, `S` and `W`. Every line ends with `\n`.

## Terminal rendering, and one design choice

Each cell is drawn **two characters wide and two lines tall**, so that
the walls it shares with its neighbours have somewhere to be drawn. A
maze of `WIDTH` × `HEIGHT` cells therefore occupies:

- `2 × WIDTH + 1` columns
- `2 × HEIGHT + 1` lines, plus one status line, six for the menu and one
  for the prompt — so `2 × HEIGHT + 9` lines in total

With the shipped `config.txt` (38 × 28), that is **77 columns by 65
lines**.

The whole program runs inside the terminal's **alternate screen
buffer**, the second, blank screen that full-screen programs such as
`vim`, `less` or `htop` switch to. Each refresh sends the cursor home
and repaints the maze, the status line and the menu over the previous
frame. Two consequences: the display never scrolls and never stacks
copies of itself, and the user's scrollback is handed back untouched on
exit.

**The design choice, and its limit.** Repainting in place assumes the
whole screen fits in the window. The alternate screen is exactly as
large as the terminal, so when the maze needs more lines than the
window has, the terminal scrolls to make room and "cursor home" no
longer lands on the top of the maze: the frames start drifting and the
display degrades. Nothing is lost — the maze itself, the output file
and the solution are unaffected, and resizing the window or quitting
and restarting puts the display right — but it is not pleasant to look
at.

The choice made here is to **keep the renderer simple and require a
large enough terminal**, rather than to grow a fallback mode for small
windows. Repainting in place is what makes the display stable in the
first place; a renderer able to handle both cases would need scrolling,
viewports and clipping, which is a lot of machinery for a program whose
point is elsewhere. The rule of thumb, then:

> Your terminal must have at least `2 × WIDTH + 1` columns and
> `2 × HEIGHT + 9` lines. Enlarge the window, reduce the font size, or
> lower `WIDTH` and `HEIGHT` in the configuration file.

For a standard 80 × 24 terminal, that means keeping `WIDTH` at 39 or
below and `HEIGHT` at 7 or below.

**A second consequence: the mouse wheel.** The alternate screen has no
scrollback — it is a single screen, with nothing above it to scroll
back to. Terminal emulators work around this with *alternate scroll
mode*: while that screen is active, they turn each wheel notch into an
up or down arrow key sent to the program's standard input, so that the
wheel keeps working in programs such as `less` or `man`, which move
with the arrow keys.

A-Maze-ing has nothing to scroll and does not read the arrow keys, so
scrolling while the menu is waiting simply types those sequences into
the prompt, where the terminal echoes them in caret notation:

```
Choice? (1-4): ^[[A^[[A^[[A
```

`^[` is how a terminal displays the Escape character, so `^[[A` is one
`ESC [ A` — one wheel notch. This is display only: the program reads
the line, fails to read a number out of it, answers `Please pick a
number between 1 and 4.` and repaints a clean screen. Nothing is typed
into the maze, and nothing is lost.

Silencing it would mean asking the emulator to stop translating the
wheel, by turning alternate scroll mode off on entering the alternate
screen and back on when leaving it. That was left out on purpose: it is
a terminal-specific mode, supported by most emulators but not all, and
the behaviour it would fix is a transient line of text on a screen that
is about to be repainted anyway. Documenting it is the better trade
here.

## Resources

### On maze generation

- Jamis Buck, *Maze Generation: Recursive Backtracking* —
  <https://weblog.jamisbuck.org/2010/12/27/maze-generation-recursive-backtracking>
- Jamis Buck, *Mazes for Programmers*, Pragmatic Bookshelf, 2015
- Walter D. Pullen, *Think Labyrinth!: Maze Algorithms* —
  <https://www.astrolog.org/labyrnth/algrithm.htm>
- Wikipedia, *Maze generation algorithm* —
  <https://en.wikipedia.org/wiki/Maze_generation_algorithm>
- Wikipedia, *Breadth-first search* —
  <https://en.wikipedia.org/wiki/Breadth-first_search>

### On terminal rendering

- Wikipedia, *ANSI escape code* —
  <https://en.wikipedia.org/wiki/ANSI_escape_code>
- Thomas Dickey, *XTerm Control Sequences* —
  <https://invisible-island.net/xterm/ctlseqs/ctlseqs.html>

### On Python

- PEP 8 (style), PEP 257 (docstrings), PEP 484 (type hints)
- The `random`, `collections.deque` and `typing` modules of the
  standard library

### How AI was used

<!-- TODO pficcare: check this section says what you actually did, and
     be ready to defend every line of it during the evaluation. -->

AI (Claude) was used as a **tutor, not as a code generator**. The
working rule, set from the start, was: explain the reasoning, offer two
or three approaches, and let me pick and write the code. Concretely, it
was used for:

- **Explaining concepts** before implementing them: how a bitmask
  encodes four walls in one digit, why a breadth-first search finds the
  shortest path where a depth-first search does not, what the alternate
  screen buffer is and why `vim` uses it. This is the role it played
  most: a teacher to understand the theory and the *why* behind a
  choice, not just the *what*, before any line was written.
- **Diagnosing bugs**, by explaining a mechanism rather than handing
  over a patch. Two examples: the connectivity bug in the first
  generator, where the "give up after N tries" heuristic left
  unreachable cells; and the rendering glitch where each animation
  frame stacked on top of the previous one, which turned out to be
  three separate causes at once.
- **Advising on style**, once code already worked, to make it cleaner
  and more idiomatic: shorter docstrings that keep only what a reader
  needs, or reworking a "pick one, give up on failure" pattern into
  Python's `random.Random.shuffle` plus a plain loop.
- **Reviewing** the code for compliance with the subject and with
  `flake8` / `mypy --strict`.

It was **not** used to write the generation algorithm, the solver, or
the rendering logic, all of which were written by hand and can be
explained line by line.

## Team and project management

<!-- TODO pficcare: this section is yours to write — nobody else can.
     The subject (chapter VII) asks explicitly for the four points
     below. Replace each placeholder with what actually happened. -->

### Roles

Solo project. TODO: state what you took charge of.

### Planning, and how it evolved

TODO: what you had planned at the start, in what order, and what
actually happened — what took longer than expected, what had to be
rewritten, what was dropped.

### What worked well, what could be improved

TODO. Two candidates from the history of this project, worth writing up
because they are real: splitting the prototype into three modules
(`mazegen.py`, `config_parser.py`, `a_maze_ing.py`) made everything
afterwards easier; and the first generation algorithm had to be
rewritten once a test showed it left unreachable cells in 198 runs out
of 200.

### Tools

TODO. Candidates: Git, `flake8`, `mypy`, `make`, a virtual environment,
`pdb`, and Claude as described above.
