"""
Spring System Physics Simulation.

This simulation models the behavior of interconnected spring-mass systems.
It demonstrates principles of oscillatory motion, Hooke's Law, harmonic and
anharmonic oscillations, and how energy transfers through coupled oscillators.
The simulation shows how springs store and release potential energy, how damping
affects motion decay, and how complex behaviors emerge when multiple springs
interact. It visualizes concepts like resonance, natural frequency, and how
initial conditions and interconnectedness affect the evolution of the system -
principles that are fundamental to understanding mechanical vibrations in
engineering systems and natural phenomena.
"""

import pygame
import pymunk
import pymunk.pygame_util
import sys
import math

# Constants
WIDTH, HEIGHT = 800, 600
BACKGROUND = (25, 25, 40)  # Dark blue-gray background
GROUND_COLOR = (80, 200, 120)  # Green ground
SPRING_COLOR = (255, 215, 0)  # Gold spring
BALL_COLOR = (220, 120, 120)  # Soft red ball
TEXT_COLOR = (220, 220, 240)  # Light text
GRID_COLOR = (50, 50, 70)  # Subtle grid lines

# Pygame initialization
pygame.init()
pygame.display.set_caption("Spring Physics Simulation")
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 16)

# Pymunk initialization
space = pymunk.Space()
space.gravity = (0, 900)  # simulate gravity

# Create a static body for the ground
ground_body = pymunk.Body(body_type=pymunk.Body.STATIC)
ground_height = HEIGHT - 50
ground_shape = pymunk.Segment(ground_body, (0, ground_height), (WIDTH, ground_height), 10)
ground_shape.elasticity = 0.9
ground_shape.friction = 0.5
ground_shape.color = GROUND_COLOR  # For debug drawing only
space.add(ground_body, ground_shape)

