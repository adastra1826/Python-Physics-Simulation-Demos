import pygame
import pymunk
import pymunk.pygame_util
import random
import math
from pygame import gfxdraw

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Staircase Physics Simulation")

# Clock for controlling frame rate
clock = pygame.time.Clock()
FPS = 60

# Colors
BACKGROUND = (10, 10, 30)
STAIR_COLORS = [
    (70, 40, 120),  # Purple base
    (80, 50, 130),
    (90, 60, 140),
    (100, 70, 150),
    (110, 80, 160)
]
BALL_COLORS = [
    (255, 100, 100),  # Red
    (100, 255, 100),  # Green
    (100, 100, 255),  # Blue
    (255, 255, 100),  # Yellow
    (255, 100, 255),  # Pink
    (100, 255, 255),  # Cyan
]

# Physics setup
space = pymunk.Space()
space.gravity = (0, 900)  # Default gravity
draw_options = pymunk.pygame_util.DrawOptions(screen)

# Create the stairs
def create_stairs(stair_pattern="standard"):
    """
    Create a staircase with the specified pattern.
    
    Args:
        stair_pattern (str): The pattern of stairs to create:
            - "standard": Regular evenly-spaced stairs
            - "wide": Wider steps with more space between them
            - "narrow": Narrower steps with less space between them
            - "spiral": Stairs that form a spiral pattern
    
    Returns:
        list: List of tuples containing (body, shape, color) for each stair
    """
    global stair_width, stair_height
    
    # Remove existing stairs from space
    for body, shape, _ in stairs:
        space.remove(shape, body)
    
    new_stairs = []
    num_stairs = 10
    
    if stair_pattern == "wide":
        stair_width = WIDTH // (num_stairs / 2)
        stair_height = 25
    elif stair_pattern == "narrow":
        stair_width = WIDTH // (num_stairs * 1.5)
        stair_height = 15
    else:
        stair_width = WIDTH // (num_stairs + 1)
        stair_height = 20
        
    # Create stairs based on pattern
    for i in range(num_stairs):
        if stair_pattern == "standard":
            x = (i + 1) * stair_width
            y = HEIGHT - (i + 1) * 40
            
        elif stair_pattern == "wide":
            x = (i + 1) * (stair_width / 2)
            y = HEIGHT - (i + 1) * 50
            
        elif stair_pattern == "narrow":
            x = (i + 1) * (stair_width * 1.2)
            y = HEIGHT - (i + 1) * 30
            
        elif stair_pattern == "spiral":
            angle = i * (math.pi / 5)
            radius = 200 - (i * 10)
            center_x, center_y = WIDTH / 2, HEIGHT / 2
            x = center_x + radius * math.cos(angle) - stair_width / 2
            y = center_y + radius * math.sin(angle) - stair_height / 2
            
        # Create a box shape for the stair
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = (x, y)
        shape = pymunk.Poly.create_box(body, (stair_width, stair_height))
        shape.elasticity = 0.5
        shape.friction = 0.7
        space.add(body, shape)
        
        # Store stair info for drawing
        color_idx = i % len(STAIR_COLORS)
        new_stairs.append((body, shape, STAIR_COLORS[color_idx]))
        
    return new_stairs

# Ball properties
ball_radius = 15
balls = []

# Particle system
particles = []

class Particle:
    """
    A visual particle emitted during collisions to enhance visual feedback.
    
    Particles have position, velocity, color, size, and lifespan properties.
    They gradually fade and shrink over time until they disappear.
    """
    def __init__(self, x, y, color):
        """
        Initialize a new particle at the specified position with given color.
        
        Args:
            x (float): X-coordinate of the particle's starting position
            y (float): Y-coordinate of the particle's starting position
            color (tuple): RGB color tuple for the particle
        """
        self.x = x
        self.y = y
        self.color = color
        self.size = random.uniform(1, 3)
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.life = random.uniform(30, 60)
    
    def update(self):
        """
        Update particle position, size, and lifespan for the next frame.
        
        Particles move according to their velocity, gradually shrink in size,
        and decrease their remaining lifespan.
        """
        self.x += self.vx
        self.y += self.vy
        self.size -= 0.05
        self.life -= 1
        
    def draw(self, surface):
        """
        Draw the particle on the specified surface.
        
        Particle opacity is determined by its remaining life.
        
        Args:
            surface (pygame.Surface): Surface on which to draw the particle
        """
        alpha = min(255, max(0, self.life * 4))
        color = (self.color[0], self.color[1], self.color[2], alpha)
        gfxdraw.filled_circle(surface, int(self.x), int(self.y), int(self.size), color)

