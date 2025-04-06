import pymunk
import pymunk.pygame_util
import pygame
import math

# Global variables
# Dimensions
WIDTH, HEIGHT = 650, 300
CEILING_THICKNESS = 10

# Pendulums
NUM_PENDULUMS = 5
PENDULUM_LENGTH = 200
PENDULUM_WIDTH = 2
JOINT_SPACING = 5

# Balls
BALL_RADIUS = 20
BALL_MASS = 10
BALL_ELASTICITY = 0.99
BALL_FRICTION = 0.01

# Colors
BACKGROUND_COLOR = (10, 10, 10, 255)
END_BALL_COLOR = (255, 0, 0, 255)
MIDDLE_BALL_COLOR = (0, 255, 0, 255)
SEGMENT_COLOR = (100, 100, 100, 255)

# Starting force
FORCE = -6000

# Space
GRAVITY = 0, 981
DAMPING = 0.99

# Time scale (number is the denominator of the fraction 1/x)
# For example, 2 means 1/2 speed, 3 means 1/3 speed, etc.
# This adjustment was made to speed the simulation up while allowing accurate physics simulation
TIME_SCALE = 2
FPS = 60

class NewtonsCradle:
    def __init__(self):
        """Initialize the Newton's Cradle simulation."""
        self.space = pymunk.Space()
        self.space.gravity = GRAVITY
        self.space.damping = DAMPING
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        self.ball_moment = pymunk.moment_for_circle(BALL_MASS, 0, BALL_RADIUS)
        self.create_objects()
        self.apply_force()

    def create_objects(self):
        """Create the objects in the simulation."""
        # Create top segment
        segment_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        segment_shape = pymunk.Segment(segment_body, (0, 0), (WIDTH, 0), CEILING_THICKNESS)
        self.space.add(segment_body, segment_shape)

        # Determine start position and spacing for pendulums
        length = NUM_PENDULUMS * (BALL_RADIUS * 2)
        start_x = WIDTH // 2 - length // 2
        spacing = length // NUM_PENDULUMS
        # Create pendulums
        for i in range(NUM_PENDULUMS):
            x = start_x + (i * spacing)
            # Create a body which will have the pendulum and ball shapes attached to it
            pendulum_body = pymunk.Body(BALL_MASS, self.ball_moment)
            pendulum_body.center_of_gravity = (0, PENDULUM_LENGTH)
            pendulum_body.position = x, CEILING_THICKNESS + (JOINT_SPACING * 2)
            pendulum_shape = pymunk.Segment(pendulum_body, (0, 0), (0, PENDULUM_LENGTH), PENDULUM_WIDTH)
            pendulum_shape.color = SEGMENT_COLOR
            # Create a pivot joint to attach the pendulum to the ceiling
            pivot_joint = pymunk.PivotJoint(segment_body, pendulum_body, (x, CEILING_THICKNESS + JOINT_SPACING))
            # Set max force to infinity to prevent the joint from displacing
            pivot_joint.max_force = math.inf
            ball_shape = pymunk.Circle(pendulum_body, BALL_RADIUS, (0, PENDULUM_LENGTH))
            ball_shape.elasticity = BALL_ELASTICITY
            ball_shape.friction = BALL_FRICTION
            if i == 0 or i == NUM_PENDULUMS - 1:
                ball_shape.color = END_BALL_COLOR
            else:
                ball_shape.color = MIDDLE_BALL_COLOR
            # Add the body, shapes, and joint to the space
            self.space.add(pendulum_body, pendulum_shape, pivot_joint, ball_shape)

    def apply_force(self):
        """Apply a force to the first pendulum in the simulation."""
        pendulum_body = self.space.shapes[1].body
        pendulum_body.apply_impulse_at_local_point((FORCE, 0), (0, PENDULUM_LENGTH))

    def run_simulation(self):
        """Run the simulation, allowing the user to pause, reset, or quit the simulation."""
        clock = pygame.time.Clock()
        paused = False
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        paused = not paused
                    elif event.key == pygame.K_r:
                        return True
                    elif event.key == pygame.K_q:
                        return False

            # Step the simulation with handling for the time scale
            if not paused:
                dt = 1 / (FPS * TIME_SCALE)
                for _ in range(10):
                    self.space.step(dt)

            # Draw the simulation
            self.screen.fill(BACKGROUND_COLOR)
            self.space.debug_draw(self.draw_options)
            pygame.display.flip()
            clock.tick(FPS)
        
def main():
    """Run the Newton's Cradle simulation using a boolean flag to reset/quit the simulation."""
    pygame.init()
    reset = True
    while reset:
        simulation = NewtonsCradle()
        reset = simulation.run_simulation()
    pygame.quit()

if __name__ == "__main__":
    main()