# Create a dynamic body for the spring
spring_body = pymunk.Body(mass=1, moment=10)
spring_body.position = (WIDTH // 2, HEIGHT // 2)
spring_shape = pymunk.Circle(spring_body, 20)
spring_shape.elasticity = 0.9
spring_shape.friction = 0.5
spring_shape.color = BALL_COLOR  # For debug drawing only
space.add(spring_body, spring_shape)

# Create a spring joint
rest_length = 200
stiffness = 100
damping = 0.8
spring_joint = pymunk.DampedSpring(
    spring_body, ground_body, 
    (0, 0),  # Local anchor on spring_body
    (WIDTH // 2, 0),  # Local anchor on ground_body
    rest_length, stiffness, damping
)
space.add(spring_joint)

# Create trail effect
trail = []
MAX_TRAIL = 50

# Drawing helper for spring
def draw_spring(surface, start_pos, end_pos, color, width=2, coils=8, amplitude=10):
    """
    Draw a coiled spring between two points.

    Args:
        surface (pygame.Surface): The surface to draw on.
        start_pos (tuple): The starting position of the spring (x, y).
        end_pos (tuple): The ending position of the spring (x, y).
        color (tuple): The color of the spring in RGB format.
        width (int, optional): The width of the spring lines. Defaults to 2.
        coils (int, optional): The number of coils in the spring. Defaults to 8.
        amplitude (int, optional): The amplitude of the coils. Defaults to 10.
    """
    dx = end_pos[0] - start_pos[0]
    dy = end_pos[1] - start_pos[1]
    length = math.sqrt(dx*dx + dy*dy)
    
    # Unit direction vector
    if length > 0:
        udx, udy = dx/length, dy/length
    else:
        return
    
    # Perpendicular unit vector
    perpx, perpy = -udy, udx
    
    # Draw the coiled spring
    segment_length = length / (coils * 2)
    points = [start_pos]
    
    for i in range(1, coils * 2):
        # Alternate direction of coil
        side = amplitude if i % 2 else -amplitude
        # Position along spring length
        pos = i * segment_length
        x = start_pos[0] + udx * pos + perpx * side
        y = start_pos[1] + udy * pos + perpy * side
        points.append((x, y))
    
    points.append(end_pos)
    
    # Draw the spring
    if len(points) > 1:
        pygame.draw.lines(surface, color, False, points, width)

# Main loop
running = True
paused = False
show_debug = False
frame_count = 0
#
while running:
    """
    The main function to run the spring physics simulation.
    Initializes the Pygame environment, creates the simulation objects, and runs the main loop.
    """
    for event in pygame.event.get():
        """
        Handles user input events such as quitting, key presses, and mouse clicks.
        """
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
            elif event.key == pygame.K_d:
                show_debug = not show_debug
            elif event.key == pygame.K_r:
                # Reset ball position
                spring_body.position = (WIDTH // 2, HEIGHT // 2)
                spring_body.velocity = (0, 0)
                trail = []
            elif event.key == pygame.K_UP:
                stiffness += 20
                spring_joint.stiffness = stiffness
            elif event.key == pygame.K_DOWN:
                stiffness = max(20, stiffness - 20)
                spring_joint.stiffness = stiffness
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Grab the ball with mouse
            mouse_pos = pygame.mouse.get_pos()
            if ((mouse_pos[0] - spring_body.position.x)**2 + 
                (mouse_pos[1] - spring_body.position.y)**2 <= spring_shape.radius**2):
                spring_body.position = pymunk.Vec2d(mouse_pos[0], mouse_pos[1])
                spring_body.velocity = (0, 0)
    
    # Get mouse position if mouse button is held down
    if pygame.mouse.get_pressed()[0]:
        mouse_pos = pygame.mouse.get_pos()
        spring_body.position = pymunk.Vec2d(mouse_pos[0], mouse_pos[1])
        spring_body.velocity = (0, 0)
    
    # Clear screen
    screen.fill(BACKGROUND)
    
    # Draw grid
    for x in range(0, WIDTH, 50):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, 50):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y), 1)
    
    # Draw trail
    if len(trail) > 1:
        """
        Draws the trail of the spring body.
        """
        for i in range(1, len(trail)):
            alpha = int(255 * (i / len(trail)))
            color = (BALL_COLOR[0], BALL_COLOR[1], BALL_COLOR[2], alpha)
            width = max(1, int(i / len(trail) * 3))
            pygame.draw.line(screen, color, 
                            (int(trail[i-1][0]), int(trail[i-1][1])),
                            (int(trail[i][0]), int(trail[i][1])), width)
    
    # Draw ground
    pygame.draw.rect(screen, GROUND_COLOR, (0, ground_height, WIDTH, HEIGHT - ground_height))
    
   # Draw spring anchor point (at top)
    pygame.draw.circle(screen, SPRING_COLOR, (WIDTH // 2, 0), 8)
        
    # Draw spring
    spring_start = (spring_body.position.x, spring_body.position.y)
    spring_end = (WIDTH // 2, 0)  # Connect to top of screen
    draw_spring(screen, spring_start, spring_end, SPRING_COLOR, 3)
    
    # Draw ball
    pygame.draw.circle(screen, BALL_COLOR, (int(spring_body.position.x), int(spring_body.position.y)), int(spring_shape.radius))
    
    # Update physics if not paused
    if not paused:
        # Add current position to trail
        trail.append((spring_body.position.x, spring_body.position.y))
        if len(trail) > MAX_TRAIL:
            trail.pop(0)
        
        space.step(1/60.0)
        frame_count += 1
    
    # Display information
    info_texts = [
        f"FPS: {int(clock.get_fps())}",
        f"Stiffness: {int(stiffness)}",
        f"Damping: {damping:.2f}",
        f"Ball position: ({int(spring_body.position.x)}, {int(spring_body.position.y)})",
        f"Velocity: ({int(spring_body.velocity.x)}, {int(spring_body.velocity.y)})",
        f"Energy: {int(spring_body.kinetic_energy)}",
        "",
        "Controls:",
        "SPACE - Pause/Resume",
        "R - Reset position",
        "UP/DOWN - Adjust stiffness",
        "D - Toggle debug",
        "Mouse - Drag ball"
    ]
    
    for i, text in enumerate(info_texts):
        text_surface = font.render(text, True, TEXT_COLOR)
        screen.blit(text_surface, (10, 10 + i * 20))
    
    # Show "PAUSED" overlay when game is paused
    if paused:
        pause_font = pygame.font.SysFont("Arial", 48, bold=True)
        pause_text = pause_font.render("PAUSED", True, (255, 255, 255))
        text_rect = pause_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 100))
        # Draw semi-transparent background
        s = pygame.Surface((pause_text.get_width() + 20, pause_text.get_height() + 20), pygame.SRCALPHA)
        s.fill((0, 0, 0, 128))
        screen.blit(s, (text_rect.x - 10, text_rect.y - 10))
        screen.blit(pause_text, text_rect)
    
    # Update display
    pygame.display.flip()
    clock.tick(60)

# Clean up properly
pygame.quit()
sys.exit()