#!/usr/bin/env python3
"""Reading, conversion and validation of the configuration file.

The file follows the `KEY=VALUE` format, one pair per line (subject
IV.3). Blank lines and lines starting with '#' are ignored. Unknown
keys are accepted then ignored, the subject allowing extra keys to be
added.
"""

import sys
from dataclasses import dataclass

# Keys the subject (IV.3) requires the file to carry.
REQUIRED_KEYS = frozenset({
    "WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT",
})

# Below 3x3 the Pac-Man mode makes no sense: the four corners and the
# centre must be distinct cells (subject IV.4).
MIN_SIDE = 3

# Values accepted for PERFECT, compared in lower case.
TRUE_VALUES = frozenset({"true", "1", "yes", "on"})
FALSE_VALUES = frozenset({"false", "0", "no", "off"})


class ConfigError(Exception):
    """Raised when the configuration file cannot be used."""


@dataclass
class MazeConfig:
    """Validated configuration, ready for the generator to use.

    Attributes:
        width: Maze width, in cells (X axis, columns).
        height: Maze height, in cells (Y axis, rows).
        entry: Entry cell, in the internal `(y, x)` form.
        exit: Exit cell, in the internal `(y, x)` form.
        output_file: Path of the hexadecimal output file.
        perfect: True for a perfect maze, False for a playable
            Pac-Man style board.
        seed: Random seed, or None for a different maze on every run.
    """

    width: int
    height: int
    entry: tuple[int, int]
    exit: tuple[int, int]
    output_file: str
    perfect: bool
    seed: int | None


def read_pairs(path: str) -> dict[str, str]:
    """Reads the file and returns its raw KEY=VALUE pairs.

    Args:
        path: Path of the configuration file.

    Returns:
        The pairs read, values neither converted nor validated. Should
        a key appear twice, the last occurrence wins.

    Raises:
        ConfigError: If the file cannot be read, or if a line is
            neither blank, nor a comment, nor a valid pair.
    """
    pairs: dict[str, str] = {}
    try:
        with open(path, encoding="utf-8") as config_file:
            for number, line in enumerate(config_file, start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if "=" not in stripped:
                    raise ConfigError(
                        f"line {number}: '{stripped}' is not a "
                        f"KEY=VALUE pair"
                    )
                key, value = stripped.split("=", 1)
                pairs[key.strip()] = value.strip()
    except OSError as err:
        raise ConfigError(
            f"cannot read '{path}': {err.strerror}"
        ) from err
    except UnicodeDecodeError as err:
        raise ConfigError(
            f"'{path}' is not a valid text file"
        ) from err
    return pairs


def to_int(key: str, raw: str) -> int:
    """Converts a raw value into an integer.

    Args:
        key: Name of the key, used in the error message.
        raw: Raw value read from the file.

    Returns:
        The converted value.

    Raises:
        ConfigError: If the value is not an integer.
    """
    try:
        return int(raw)
    except ValueError as err:
        raise ConfigError(
            f"{key}: '{raw}' is not a whole number"
        ) from err


def to_bool(key: str, raw: str) -> bool:
    """Converts a raw value into a boolean.

    Args:
        key: Name of the key, used in the error message.
        raw: Raw value read from the file.

    Returns:
        The converted value.

    Raises:
        ConfigError: If the value is neither true nor false.
    """
    lowered = raw.lower()
    if lowered in TRUE_VALUES:
        return True
    if lowered in FALSE_VALUES:
        return False
    raise ConfigError(
        f"{key}: '{raw}' is neither true nor false "
        f"(expected True or False)"
    )


def to_cell(key: str, raw: str) -> tuple[int, int]:
    """Converts an 'x,y' coordinate into an internal `(y, x)` pair.

    The subject writes coordinates as `(x, y)` while the grid is
    indexed `grid[y][x]`. The swap happens here, once and for all, so
    that the rest of the program only ever knows one convention.

    Args:
        key: Name of the key, used in the error message.
        raw: Raw value read from the file, in 'x,y' form.

    Returns:
        The cell, in the internal `(y, x)` form.

    Raises:
        ConfigError: If the value is not two integers parted by a
            comma.
    """
    parts = raw.split(",")
    if len(parts) != 2:
        raise ConfigError(f"{key}: '{raw}' is not in x,y form")
    x = to_int(key, parts[0].strip())
    y = to_int(key, parts[1].strip())
    return (y, x)


def validate(config: MazeConfig) -> None:
    """Checks that the configuration describes a workable maze.

    Applies the three rules the subject states (IV.4) about entry and
    exit: they exist, they differ, and they fit inside the grid. No
    constraint on sitting along the border: entry and exit do not
    pierce the outer wall, they are plain cells that happen to be
    marked.

    Args:
        config: Converted configuration, not validated yet.

    Raises:
        ConfigError: If any of the rules is broken.
    """
    if config.width < MIN_SIDE or config.height < MIN_SIDE:
        raise ConfigError(
            f"WIDTH and HEIGHT must be at least {MIN_SIDE} "
            f"(got {config.width}x{config.height})"
        )
    if not config.output_file:
        raise ConfigError("OUTPUT_FILE cannot be empty")
    if config.entry == config.exit:
        raise ConfigError("ENTRY and EXIT point at the same cell")
    cells = (("ENTRY", config.entry), ("EXIT", config.exit))
    for key, (y, x) in cells:
        if not 0 <= x < config.width:
            raise ConfigError(
                f"{key}: x={x} lies out of bounds "
                f"(expected 0 to {config.width - 1})"
            )
        if not 0 <= y < config.height:
            raise ConfigError(
                f"{key}: y={y} lies out of bounds "
                f"(expected 0 to {config.height - 1})"
            )


def parse_config(path: str) -> MazeConfig:
    """Reads, converts and validates a configuration file.

    Args:
        path: Path of the configuration file.

    Returns:
        The validated configuration.

    Raises:
        ConfigError: If the file cannot be read, if a required key is
            missing, if a value is malformed, or if the maze described
            cannot be built.
    """
    pairs = read_pairs(path)
    missing = REQUIRED_KEYS - set(pairs)
    if missing:
        raise ConfigError(
            "missing required keys: " + ", ".join(sorted(missing))
        )
    raw_seed = pairs.get("SEED", "")
    config = MazeConfig(
        width=to_int("WIDTH", pairs["WIDTH"]),
        height=to_int("HEIGHT", pairs["HEIGHT"]),
        entry=to_cell("ENTRY", pairs["ENTRY"]),
        exit=to_cell("EXIT", pairs["EXIT"]),
        output_file=pairs["OUTPUT_FILE"],
        perfect=to_bool("PERFECT", pairs["PERFECT"]),
        seed=to_int("SEED", raw_seed) if raw_seed else None,
    )
    validate(config)
    return config


def main() -> None:
    """Prints the configuration given as argument, for testing."""
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} config.txt")
        return
    try:
        print(parse_config(sys.argv[1]))
    except ConfigError as err:
        print(f"Error: {err}")


if __name__ == "__main__":
    main()
