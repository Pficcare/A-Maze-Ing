*Part of [A-Maze-ing](../README.md), a 42 School project by pficcare.*

# mazegen

## Description

`mazegen` is the reusable maze-generation library behind A-Maze-ing. It
builds a grid of cells, draws the "42" pattern on it, carves the
corridors with a randomized depth-first search, and solves the result
with a breadth-first search — with **no display code at all**, so it
can be dropped into a terminal program, a graphical one, or a test
suite alike.

Pure standard library, no third-party dependency.

## Installation

Install the built wheel:

```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

or, from a source checkout of the [A-Maze-ing repository](..):

```bash
python3 -m build
```

See [Packaging](#packaging) below for what this produces.

## Usage

### Quick start

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
Note that `entry` and `exit` are given as `(y, x)`, the convention used
throughout the module.

`ValueError` is raised if the grid is smaller than 3×3, or if entry and
exit are equal or fall outside the grid.

### Access the structure

`maze.grid` is a `list[list[dict]]`, indexed `grid[y][x]`. Each cell is
a dictionary:

```python
>>> maze.grid[0][0]
{'wall': 15, 'visited': True, 'color': [0, 0, 0], 'logo': False, 'path': False}
```

| Field | Meaning |
| --- | --- |
| `wall` | bitmask of the closed walls: `N=1`, `E=2`, `S=4`, `W=8`. `15` is `1111`, so north, south, east and west are closed |
| `visited` | used by the generation walk |
| `color` | `[r, g, b]`, left to the caller to use |
| `logo` | `True` if the cell belongs to the "42" pattern |
| `path` | `True` if the caller flagged the cell as part of the solution |

Useful attributes: `maze.width`, `maze.height`, `maze.entry`,
`maze.exit`, `maze.perfect`, `maze.seed`, and `maze.logo_drawn`, which
is `False` when the pattern had to be skipped for lack of room.

`maze.to_hex()` returns the same walls as one hexadecimal digit per
cell, one string per row:

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

## Packaging

Built from `pyproject.toml` at the root of the repository, with
`build` (wrapped by `make build`):

```bash
python3 -m build --wheel --outdir .
```

This produces `mazegen-1.0.0-py3-none-any.whl` directly at the root of
the repository. Installing it gives `from mazegen import
MazeGenerator`, with no other file from the A-Maze-ing repository
needed.

## License

MIT — see [LICENSE.md](../LICENSE.md) at the root of the repository.
