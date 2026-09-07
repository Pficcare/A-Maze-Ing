#!/usr/bin/env python3
"""Reusable maze generator.

This module exposes a single class, `MazeGenerator`, which builds a
grid of cells, draws the "42" pattern on it, carves the corridors, and
solves the resulting maze.

It deliberately contains no display code: the structure is exposed as
is and the visual representation is left to the caller, so the module
stays usable from a terminal as well as from a graphical interface.

Example:

    from mazegen import MazeGenerator

    maze = MazeGenerator(width=35, height=20, seed=42)
    maze.generate()

    cells = maze.solved()         # [(0, 0), (0, 1), (1, 1), ...]
    print(maze.solution_letters)  # 'ESEENEEESSSEES...'
    print(maze.grid[0][0]["wall"])
"""

import random
from collections import deque
from typing import TypedDict

# One wall per bit: N=1, E=2, S=4, W=8. A bit set to 1 means closed.
N, E, S, W = 1, 2, 4, 8

# All four walls closed: the starting state of every cell.
ALL_CLOSE = 15

DIRECTIONS = [N, S, E, W]

# Wall to open on the neighbour when opening one of our own.
OPPOSITE = {N: S, S: N, E: W, W: E}

# (dx, dy) move bound to each direction.
DELTA = {N: (0, -1), S: (0, 1), E: (1, 0), W: (-1, 0)}

# Reverse table: recovers the direction from a move.
STEP = {delta: direction for direction, delta in DELTA.items()}

# Letter expected in the output file (subject IV.5).
LETTER = {N: "N", E: "E", S: "S", W: "W"}

# The "42" pattern as pixels: 1 is a filled cell, 0 a free one.
PATTERN_42 = [
    [1, 0, 1, 0, 1, 1, 1],
    [1, 0, 1, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 1],
    [0, 0, 1, 0, 1, 0, 0],
    [0, 0, 1, 0, 1, 1, 1],
]

# Largest share of the grid the "42" pattern may cover.
LOGO_RATIO = 0.12

# Largest scaling factor, so the pattern stays readable.
MAX_LOGO_SCALE = 3

# Below 3x3 the four corners and the centre are no longer distinct
# cells, which makes the Pac-Man style board meaningless.
MIN_SIDE = 3


class MazeError(Exception):
    """Raised when the maze cannot be produced or solved."""


class Dictype(TypedDict):
    """Contents of a single grid cell.

    Attributes:
        wall: Bitmask of the closed walls (N=1, E=2, S=4, W=8).
        visited: True once carving has reached the cell.
        color: Free RGB colour, for the caller to use.
        logo: True if the cell belongs to the "42" pattern.
        path: True if the cell belongs to the solution path.
    """

    wall: int
    visited: bool
    color: list[int]
    logo: bool
    path: bool


