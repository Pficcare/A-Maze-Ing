#!/usr/bin/env python3
"""A-Maze-ing: maze generator entry point.

Reads a configuration file, generates the maze described by it, writes
it to the output file, then displays it and offers a small menu.

Usage:
    python3 a_maze_ing.py config.txt
"""

import sys
import time

from config_parser import ConfigError, MazeConfig, parse_config
from mazegen import E, N, S, W, Dictype, MazeError, MazeGenerator

# How long each frame of the path reveal stays on screen, in seconds.
ANIMATION_DELAY = 0.05

RESET = "\033[0m"

# Alternate screen buffer, the one `vim` and `less` draw into. Entering
# it hands over a blank screen; leaving it puts the previous content
# back untouched, so an animation never pollutes the scrollback.
ALT_SCREEN_ON = "\033[?1049h"
ALT_SCREEN_OFF = "\033[?1049l"

# Cursor Home: moves to the top-left corner. Being an absolute move,
# it needs no line counting and cannot drift, unlike Cursor Up.
CURSOR_HOME = "\033[H"

# Hiding the cursor while redrawing stops it from flickering across
# the frame as it is being painted.
CURSOR_HIDE = "\033[?25l"
CURSOR_SHOW = "\033[?25h"

# Redrawing in place overwrites, it does not clear: a line shorter
# than the one it replaces would leave the tail of the old one behind.
# ERASE_LINE wipes from the cursor to the end of its line, ERASE_BELOW
# from the cursor to the bottom of the screen.
ERASE_LINE = "\033[K"
ERASE_BELOW = "\033[J"

# Solid block: walls, pattern and path are all drawn with it, only
# the colour telling them apart.
BLOCK = "█"

THEME_RED = {
    "wall":  "\033[38;2;178;34;34m",    # firebrick, deep red
    "logo":  "\033[38;2;255;140;0m",    # golden orange, warm contrast
    "path":  "\033[38;2;255;99;71m",    # tomato, light coral
    "entry": "\033[38;2;50;205;50m",    # lime green
    "exit":  "\033[38;2;255;0;0m",      # bright red
}

THEME_GREEN = {
    "wall":  "\033[38;2;34;139;34m",    # forest green
    "logo":  "\033[38;2;255;215;0m",    # gold
    "path":  "\033[38;2;144;238;144m",  # light green
    "entry": "\033[38;2;0;255;127m",    # spring green
    "exit":  "\033[38;2;220;20;60m",    # crimson
}

THEME_BLUE = {
    "wall":  "\033[38;2;70;130;180m",   # steel blue
    "logo":  "\033[38;2;255;215;0m",    # gold
    "path":  "\033[38;2;135;206;235m",  # sky blue
    "entry": "\033[38;2;50;205;50m",    # lime green
    "exit":  "\033[38;2;255;69;0m",     # orange red
}

THEME_YELLOW = {
    "wall":  "\033[38;2;218;165;32m",   # goldenrod
    "logo":  "\033[38;2;184;134;11m",   # dark gold
    "path":  "\033[38;2;215;215;214m",  # pale yellow
    "entry": "\033[38;2;50;205;50m",    # lime green
    "exit":  "\033[38;2;220;20;60m",    # crimson
}

THEME_BLACK = {
    "wall":  "\033[38;2;0;0;0m",   # black
    "logo":  "\033[38;2;184;134;11m",   # dark gold
    "path":  "\033[38;2;255;255;255m",  # white
    "entry": "\033[38;2;50;205;50m",    # lime green
    "exit":  "\033[38;2;220;20;60m",    # crimson
}

THEMES = [THEME_BLACK, THEME_RED, THEME_GREEN, THEME_BLUE, THEME_YELLOW]

MENU = """
=== A-Maze-ing ===
1. Re-generate a new maze
2. Show / Hide the shortest path
3. Rotate the wall colours
4. Quit"""


def colors(txt: str, color: str) -> str:
    """Wraps a single character in an ANSI colour.

    The character is wrapped, never the whole line.

    Args:
        txt: The character to paint.
        color: The ANSI escape sequence opening the colour.

    Returns:
        The character, painted then reset.
    """
    return f"{color}{txt}{RESET}"


