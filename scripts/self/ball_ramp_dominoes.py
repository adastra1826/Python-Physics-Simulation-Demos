
import pymunk
import pymunk.pygame_util
import pygame
import math

# Global variables
# Dimensions
WIDTH, HEIGHT = 1200, 600

# Ball
BALL_MASS = 3
BALL_RADIUS = 15
BALL_FRICTION = 0.9
BALL_ELASTICITY = 0.95

# Domino
DOMINO_HEIGHT = 60
DOMINO_WIDTH = DOMINO_HEIGHT // 4
DOMINO_SPACING = DOMINO_HEIGHT // 2
DOMINO_MASS = 1
DOMINO_FRICTION = 0.9
DOMINO_ELASTICITY = 0.2

# Floor
FLOOR_THICKNESS = 5
FLOOR_HEIGHT = 20
FLOOR_FRICTION = 0.9
FLOOR_ELASTICITY = 0.4

# Ramp
RAMP_ANGLE = 45
RAMP_PROPORTION = 1 / 4

# Colors
# Pymunk objects need an alpha channel, Pygame objects do not
BACKGROUND_COLOR = (0, 200, 200)
BALL_COLOR = (200, 0, 0, 255)
DOMINO_COLOR = (200, 200, 0, 255)
FLOOR_COLOR = (200, 200, 200, 255)

# Space
SPACE_GRAVITY = 0, 981
SPACE_DAMPING = 0.8
FPS = 60

# Simulation class, which handles creating the objects and running the simulation
class Simulation:
    def __init__(self):
        """Initialize the simulation."""
        self.space = pymunk.Space()
        self.space.gravity = SPACE_GRAVITY
        self.space.damping = SPACE_DAMPING
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        self.domino_moment = pymunk.moment_for_box(DOMINO_MASS, (DOMINO_WIDTH, DOMINO_HEIGHT))
        self.ball_moment = pymunk.moment_for_circle(BALL_MASS, 0, BALL_RADIUS)
        self.running = True
        self.paused = False
        self.create_objects()

    def create_objects(self):
        """Create the objects in the simulation."""
        # Create floor
        floor_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        floor_shape = pymunk.Segment(floor_body, (0, HEIGHT - FLOOR_HEIGHT), (WIDTH, HEIGHT - FLOOR_HEIGHT), FLOOR_THICKNESS)
        floor_shape.elasticity = FLOOR_ELASTICITY
        floor_shape.friction = FLOOR_FRICTION
        floor_shape.color = FLOOR_COLOR
        self.space.add(floor_shape, floor_body)

        # Create ramp
        # Calculate the intersection of the ramp with the left side of the screen based on the angle
        # Modulo 90 to ensure the ramp is always oriented correctly
        degrees = (RAMP_ANGLE % 90)
        radians = math.radians(degrees)
        # Calculate the y-intercept point of the line with the left wall based on the angle of the ramp
        y = (HEIGHT - FLOOR_HEIGHT) + math.tan(radians) * (-WIDTH * RAMP_PROPORTION)
        ramp_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        ramp_shape = pymunk.Segment(ramp_body, (0, y), (WIDTH * RAMP_PROPORTION, HEIGHT - FLOOR_HEIGHT), FLOOR_THICKNESS)
        ramp_shape.elasticity = FLOOR_ELASTICITY
        ramp_shape.friction = FLOOR_FRICTION
        ramp_shape.color = FLOOR_COLOR
        self.space.add(ramp_body, ramp_shape)

        # Create dominoes
        # Calculate the starting x position, number, and spacing of the dominoes
        length = WIDTH - (WIDTH * RAMP_PROPORTION)
        interval = int(length / (DOMINO_WIDTH + DOMINO_SPACING))
        start_x = WIDTH * RAMP_PROPORTION
        # Create and add the dominoes
        for i in range(interval):
            domino_body = pymunk.Body(DOMINO_MASS, self.domino_moment)
            domino_body.position = (start_x + (i * (DOMINO_WIDTH + DOMINO_SPACING)) + (FLOOR_THICKNESS * 3), HEIGHT - FLOOR_HEIGHT - (DOMINO_HEIGHT / 2))
            domino_shape = pymunk.Poly.create_box(domino_body, size=(DOMINO_WIDTH, DOMINO_HEIGHT))
            domino_shape.elasticity = DOMINO_ELASTICITY
            domino_shape.friction = DOMINO_FRICTION
            domino_shape.color = DOMINO_COLOR
            self.space.add(domino_body, domino_shape)

    def create_ball(self, mouse_pos):
        """Create a ball at the mouse position when the mouse is clicked."""
        ball_body = pymunk.Body(BALL_MASS, self.ball_moment)
        ball_body.position = mouse_pos
        ball_shape = pymunk.Circle(ball_body, BALL_RADIUS)
        ball_shape.elasticity = BALL_ELASTICITY
        ball_shape.friction = BALL_FRICTION
        ball_shape.color = BALL_COLOR
        self.space.add(ball_body, ball_shape)
        
    def draw_ball(self, mouse_pos):
        """Draw the ball at the mouse position."""
        pygame.draw.circle(self.screen, BALL_COLOR, mouse_pos, BALL_RADIUS)

    def handle_events(self):
        """Handle events/input in the simulation."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.create_ball(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    return True
                elif event.key == pygame.K_q:
                    self.running = False

    def run(self):
        """Run the simulation."""
        while self.running:
            self.screen.fill(BACKGROUND_COLOR)
            if not self.paused:
                self.space.step(1 / FPS)
            mouse_pos = pygame.mouse.get_pos()
            self.draw_ball(mouse_pos)
            self.space.debug_draw(self.draw_options)
            pygame.display.flip()
            self.clock.tick(FPS)
            if self.handle_events():
                return True
        return False

def main():
    """Main entry point for the script."""
    pygame.init()
    # If the user resets the simulation, create a new instance of the simulation using a while loop
    while True:
        sim = Simulation()
        if not sim.run():
            break
    pygame.quit()

if __name__ == "__main__":
    main()