#!/usr/bin/env python3
from typing import TypedDict
import random


## 1 = 0001, 2 = 0010, 4 = 0100, 8 = 1000 15 = 1111 (Tous ferme)

N, E, S, W = 1, 2, 4, 8

OPPOSITE = {N: S, S: N, E: W, W: E}

DELTA = {N: (0, -1), S: (0, 1), E: (1, 0), W: (-1, 0)}

        ## (X,Y) 


DIRECTIONS = [N, S, E, W]

AXE_Y = 30
AXE_X = 45
TOTAL = AXE_Y + AXE_X

PATTERN_42 = [
    [1, 0, 1, 0, 1, 1, 1],
    [1, 0, 1, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 1],
    [0, 0, 1, 0, 1, 0, 0],
    [0, 0, 1, 0, 1, 1, 1]
]


class Dictype(TypedDict):
    wall: int
    visited: bool
    color: list[int]
    logo: bool



def build_logo_42() -> list[tuple[int, int]]:

    heigh_logo = len(PATTERN_42) #4
    larg_logo = len(PATTERN_42[0]) # 6
    center_axe_y = heigh_logo//2 # 2
    center_axe_x = larg_logo//2 # 3
    coord_logo: list[tuple[int,int]] = []

    for i, line in enumerate(PATTERN_42):
        for j, data in enumerate(line):
            if data == 1:
                y_pos = i - center_axe_y
                x_pos = j - center_axe_x
                coord_logo.append((y_pos, x_pos))
    return coord_logo


def scale_logo() -> int:
    
    ratio: float = 0.12
    max_logo_size: float = ratio*AXE_X*AXE_Y
    heigh_logo = len(PATTERN_42) #4
    larg_logo = len(PATTERN_42[0]) # 6
    
    logo_position: list[tuple[int,int]] = build_logo_42()
    logo_len = len(logo_position)

    scale = 1
    max_scale = 0

    while True:
        new_larg = larg_logo * scale
        new_h = heigh_logo * scale
        if new_larg > AXE_X or new_h > AXE_Y:
            break
        new_logo_scale = logo_len*scale**2
        if new_logo_scale > max_logo_size:
            break
        max_scale = scale
        scale += 1

    if max_scale >= 4:
        max_scale = 3

    return max_scale

def i_m_logo(grid) -> None:
    
    scale: int = scale_logo()
    if scale == 0:
        return None
    center_row = AXE_Y//2
    center_col = AXE_X//2
    logo_coords: list[tuple[int,int]] = build_logo_42()
    center = scale//2

    for y_row, x_col in logo_coords:
        row = center_row + y_row * scale - center 
        col = center_col + x_col * scale - center 

        for y in range(scale):
            for x in range(scale):
                s_row = row + y
                s_col = col + x
                if 0 <= s_row < AXE_Y and 0 <= s_col < AXE_X:
                    grid[s_row][s_col]["visited"] = True
                    grid[s_row][s_col]["logo"] = True



    

        '''En gros on part du centre et on va ajouter les coord de logo_coord, et multiruplu les coord
                 par scale pour els etendre si coord- 4,2 x 2 -> 8,4 


        '''






def the_architect(grid: list[list[Dictype]], imparfect: bool) -> None:

    tries = 4
    grid[0][0]["visited"] = True
    stack: list[tuple[int,int]] = [(0,0)]
    last_d: list[int] = []

    while stack:
        row, col = stack[-1]
        d = random.choice(DIRECTIONS)
        nc = col + DELTA[d][0]
        nr = row + DELTA[d][1]
        if nr >= 0 and nr < AXE_Y and nc >= 0 and nc < AXE_X:
            if grid[nr][nc]["visited"] is not True:
                grid[nr][nc]["color"] = [100, 100, 100]
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

    # if imparfect:
    #     for row in range(AXE_Y):
    #         for col in range(AXE_X):
    #             if grid[row][col]["wall"].bit_count() == 3:
                        


  
    ## A la fin du wild on declenche un animation pour signer que le maze est pret
    ## Ou un text like "Letgo"

    ## safe_d = []
    ## sd.append(d)
    ## if d in sd  choose an other directions
    ## sd.pop(-1)
    ## pour eviter de choisir 2 fois de suite la meme direction 


def can_you_see_me(grid: list[list[Dictype]]) -> None:

    line = ""

    for cell in grid[0]:
        line += "+"
        if cell["wall"] & N:
            line += "-"
        else:
            line += " "
    line += "+" 
    print(f"{line}")

    for row in grid:
        floor = ""
        for cell in row:
            if cell["logo"] == True:
                floor += "#"
            elif cell["wall"] & W:
                floor += "|"
            else:
                floor += " "
            floor += " "
        if row[-1]["wall"] & E:
            floor += "|" 
        else:
            floor += " "
        print(f"{floor}")

        wall = "" 
        for cell in row:
            wall += "+"
            if cell["logo"] == True:
                wall += "#"
            elif cell["wall"] & S:
                wall += "-"
            else:
                wall += " "
        wall += "+"
        print(f"{wall}")


## A reecrir avec line += "+" if ... else " "


def generate_grid() -> list[list[Dictype]]:

    # if TOTAL <= 3:
    #     raise

    grid: list[list[Dictype]] = [[
        {"wall": 15, "visited": False, "color": [0,0,0], "logo": False} for _ in range(AXE_X)] 
            for _ in range(AXE_Y)]
    return grid








def main() -> None:
    
    grid = generate_grid()
    i_m_logo(grid)
    imparfect = False
    the_architect(grid, imparfect)
    can_you_see_me(grid)
    while True:
        print("=== A-Maze-ing ===")
        print("1. Re-generate a new maze")
        print("2. Show / Hide the shortest path")
        print("3. Rotate the wall colours")
        print("4. Quit")
        user_input: int = int(input("Make you choice: "))
        match user_input:
            case 1:
                grid = generate_grid()
                the_architect(grid, imparfect)
            case 2:
                pass
            case 3:
                pass
            case 4:
                break
            case _:
                pass


''' 

J ai un maze, une grille avec des index. Je dois parcourir chaque combinaisons d index et faire un check sur wall pour decider si j ouvre un autre cote.

 [0][0]
 je check quel mur est ouvert et est un cul de sacvet ouvre un autre mur ou pas en fonction du retour de random.
 et j applique le changement pour les exterieur conditon si y[0]
 quand x vaut 0 et y 0 a x ou quand y vaut tjs 0 et x de 0 ou a la AVE_X (colone) ou AXE_Y (Ligne)
 donc x vaut 0 ou AXE_X et Y vaut 0 ou AXE_Y
    il faut donc comparer cette valeur mais comme on utilise range on l a deja.

    juste a parcourir la liste, et comment retirer une direction pour les exte.
    Surement une comparaison comme on a les bits 
    genre if d == N or if d == E avec la bonne combinaison d index.

    for y in rangerow
        for x in rangecol
        if grid[y][x]["wall"].bit_count(1) == 3
            d = random.choix(direction)
            if y == 0 or y == AXE_Y


Avant d ouvrure les murs passer les case ddu logo en visited = true que logo les saute via le if

CALCULE DES CASES DU CENTRE:

    AXE_X / 2  // comment ca fonctionne is nombre impaire ? Float a utiliser ?
    AXE_Y / 2
    En gros 8/2=4 x = 4 On est dans la case au ceentre de la grille
            6/2=3 y = 3

'''
    


if __name__ == "__main__":
    main()

