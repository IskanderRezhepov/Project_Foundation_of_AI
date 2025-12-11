from collections import deque
import argparse
import os
import sys
import time

# --- Optional colors (using colorama if available) ---

try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)

    COLOR_ENABLED = True
except ImportError:
    # Fallback: no colors if colorama is not installed
    COLOR_ENABLED = False

    class Dummy:
        RESET_ALL = ""
    class DummyFore:
        RED = GREEN = YELLOW = CYAN = BLUE = MAGENTA = WHITE = ""
    class DummyStyle:
        BRIGHT = NORMAL = ""
    Fore = DummyFore()
    Style = DummyStyle()
    Style.RESET_ALL = ""


class Maze:
    """
    Maze representation.

    Symbols in the input:
        # = wall
        . = free cell
        S = start
        G = goal
    """

    def __init__(self, grid):
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0]) if self.rows > 0 else 0

        self.start = None
        self.goal = None

        for r in range(self.rows):
            for c in range(self.cols):
                if grid[r][c] == "S":
                    self.start = (r, c)
                elif grid[r][c] == "G":
                    self.goal = (r, c)

        if self.start is None or self.goal is None:
            raise ValueError("Maze must contain 'S' (start) and 'G' (goal)")

    def in_bounds(self, pos):
        r, c = pos
        return 0 <= r < self.rows and 0 <= c < self.cols

    def passable(self, pos):
        r, c = pos
        return self.grid[r][c] != "#"

    def neighbors(self, pos):
        r, c = pos
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            np = (nr, nc)
            if self.in_bounds(np) and self.passable(np):
                yield np


def reconstruct_path(came_from, start, goal):
    if goal not in came_from:
        return None
    cur = goal
    path = [cur]
    while cur != start:
        cur = came_from[cur]
        path.append(cur)
    path.reverse()
    return path


def bfs(maze, animate=False, delay=0.03):
    start, goal = maze.start, maze.goal
    frontier = deque([start])
    visited = {start}
    came_from = {start: None}

    # For optional animation, keep track of exploration
    explored_order = []

    while frontier:
        cur = frontier.popleft()
        explored_order.append(cur)

        if cur == goal:
            break

        for nb in maze.neighbors(cur):
            if nb not in visited:
                visited.add(nb)
                frontier.append(nb)
                came_from[nb] = cur

        if animate:
            show_exploration(maze, explored_order, current=cur, algo_name="BFS")
            time.sleep(delay)

    return reconstruct_path(came_from, start, goal), explored_order

