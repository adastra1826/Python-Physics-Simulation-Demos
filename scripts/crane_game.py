"""
Crane Simulation with Pymunk Physics

This script simulates a crane that can move objects from one location to another.
The crane can be controlled using keyboard inputs to move, raise/lower the hook,
and attach/detach objects. The goal is to move objects into a container.

Features:
- Realistic physics simulation using Pymunk
- Interactive crane controls
- Object attachment/detachment
- Container for collecting objects
- Visual indicators for grab status and object count
"""

import pymunk
import pymunk.pygame_util
import pygame
import math

# Initialize Pygame
pygame.init()

# Simulation parameters
FPS = 60  # Frames per second
WIDTH, HEIGHT = 800, 800  # Window dimensions

# Space physics parameters
SPACE_GRAVITY = (0, 981)  # Gravity vector (x, y) in pixels/second²
SPACE_DAMPING = 0.9  # Damping factor to simulate air resistance

# Dimensions and properties for various components
# Ground
GROUND_THICKNESS = 10  # Thickness of the ground in pixels
GROUND_ELASTICITY = 0.1  # How bouncy the ground is (0-1)
GROUND_FRICTION = 0.5  # How much friction the ground has (0-1)

# Crane dimensions and properties
CRANE_BASE_WIDTH, CRANE_BASE_HEIGHT = 50, 50  # Base dimensions
BOOM_Y_POS = 300  # Vertical position of the boom
BOOM_THICKNESS = 10  # Thickness of the boom
BOOM_LENGTH = WIDTH - 300  # Length of the main boom
COUNTER_BOOM_LENGTH = BOOM_LENGTH / 4  # Length of the counter-balance boom
MAST_HEIGHT = HEIGHT - GROUND_THICKNESS - CRANE_BASE_HEIGHT - BOOM_Y_POS  # Height of the mast
MAST_THICKNESS = 10  # Thickness of the mast

# Counterweight properties
COUNTERWEIGHT_WIDTH, COUNTERWEIGHT_HEIGHT = 30, 30  # Counterweight dimensions
COUNTERWEIGHT_MASS = 10  # Mass of the counterweight

# Trolley properties
TROLLEY_WIDTH, TROLLEY_HEIGHT = 20, 20  # Trolley dimensions
TROLLEY_MIN_X = TROLLEY_WIDTH * 2  # Minimum x-position of the trolley
TROLLEY_MAX_X = BOOM_LENGTH - TROLLEY_WIDTH  # Maximum x-position of the trolley

# Hook properties
HOOK_WIDTH, HOOK_HEIGHT = 10, 10  # Hook dimensions
HOOK_MASS = 1  # Mass of the hook

# Obstacle (object to be moved) properties
OBSTACLE_WIDTH, OBSTACLE_HEIGHT = 30, 30  # Obstacle dimensions
OBSTACLE_MASS = 10  # Mass of each obstacle
OBSTACLE_ELASTICITY = 0.9  # How bouncy the obstacles are (0-1)
OBSTACLE_FRICTION = 0.5  # How much friction the obstacles have (0-1)

# Container properties
CONTAINER_WIDTH, CONTAINER_HEIGHT = OBSTACLE_WIDTH * 4, OBSTACLE_HEIGHT * 5  # Container dimensions
CONTAINER_WALL_THICKNESS = BOOM_THICKNESS / 2  # Thickness of container walls
CONTAINER_ELASTICITY = 0.7  # How bouncy the container walls are (0-1)
CONTAINER_FRICTION = 0.5  # How much friction the container walls have (0-1)

# Rope parameters
INITIAL_ROPE_LENGTH = 100  # Initial length of the rope
ROPE_STIFFNESS = 1000  # How stiff the rope is
ROPE_DAMPING = 60  # How much the rope dampens movement
MIN_ROPE_LENGTH = 20  # Minimum rope length
MAX_ROPE_LENGTH = 500  # Maximum rope length

# Map keys to controls
K_MOVE_LEFT = pygame.K_a  # Move crane left
K_MOVE_RIGHT = pygame.K_d  # Move crane right
K_TROLLEY_LEFT = pygame.K_j  # Move trolley left
K_TROLLEY_RIGHT = pygame.K_l  # Move trolley right
K_HOOK_UP = pygame.K_i  # Raise hook
K_HOOK_DOWN = pygame.K_k  # Lower hook
K_ATTACH = pygame.K_w  # Attach/detach objects
K_DETACH = pygame.K_w

# Movement speeds
CRANE_MOVE_SPEED = 1  # Speed of crane movement
TROLLEY_MOVE_SPEED = 3  # Speed of trolley movement
ROPE_MOVE_SPEED = 3  # Speed of rope extension/retraction

