"""
Water Ripples Physics Simulation (Version 2).

This simulation models the formation and propagation of ripples on a water surface.
It demonstrates principles of wave dynamics, including how disturbances create
circular waves that expand outward, how these waves reflect off boundaries,
and how multiple wave sources create interference patterns. The simulation uses
a simplified wave equation to model how energy transfers through the water medium,
creating the characteristic expanding rings and interference patterns observed
when disturbing a calm water surface.
"""

import pygame
import numpy as np
import sys
import time

# Display and grid settings
WIDTH, HEIGHT = 600, 600
FPS = 60
GRID_SPACING = 2
COLS = WIDTH // GRID_SPACING
ROWS = HEIGHT // GRID_SPACING

# Wave physics constants
DAMPING = 0.985
DROP_INTERVAL = 60  # frames between drops
AMPLITUDE = 1000

# Color settings
BG_COLOR = (10, 10, 30)
COLOR_SCALE = np.array([0, 180, 255])

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Water Ripple Simulation")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 28)

# Surface for pixel shading
ripple_surface = pygame.Surface((COLS, ROWS))
scaled_surface = pygame.transform.scale(ripple_surface, (WIDTH, HEIGHT))

# Initialize wave buffers
current = np.zeros((COLS, ROWS), dtype=np.float32)
previous = np.zeros((COLS, ROWS), dtype=np.float32)
frame_counter = 0
start_time = time.time()


def disturb(x, y, magnitude=AMPLITUDE):
    """
    Simulates a water droplet impact by adding energy to the wave grid.
    """
    if 2 < x < COLS - 3 and 2 < y < ROWS - 3:
        current[x, y] += magnitude


def update_ripples():
    """
    Vectorized wave propagation update using a 2D wave approximation formula.
    Applies damping to simulate energy loss.
    """
    global current, previous
    laplace = (
        np.roll(previous, 1, axis=0) +
        np.roll(previous, -1, axis=0) +
        np.roll(previous, 1, axis=1) +
        np.roll(previous, -1, axis=1)
    ) / 2 - current

    current = laplace * DAMPING
    current[0, :] = current[-1, :] = current[:, 0] = current[:, -1] = 0  # boundary conditions
    previous, current = current, previous


def draw_ripples():
    """
    Renders the ripple heightmap to a surface using a fluid-like color gradient.
    """
    normalized = np.clip((previous + 255) / 510, 0, 1)
    pixel_array = (normalized[..., None] * COLOR_SCALE).astype(np.uint8)
    pygame.surfarray.blit_array(ripple_surface, pixel_array.swapaxes(0, 1))
    scaled = pygame.transform.smoothscale(ripple_surface, (WIDTH, HEIGHT))
    screen.blit(scaled, (0, 0))


def draw_overlays(elapsed_time):
    """
    Draws HUD overlays including time counter and amplitude scale.
    """
    time_text = font.render(f"Time elapsed: {int(elapsed_time)}s", True, (255, 255, 255))
    amp_text = font.render("Amplitude scale: Blue -> Bright Cyan", True, (100, 200, 255))
    screen.blit(time_text, (10, 10))
    screen.blit(amp_text, (10, 40))


def main():
    global frame_counter
    running = True

    while running:
        screen.fill(BG_COLOR)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Drop a ripple periodically
        if frame_counter % DROP_INTERVAL == 0:
            x = np.random.randint(10, COLS - 10)
            y = np.random.randint(10, ROWS - 10)
            disturb(x, y)

        update_ripples()
        draw_ripples()
        draw_overlays(time.time() - start_time)

        pygame.display.flip()
        clock.tick(FPS)
        frame_counter += 1


if __name__ == "__main__":
    main()
