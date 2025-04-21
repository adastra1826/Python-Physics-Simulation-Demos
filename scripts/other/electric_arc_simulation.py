import pygame
import numpy as np
import random
from collections import deque

# Window dimensions
WIDTH, HEIGHT = 800, 600

# Colors for display
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)       # Start point
GREEN = (0, 255, 0)     # Conductor
BLUE = (0, 0, 255)      # End point
GRAY = (150, 150, 150)  # Insulator
YELLOW = (255, 255, 0)  # Lightning path
ORANGE = (255, 165, 0)  # Lightning flicker

# Size of the simulation grid
GRID_SIZE = 50

class Simulation:
    def __init__(self):
        # Initialize the grid and element states
        self.grid = np.zeros((GRID_SIZE, GRID_SIZE))
        self.fixed = np.zeros((GRID_SIZE, GRID_SIZE), dtype=bool)
        self.insulators = np.zeros((GRID_SIZE, GRID_SIZE), dtype=bool)
        self.conductors = np.zeros((GRID_SIZE, GRID_SIZE), dtype=bool)
        self.start_point = None
        self.end_point = None

        # Lightning path data
        self.bolt_paths = []  # Each is (path_list, is_fork)
        self.finished_paths = []
        self.growing = False

        # Set edges as perfect insulators
        self.insulators[0, :] = True
        self.insulators[-1, :] = True
        self.insulators[:, 0] = True
        self.insulators[:, -1] = True
        self.fixed[self.insulators] = True
        self.grid[self.insulators] = 0.0

    # Set a high-potential start point
    def set_start_point(self, x, y):
        self.start_point = (x, y)
        self.grid[x, y] = 15.0
        self.fixed[x, y] = True

    # Set a low-potential end point
    def set_end_point(self, x, y):
        self.end_point = (x, y)
        self.grid[x, y] = -15.0
        self.fixed[x, y] = True

    # Place an insulator cell
    def add_insulator(self, x, y):
        self.insulators[x, y] = True
        self.fixed[x, y] = True
        self.grid[x, y] = 0.0
        self.conductors[x, y] = False

    # Place a conductor cell
    def add_conductor(self, x, y):
        if self.insulators[x, y]:
            return
        self.conductors[x, y] = True
        self.fixed[x, y] = False
        self.grid[x, y] = 0.0

    # Detect connected regions of conductor cells
    def get_conductor_groups(self):
        visited = np.zeros_like(self.conductors, dtype=bool)
        groups = []
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if self.conductors[i, j] and not visited[i, j]:
                    queue = deque()
                    group = []
                    queue.append((i, j))
                    visited[i, j] = True
                    while queue:
                        x, y = queue.popleft()
                        group.append((x, y))
                        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                                if self.conductors[nx, ny] and not visited[nx, ny]:
                                    visited[nx, ny] = True
                                    queue.append((nx, ny))
                    groups.append(group)
        return groups

    # Laplace solver + conductor equipotential logic
    def simulate(self, iterations=1):
        for _ in range(iterations):
            new_grid = self.grid.copy()
            for i in range(1, GRID_SIZE - 1):
                for j in range(1, GRID_SIZE - 1):
                    if self.fixed[i, j] or self.insulators[i, j] or self.conductors[i, j]:
                        continue
                    values = []
                    for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < GRID_SIZE and 0 <= nj < GRID_SIZE and not self.insulators[ni, nj]:
                            values.append(self.grid[ni, nj])
                    if values:
                        new_grid[i, j] = sum(values) / len(values)

            # Update each connected conductor group to shared potential
            for group in self.get_conductor_groups():
                potentials = []
                for (x, y) in group:
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and not self.insulators[nx, ny] and not self.conductors[nx, ny]:
                            potentials.append(self.grid[nx, ny])
                if potentials:
                    avg = sum(potentials) / len(potentials)
                    for (x, y) in group:
                        new_grid[x, y] = avg

            self.grid = new_grid

    # Begin the lightning strike
    def start_lightning(self):
        if not self.start_point or not self.end_point:
            return
        self.bolt_paths = [([self.start_point], False)]
        self.finished_paths = []
        self.growing = True

    # Step-wise growth of lightning
    def grow_lightning(self):
        if not self.growing or not self.bolt_paths:
            self.growing = False
            return

        new_paths = []
        for path, is_fork in self.bolt_paths:
            current = path[-1]
            if current == self.end_point:
                self.finished_paths.append(path)
                continue

            x, y = current
            neighbors = []
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    if (nx, ny) not in path and not self.insulators[nx, ny]:
                        potential = self.grid[nx, ny]
                        if is_fork:
                            potential += random.uniform(-0.5, 0.5)
                        neighbors.append(((nx, ny), potential))

            if not neighbors:
                continue

            min_potential = min(neighbors, key=lambda x: x[1])[1]
            candidates = [pos for pos, pot in neighbors if np.isclose(pot, min_potential, atol=0.2)]
            chosen = random.choice(candidates)

            if is_fork and self.grid[chosen[0], chosen[1]] > -2:
                continue

            new_path = path + [chosen]
            new_paths.append((new_path, is_fork))

            if not is_fork and len(path) > 5:
                fork_prob = max(0.3 - 0.005 * len(path), 0)
                if random.random() < fork_prob:
                    fork_candidates = [pos for pos in candidates if pos != chosen]
                    if fork_candidates:
                        fork_pos = random.choice(fork_candidates)
                        fork_path = path + [fork_pos]
                        new_paths.append((fork_path, True))

        self.bolt_paths = new_paths
        if not self.bolt_paths:
            self.growing = False


