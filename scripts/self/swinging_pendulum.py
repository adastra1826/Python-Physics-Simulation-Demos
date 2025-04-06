"""
Swinging Pendulum Physics Simulation.

This simulation models a pendulum that swings in a 2D plane under gravity.
Users can draw rectangular groups of boxes that will interact with the
pendulum, demonstrating momentum transfer, collision physics, and gravity.
The pendulum behaves according to real-world physics principles, with
elastic collisions and friction affecting the motion of objects.
"""

import pymunk
import pymunk.pygame_util
import pygame
import sys

# Global variables
WIDTH, HEIGHT = 600, 800
PENDULUM_MASS = 1000
PENDULUM_LENGTH = HEIGHT - 200
PENDULUM_SWING = -800000
BOX_DIVIDE = 4
BOX_MASS = 10
BACKGROUND_COLOR = (200, 200, 200)
DRAW_OUTLINE_COLOR = (0, 0, 0)
PENDULUM_COLOR = (200, 0, 0, 255)
COLLISION_COLOR = (255, 255, 0, 255)


def create_pendulum(space):
    """Creates a swinging pendulum, and joint it attaches to, and starts the pendulum swinging."""
    # Create body and segment for the pendulum, and add to the space
    moment = pymunk.moment_for_segment(PENDULUM_MASS, (0, -PENDULUM_LENGTH), (0, 0), 10)
    pendulum_body = pymunk.Body(PENDULUM_MASS, moment)
    pendulum_body.position = WIDTH / 2, PENDULUM_LENGTH
    pendulum_shape = pymunk.Segment(pendulum_body, (0, -PENDULUM_LENGTH), (0, 0), 10)
    pendulum_shape.elasticity = 0.1
    pendulum_shape.friction = 0
    pendulum_shape.color = PENDULUM_COLOR
    space.add(pendulum_body, pendulum_shape)

    # Create pivot joint which the pendulum rotates about, and add to the space
    pivot_body = pymunk.Body(body_type=pymunk.Body.STATIC)
    pivot_body.position = WIDTH / 2, 0
    pivot_joint = pymunk.PivotJoint(pivot_body, pendulum_body, pivot_body.position)
    space.add(pivot_joint)
    
    # Start pendulum swing
    swing_strength = PENDULUM_SWING
    pendulum_body.apply_impulse_at_local_point((swing_strength, 0), (-PENDULUM_LENGTH, 0))
    

def create_platform(space):
    """Creates the bottom platform."""
    # Create platform body and segment, and add to the space
    platform_body = pymunk.Body(body_type=pymunk.Body.STATIC)
    platform_shape = pymunk.Segment(platform_body, (0, 0), (WIDTH, 0), 10)
    platform_shape.elasticity = 0.95
    platform_shape.friction = 1
    platform_body.position = 0, HEIGHT
    space.add(platform_body, platform_shape)


def add_boxes(space, start_x, start_y, dx, dy):
    """"Creates boxes to fill a given rectangular area and adds them to the space."""
    # Calculate how wide and tall each small box will be based on how many subdivisions there are
    small_width, small_height = dx / BOX_DIVIDE, dy / BOX_DIVIDE
    moment = pymunk.moment_for_box(BOX_MASS, [small_width, small_height])
    # Create and add each smaller box to the space
    for x in range(BOX_DIVIDE):
        for y in range(BOX_DIVIDE):
            box_body = pymunk.Body(BOX_MASS, moment)
            # Box positions are measured from the center,
            # so the position for each box is normalized to the center of the box in the corner
            # where the mouse started drawing, and then multiplied by the width/height times the
            # row/column that the box is in, to find the center coordinates for each box
            box_body.position = ((start_x - (small_width / 2) - (small_width * x)), (start_y - (small_height / 2) - (small_height * y)))
            box = pymunk.Poly.create_box(box_body, [small_width, small_height], 1)
            box.elasticity = 0
            box.friction = 1
            space.add(box_body, box)


def simulation():
    """
    Main simulation loop. It is completely self contained.
    Every time it runs, a new simulation begins.
    Returns True (reset the simulation), or False (end the program)
    """
    # Create the main space, set the gravity, and add the pendulum and platform
    space = pymunk.Space()
    space.gravity = (0, 981)
    create_pendulum(space)
    create_platform(space)

    # Set up the screen
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    draw_options.collision_point_color = COLLISION_COLOR

    # Set up the running loop
    paused = False
    drawing = False
    # Declare the mouse position variables
    start_x, start_y = 0, 0
    # Main running loop
    while True:        
        screen.fill(BACKGROUND_COLOR)
        # Process all inputs
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Return False to quit the program
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    # Return True to reset the simulation
                    return True
                elif event.key == pygame.K_q:
                    return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Set the starting mouse position and drawing to True
                drawing = True
                start_x, start_y = pygame.mouse.get_pos()
            elif event.type == pygame.MOUSEMOTION and drawing:
                # Draw the outline of the rectangle as it is being pulled across the screen
                cur_x, cur_y = pygame.mouse.get_pos()
                rect_x = min(start_x, cur_x)
                rect_y = min(start_y, cur_y)
                rect_width = abs(start_x - cur_x)
                rect_height = abs(start_y - cur_y)                
                outline = pygame.Rect(rect_x, rect_y, rect_width, rect_height)
                pygame.draw.rect(screen, DRAW_OUTLINE_COLOR, outline, 1)
            elif event.type == pygame.MOUSEBUTTONUP:
                # Add the boxes to the simulation
                drawing = False
                end_x, end_y = pygame.mouse.get_pos()
                dx, dy = start_x - end_x, start_y - end_y
                # If the number of pixels covered in the x or y direction 
                # is less than the number of box subdivides, do nothing
                if abs(dx) < BOX_DIVIDE or abs(dy) < BOX_DIVIDE:
                    break                
                add_boxes(space, start_x, start_y, dx, dy)

        if not paused:
            space.step(1 / 60)
        space.debug_draw(draw_options)

        pygame.display.flip()
        clock.tick(60)


def main():
    """Dispatches the simulation loop, and handles resetting or ending the program."""
    reset = True
    while reset:
        reset = simulation()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    """Runs the main() function."""
    main()