class MazeGenerator:
    """Generates a maze over a rectangular grid of cells.

    The grid is indexed `grid[y][x]`: the outer list holds the rows
    (Y axis), the inner list the columns (X axis). Every coordinate
    handled by this class follows the same `(y, x)` convention.

    Attributes:
        width: Grid width, in cells.
        height: Grid height, in cells.
        entry: Entry cell, in `(y, x)` form.
        exit: Exit cell, in `(y, x)` form.
        perfect: True for a perfect maze (a single path), False for a
            playable board carrying loops.
        seed: Random seed, or None to draw differently every time.
        grid: The grid produced by `generate()`.
        logo_drawn: False when the "42" pattern had to be skipped, the
            grid being too small to hold it.
    """

    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int] = (0, 0),
        exit: tuple[int, int] | None = None,
        perfect: bool = False,
        seed: int | None = None,
    ) -> None:
        """Prepares a generator, without generating anything yet.

        Args:
            width: Grid width, in cells.
            height: Grid height, in cells.
            entry: Entry cell, in `(y, x)` form.
            exit: Exit cell, in `(y, x)` form. Defaults to the cell two
                steps away from the bottom-right corner.
            perfect: True for a perfect maze, False for a board
                carrying loops.
            seed: Random seed, or None for a different maze on every
                generation.

        Raises:
            ValueError: If the grid is too small, or if entry and exit
                are the same cell or fall outside the grid.
        """
        if width < MIN_SIDE or height < MIN_SIDE:
            raise ValueError(
                f"the grid must be at least "
                f"{MIN_SIDE}x{MIN_SIDE} (got {width}x{height})"
            )
        if exit is None:
            exit = (height - 2, width - 2)
        self.width = width
        self.height = height
        self.entry = entry
        self.exit = exit
        self.perfect = perfect
        self.seed = seed
        self.logo_drawn = False
        self.grid: list[list[Dictype]] = []
        self._rng = random.Random(seed)
        self._solution: list[tuple[int, int]] | None = None
        self.check_cells()

    def check_cells(self) -> None:
        """Checks that entry and exit are usable.

        Raises:
            ValueError: If both cells are the same, or if either one
                falls outside the grid.
        """
        if self.entry == self.exit:
            raise ValueError("entry and exit are the same cell")
        cells = (("entry", self.entry), ("exit", self.exit))
        for name, (y, x) in cells:
            if not 0 <= x < self.width or not 0 <= y < self.height:
                raise ValueError(
                    f"{name}={(y, x)} lies outside the "
                    f"{self.width}x{self.height} grid"
                )

    def generate(self) -> None:
        """Produces a complete maze into `self.grid`.

        Chains building the grid, drawing the "42" pattern, carving the
        corridors, then, unless a perfect maze was asked for, opening
        extra loops.

        Calling this method again with the same seed reproduces exactly
        the same maze.
        """
        self._rng = random.Random(self.seed)
        self._solution = None
        self.grid = self.generate_grid()
        self.i_m_logo()
        self.the_architect()
        if not self.perfect:
            self.imperfection()

    def generate_grid(self) -> list[list[Dictype]]:
        """Builds a fresh grid whose cells are all fully closed.

        Returns:
            The grid, holding `height` rows of `width` cells.
        """
        return [
            [
                {
                    "wall": ALL_CLOSE,
                    "visited": False,
                    "color": [0, 0, 0],
                    "logo": False,
                    "path": False,
                }
                for _ in range(self.width)
            ]
            for _ in range(self.height)
        ]

    @staticmethod
    def build_logo_42() -> list[tuple[int, int]]:
        """Turns the "42" pattern into offsets around its centre.

        Returns:
            The `(dy, dx)` offsets of the filled cells only, relative
            to the centre of the pattern.
        """
        height = len(PATTERN_42)
        width = len(PATTERN_42[0])
        center_y = height // 2
        center_x = width // 2
        offsets: list[tuple[int, int]] = []
        for i, line in enumerate(PATTERN_42):
            for j, filled in enumerate(line):
                if filled == 1:
                    offsets.append((i - center_y, j - center_x))
        return offsets

    def scale_logo(self) -> int:
        """Computes the scaling factor of the "42" pattern.

        Grows the pattern as long as it fits in the grid and covers no
        more than `LOGO_RATIO` of its area.

        Returns:
            The scaling factor, or 0 when even the unscaled pattern
            does not fit in the grid.
        """
        max_size = LOGO_RATIO * self.width * self.height
        height = len(PATTERN_42)
        width = len(PATTERN_42[0])
        filled = len(self.build_logo_42())
        scale = 1
        best = 0
        while True:
            if width * scale > self.width:
                break
            if height * scale > self.height:
                break
            if filled * scale ** 2 > max_size:
                break
            best = scale
            scale += 1
        return min(best, MAX_LOGO_SCALE)

    def i_m_logo(self) -> None:
        """Draws the "42" pattern at the centre of the grid.

        Every pixel becomes a block of `scale` cells marked as
        visited, so carving walks around them. Entry and exit cells
        are spared even if that means a notch in the pattern.

        Prints a message and leaves `logo_drawn` False when the grid
        is too small to hold it (as the subject requires).
        """
        scale = self.scale_logo()
        if scale == 0:
            print(
                "The '42' pattern cannot be displayed: "
                "the grid is too small."
            )
            self.logo_drawn = False
            return
        center_y = self.height // 2
        center_x = self.width // 2
        shift = scale // 2
        for offset_y, offset_x in self.build_logo_42():
            row = center_y + offset_y * scale - shift
            col = center_x + offset_x * scale - shift
            for step_y in range(scale):
                for step_x in range(scale):
                    y = row + step_y
                    x = col + step_x
                    if not 0 <= y < self.height:
                        continue
                    if not 0 <= x < self.width:
                        continue
                    if (y, x) in (self.entry, self.exit):
                        continue
                    self.grid[y][x]["visited"] = True
                    self.grid[y][x]["logo"] = True
        self.logo_drawn = True

    def free_the_neighbours(self, row: int, col: int) -> list[int]:
        """Lists the directions leading to an untouched cell.

        Args:
            row: Row of the current cell.
            col: Column of the current cell.

        Returns:
            The directions whose neighbouring cell fits inside the grid
            and has not been visited yet.
        """
        free: list[int] = []
        for d in DIRECTIONS:
            col_step, row_step = DELTA[d]
            next_row = row + row_step
            next_col = col + col_step
            if not 0 <= next_row < self.height:
                continue
            if not 0 <= next_col < self.width:
                continue
            if not self.grid[next_row][next_col]["visited"]:
                free.append(d)
        return free

    def the_architect(self) -> None:
        """Carves the corridors with a depth-first walk.

        Moves to a randomly picked untouched neighbour, opening the
        shared wall on both sides, and steps back once none are left.
        Free neighbours are recomputed before every draw, which is
        what guarantees full connectivity.
        """
        start_y, start_x = self.entry
        self.grid[start_y][start_x]["visited"] = True
        stack: list[tuple[int, int]] = [self.entry]
        while stack:
            row, col = stack[-1]
            free = self.free_the_neighbours(row, col)
            if not free:
                stack.pop()
                continue
            direction = self._rng.choice(free)
            col_step, row_step = DELTA[direction]
            next_row = row + row_step
            next_col = col + col_step
            self.grid[next_row][next_col]["visited"] = True
            self.grid[next_row][next_col]["color"] = [100, 100, 100]
            self.grid[row][col]["wall"] &= ~direction
            self.grid[next_row][next_col]["wall"] &= ~OPPOSITE[direction]
            stack.append((next_row, next_col))

    def closed_neighbours(self, row: int, col: int) -> list[int]:
        """Lists the directions leading to a real cell through a
        closed wall.

        Filters out the permanent border walls, which are closed too
        but have no cell on their far side.

        Args:
            row: Row of the cell.
            col: Column of the cell.

        Returns:
            The directions whose wall is closed and whose neighbour
            exists inside the grid.
        """
        closed: list[int] = []
        for d in DIRECTIONS:
            if not self.grid[row][col]["wall"] & d:
                continue
            col_step, row_step = DELTA[d]
            next_row = row + row_step
            next_col = col + col_step
            if not 0 <= next_row < self.height:
                continue
            if not 0 <= next_col < self.width:
                continue
            closed.append(d)
        return closed

    def imperfection(self) -> None:
        """Opens one extra way out of every dead-end.

        A cell with three closed walls is a dead-end; tearing one down
        creates a loop. Walks the whole grid, border included, so a
        small grid still gets at least one loop (subject IV.4 forbids
        a plain tree in this mode). Never opens a wall facing the "42"
        pattern; every closed direction is tried, in random order,
        before a cell is accepted as a dead-end for good.
        """
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x]["wall"].bit_count() != 3:
                    continue
                closed = self.closed_neighbours(y, x)
                self._rng.shuffle(closed)
                for direction in closed:
                    col_step, row_step = DELTA[direction]
                    next_y = y + row_step
                    next_x = x + col_step
                    if self.grid[next_y][next_x]["logo"]:
                        continue
                    self.grid[y][x]["wall"] &= ~direction
                    self.grid[next_y][next_x]["wall"] &= ~OPPOSITE[direction]
                    break

    def you_cannot_hide(self) -> dict[tuple[int, int], tuple[int, int] | None]:
        """Explores the maze breadth-first, starting from the entry.

        Growing distance means a cell's first visit is along a
        shortest path, so recording where each cell was reached from
        is enough to walk that path back later.

        Returns:
            For each reachable cell, the cell it was reached from. The
            entry maps to None, marking the end of the walk back.

        Raises:
            MazeError: If the maze has not been generated yet.
        """
        if not self.grid:
            raise MazeError("call generate() before you_cannot_hide()")
        came_from: dict[tuple[int, int], tuple[int, int] | None] = {
            self.entry: None
        }
        queue = deque([self.entry])
        while queue:
            y, x = queue.popleft()
            if (y, x) == self.exit:
                break
            for d in DIRECTIONS:
                if self.grid[y][x]["wall"] & d:
                    continue
                col_step, row_step = DELTA[d]
                neighbour = (y + row_step, x + col_step)
                if neighbour not in came_from:
                    came_from[neighbour] = (y, x)
                    queue.append(neighbour)
        return came_from

    def solved(self) -> list[tuple[int, int]]:
        """Walks the shortest path back, from the exit to the entry.

        Reads the map from `you_cannot_hide()` backwards until the
        entry answers None, then flips the list into walking order.
        Cached until the next generation.

        Returns:
            The cells of the path, ordered from entry to exit, both
            included.

        Raises:
            MazeError: If the maze has not been generated yet, or if no
                path links the entry to the exit.
        """
        if self._solution is not None:
            return self._solution
        came_from = self.you_cannot_hide()
        if self.exit not in came_from:
            raise MazeError(
                f"no path links {self.entry} to {self.exit}"
            )
        cells: list[tuple[int, int]] = []
        cell: tuple[int, int] | None = self.exit
        while cell is not None:
            cells.append(cell)
            cell = came_from[cell]
        cells.reverse()
        self._solution = cells
        return cells

    @property
    def solution_letters(self) -> str:
        """The solution path spelled with the letters N, E, S and W.

        Each letter describes the step leading from one cell to the
        next, in the form the output file expects (subject IV.5).

        Returns:
            The run of directions, for instance 'ESEENEEESSS'.

        Raises:
            MazeError: If the maze has not been generated yet, or if it
                admits no solution.
        """
        cells = self.solved()
        letters: list[str] = []
        for (y, x), (next_y, next_x) in zip(cells, cells[1:]):
            step = (next_x - x, next_y - y)
            letters.append(LETTER[STEP[step]])
        return "".join(letters)

    def to_hex(self) -> list[str]:
        """Exports the walls as one hexadecimal digit per cell.

        Each bit is a closed wall, in the order the subject imposes
        (IV.5): bit 0 north, 1 east, 2 south, 3 west — the encoding
        already used internally.

        Returns:
            One string per grid row.

        Raises:
            MazeError: If the maze has not been generated yet.
        """
        if not self.grid:
            raise MazeError("call generate() before to_hex()")
        return [
            "".join(f"{cell['wall']:x}" for cell in row)
            for row in self.grid
        ]