# Ball class
class Ball:
    """
    Represents a physical ball that interacts with the environment.
    
    A ball has physical properties (position, velocity, mass), visual properties (color, trails),
    and interacts with the physics engine through its body and shape.
    """
    def __init__(self, x, y):
        """
        Initialize a new ball at the specified position.
        
        Args:
            x (float): X-coordinate of the ball's starting position
            y (float): Y-coordinate of the ball's starting position
        """
        # Create physical body with appropriate mass and moment of inertia
        self.body = pymunk.Body(1, pymunk.moment_for_circle(1, 0, ball_radius))
        self.body.position = (x, y)
        
        # Create circular shape for collision detection
        self.shape = pymunk.Circle(self.body, ball_radius)
        self.shape.elasticity = 0.8
        self.shape.friction = 0.7
        self.shape.collision_type = 1  # Used for collision handling
        
        # Visual properties
        self.color = random.choice(BALL_COLORS)
        self.last_positions = []  # For motion trails
        
        # Add to physics space
        space.add(self.body, self.shape)
    
    def update_trail(self):
        """
        Update the ball's motion trail by recording its current position.
        
        Maintains a fixed-length history of positions to create a fading trail effect.
        """
        self.last_positions.append((self.body.position.x, self.body.position.y))
        if len(self.last_positions) > 10:  # Keep only 10 positions for the trail
            self.last_positions.pop(0)
            
    def draw_trail(self, surface):
        """
        Draw the ball's motion trail on the specified surface.
        
        More recent positions have higher opacity and larger size.
        
        Args:
            surface (pygame.Surface): Surface on which to draw the trail
        """
        for i, pos in enumerate(self.last_positions):
            alpha = i * 25  # Fade out older positions
            size = ball_radius * (i / 10)  # Smaller size for older positions
            color = (self.color[0], self.color[1], self.color[2], alpha)
            if size > 0:
                gfxdraw.filled_circle(surface, int(pos[0]), int(pos[1]), int(size), color)

# Create a surface for trails with alpha support
trail_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

# Collision handler for particle generation
def collision_handler(arbiter, space, data):
    """
    Handle collisions between balls and other objects in the physics space.
    
    This callback is triggered when a collision occurs. It generates visual particles
    based on the force of impact to provide visual feedback of the collision.
    
    Args:
        arbiter (pymunk.Arbiter): Contains information about the collision
        space (pymunk.Space): The physics space
        data (dict): Custom data passed to the handler, including a ball dictionary
        
    Returns:
        bool: True to allow the colliding objects to interact physically
    """
    for c in arbiter.contact_point_set.points:
        force = arbiter.total_impulse.length
        if force > 20:  # Only generate particles for significant collisions
            pos = c.point_a
            ball = data['ball_dict'].get(arbiter.shapes[0], None)
            if ball:
                for _ in range(int(force / 10)):
                    particles.append(Particle(pos.x, pos.y, ball.color))
    return True

# Initialize variables
stairs = []
current_stair_pattern = "standard"

# Create initial stairs
stairs = create_stairs(current_stair_pattern)