# Colors (RGBA format)
BACKGROUND_COLOR = (173, 216, 230, 255)  # Light blue background
CRANE_COLOR = (255, 215, 0, 255)  # Gold crane
TROLLEY_COLOR = (255, 165, 0, 255)  # Orange trolley
HOOK_COLOR = (255, 0, 0, 255)  # Red hook
CONTAINER_COLOR = (0, 0, 255, 255)  # Blue container
GROUND_COLOR = (139, 69, 19, 255)  # Brown ground
OBSTACLE_COLOR = (105, 105, 105, 255)  # Gray obstacles
CAN_GRAB_COLOR = (10, 255, 10, 255)  # Green for "can grab" indicator
CANNOT_GRAB_COLOR = (255, 10, 10, 255)  # Red for "cannot grab" indicator

def simulate():
    """
    Main simulation function that sets up the physics world and runs the game loop.
    
    This function:
    1. Sets up the Pygame display and Pymunk physics space
    2. Creates all physical objects (crane, trolley, hook, obstacles, container)
    3. Runs the main game loop handling input, physics updates, and rendering
    
    Returns:
        bool: True if simulation should be reset, False if it should quit
    """
    # Set up the display
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # Set up the Pymunk space
    space = pymunk.Space()
    space.gravity = SPACE_GRAVITY
    space.damping = SPACE_DAMPING

    # Counter for objects in container
    objects_in_container = 0

    # Create the ground
    ground_body = pymunk.Body(body_type=pymunk.Body.STATIC)
    ground_shape = pymunk.Segment(ground_body, (0, HEIGHT - GROUND_THICKNESS), (WIDTH, HEIGHT - GROUND_THICKNESS), 5)
    ground_shape.elasticity = GROUND_ELASTICITY
    ground_shape.friction = GROUND_FRICTION
    ground_shape.color = GROUND_COLOR
    space.add(ground_body, ground_shape)

    # Create the crane body (kinematic body that doesn't respond to physics)
    crane_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)

    # Create the crane base
    crane_body.position = (100, HEIGHT - GROUND_THICKNESS - CRANE_BASE_HEIGHT / 2)
    crane_base_shape = pymunk.Poly.create_box(crane_body, size=(CRANE_BASE_WIDTH, CRANE_BASE_HEIGHT))
    crane_base_shape.color = CRANE_COLOR
    mast_shape = pymunk.Segment(crane_body, (0, -CRANE_BASE_HEIGHT / 2), (0, -CRANE_BASE_HEIGHT / 2 - MAST_HEIGHT), BOOM_THICKNESS)
    mast_shape.color = CRANE_COLOR
    boom_shape = pymunk.Segment(crane_body, (0, -CRANE_BASE_HEIGHT / 2 - MAST_HEIGHT), (BOOM_LENGTH, - CRANE_BASE_HEIGHT / 2 - MAST_HEIGHT), BOOM_THICKNESS)
    boom_shape.color = CRANE_COLOR
    counter_boom_shape = pymunk.Segment(crane_body, (0, -CRANE_BASE_HEIGHT / 2 - MAST_HEIGHT), (-COUNTER_BOOM_LENGTH, -CRANE_BASE_HEIGHT / 2 - MAST_HEIGHT), BOOM_THICKNESS)
    counter_boom_shape.color = CRANE_COLOR
    counterweight_shape = pymunk.Segment(crane_body, (-COUNTER_BOOM_LENGTH, -CRANE_BASE_HEIGHT / 2 - MAST_HEIGHT + BOOM_THICKNESS), (-COUNTER_BOOM_LENGTH, -CRANE_BASE_HEIGHT / 2 - MAST_HEIGHT + BOOM_THICKNESS - COUNTERWEIGHT_HEIGHT), COUNTERWEIGHT_WIDTH)
    counterweight_shape.color = CRANE_COLOR
    space.add(crane_body, crane_base_shape, mast_shape, boom_shape, counter_boom_shape, counterweight_shape)

    # Create the trolley (kinematic body that moves along the boom)
    trolley_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
    trolley_body.position = (crane_body.position.x + TROLLEY_WIDTH * 2, crane_body.position.y - CRANE_BASE_HEIGHT / 2 - MAST_HEIGHT + BOOM_THICKNESS + TROLLEY_HEIGHT / 2)
    trolley_shape = pymunk.Poly.create_box(trolley_body, size=(TROLLEY_WIDTH, TROLLEY_HEIGHT))
    trolley_shape.color = TROLLEY_COLOR
    space.add(trolley_body, trolley_shape)

    # Create the hook as a dynamic body (responds to physics)
    hook_moment = pymunk.moment_for_box(HOOK_MASS, (HOOK_WIDTH, HOOK_HEIGHT))
    hook_body = pymunk.Body(mass=HOOK_MASS, moment=hook_moment)
    hook_body.position = (trolley_body.position.x, trolley_body.position.y + TROLLEY_HEIGHT / 2 + INITIAL_ROPE_LENGTH)
    hook_shape = pymunk.Poly.create_box(hook_body, size=(HOOK_WIDTH, HOOK_HEIGHT))
    hook_shape.color = HOOK_COLOR
    space.add(hook_body, hook_shape)

    # Create a rope (constraint) between the trolley and the hook
    rope_length = INITIAL_ROPE_LENGTH
    rope = pymunk.DampedSpring(trolley_body, hook_body, (0, TROLLEY_HEIGHT / 2), (0, -HOOK_HEIGHT / 2), rope_length, ROPE_STIFFNESS, ROPE_DAMPING)
    space.add(rope)

    # Create the objects to be moved
    objects = []
    for i in range(8):
        object_moment = pymunk.moment_for_box(OBSTACLE_MASS, (OBSTACLE_WIDTH, OBSTACLE_HEIGHT))
        object_body = pymunk.Body(mass=OBSTACLE_MASS, moment=object_moment)
        object_body.position = (crane_body.position.x + 100 + i * (OBSTACLE_WIDTH * 2), HEIGHT - GROUND_THICKNESS - OBSTACLE_HEIGHT / 2)
        object_shape = pymunk.Poly.create_box(object_body, size=(OBSTACLE_WIDTH, OBSTACLE_HEIGHT))
        object_shape.elasticity = OBSTACLE_ELASTICITY
        object_shape.friction = OBSTACLE_FRICTION
        object_shape.color = OBSTACLE_COLOR
        space.add(object_body, object_shape)
        objects.append((object_body, object_shape))

    # Create the container
    container_body = pymunk.Body(body_type=pymunk.Body.STATIC)
    container_body.position = (WIDTH - CONTAINER_WIDTH / 2 - OBSTACLE_WIDTH, HEIGHT - GROUND_THICKNESS - CONTAINER_WALL_THICKNESS)
    space.add(container_body)
    edges = [
        ((-CONTAINER_WIDTH / 2, -CONTAINER_HEIGHT), (-CONTAINER_WIDTH / 2, 0)),  # Left wall
        ((-CONTAINER_WIDTH / 2, 0), (CONTAINER_WIDTH / 2, 0)),  # Bottom
        ((CONTAINER_WIDTH / 2, 0), (CONTAINER_WIDTH / 2, -CONTAINER_HEIGHT)),  # Right wall
    ]
    for edge in edges:
        container_shape = pymunk.Segment(container_body, edge[0], edge[1], CONTAINER_WALL_THICKNESS)
        container_shape.elasticity = CONTAINER_ELASTICITY
        container_shape.friction = CONTAINER_FRICTION
        space.add(container_shape)

    # Set up the drawing options
    draw_options = pymunk.pygame_util.DrawOptions(screen)

    # Game loop
    attached_object = None  # Currently attached object (if any)
    paused = False  # Pause state
    while True:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == K_ATTACH or event.key == K_DETACH:
                    if attached_object is None:
                        # Try to attach to an object
                        for obj in objects:
                            if (
                                hook_body.position.x > obj[0].position.x - OBSTACLE_WIDTH / 2 and 
                                hook_body.position.x < obj[0].position.x + OBSTACLE_WIDTH / 2 and
                                hook_body.position.y > obj[0].position.y - OBSTACLE_HEIGHT / 2 - HOOK_HEIGHT
                            ):
                                # Create a joint between the hook and the object
                                joint = pymunk.PivotJoint(hook_body, obj[0], hook_body.position)
                                joint.max_force = math.inf
                                space.add(joint)
                                attached_object = obj
                                break
                    else:
                        # Detach from the current object
                        # Remove all joints between the hook and the attached object
                        for joint in space.constraints:
                            if isinstance(joint, pymunk.PivotJoint) and (joint.a == hook_body or joint.b == hook_body):
                                space.remove(joint)
                        attached_object = None
                elif event.key == pygame.K_SPACE:
                    paused = not paused  # Toggle pause state
                elif event.key == pygame.K_r:
                    return True  # Reset simulation
                elif event.key == pygame.K_q:
                    return False  # Quit simulation

        # Handle continuous key presses for movement
        keys = pygame.key.get_pressed()
        if keys[K_MOVE_LEFT]:
            crane_body.position = (crane_body.position.x - CRANE_MOVE_SPEED, crane_body.position.y)
            trolley_body.position = (trolley_body.position.x - CRANE_MOVE_SPEED, trolley_body.position.y)
        if keys[K_MOVE_RIGHT]:
            crane_body.position = (crane_body.position.x + CRANE_MOVE_SPEED, crane_body.position.y)
            trolley_body.position = (trolley_body.position.x + CRANE_MOVE_SPEED, trolley_body.position.y)
        if keys[K_HOOK_UP]:
            # Decrease rope length (raise hook)
            rope_length = max(MIN_ROPE_LENGTH, rope_length - ROPE_MOVE_SPEED)
            rope.rest_length = rope_length
        if keys[K_HOOK_DOWN]:
            # Increase rope length (lower hook)
            rope_length = min(MAX_ROPE_LENGTH, rope_length + ROPE_MOVE_SPEED)
            rope.rest_length = rope_length
        if keys[K_TROLLEY_LEFT]:
            trolley_body.position = (max(TROLLEY_MIN_X + crane_body.position.x, trolley_body.position.x - TROLLEY_MOVE_SPEED), trolley_body.position.y)
        if keys[K_TROLLEY_RIGHT]:
            trolley_body.position = (min(TROLLEY_MAX_X + crane_body.position.x, trolley_body.position.x + TROLLEY_MOVE_SPEED), trolley_body.position.y)

        # Check if any objects are in the container
        objects_in_container = 0
        for obj in objects:
            # Check if object is within container bounds
            if (obj[0].position.x > WIDTH - CONTAINER_WIDTH - OBSTACLE_WIDTH and 
                obj[0].position.x < WIDTH - OBSTACLE_WIDTH and
                obj[0].position.y > HEIGHT - GROUND_THICKNESS - CONTAINER_HEIGHT and
                obj[0].position.y < HEIGHT - GROUND_THICKNESS):
                objects_in_container += 1

        # Check if hook can grab any object
        can_grab = False
        for obj in objects:
            if (hook_body.position.x > obj[0].position.x - OBSTACLE_WIDTH / 2 and 
                hook_body.position.x < obj[0].position.x + OBSTACLE_WIDTH / 2 and
                hook_body.position.y > obj[0].position.y - OBSTACLE_HEIGHT / 2 - HOOK_HEIGHT):
                can_grab = True
                break

        # Draw control instructions
        font = pygame.font.Font(None, 24)
        controls = [
            "Controls:",
            "A/D - Move crane left/right",
            "J/L - Move trolley left/right",
            "I/K - Raise/lower hook",
            "W - Attach/detach objects",
            "Space - Pause simulation",
            "R - Reset simulation",
            "Q - Quit"
        ]
        
        # Add container counter to controls
        controls.append(f"Objects in container: {objects_in_container}/{len(objects)}")
        
        # Add grab indicator to controls
        grab_text = "Can grab" if can_grab else "Cannot grab"
        controls.append(grab_text)
        
        # Calculate total height needed for all text
        line_height = 25
        total_height = len(controls) * line_height
        
        # Clear the screen and draw the background
        screen.fill(BACKGROUND_COLOR)
        
        # Draw the physics objects
        space.debug_draw(draw_options)
        
        # Draw the rope manually (since it's a constraint)
        pygame.draw.line(screen, HOOK_COLOR, 
                         (trolley_body.position.x, trolley_body.position.y + TROLLEY_HEIGHT / 2),
                         (hook_body.position.x, hook_body.position.y - HOOK_HEIGHT / 2), 2)
        
        # Draw semi-transparent background for text
        text_surface = pygame.Surface((250, total_height + 10))
        text_surface.set_alpha(128)
        text_surface.fill((255, 255, 255))
        screen.blit(text_surface, (10, 10))
        
        # Draw each line of text
        for i, text in enumerate(controls):
            # Use different color for the grab indicator
            if i == len(controls) - 1:  # Last line is the grab indicator
                text_color = CAN_GRAB_COLOR if can_grab else CANNOT_GRAB_COLOR
            else:
                text_color = (0, 0, 0)
            
            text_surface = font.render(text, True, text_color)
            screen.blit(text_surface, (15, 15 + i * line_height))
        
        # Update the display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(60)

        # Update physics if not paused
        if not paused:
            space.step(1 / FPS)

def main():
    """
    Main entry point for the application.
    
    This function runs the simulation in a loop, allowing for resetting
    the simulation when requested.
    """
    reset = True
    while reset:
        reset = simulate()

    pygame.quit()

if __name__ == '__main__':
    main()

