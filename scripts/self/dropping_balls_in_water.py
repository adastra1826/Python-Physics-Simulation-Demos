import pygame
import pymunk
import pymunk.pygame_util
import numpy as np

# Reference Values
WIDTH_METERS, HEIGHT_METERS = 1, 2
BALL_RADIUS_METERS = 0.05
PARTICLE_RADIUS_METERS = 0.01

# Simulation Window Size
WIDTH, HEIGHT = 400, 800

# Scale Factor
SCALE = WIDTH / WIDTH_METERS

# Calculated Constants
BALL_RADIUS = BALL_RADIUS_METERS * SCALE
PARTICLE_RADIUS = PARTICLE_RADIUS_METERS * SCALE

# Constants
FLUID_DENSITY = 1
GRAVITY = 981
SMOOTHING_LENGTH = 10.0
NUM_PARTICLES = 3000
PARTICLE_RESTITUTION = 0.9

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

class Particle:
    def __init__(self, x, y, space):
        self.body = pymunk.Body(0.0015, pymunk.moment_for_circle(0.0015, PARTICLE_RADIUS, PARTICLE_RADIUS))
        self.body.position = x, y
        self.shape = pymunk.Circle(self.body, PARTICLE_RADIUS)
        self.shape.elasticity = 0.0
        self.shape.friction = 0.0
        space.add(self.body, self.shape)
        
class Ball:
    def __init__(self, x, y, space):
        self.body = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BALL_RADIUS))
        self.body.position = x, y
        self.shape = pymunk.Circle(self.body, BALL_RADIUS)
        self.shape.elasticity = 0.9
        self.shape.friction = 0.9
        space.add(self.body, self.shape)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    space = pymunk.Space()
    space.gravity = (0, GRAVITY)

    static_lines = [
        pymunk.Segment(space.static_body, (0, 0), (WIDTH, 0), 1.0),
        pymunk.Segment(space.static_body, (WIDTH, 0), (WIDTH, HEIGHT), 1.0),
        pymunk.Segment(space.static_body, (WIDTH, HEIGHT), (0, HEIGHT), 1.0),
        pymunk.Segment(space.static_body, (0, HEIGHT), (0, 0), 1.0)
    ]
    for line in static_lines:
        line.elasticity = 1
        line.friction = 0.0
    space.add(*static_lines)

    for i in range(NUM_PARTICLES):
            x = np.random.uniform(0, WIDTH)
            y = np.random.uniform(HEIGHT // 2, HEIGHT)
            Particle(x, y, space)

    draw_options = pymunk.pygame_util.DrawOptions(screen)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                Ball(mouse_x, mouse_y, space)

        screen.fill(WHITE)
        space.step(1 / 60.0)  # Advance physics simulation
        space.debug_draw(draw_options)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
