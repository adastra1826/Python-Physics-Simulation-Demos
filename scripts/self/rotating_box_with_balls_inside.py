"""
Rotating Box with Balls Inside Physics Simulation.

This simulation models the behavior of multiple balls contained within a rotating box.
As the box rotates, the balls collide with each other and the box walls, demonstrating
principles of centrifugal force, collisions in non-inertial reference frames, and
energy transfer. The simulation shows how objects behave under rotation, how energy
is distributed throughout a closed system, and how rotational motion affects the
movement patterns of contained objects.
"""

import pymunk
import pymunk.pygame_util
import pygame

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600

CONTAINER_SIZE = 400
CONTAINER_MASS = 1000
CONTAINER_HALF_SIZE = CONTAINER_SIZE / 2
WALL_THICKNESS = 5

SLIDER_CONTROL_SCALE = 3
SLIDER_WIDTH = 200
SLIDER_HEIGHT = 20
CONTROL_WIDTH = 20
CONTROL_HEIGHT = 30

BALL_RADIUS = 10
BALL_MASS = 5

GRAVITY = 981

# Colors
BACKGROUND = (255, 255, 255)
TEXT = (0, 0, 255)
SLIDER = (0, 255, 0)
SLIDER_CONTROL = (255, 0, 0)

font = pygame.font.Font(None, 36)

# Create the game screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Create a ball object and return it
def create_ball(position):
    moment = pymunk.moment_for_circle(BALL_MASS, 0, BALL_RADIUS)
    ball_body = pymunk.Body(BALL_MASS, moment)
    ball_body.position = position
    ball_shape = pymunk.Circle(ball_body, BALL_RADIUS)
    ball_shape.elasticity = 0.9
    ball_shape.friction = 0.5
    return ball_body, ball_shape

# Main simulation loop
def run_simulation():
    
    """ Function which creates and runs the simulation. """
    
    # Create a local collision counter dictionary
    collisions = {"count": 0}

    # Define collision handler callback locally to capture 'collisions'
    def collision_begin(arbiter, space, data):
        collisions["count"] += 1
        return True
    
    # Set up the Pymunk space
    space = pymunk.Space()
    space.gravity = 0, GRAVITY
    
    handler = space.add_default_collision_handler()
    handler.begin = collision_begin

    # Create the container box
    moment = pymunk.moment_for_box(CONTAINER_MASS, (CONTAINER_SIZE, CONTAINER_SIZE))
    container_body = pymunk.Body(CONTAINER_MASS, moment)
    container_body.position = (WIDTH / 2, (HEIGHT / 2) - 50)
    space.add(container_body)

    # Because Pymunk does not support hollow shapes, one must be created by adding each edge as its own segment
    edges = [
        ((-CONTAINER_HALF_SIZE, -CONTAINER_HALF_SIZE), (CONTAINER_HALF_SIZE, -CONTAINER_HALF_SIZE)),
        ((CONTAINER_HALF_SIZE, -CONTAINER_HALF_SIZE), (CONTAINER_HALF_SIZE, CONTAINER_HALF_SIZE)),
        ((CONTAINER_HALF_SIZE, CONTAINER_HALF_SIZE), (-CONTAINER_HALF_SIZE, CONTAINER_HALF_SIZE)),
        ((-CONTAINER_HALF_SIZE, CONTAINER_HALF_SIZE), (-CONTAINER_HALF_SIZE, -CONTAINER_HALF_SIZE))
    ]

    for a, b in edges:
        segment = pymunk.Segment(container_body, a, b, WALL_THICKNESS)
        segment.elasticity = 0.9
        segment.friction = 0
        space.add(segment)
    
    # Add pivot joint to ensure the container can rotate but does not fall due to gravity
    pivot_joint = pymunk.PivotJoint(container_body, space.static_body, container_body.position)
    space.add(pivot_joint)
    
    # Create the slider control
    slider = pygame.Rect((WIDTH / 2) - (SLIDER_WIDTH / 2), HEIGHT - 50, SLIDER_WIDTH, SLIDER_HEIGHT)
    slider_control = pygame.Rect((WIDTH / 2) - (CONTROL_WIDTH / 2), HEIGHT - 50 - ((CONTROL_HEIGHT - SLIDER_HEIGHT) / 2), CONTROL_WIDTH, CONTROL_HEIGHT)
    
    # Set up the clock
    clock = pygame.time.Clock()
        
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    
    # Main simulation loop
    while True:        
        
        # Handle input 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Add a new ball to the space when the mouse is pressed
                body, shape = create_ball(pygame.mouse.get_pos())
                space.add(body, shape)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and slider_control.left > slider.left:
                    # Move the rotation speed control slider left
                    slider_control.move_ip(-5, 0)
                elif event.key == pygame.K_RIGHT and slider_control.right < slider.right:
                    # Move the rotation speed control slider right
                    slider_control.move_ip(5, 0)
                elif event.key == pygame.K_q:
                    # Return False, thereby ending the whole program
                    return False
                elif event.key == pygame.K_r:
                    # Return True, causing the simulation to reset
                    return True
        
        # Set the speed of the rotating box to be relative to the position of the control slider on the control bar
        relative_control_position = slider.centerx - slider_control.centerx
        control_scale =  -1 * ((relative_control_position / (SLIDER_WIDTH / 2)) * SLIDER_CONTROL_SCALE)
        container_body.angular_velocity = control_scale
        
        #Draw the screen
        screen.fill(BACKGROUND)
        space.debug_draw(draw_options)
        
        # Draw slider and control
        pygame.draw.rect(screen, SLIDER, slider)
        pygame.draw.rect(screen, SLIDER_CONTROL, slider_control)
        
        text_surface = font.render(str(collisions["count"]), True, TEXT)
        text_rect = text_surface.get_rect(center = (WIDTH / 2, HEIGHT - 10))
        screen.blit(text_surface, text_rect)

        # Update display
        pygame.display.flip()
        
        # Do 10 physics calculations per frame to prevent the balls from tunneling through the walls
        dt = 1/600
        for _ in range(10):
            space.step(dt)
            
        clock.tick(60)
    

def main():
    
    """ 
    Main function which handles dispatching the simulation.
    By returning True (reset) or False (quit) from the simulation when it terminates, 
    it is easy to handle rerunning or quitting the simulation.
    """
    
    reset = True
    while reset:
        reset = run_simulation()


if __name__ == "__main__":
    main()