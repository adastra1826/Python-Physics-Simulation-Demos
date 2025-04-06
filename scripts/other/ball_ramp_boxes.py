import sys
import pymunk
import pymunk.pygame_util
import pygame
import random
import math

# Initialize Pygame
pygame.init()

#########################
# SETUP AND CONSTANTS
#########################

# Set up display dimensions
WIDTH, HEIGHT = 800, 600
BALL_RADIUS = 20 # Radius of the rolling balls
BLOCK_SIZE = 50 # Size of stackable blocks
BUTTON_WIDTH = 100 # Width of UI buttons
BUTTON_HEIGHT = 30 # Height of UI buttons
BUTTON_MARGIN = 10 # Margin between UI elements
RAMP_CORNER_RADIUS = 10 # Radius for the interactive ramp corner handle

# Define colors with RGBA values for consistent rendering
BUTTON_COLOR = (100, 100, 100, 255) # Default button color
BUTTON_HOVER_COLOR = (120, 120, 120, 255) # Button color when mouse hovers over it
BUTTON_TEXT_COLOR = (255, 255, 255, 255) # Text color for buttons
RAMP_INTERACTIVE_COLOR = (255, 200, 0, 255) # Color for the interactive ramp control point
RAMP_COLOR = (100, 100, 100, 255) # Default ramp color

# Energy visualization colors
LOW_ENERGY_COLOR = (0, 255, 0, 255) # Green for low kinetic energy
HIGH_ENERGY_COLOR = (255, 0, 0, 255) # Red for high kinetic energy
MAX_KINETIC_ENERGY = 100000 # Threshold value for maximum color intensity

# Background gradient colors
BACKGROUND_START_COLOR = (25, 25, 50) # Dark blue/purple at top
BACKGROUND_END_COLOR = (70, 40, 60) # Lighter purple at bottom

# Create the main game window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
draw_options = pymunk.pygame_util.DrawOptions(screen) # Setup drawing options for pymunk objects
clock = pygame.time.Clock() # Clock for controlling frame rate

#########################
# PHYSICS SETUP
#########################

# Set up the Pymunk physics space
space = pymunk.Space() # Create the physics world
space.gravity = (0, 1000) # Set gravity (x, y) - positive y means downward
space.damping = 0.9 # Add damping to reduce velocity over time (simulates air resistance)

#########################
# BACKGROUND ELEMENTS
#########################

# Create stars for the background
stars = []
for _ in range(100):
    x = random.randint(0, WIDTH)
    y = random.randint(0, HEIGHT)
    radius = random.uniform(0.5, 2) # Random star size
    speed = random.uniform(0.1, 0.5) # Random twinkle speed
    stars.append([x, y, radius, speed])

# Create clouds for the background
clouds = []
for _ in range(5):
    x = random.randint(-100, WIDTH)
    y = random.randint(50, 200) # Keep clouds near top of screen
    speed = random.uniform(0.2, 0.8) # Random horizontal movement speed
    size = random.uniform(0.8, 1.5) # Random cloud size
    clouds.append([x, y, speed, size])

# Create a cloud image using simple shapes
cloud_img = pygame.Surface((100, 60), pygame.SRCALPHA) # Transparent surface
# Draw three overlapping ellipses to create a cloud shape
pygame.draw.ellipse(cloud_img, (255, 255, 255, 180), (0, 10, 50, 40))
pygame.draw.ellipse(cloud_img, (255, 255, 255, 180), (20, 0, 60, 50))
pygame.draw.ellipse(cloud_img, (255, 255, 255, 180), (50, 10, 50, 40))

# Initialize mountain points only once at startup to prevent flickering
def initialize_mountain_points():
    """
    Create the mountain points once to prevent flickering.
    Returns two sets of points representing different mountain ranges.
    """
    # First mountain range (farther away)
    points1 = [(0, HEIGHT - 150)]
    for x in range(0, WIDTH + 50, 50):
        # Use sine function with random variation to create natural looking peaks
        points1.append((x, HEIGHT - 150 - math.sin(x * 0.01) * 70 - random.randint(-10, 10)))
    points1.append((WIDTH, HEIGHT - 150))
    points1.append((WIDTH, HEIGHT))
    points1.append((0, HEIGHT))

    # Second mountain range (closer to viewer)
    points2 = [(0, HEIGHT - 100)]
    for x in range(0, WIDTH + 30, 30):
        # Different frequency and amplitude for variety
        points2.append((x, HEIGHT - 100 - math.sin(x * 0.02) * 50 - random.randint(-5, 5)))
    points2.append((WIDTH, HEIGHT - 100))
    points2.append((WIDTH, HEIGHT))
    points2.append((0, HEIGHT))

    return points1, points2

