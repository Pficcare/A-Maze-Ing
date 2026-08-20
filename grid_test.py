#!/usr/bin/env python3
from typing import TypedDict 
import random
import sys
import time
from collections import deque
from collections.abc import Iterator


## 1 = 0001, 2 = 0010, 4 = 0100, 8 = 1000 15 = 1111 (Tous ferme)

N, E, S, W = 1, 2, 4, 8

OPPOSITE = {N: S, S: N, E: W, W: E}

DELTA = {N: (0, -1), S: (0, 1), E: (1, 0), W: (-1, 0)}

        ## (X,Y) 


DIRECTIONS = [N, S, E, W]

AXE_Y = 20
AXE_X = 35
TOTAL = AXE_Y + AXE_X

PATTERN_42 = [
    [1, 0, 1, 0, 1, 1, 1],
    [1, 0, 1, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 1],
    [0, 0, 1, 0, 1, 0, 0],
    [0, 0, 1, 0, 1, 1, 1]
]

ENTRY: tuple[int,int] = (0,0)
EXIT: tuple[int,int] = (AXE_Y-2, AXE_X-2)





class Dictype(TypedDict):
    wall: int
    visited: bool
    color: list[int]
    logo: bool
    path: bool

RESET = "\033[0m"

THEME_ROUGE = {
    "wall":  "\033[38;2;178;34;34m",    # firebrick, rouge profond
    "logo":  "\033[38;2;255;140;0m",    # orange doré, contraste chaud
    "path":  "\033[38;2;255;99;71m",    # tomato, corail clair
    "entry": "\033[38;2;50;205;50m",    # vert lime
    "exit":  "\033[38;2;255;0;0m",      # rouge vif, se détache du mur plus sombre
}

THEME_VERT = {
    "wall":  "\033[38;2;34;139;34m",    # forest green
    "logo":  "\033[38;2;255;215;0m",    # or
    "path":  "\033[38;2;144;238;144m",  # vert clair
    "entry": "\033[38;2;0;255;127m",    # spring green
    "exit":  "\033[38;2;220;20;60m",    # crimson
}

THEME_BLEU = {
    "wall":  "\033[38;2;70;130;180m",   # steel blue
    "logo":  "\033[38;2;255;215;0m",    # or
    "path":  "\033[38;2;135;206;235m",  # sky blue
    "entry": "\033[38;2;50;205;50m",    # vert lime
    "exit":  "\033[38;2;255;69;0m",     # rouge-orangé
}

THEME_JAUNE = {
    "wall":  "\033[38;2;218;165;32m",   # goldenrod
    "logo":  "\033[38;2;184;134;11m",   # or foncé, contraste sur fond clair
    "path":  "\033[38;2;255;255;224m",  # jaune pâle
    "entry": "\033[38;2;50;205;50m",    # vert lime
    "exit":  "\033[38;2;220;20;60m",    # crimson
}

THEMES = [THEME_ROUGE, THEME_VERT, THEME_BLEU, THEME_JAUNE]




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
        print("The '42' pattern cannot be display size of grid to small.")
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


def you_cannot_hide(grid: list[list[Dictype]]) -> dict:

   
    path: dict = {ENTRY: None}
    next_move = deque([ENTRY])

    while True:
        y,x = next_move.popleft()
        if (y,x) == EXIT:
            break
        for d in DIRECTIONS:
            if not grid[y][x]["wall"] & d:
                nx = x + DELTA[d][0]
                ny = y + DELTA[d][1]
                if (ny, nx) not in path:
                    path[(ny,nx)] = (y, x)
                    next_move.append((ny,nx))
    return path



def solved(path:dict, grid: list[list[Dictype]]) -> Iterator[None]:
    
    '''acceder a exit key, recup ses valeurs les utiliser sur grid, changer les variables,
        utiliser cest nouvelle valeur comme key pour recup les nouvelles coord etc until None

    '''

    curr = EXIT

    while curr != None:
        y,x = curr
        grid[y][x]["path"] = True
        grid[y][x]["color"] = [20,20,20]
        yield
        curr = path[curr]
    



def the_architect(grid: list[list[Dictype]]) -> None:

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


def imperfection(grid) -> None:


    '''On doit parcourir chaque case et test tous les directions pour trouver les murs fermer
        stockr les dir vvalide dans une liste et les mur ouvert

    '''
    close_wall: list = []

    for y in range(1, AXE_Y-1):
        for x in range(1, AXE_X-1):
            if grid[y][x]["wall"].bit_count() == 3:
                close_wall = [d for d in DIRECTIONS if grid[y][x]["wall"] & d]
                d = random.choice(close_wall)
                nx = x + DELTA[d][0]
                ny = y + DELTA[d][1]
                if grid[ny][nx]["logo"] is not True:
                    grid[y][x]["wall"] &= ~d
                    grid[ny][nx]["wall"] &= ~OPPOSITE[d] 
    


    pass

