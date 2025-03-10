import pymunk
import pymunk.pygame_util
import pygame
import math
import random

# Global variables
# Dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 800
GRAVITY = 0, 981
SPACE_DAMPING = 0.6

# Colors
BACKGROUND_COLOR = (255, 255, 255)

# FPS
FPS = 60

# Galton Board class, which handles creating the board and running the simulation
class Simulation:
    def __init__(self):
        """Initialize the Galton Board simulation."""
        self.space = pymunk.Space()
        self.space.gravity = GRAVITY
        self.space.damping = SPACE_DAMPING
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        self.paused = False

    def run(self):
        """Run the simulation."""
        while True:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        return True
                    elif event.key == pygame.K_q:
                        return False

            if not self.paused:
                dt = 1 / 600
                for _ in range(20):
                    self.space.step(dt)

            self.screen.fill(BACKGROUND_COLOR)
            self.space.debug_draw(self.draw_options)
            pygame.display.flip()
            self.clock.tick(FPS)
            
def main():
    """Run the Galton Board simulation using a boolean flag to reset/quit the simulation."""
    pygame.init()
    reset = True
    while reset:
        game = Simulation()
        reset = game.run()
    pygame.quit()

if __name__ == "__main__":
    main()