# Visual rendering function
def draw_simulation(screen, simulation):
    cell_width = WIDTH // GRID_SIZE
    cell_height = HEIGHT // GRID_SIZE

    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            x = i * cell_width
            y = j * cell_height
            val = simulation.grid[i, j]

            if simulation.insulators[i, j]:
                color = GRAY
            elif simulation.conductors[i, j]:
                color = GREEN
            else:
                norm = np.clip(val / 10.0, -1, 1)
                if norm > 0:
                    r = int(255 * norm)
                    color = (r, 0, 0)
                elif norm < 0:
                    b = int(255 * -norm)
                    color = (0, 0, b)
                else:
                    color = (0, 0, 0)

            pygame.draw.rect(screen, color, (x, y, cell_width, cell_height))

    # Flicker effect for growing lightning
    flicker_colors = [YELLOW, ORANGE, WHITE]
    for path, _ in simulation.bolt_paths:
        for (i, j) in path:
            x = i * cell_width
            y = j * cell_height
            color = random.choice(flicker_colors)
            pygame.draw.rect(screen, color, (x, y, cell_width, cell_height))

    # Finalized lightning path
    for path in simulation.finished_paths:
        for (i, j) in path:
            x = i * cell_width
            y = j * cell_height
            pygame.draw.rect(screen, YELLOW, (x, y, cell_width, cell_height))

    # Draw start and end points
    if simulation.start_point:
        x, y = simulation.start_point
        pygame.draw.circle(screen, RED, (x * cell_width + cell_width // 2, y * cell_height + cell_height // 2), min(cell_width, cell_height) // 2)
    if simulation.end_point:
        x, y = simulation.end_point
        pygame.draw.circle(screen, BLUE, (x * cell_width + cell_width // 2, y * cell_height + cell_height // 2), min(cell_width, cell_height) // 2)

    # Legend UI
    font = pygame.font.SysFont(None, 24)
    legend_lines = [
        "Left Click: Set start (red)/end (blue) point",
        "Shift + Click: Place insulator (gray)",
        "Ctrl + Click: Place conductor (green)",
        "Press S to start simulation",
        "Press Enter to start lightning"
    ]
    for idx, line in enumerate(legend_lines):
        text = font.render(line, True, WHITE)
        screen.blit(text, (10, HEIGHT - 120 + idx * 20))


# Main Pygame loop
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2D Lightning Simulator")
    clock = pygame.time.Clock()
    simulation = Simulation()

    running = True
    simulating = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                x //= WIDTH // GRID_SIZE
                y //= HEIGHT // GRID_SIZE
                mods = pygame.key.get_mods()

                if mods & pygame.KMOD_SHIFT:
                    simulation.add_insulator(x, y)
                elif mods & pygame.KMOD_CTRL:
                    simulation.add_conductor(x, y)
                else:
                    if not simulation.start_point:
                        simulation.set_start_point(x, y)
                    elif not simulation.end_point:
                        simulation.set_end_point(x, y)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    simulating = True
                if event.key == pygame.K_RETURN:
                    simulation.start_lightning()

        if simulating:
            simulation.simulate(5)

        if simulation.growing:
            simulation.grow_lightning()

        screen.fill(BLACK)
        draw_simulation(screen, simulation)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()