def can_you_see_me(grid: list[list[Dictype]], corners: list[list[bool]], theme: dict) -> None:

    line = ""
    for c, cell in enumerate(grid[0]):
        line += colors("█", theme["wall"]) if corners[0][c] else " "
        if cell["wall"] & N:
            line += colors("█", theme["wall"])
        else:
            line += " "
    line += colors("█", theme["wall"]) if corners[0][AXE_X] else " "
    print(f"{line}")

    for row_idx, row in enumerate(grid):
        floor = ""
        for c, cell in enumerate(row):
            if (row_idx, c) == ENTRY:
                floor += colors("X", theme["entry"])
            elif (row_idx, c) == EXIT:
                floor += colors("X", theme["exit"])
            elif cell["logo"] == True:
                floor += colors("█", theme["logo"])
            elif cell["wall"] & W:
                floor += colors("█", theme["wall"])
            else:
                floor += " "
            if cell["path"] == True:
                floor += colors("█", theme["path"])
            else:
                floor += " "
        if row[-1]["wall"] & E:
            floor += colors("█", theme["wall"])
        else:
            floor += " "
        print(f"{floor}")

        r = row_idx + 1
        wall = ""
        for c, cell in enumerate(row):
            wall += colors("█", theme["wall"]) if corners[r][c] else " "
            if cell["logo"] == True:
                wall += colors("█", theme["logo"])
            elif cell["wall"] & S:
                wall += colors("█", theme["wall"])
            else:
                wall += " "
        wall += colors("█", theme["wall"]) if corners[r][AXE_X] else " "
        print(f"{wall}")


def render_corner(grid: list[list[Dictype]]) -> list[list[bool]]:


    corners: list[list[bool]] = []

    for r in range(AXE_Y + 1):
        row: list[bool] = []
        for c in range(AXE_X + 1):

            haut = False
            if r > 0:
                if c < AXE_X:
                    haut = bool(grid[r-1][c]["wall"] & W)
                else:
                    haut = bool(grid[r-1][AXE_X-1]["wall"] & E)

            bas = False
            if r < AXE_Y:
                if c < AXE_X:
                    bas = bool(grid[r][c]["wall"] & W)
                else:
                    bas = bool(grid[r][AXE_X-1]["wall"] & E)

            gauche = False
            if c > 0:
                if r < AXE_Y:
                    gauche = bool(grid[r][c-1]["wall"] & N)
                else:
                    gauche = bool(grid[AXE_Y-1][c-1]["wall"] & S)

            droite = False
            if c < AXE_X:
                if r < AXE_Y:
                    droite = bool(grid[r][c]["wall"] & N)
                else:
                    droite = bool(grid[AXE_Y-1][c]["wall"] & S)

            row.append(haut or bas or gauche or droite)
        corners.append(row)

    return corners


def generate_grid() -> list[list[Dictype]]:

    if TOTAL < 9:
        print("Error size to small")

    grid: list[list[Dictype]] = [[
        {"wall": 15, 
         "visited": False, 
         "color": [0,0,0], 
         "logo": False, 
         "path": False} for _ in range(AXE_X)] 
            for _ in range(AXE_Y)]
    return grid



def colors(txt: str, color: str) -> str:
    return f"{color}{txt}{RESET}"



def main() -> None:
    
    curr_tidx = 0
    theme = THEMES[curr_tidx]

    imperect = False

    grid = generate_grid()
    i_m_logo(grid)
    the_architect(grid)
    if imperect is True:
        imperfection(grid)
    corners = render_corner(grid)
    can_you_see_me(grid, corners, theme)

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
                i_m_logo(grid)
                the_architect(grid)
                if imperect is True:
                    imperfection(grid)
                    corners = render_corner(grid)
                can_you_see_me(grid, corners, theme)
            case 2:
                path = you_cannot_hide(grid)
                for _ in solved(path, grid):
                    print(f"\033[{2*AXE_Y+1}A", end="")
                    can_you_see_me(grid, corners, theme)
                    sys.stdout.flush()
                    time.sleep(0.05)
            case 3:
                curr_tidx = (curr_tidx + 1) % len(THEMES)
                theme = THEMES[curr_tidx]
                can_you_see_me(grid, corners, theme)
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

