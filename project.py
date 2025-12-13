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

def dfs(maze, animate=False, delay=0.03):
    start, goal = maze.start, maze.goal
    stack = [start]
    visited = {start}
    came_from = {start: None}
    explored_order = []

    while stack:
        cur = stack.pop()
        explored_order.append(cur)

        if cur == goal:
            break

        for nb in maze.neighbors(cur):
            if nb not in visited:
                visited.add(nb)
                stack.append(nb)
                came_from[nb] = cur

        if animate:
            show_exploration(maze, explored_order, current=cur, algo_name="DFS")
            time.sleep(delay)

    return reconstruct_path(came_from, start, goal), explored_order


# --- Pretty printing helpers ---

def clear_screen():
    # Clear console (for animation)
    os.system("cls" if os.name == "nt" else "clear")


def color_cell(ch, is_path=False, is_start=False, is_goal=False, is_explored=False, is_current=False):
    """
    Map characters to pretty colored output.
    """
    if not COLOR_ENABLED:
        return ch

    # Walls
    if ch == "#":
        return Style.BRIGHT + Fore.WHITE + "█" + Style.RESET_ALL

    # Start & goal
    if is_start:
        return Style.BRIGHT + Fore.GREEN + "S" + Style.RESET_ALL
    if is_goal:
        return Style.BRIGHT + Fore.RED + "G" + Style.RESET_ALL

    # Path
    if is_path:
        return Style.BRIGHT + Fore.YELLOW + "•" + Style.RESET_ALL

    # Currently expanded node
    if is_current:
        return Style.BRIGHT + Fore.CYAN + "@" + Style.RESET_ALL

    # Explored but not on final path
    if is_explored:
        return Fore.BLUE + "·" + Style.RESET_ALL

    # Normal free cell
    if ch == ".":
        return " "

    return ch


def print_maze_pretty(maze, path=None, explored=None, current=None, frame_title=None):
    """
    Print maze with optional path and exploration coloring.
    """
    if explored is None:
        explored = set()
    else:
        explored = set(explored)

    path = set(path) if path else set()

    if frame_title:
        print(frame_title)
        print("-" * len(frame_title))

    for r in range(maze.rows):
        row_str = []
        for c in range(maze.cols):
            pos = (r, c)
            ch = maze.grid[r][c]
            is_start = (pos == maze.start)
            is_goal = (pos == maze.goal)
            is_path = pos in path and not (is_start or is_goal)
            is_explored = pos in explored and not is_path and not is_start and not is_goal
            is_current = (current is not None and pos == current)

            row_str.append(color_cell(ch, is_path, is_start, is_goal, is_explored, is_current))
        print("".join(row_str))
    print()


def show_exploration(maze, explored_order, current, algo_name):
    clear_screen()
    print_maze_pretty(
        maze,
        path=None,
        explored=explored_order,
        current=current,
        frame_title=f"{algo_name} exploring..."
    )


def mark_path(maze, path):
    """
    Return a new maze grid (list of strings) with path marked as '*'.
    This is kept as a non-colored, simple version for logs if needed.
    """
    grid = [list(row) for row in maze.grid]
    if path is None:
        return ["".join(row) for row in grid]

    for (r, c) in path:
        if grid[r][c] not in ("S", "G", "#"):
            grid[r][c] = "*"

    return ["".join(row) for row in grid]

# --- Default maze ---

DEFAULT_MAZE = [
    "###########",
    "#S..#....G#",
    "#.#.#.##..#",
    "#.#...#...#",
    "#.#####.#.#",
    "#.......#.#",
    "###########",
]


def load_maze_from_file(path):
    with open(path, "r") as f:
        lines = [line.rstrip("\n") for line in f if line.strip("\n")]

    if len(set(len(line) for line in lines)) != 1:
        raise ValueError("All rows in the maze file must have the same length.")

    return lines


def main():
    parser = argparse.ArgumentParser(description="Maze solver using BFS and DFS (pretty visual version).")
    parser.add_argument(
        "--algo",
        choices=["bfs", "dfs", "both"],
        default="both",
        help="Which algorithm to run (default: both)."
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to a text file containing the maze."
    )
    parser.add_argument(
        "--animate",
        action="store_true",
        help="Animate the exploration process step-by-step."
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.03,
        help="Delay between animation frames in seconds (default: 0.03)."
    )
    args = parser.parse_args()

    # Load maze
    if args.file:
        if not os.path.exists(args.file):
            print(f"File not found: {args.file}")
            sys.exit(1)
        grid = load_maze_from_file(args.file)
    else:
        grid = DEFAULT_MAZE

    maze = Maze(grid)

    clear_screen()
    print("Original maze:")
    print_maze_pretty(maze)
    time.sleep(0.5)

    # BFS
    if args.algo in ("bfs", "both"):
        if args.animate:
            clear_screen()
        print("=== BFS ===")
        path_bfs, explored_bfs = bfs(maze, animate=args.animate, delay=args.delay)
        if args.animate:
            clear_screen()
        if path_bfs is None:
            print("No path found by BFS.")
        else:
            print(f"BFS path length (number of cells): {len(path_bfs)}")
            print_maze_pretty(maze, path=path_bfs, explored=explored_bfs, frame_title="BFS final path")
        input("Press Enter to continue...\n")

    # DFS
    if args.algo in ("dfs", "both"):
        if args.animate:
            clear_screen()
        print("=== DFS ===")
        path_dfs, explored_dfs = dfs(maze, animate=args.animate, delay=args.delay)
        if args.animate:
            clear_screen()
        if path_dfs is None:
            print("No path found by DFS.")
        else:
            print(f"DFS path length (number of cells): {len(path_dfs)}")
            print_maze_pretty(maze, path=path_dfs, explored=explored_dfs, frame_title="DFS final path")
        # No extra input if it's the last, but fine for showing during demo


if __name__ == "__main__":
    main()