def render_corner(grid: list[list[Dictype]]) -> list[list[bool]]:
    """Works out which wall corners have to be filled in.

    A corner is painted as soon as one of its four touching walls is
    closed, so neighbouring walls read as one continuous line.

    Args:
        grid: The maze grid.

    Returns:
        A table of `height + 1` rows of `width + 1` booleans, True
        standing for a corner to paint.
    """
    height = len(grid)
    width = len(grid[0])
    corners: list[list[bool]] = []
    for r in range(height + 1):
        row: list[bool] = []
        for c in range(width + 1):
            above = False
            if r > 0:
                if c < width:
                    above = bool(grid[r - 1][c]["wall"] & W)
                else:
                    above = bool(grid[r - 1][width - 1]["wall"] & E)

            below = False
            if r < height:
                if c < width:
                    below = bool(grid[r][c]["wall"] & W)
                else:
                    below = bool(grid[r][width - 1]["wall"] & E)

            left = False
            if c > 0:
                if r < height:
                    left = bool(grid[r][c - 1]["wall"] & N)
                else:
                    left = bool(grid[height - 1][c - 1]["wall"] & S)

            right = False
            if c < width:
                if r < height:
                    right = bool(grid[r][c]["wall"] & N)
                else:
                    right = bool(grid[height - 1][c]["wall"] & S)

            row.append(above or below or left or right)
        corners.append(row)
    return corners


def all_logo(
    grid: list[list[Dictype]],
    cells: tuple[tuple[int, int], ...],
) -> bool:
    """Tells whether every listed cell belongs to the "42" pattern.

    A wall or corner is shared by several cells, so it only takes the
    pattern's colour when all of them belong to it, keeping the colour
    from bleeding into the maze around it. A cell outside the grid
    never counts as part of the pattern.

    Args:
        grid: The maze grid.
        cells: The cells touching one character, as `(y, x)` pairs.

    Returns:
        True if all of them exist and carry the pattern.
    """
    height = len(grid)
    width = len(grid[0])
    for y, x in cells:
        if not (0 <= y < height and 0 <= x < width):
            return False
        if not grid[y][x]["logo"]:
            return False
    return True


def can_you_see_me(
    maze: MazeGenerator,
    corners: list[list[bool]],
    theme: dict[str, str],
) -> None:
    """Prints the maze to the console, line by line.

    Each cell is 2 characters wide and 2 lines tall, room enough for
    its shared walls. Drawing priority: entry/exit, then the "42"
    pattern, then walls, then the path, so the path never hides a
    wall. The path is also painted on open joints so it reads as a
    corridor rather than a dotted line.

    Args:
        maze: The generated maze.
        corners: The corner table from `render_corner()`.
        theme: The colours to paint with.
    """
    grid = maze.grid
    width = len(grid[0])
    wall_block = colors(BLOCK, theme["wall"])
    logo_block = colors(BLOCK, theme["logo"])

    def corner(r: int, c: int) -> str:
        """Picks the colour of a single corner post."""
        if not corners[r][c]:
            return " "
        touching = ((r - 1, c - 1), (r - 1, c), (r, c - 1), (r, c))
        return logo_block if all_logo(grid, touching) else wall_block

    line = ""
    for c, cell in enumerate(grid[0]):
        line += corner(0, c)
        line += wall_block if cell["wall"] & N else " "
    line += corner(0, width)
    print(line)

    for row_idx, row in enumerate(grid):
        floor = ""
        for c, cell in enumerate(row):
            if (row_idx, c) == maze.entry:
                floor += colors("X", theme["entry"])
            elif (row_idx, c) == maze.exit:
                floor += colors("X", theme["exit"])
            elif cell["wall"] & W:
                touching = ((row_idx, c - 1), (row_idx, c))
                floor += (logo_block if all_logo(grid, touching)
                          else wall_block)
            elif cell["path"]:
                floor += colors(BLOCK, theme["path"])
            else:
                floor += " "
            if cell["logo"]:
                floor += logo_block
            elif cell["path"]:
                floor += colors(BLOCK, theme["path"])
            else:
                floor += " "
        floor += wall_block if row[-1]["wall"] & E else " "
        print(floor)

        r = row_idx + 1
        wall = ""
        for c, cell in enumerate(row):
            wall += corner(r, c)
            below_on_path = r < len(grid) and grid[r][c]["path"]
            if cell["wall"] & S:
                touching = ((row_idx, c), (row_idx + 1, c))
                wall += (logo_block if all_logo(grid, touching)
                         else wall_block)
            elif cell["path"] and below_on_path:
                wall += colors(BLOCK, theme["path"])
            else:
                wall += " "
        wall += corner(r, width)
        print(wall)


def write_maze_file(maze: MazeGenerator, path: str) -> None:
    """Writes the maze to the output file (subject IV.5).

    One hex digit per cell, one row per line, then a blank line and
    three more: entry, exit, and the shortest path spelled N/E/S/W.
    Coordinates are written back as `x,y`, mirroring the config
    parser's swap on the way in.

    Args:
        maze: The generated maze.
        path: Name of the file to write.

    Raises:
        MazeError: If the file cannot be written, or if the maze holds
            no solution.
    """
    entry_y, entry_x = maze.entry
    exit_y, exit_x = maze.exit
    lines = maze.to_hex()
    lines.append("")
    lines.append(f"{entry_x},{entry_y}")
    lines.append(f"{exit_x},{exit_y}")
    lines.append(maze.solution_letters)
    try:
        with open(path, "w", encoding="utf-8") as output:
            for line in lines:
                output.write(f"{line}\n")
    except OSError as err:
        raise MazeError(
            f"cannot write '{path}': {err.strerror}"
        ) from err