# Generate mountain points once at startup
mountain_points1, mountain_points2 = initialize_mountain_points()

# List to store impact visual effects
impact_effects = []

#########################
# PHYSICS OBJECT CREATION FUNCTIONS
#########################

def create_ramp(space, start_point, end_point):
    """
    Creates an inclined ramp for the ball to roll down.

    Args:
        space: The pymunk space to add the ramp to
        start_point: The top point of the ramp (x, y)
        end_point: The bottom point of the ramp (x, y)

    Returns:
        Tuple of (body, shape) for the ramp
    """
    body = pymunk.Body(body_type=pymunk.Body.STATIC) # Static body doesn't move
    shape = pymunk.Segment(body, start_point, end_point, 8) # Line segment with thickness 8
    shape.elasticity = 0.1 # Low elasticity (not very bouncy)
    shape.friction = 1.0 # High friction for better rolling
    shape.color = RAMP_COLOR # Set default ramp color
    space.add(body, shape) # Add both body and shape to the physics space
    return body, shape

def create_ground(space):
    """
    Creates the static ground where blocks will be stacked.

    Args:
        space: The pymunk space to add the ground to

    Returns:
        Tuple of (body, shape) for the ground
    """
    body = pymunk.Body(body_type=pymunk.Body.STATIC) # Static body doesn't move
    shape = pymunk.Segment(body, (50, HEIGHT - 50), (WIDTH - 50, HEIGHT - 50), 5) # Horizontal line
    shape.elasticity = 0.9 # More bouncy than the ramp
    shape.friction = 1.0 # High friction
    space.add(body, shape)
    return body, shape

def create_ball(space, position):
    """
    Creates a rolling ball at a specified position.

    Args:
        space: The pymunk space to add the ball to
        position: The (x, y) position to place the ball

    Returns:
        Tuple of (body, shape) for the ball
    """
    mass = 50
    radius = BALL_RADIUS
    moment = pymunk.moment_for_circle(mass, 0, radius) # Calculate moment of inertia for a circle
    body = pymunk.Body(mass, moment)
    body.position = position
    shape = pymunk.Circle(body, radius)
    shape.elasticity = 0.8 # Fairly bouncy
    shape.friction = 0.5 # Medium friction
    shape.filter = pymunk.ShapeFilter(categories=1, mask=1) # For collision filtering

    # Add a custom attribute to track previous kinetic energy for impact detection
    body.prev_kinetic_energy = 0

    space.add(body, shape)
    return body, shape

def create_blocks(space):
    """
    Creates a stack of blocks.

    Args:
        space: The pymunk space to add the blocks to

    Returns:
        Tuple of (list of block bodies/shapes, list of initial positions)
    """
    blocks = []
    initial_block_positions = [] # Store initial positions for reset functionality

    # Create a 5x3 grid of blocks
    for i in range(5): # Rows
        for j in range(3): # Columns
            mass = 1
            size = (BLOCK_SIZE, BLOCK_SIZE)
            moment = pymunk.moment_for_box(mass, size) # Calculate moment of inertia for a box
            body = pymunk.Body(mass, moment)
            body.position = (WIDTH - 300 + j * BLOCK_SIZE, HEIGHT - 100 - i * BLOCK_SIZE)
            shape = pymunk.Poly.create_box(body, size)
            shape.elasticity = 0.3 # Not very bouncy
            shape.friction = 0.7 # Fairly high friction

            # Add a custom attribute to track previous kinetic energy for impact detection
            body.prev_kinetic_energy = 0

            space.add(body, shape)
            blocks.append((body, shape))
            initial_block_positions.append(body.position) # Store initial position

    return blocks, initial_block_positions

def reset_blocks(blocks, initial_block_positions):
    """
    Resets blocks to their initial positions.

    Args:
        blocks: List of (body, shape) tuples for the blocks
        initial_block_positions: List of initial positions
    """
    for i, (body, shape) in enumerate(blocks):
        body.position = initial_block_positions[i]
        body.velocity = (0, 0) # Stop movement
        body.angular_velocity = 0 # Stop rotation
        body.prev_kinetic_energy = 0 # Reset energy tracking