# Process keyboard controls
def process_keys():
    """
    Process keyboard input to control simulation parameters.
    
    Handles:
    - Gravity direction and strength (arrow keys)
    - Adding new balls (space)
    - Modifying stair elasticity (e/d keys)
    - Clearing all objects (c key)
    - Resetting gravity (r key)
    - Changing stair patterns (1-5 keys)
    
    This function should be called once per frame to check for user input.
    """
    keys = pygame.key.get_pressed()
    global stairs, current_stair_pattern
    
    # Gravity controls
    gravity_change = 50
    if keys[pygame.K_UP]:
        space.gravity = (space.gravity.x, space.gravity.y - gravity_change)
    if keys[pygame.K_DOWN]:
        space.gravity = (space.gravity.x, space.gravity.y + gravity_change)
    if keys[pygame.K_LEFT]:
        space.gravity = (space.gravity.x - gravity_change, space.gravity.y)
    if keys[pygame.K_RIGHT]:
        space.gravity = (space.gravity.x + gravity_change, space.gravity.y)
    
    # Reset gravity
    if keys[pygame.K_r]:
        space.gravity = (0, 900)
    
    # Add new balls
    if keys[pygame.K_SPACE]:
        x = random.randint(ball_radius, WIDTH - ball_radius)
        y = random.randint(ball_radius, HEIGHT // 4)
        add_ball(x, y)
    
    # Modify stair elasticity
    if keys[pygame.K_e]:
        for _, shape, _ in stairs:
            shape.elasticity = min(1.0, shape.elasticity + 0.01)
    if keys[pygame.K_d]:
        for _, shape, _ in stairs:
            shape.elasticity = max(0.0, shape.elasticity - 0.01)
    
    # Clear all balls
    if keys[pygame.K_c]:
        for ball in balls[:]:
            remove_ball(ball)
        particles.clear()
        
    # Change stair pattern
    key_pressed = False
    new_pattern = current_stair_pattern
    
    if keys[pygame.K_1] and not key_pressed:
        new_pattern = "standard"
        key_pressed = True
    elif keys[pygame.K_2] and not key_pressed:
        new_pattern = "wide"
        key_pressed = True
    elif keys[pygame.K_3] and not key_pressed:
        new_pattern = "narrow"
        key_pressed = True
    elif keys[pygame.K_4] and not key_pressed:
        new_pattern = "spiral"
        key_pressed = True
        
    if new_pattern != current_stair_pattern:
        current_stair_pattern = new_pattern
        stairs = create_stairs(current_stair_pattern)

def add_ball(x, y):
    """
    Create a new ball at the specified position and add it to the simulation.
    
    Args:
        x (float): X-coordinate for the new ball
        y (float): Y-coordinate for the new ball
        
    Returns:
        Ball: The newly created ball object
    """
    ball = Ball(x, y)
    balls.append(ball)
    ball_dict[ball.shape] = ball  # Register ball in the shape dictionary for collision handling
    return ball

def remove_ball(ball):
    """
    Remove a ball from the simulation.
    
    Handles proper cleanup by removing the ball from all relevant collections
    and from the physics space.
    
    Args:
        ball (Ball): The ball object to remove
    """
    if ball in balls:
        balls.remove(ball)
        if ball.shape in ball_dict:
            del ball_dict[ball.shape]
        space.remove(ball.shape, ball.body)

# Set up collision handlers
ball_dict = {}  # Map shapes to ball objects
handler = space.add_collision_handler(1, 0)
handler.data["ball_dict"] = ball_dict
handler.post_solve = collision_handler

# Font for displaying info
font = pygame.font.SysFont(None, 24)

# Add initial balls
for i in range(3):
    x = WIDTH // 2 + random.randint(-100, 100)
    y = HEIGHT // 4
    add_ball(x, y)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                add_ball(event.pos[0], event.pos[1])
    
    # Process keyboard controls
    process_keys()
    
    # Clear the screen
    screen.fill(BACKGROUND)
    trail_surface.fill((0, 0, 0, 0))  # Clear the trail surface
    
    # Update physics
    space.step(1/FPS)
    
    # Draw stairs
    for body, _, color in stairs:
        vertices = []
        for x, y in pymunk.Poly.create_box(body, (stair_width, stair_height)).get_vertices():
            vertices.append(pymunk.pygame_util.to_pygame((body.position.x + x, body.position.y + y), screen))
        pygame.draw.polygon(screen, color, vertices)
        pygame.draw.polygon(screen, (255, 255, 255), vertices, 1)  # White outline
    
    # Update and draw ball trails
    for ball in balls:
        ball.update_trail()
        ball.draw_trail(trail_surface)
    
    # Draw the trail surface
    screen.blit(trail_surface, (0, 0))
    
    # Draw balls
    for ball in balls:
        pos = pymunk.pygame_util.to_pygame(ball.body.position, screen)
        pygame.draw.circle(screen, ball.color, pos, ball_radius)
        
        # Add highlight to make balls look 3D
        highlight_pos = (int(pos[0] - ball_radius/3), int(pos[1] - ball_radius/3))
        pygame.draw.circle(screen, (255, 255, 255, 150), highlight_pos, ball_radius/4)
    
    # Update and draw particles
    new_particles = []
    for particle in particles:
        particle.update()
        if particle.life > 0 and particle.size > 0:
            particle.draw(trail_surface)
            new_particles.append(particle)
    particles = new_particles
    
    # Clean up balls that have fallen off the screen
    for ball in balls[:]:
        if ball.body.position.y > HEIGHT + 100:
            remove_ball(ball)
    
    # Display controls info
    info_text = [
        "Controls:",
        "SPACE - Add balls",
        "MOUSE CLICK - Add ball at cursor",
        "UP/DOWN/LEFT/RIGHT - Change gravity",
        "R - Reset gravity",
        "E/D - Increase/Decrease bounce",
        "C - Clear all objects",
        "1-5 - Change stair pattern:",
        "  1: Standard",
        "  2: Wide",
        "  3: Narrow", 
        
        "  4: Spiral",
        f"Pattern: {current_stair_pattern}",
        f"Balls: {len(balls)}",
        f"Gravity: ({space.gravity.x:.0f}, {space.gravity.y:.0f})",
        f"Elasticity: {stairs[0][1].elasticity:.2f}"
    ]
    
    for i, text in enumerate(info_text):
        text_surface = font.render(text, True, (255, 255, 255))
        screen.blit(text_surface, (10, 10 + i * 20))
    
    # Update the display
    pygame.display.flip()
    
    # Cap the frame rate
    clock.tick(FPS)

pygame.quit()