def mark_path(maze: MazeGenerator, shown: bool) -> None:
    """Flags, or unflags, the cells of the solution path.

    Args:
        maze: The solved maze.
        shown: True to light the path up, False to clear it.
    """
    for y, x in maze.solved():
        maze.grid[y][x]["path"] = shown


def draw_screen(
    maze: MazeGenerator,
    corners: list[list[bool]],
    theme: dict[str, str],
) -> None:
    """Redraws the whole screen in place, from its top-left corner.

    Moving the cursor home first means every frame lands on the same
    rows instead of piling up below the previous one. `ERASE_BELOW`
    wipes the answer typed on the previous turn.

    Args:
        maze: The maze to display.
        corners: The corner table from `render_corner()`.
        theme: The colours to paint with.
    """
    print(CURSOR_HOME, end="")
    can_you_see_me(maze, corners, theme)
    print(MENU)
    print(ERASE_BELOW, end="")


def animate_path(
    maze: MazeGenerator,
    corners: list[list[bool]],
    theme: dict[str, str],
) -> None:
    """Reveals the solution path one cell at a time, exit to entry.

    Lights up a cell, redraws, waits one frame, repeats. The cursor is
    hidden for the duration to avoid flicker, and shown again whatever
    happens, Ctrl-C included.

    Args:
        maze: The solved maze.
        corners: The corner table from `render_corner()`.
        theme: The colours to paint with.
    """
    print(CURSOR_HIDE, end="")
    try:
        for y, x in reversed(maze.solved()):
            maze.grid[y][x]["path"] = True
            draw_screen(maze, corners, theme)
            sys.stdout.flush()
            time.sleep(ANIMATION_DELAY)
    finally:
        print(CURSOR_SHOW, end="")


def new_maze(config: MazeConfig) -> MazeGenerator:
    """Builds a maze from a configuration and saves it.

    Args:
        config: The validated configuration.

    Returns:
        The freshly generated maze.

    Raises:
        MazeError: If the maze cannot be solved or saved.
        ValueError: If the configuration describes an impossible maze.
    """
    maze = MazeGenerator(
        width=config.width,
        height=config.height,
        entry=config.entry,
        exit=config.exit,
        perfect=config.perfect,
        seed=config.seed,
    )
    maze.generate()
    write_maze_file(maze, config.output_file)
    return maze


def ask_choice() -> int:
    """Reads the user's pick.

    Returns:
        The number picked, or 4 to quit when the input stream closes.
        Anything unreadable returns 0, which no entry matches.
    """
    try:
        return int(input("Choice? (1-4): "))
    except ValueError:
        return 0
    except (EOFError, KeyboardInterrupt):
        print()
        return 4


def main() -> None:
    """Runs the generator, then loops on the user menu."""
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} config.txt")
        return
    try:
        config = parse_config(sys.argv[1])
        maze = new_maze(config)
    except (ConfigError, MazeError, ValueError) as err:
        print(f"Error: {err}")
        return

    theme_idx = 0
    theme = THEMES[theme_idx]
    path_shown = False
    corners = render_corner(maze.grid)

    # The alternate screen is entered only now, once the configuration
    # has been read and the maze built: an error raised above must stay
    # readable on the normal screen, which leaving the buffer would
    # otherwise wipe along with everything else drawn on it.
    print(ALT_SCREEN_ON, end="")
    try:
        while True:
            draw_screen(maze, corners, theme)
            choice = ask_choice()
            try:
                match choice:
                    case 1:
                        maze = new_maze(config)
                        path_shown = False
                        corners = render_corner(maze.grid)
                    case 2:
                        path_shown = not path_shown
                        if path_shown:
                            animate_path(maze, corners, theme)
                        else:
                            mark_path(maze, False)
                    case 3:
                        theme_idx = (theme_idx + 1) % len(THEMES)
                        theme = THEMES[theme_idx]
                    case 4:
                        return
                    case _:
                        pass
            except (MazeError, ValueError):
                pass
    finally:
        # Reached by the `return` above, by Ctrl-C, and by any error
        # left unhandled: the buffer is always given back, so the user
        # never lands in a terminal missing its history or its cursor.
        print(CURSOR_SHOW + ALT_SCREEN_OFF, end="")
        sys.stdout.flush()


if __name__ == "__main__":
    # Ctrl-C is caught here rather than around every call able to run
    # for a while: a single guard at the entry point covers parsing,
    # generation, rendering and the path animation alike, and keeps
    # `main()` free of a concern that is not its own. Whatever was
    # running has already unwound its own `finally` by the time the
    # interrupt reaches this point, so the alternate screen is left
    # and the cursor is back before anything is printed.
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