def clear_balls(space, balls):
    """
    Removes all balls from the physics space.

    Args:
        space: The pymunk space to remove the balls from
        balls: List of (body, shape) tuples for the balls
    """
    for body, shape in balls:
        space.remove(body, shape)
    balls.clear() # Empty the list

#########################
# PHYSICS CALCULATIONS
#########################

def calculate_kinetic_energy(body):
    """
    Calculate the kinetic energy of a body.

    Args:
        body: A pymunk Body object

    Returns:
        Total kinetic energy (linear + rotational)
    """
    linear_velocity = body.velocity.length
    angular_velocity = body.angular_velocity

    # KE = 0.5 * m * v² + 0.5 * I * ω²
    linear_energy = 0.5 * body.mass * linear_velocity**2
    angular_energy = 0.5 * body.moment * angular_velocity**2

    return linear_energy + angular_energy

def get_energy_color(energy):
    """
    Get a color ranging from green to red based on kinetic energy.

    Args:
        energy: The kinetic energy value

    Returns:
        RGBA color tuple representing energy level (now with alpha)
    """
    # Calculate ratio between 0 and 1 based on energy compared to max
    ratio = min(energy / MAX_KINETIC_ENERGY, 1.0)

    # Linear interpolation between low and high energy colors
    r = int(LOW_ENERGY_COLOR[0] + (HIGH_ENERGY_COLOR[0] - LOW_ENERGY_COLOR[0]) * ratio)
    g = int(LOW_ENERGY_COLOR[1] + (HIGH_ENERGY_COLOR[1] - LOW_ENERGY_COLOR[1]) * ratio)
    b = int(LOW_ENERGY_COLOR[2] + (HIGH_ENERGY_COLOR[2] - LOW_ENERGY_COLOR[2]) * ratio)

    return (r, g, b, 255)  # Return RGBA by adding alpha=255

def add_impact_effect(position, energy):
    """
    Add a visual impact effect at the given position with size based on energy.

    Args:
        position: The (x, y) position for the effect
        energy: The energy value that determines the effect size
    """
    # Scale radius with energy, capped at 50
    radius = min(10 + energy / 5000, 50)

    # Scale lifetime with energy, capped at 60 frames
    lifetime = min(30 + energy / 2000, 60)

    # Add the effect to the list
    impact_effects.append({
        'position': position,
        'radius': radius,
        'lifetime': lifetime,
        'max_lifetime': lifetime, # Store original lifetime for fade calculations
        'energy': energy
    })

#########################
# DRAWING FUNCTIONS
#########################

def draw_gradient_background(screen, start_color, end_color):
    """
    Draw a vertical gradient background.

    Args:
        screen: The pygame surface to draw on
        start_color: RGB color for the top of the screen
        end_color: RGB color for the bottom of the screen
    """
    # Fill with start color first to ensure no flickering
    screen.fill(start_color)

    # Draw horizontal lines with gradually changing color
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        # Linear interpolation between start and end colors
        r = start_color[0] * (1 - ratio) + end_color[0] * ratio
        g = start_color[1] * (1 - ratio) + end_color[1] * ratio
        b = start_color[2] * (1 - ratio) + end_color[2] * ratio
        pygame.draw.line(screen, (int(r), int(g), int(b)), (0, y), (WIDTH, y))

def draw_mountains(screen, points1, points2):
    """
    Draw decorative mountains in the background using pre-defined points.

    Args:
        screen: The pygame surface to draw on
        points1: List of points for the farther mountain range
        points2: List of points for the closer mountain range
    """
    mountain_color1 = (60, 70, 90) # Darker for farther mountains
    mountain_color2 = (80, 90, 110) # Lighter for closer mountains

    # Draw mountains as filled polygons
    pygame.draw.polygon(screen, mountain_color1, points1)
    pygame.draw.polygon(screen, mountain_color2, points2)

def draw_button(screen, rect, text, mouse_pos, clicked):
    """
    Draws a button with hover and click effects.

    Args:
        screen: The pygame surface to draw on
        rect: The pygame Rect for the button
        text: The text to display on the button
        mouse_pos: Current mouse position (x, y)
        clicked: Boolean indicating if mouse was clicked

    Returns:
        Boolean indicating if this button was clicked
    """
    # Determine button color based on mouse interaction
    color = BUTTON_COLOR
    if rect.collidepoint(mouse_pos):
        color = BUTTON_HOVER_COLOR
        if clicked:
            color = BUTTON_COLOR # Standard color on click

    # Draw the button rectangle
    pygame.draw.rect(screen, color, rect)

    # Draw the button text
    font = pygame.font.Font(None, 24)
    text_surface = font.render(text, True, BUTTON_TEXT_COLOR)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)

    # Return True if button is clicked
    return rect.collidepoint(mouse_pos) and clicked

