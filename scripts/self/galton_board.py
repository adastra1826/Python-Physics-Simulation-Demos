"""
Galton Board Physics Simulation.

This simulation models a Galton Board (also known as a bean machine or quincunx),
which is a device that demonstrates binomial probability distribution through
physical means. Balls drop from a hopper at the top, bounce off pegs arranged
in rows, and collect in columns at the bottom, forming a bell-shaped distribution.
The simulation demonstrates principles of probability, random walks, and how
small random deviations accumulate to create predictable statistical patterns.
"""

import pymunk
import pymunk.pygame_util
import pygame
import math
import random

# Global variables
# Dimensions
WIDTH, HEIGHT = 700, 800
GRAVITY = 981
DAMPING = 0.6

# Balls
NUM_BALLS = 100
BALL_MASS = 1
BALL_ELASTICITY = 0.5
BALL_FRICTION = 0.1
BALL_RADIUS = 8

# Pegs
PEG_RADIUS = 6
PEG_ELASTICITY = 1
PEG_FRICTION = 0.0

PEG_FIRST_ROW = 9
PEG_ROWS = 15
PEG_HORIZONTAL_SPACING = BALL_RADIUS * 4
PEG_VERTICAL_SPACING = math.sqrt(3) * BALL_RADIUS * 2

# Hopper
HOPPER_HEIGHT = 150
HOPPER_VERTICAL_OFFSET = -BALL_RADIUS
HOPPER_OPENING = BALL_RADIUS * 5

# Columns
COLUMN_WIDTH = 2
COLUMN_HEIGHT = BALL_RADIUS * 19
COLUMN_SPACING = BALL_RADIUS * 2 + (COLUMN_WIDTH * 2)
WALL_FRICTION = 0.0
WALL_ELASTICITY = 1.0

# Colors
BACKGROUND_COLOR = (255, 255, 255)
WALL_COLOR = (200, 200, 200, 255)
PEG_COLOR = (0, 0, 0, 255)
BALL_COLOR = (200, 0, 0, 255)

# FPS
FPS = 60

# Galton Board class, which handles creating the board and running the simulation
class GaltonBoard:
    def __init__(self):
        """Initialize the Galton Board simulation."""
        self.space = pymunk.Space()
        self.space.gravity = (0, GRAVITY)
        self.space.damping = DAMPING
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        self.moment = pymunk.moment_for_circle(BALL_MASS, 0, BALL_RADIUS)
        self.paused = False
        self.create_edges()
        self.create_board()
        self.create_hopper()
        self.create_columns()
        self.add_balls()
    
    def create_edges(self):
        """Create the edges of the board."""
        # Describe the edges
        edges = [
            ((0, 0), (0, HEIGHT)),
            ((0, HEIGHT), (WIDTH, HEIGHT)),
            ((WIDTH, HEIGHT), (WIDTH, 0))
        ]
        # Add the edges to the space
        for a, b in edges:
            segment = pymunk.Segment(self.space.static_body, a, b, COLUMN_WIDTH)
            segment.elasticity = WALL_ELASTICITY
            segment.friction = WALL_FRICTION
            self.space.add(segment)

    def create_hopper(self):
        """Create the hopper which funnels balls into the board."""
        hopper_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        hopper_body.position = (WIDTH / 2, 0)
        self.space.add(hopper_body)
        # Describe the hopper edges
        edges = [
            ((-WIDTH / 2, 0), (-HOPPER_OPENING / 2, HOPPER_HEIGHT)),
            ((WIDTH / 2, 0), (HOPPER_OPENING / 2, HOPPER_HEIGHT + HOPPER_VERTICAL_OFFSET)),
            ((-WIDTH / 2, 0), (-WIDTH / 2, -HOPPER_HEIGHT)),
            ((WIDTH / 2, 0), (WIDTH / 2, -HOPPER_HEIGHT)),
            ((-HOPPER_OPENING / 2, HOPPER_HEIGHT), (-HOPPER_OPENING/ 2, HOPPER_HEIGHT + (BALL_RADIUS * 2))),
            ((HOPPER_OPENING / 2, HOPPER_HEIGHT + HOPPER_VERTICAL_OFFSET), (HOPPER_OPENING / 2, HOPPER_HEIGHT + (BALL_RADIUS * 2))),
        ]
        # Add the hopper edges to the space
        for a, b in edges:
            segment = pymunk.Segment(hopper_body, a, b, COLUMN_WIDTH)
            segment.elasticity = WALL_ELASTICITY
            segment.friction = WALL_FRICTION
            self.space.add(segment)

    def create_board(self):
        """Create the board with pegs."""
        # Create a static body to attach the pegs to
        board_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        board_body.position = (WIDTH / 2, HOPPER_HEIGHT + PEG_VERTICAL_SPACING)
        self.space.add(board_body)        
        # Create the pegs
        each_row = [-PEG_HORIZONTAL_SPACING / 2, PEG_VERTICAL_SPACING]
        each_peg = PEG_HORIZONTAL_SPACING
        for i, peg in enumerate(range(PEG_FIRST_ROW - 1, PEG_ROWS + PEG_FIRST_ROW - 1), start=1):
            y = each_row[1] * i
            for j in range(peg + 1):
                x =  (each_row[0] * peg) + (each_peg * j)
                peg_shape = pymunk.Circle(board_body, PEG_RADIUS, (x, y))
                peg_shape.color = PEG_COLOR
                peg_shape.elasticity = PEG_ELASTICITY
                peg_shape.friction = PEG_FRICTION
                self.space.add(peg_shape)

    def create_columns(self):
        """Create the columns at the bottom of the board. These are set to the width of the balls, ensuring perfect stacking."""
        increment = WIDTH // COLUMN_SPACING
        for i in range(increment):
            x = (i * COLUMN_SPACING) + COLUMN_SPACING
            y = HEIGHT - COLUMN_HEIGHT
            column_segment = pymunk.Segment(self.space.static_body, (x, y), (x, y + COLUMN_HEIGHT), COLUMN_WIDTH)
            column_body = pymunk.Body(body_type=pymunk.Body.STATIC)
            column_shape = pymunk.Poly.create_box(self.space.static_body, size=(COLUMN_WIDTH, COLUMN_HEIGHT))
            column_shape.elasticity = WALL_ELASTICITY
            column_shape.friction = WALL_FRICTION
            column_body.position = (x, y)
            self.space.add(column_segment)

    def add_balls(self):
        """"Add balls to the hopper."""
        for _ in range(NUM_BALLS):
            ball_body = pymunk.Body(BALL_MASS, self.moment)
            ball_shape = pymunk.Circle(ball_body, BALL_RADIUS)
            ball_shape.elasticity = BALL_ELASTICITY
            ball_shape.friction = BALL_FRICTION
            ball_shape.color = BALL_COLOR
            x = random.randint(0, WIDTH)
            y = random.randint(-HOPPER_HEIGHT // 2, 0)
            ball_body.position = (x, y)
            self.space.add(ball_body, ball_shape)

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
        game = GaltonBoard()
        reset = game.run()
    pygame.quit()

if __name__ == "__main__":
    main()