#!/usr/bin/env python3
from typing import TypedDict
import random


## 1 = 0001, 2 = 0010, 4 = 0100, 8 = 1000 15 = 1111 (Tous ferme)

N, S, E, W = 1, 2, 4, 8

OPPOSITE = {N: S, S: N, E: W, W: E}

DELTA = {N: (0, -1), S: (0, 1), E: (-1, 0), W: (1, 0)}

        ## (X,Y) 


DIRECTIONS = [N, S, E, W]

AXE_Y = 10
AXE_X = 10
TOTAL = AXE_Y + AXE_X


class Dictype(TypedDict):
    wall: int
    visited: bool
    color: tuple[int,int,int]





def the_architect(grid: list[list[Dictype]]) -> None:

    tries = 4
    grid[0][0]["visited"] = True
    stack: list[tuple[int,int]] = [(0,0)]

    while stack:
        row, col = stack[-1]
        d = random.choice(DIRECTIONS)
        nc = col + DELTA[d][0]
        nr = row + DELTA[d][1]
        if nr >= 0 and nr < AXE_Y and nc >= 0 and nc < AXE_X:
            if grid[nr][nc]["visited"] is not True:
                grid[nr][nc]["color"] = (100, 100, 100)
                grid[nr][nc]["visited"] = True
                grid[row][col]["wall"] &= ~d 
                grid[nr][nc]["wall"] &= ~OPPOSITE[d]
                stack.append((nr, nc))
                tries = 4
            else:
                tries -= 1
        if tries <= 0:
            stack.pop(-1)
            tries = 4

    ## A la fin du wild on declenche un animation pour signer que le maze est pret
    ## Ou un text like "Letgo"


def can_you_see_me(grid: list[list[Dictype]]) -> None:

    line = "*"
    for col in grid[0]:
        line += "-"
    line += "*" 
    print(f"{line}")

    for row in grid:
        line = ""
        for cell in row:
            if cell["wall"] & S:
                line += "-"
            else:
                line += " "
        print(f"{line}\n")
        for cell in row:
            if cell["wall"] & W:
                line += "|"
            if cell["wall"] & E:
                line += "|"
            else:
                line += " "
        print(f"{line}")






    




def generate_grid() -> list[list[Dictype]]:

    # if TOTAL <= 3:
    #     raise

    grid: list[list[Dictype]] = [[{"wall": 15, "visited": False, "color": (0,0,0)} for _ in range(AXE_X)] 
            for _ in range(AXE_Y)]
    return grid


def main() -> None:
    
    grid = generate_grid()
    the_architect(grid)
    can_you_see_me(grid)
    


if __name__ == "__main__":
    main()