#########################
# INITIALIZE GAME OBJECTS
#########################

# Initial positions
ramp_start_point = (WIDTH / 5, HEIGHT - 200) # Top of the ramp
ramp_end_point = (WIDTH / 2, HEIGHT - 50) # Bottom of the ramp

# Create static physics objects
ground_shape = create_ground(space)
ramp_body, ramp_shape = create_ramp(space, ramp_start_point, ramp_end_point)

# Create dynamic physics objects
blocks, initial_block_positions = create_blocks(space)
balls = [] # Start with no balls

# Create UI elements
reset_button_rect = pygame.Rect(WIDTH - (BUTTON_WIDTH + BUTTON_MARGIN), BUTTON_MARGIN,
                                    BUTTON_WIDTH, BUTTON_HEIGHT)
clear_balls_button_rect = pygame.Rect(WIDTH - (BUTTON_WIDTH + BUTTON_MARGIN),
                                            BUTTON_MARGIN * 2 + BUTTON_HEIGHT,
                                            BUTTON_WIDTH, BUTTON_HEIGHT)

# Energy display box
energy_display_rect = pygame.Rect(10, 10, 200, 30)

# Interaction state variables
dragging_ramp_corner = False # Flag for drag state
ramp_corner_offset = (0, 0) # Offset between mouse and corner when dragging
interactive_corner_pos = ramp_start_point # Position of draggable ramp corner

#########################
# COLLISION HANDLING
#########################

def collision_handler(arbiter, space, data):
    """
    Handle collisions between shapes - detect impacts and create visual effects.

    Args:
        arbiter: The pymunk Arbiter object containing collision data
        space: The pymunk Space
        data: Additional data (unused)

    Returns:
        True to allow the default collision behavior
    """
    shapes = arbiter.shapes
    bodies = [shapes[0].body, shapes[1].body]

    # Calculate impact energy for each colliding body
    for body in bodies:
        # Ensure prev_kinetic_energy exists, initialize if not
        if not hasattr(body, 'prev_kinetic_energy'):
            body.prev_kinetic_energy = 0

        # Get current energy
        current_energy = calculate_kinetic_energy(body)

        # Calculate change in energy
        energy_change = abs(body.prev_kinetic_energy - current_energy)

        # If significant energy change, add impact effect
        if energy_change > 5000: # Threshold to avoid effects for small impacts
            add_impact_effect(body.position, energy_change)

        # Update previous energy
        body.prev_kinetic_energy = current_energy

    return True # Continue with normal collision handling

# Set up collision handler
handler = space.add_default_collision_handler()
handler.post_solve = collision_handler # Called after collision is resolved

#########################
# MAIN GAME LOOP
#########################

running = True
while running:
    # Get current mouse position and reset click state
    mouse_pos = pygame.mouse.get_pos()
    mouse_clicked = False

    # Draw background elements
    draw_gradient_background(screen, BACKGROUND_START_COLOR, BACKGROUND_END_COLOR)

    # Update and draw stars (twinkling effect)
    for star in stars:
        x, y, radius, speed = star
        # Calculate brightness based on time for twinkling effect
        brightness = 150 + int(50 * math.sin(pygame.time.get_ticks() * speed * 0.01))
        color = (brightness, brightness, brightness)
        pygame.draw.circle(screen, color, (int(x), int(y)), radius)

    # Draw mountains using pre-defined points
    draw_mountains(screen, mountain_points1, mountain_points2)

    # Update and draw clouds
    for cloud in clouds:
        x, y, speed, size = cloud
        # Move cloud horizontally
        x += speed
        # Wrap around when off screen
        if x > WIDTH + 100:
            x = -100
            y = random.randint(50, 200)
        cloud[0] = x # Update x position in the list

        # Scale and draw the cloud
        scaled_cloud = pygame.transform.scale(cloud_img, (int(100 * size), int(60 * size)))
        screen.blit(scaled_cloud, (int(x), int(y)))

    #########################
    # EVENT HANDLING
    #########################

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_clicked = True

            # Check if reset button was clicked
            if reset_button_rect.collidepoint(mouse_pos):
                reset_blocks(blocks, initial_block_positions)

            # Check if clear balls button was clicked
            elif clear_balls_button_rect.collidepoint(mouse_pos):
                clear_balls(space, balls)

            # Check if ramp corner was clicked for dragging
            elif math.dist(mouse_pos, interactive_corner_pos) <= RAMP_CORNER_RADIUS:
                dragging_ramp_corner = True
                # Calculate offset between mouse position and corner position
                ramp_corner_offset = (interactive_corner_pos[0] - mouse_pos[0],
                                            interactive_corner_pos[1] - mouse_pos[1])

            # If no UI element clicked, create a ball at mouse position
            else:
                balls.append(create_ball(space, event.pos))

        elif event.type == pygame.MOUSEBUTTONUP:
            dragging_ramp_corner = False # Stop dragging when mouse released

        elif event.type == pygame.MOUSEMOTION:
            # Update ramp position while dragging
            if dragging_ramp_corner:
                # Calculate new corner position based on mouse and offset
                new_corner_pos = (mouse_pos[0] + ramp_corner_offset[0],
                                   mouse_pos[1] + ramp_corner_offset[1])

                interactive_corner_pos = new_corner_pos # Update interactive corner position

                # Recreate the ramp with the new position
                space.remove(ramp_body, ramp_shape) # Remove old ramp
                ramp_body, ramp_shape = create_ramp(space, new_corner_pos, ramp_end_point)
                ramp_start_point = new_corner_pos # Update for next drag

    # Step the physics simulation (60 FPS)
    space.step(1 / 60)

    #########################
    # UPDATE OBJECT STATES
    #########################

    # Track total kinetic energy in the system
    total_kinetic_energy = 0

    # Update ball colors based on their kinetic energy
    for ball_body, ball_shape in balls:
        energy = calculate_kinetic_energy(ball_body)
        total_kinetic_energy += energy

        # Update ball color based on kinetic energy
        ball_shape.color = get_energy_color(energy)

        # Update previous energy
        ball_body.prev_kinetic_energy = energy

    # Update block colors based on their kinetic energy
    for block_body, block_shape in blocks:
        energy = calculate_kinetic_energy(block_body)
        total_kinetic_energy += energy

        # Update block color based on kinetic energy
        color = get_energy_color(energy)
        block_shape.color = color

        # Update previous energy
        block_body.prev_kinetic_energy = energy

    # Update and draw impact effects
    for i in range(len(impact_effects) - 1, -1, -1):
        effect = impact_effects[i]
        effect['lifetime'] -= 1 # Reduce remaining lifetime

        # Remove expired effects
        if effect['lifetime'] <= 0:
            impact_effects.pop(i)
        else:
            # Calculate color and opacity based on remaining lifetime
            color = get_energy_color(effect['energy'])
            alpha = int(255 * (effect['lifetime'] / effect['max_lifetime']))

            # Draw the impact circle with fading effect
            surf = pygame.Surface((effect['radius'] * 2, effect['radius'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (color[0], color[1], color[2], alpha), (effect['radius'], effect['radius']), effect['radius'])
            screen.blit(surf, (effect['position'][0] - effect['radius'], effect['position'][1] - effect['radius']))

    #########################
    # DRAW UI AND GAME OBJECTS
    #########################

    # Draw interactive ramp corner handle
    pygame.draw.circle(screen, RAMP_INTERACTIVE_COLOR,
                             (int(interactive_corner_pos[0]), int(interactive_corner_pos[1])),
                             RAMP_CORNER_RADIUS)

    # Draw all physics objects
    space.debug_draw(draw_options)

    # Draw UI Buttons
    draw_button(screen, reset_button_rect, "Reset Boxes", mouse_pos, mouse_clicked)
    draw_button(screen, clear_balls_button_rect, "Clear Balls", mouse_pos, mouse_clicked)

    # Draw energy display
    # pygame.draw.rect(screen, (0, 0, 0, 180), energy_display_rect)
    # font = pygame.font.Font(None, 24)
    # energy_text = f"Total Kinetic Energy: {int(total_kinetic_energy)}"
    # text_surface = font.render(energy_text, True, (255, 255, 255))
    # screen.blit(text_surface, (energy_display_rect.x + 5, energy_display_rect.y + 5))

    # Update display and maintain frame rate
    pygame.display.flip()
    clock.tick(60) # 60 FPS

# Clean up and exit
pygame.quit()
sys.exit()