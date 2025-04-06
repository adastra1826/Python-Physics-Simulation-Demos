"""
Interactive Physics Sliders Simulation.

This simulation provides an interactive interface with sliders to control
various physical parameters in real-time. It demonstrates how changing physical
constants affects the behavior of simulated objects, helping visualize the
relationships between parameters like gravity, friction, elasticity, and mass.
The simulation serves as an educational tool for exploring how adjusting these
parameters influences physical interactions in a controlled environment.
"""

import pygame
import pymunk
import pymunk.pygame_util
import random
import math
import sys

# Initialize pygame
pygame.init()

# Screen dimensions and settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball Physics on Zigzag Surface")
clock = pygame.time.Clock()
FPS = 60

# Colors
BACKGROUND = (20, 20, 35)
ZIGZAG_COLOR = (80, 100, 120)
TEXT_COLOR = (240, 240, 240)
TIME_COLOR = (180, 180, 220)
SLIDER_BG_COLOR = (60, 60, 80)
SLIDER_FG_COLOR = (120, 140, 200)
SLIDER_HANDLE_COLOR = (200, 220, 255)
BALL_COLORS = [
    (255, 70, 70),    # Red
    (70, 220, 70),    # Green
    (70, 120, 255),   # Blue
    (255, 220, 70),   # Yellow
    (220, 70, 220),   # Purple
    (70, 220, 220),   # Cyan
    (255, 150, 70),   # Orange
]

# Physics parameters - can be adjusted via sliders
GRAVITY = 900  # Acceleration due to gravity (pixels/s^2)
BALL_ELASTICITY = 0.7  # Coefficient of restitution (0 = inelastic, 1 = perfectly elastic)
BALL_FRICTION = 0.5  # Coefficient of friction (0 = no friction, 1 = high friction)
SPAWN_RATE = 1.0  # Balls per second
SURFACE_FRICTION = 0.8  # Friction of zigzag surface
SURFACE_ELASTICITY = 0.6  # Elasticity of zigzag surface
BALL_SIZE_RANGE = (10, 30)  # Min and max ball radius in pixels

# Zigzag parameters
ZIGZAG_WIDTH = WIDTH - 100  # Total width of zigzag pattern
ZIGZAG_TOP_Y = HEIGHT - 150  # Vertical position of zigzag
ZIGZAG_AMPLITUDE = 25  # Height of zigzags (peak-to-peak)
ZIGZAG_FREQUENCY = 12  # Number of zigzag peaks
ZIGZAG_THICKNESS = 8  # Thickness of zigzag lines

# Initialize pymunk space (physics world)
space = pymunk.Space()
space.gravity = (0, GRAVITY)  # Set gravity vector (x, y)
draw_options = pymunk.pygame_util.DrawOptions(screen)

# Game state
balls = []  # Stores all active balls
start_time = None  # When simulation started
simulation_running = False  # Whether simulation is active
zigzag_points = []  # Stores points for drawing zigzag
spawn_timer = 0  # Tracks time between ball spawns
active_slider = None  # Currently dragged slider

class Slider:
    """UI slider for adjusting simulation parameters"""
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label, format_str="{:.1f}"):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.format_str = format_str
        self.handle_radius = 10
        self.dragging = False
        
    def draw(self):
        """Draw the slider on screen"""
        # Draw background track
        pygame.draw.rect(screen, SLIDER_BG_COLOR, self.rect, border_radius=5)
        
        # Draw filled portion based on current value
        fill_width = int((self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
        pygame.draw.rect(
            screen, 
            SLIDER_FG_COLOR, 
            pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height),
            border_radius=5
        )
        
        # Draw border
        pygame.draw.rect(screen, (100, 100, 120), self.rect, 2, border_radius=5)
        
        # Draw handle at current value position
        handle_x = self.rect.x + fill_width
        handle_y = self.rect.y + self.rect.height // 2
        pygame.draw.circle(screen, SLIDER_HANDLE_COLOR, (handle_x, handle_y), self.handle_radius)
        
        # Draw label and current value
        font = pygame.font.SysFont('Arial', 16)
        text = font.render(f"{self.label}: {self.format_str.format(self.value)}", True, TEXT_COLOR)
        screen.blit(text, (self.rect.x, self.rect.y - 25))
    
    def is_over_handle(self, pos):
        """Check if mouse is over the slider handle"""
        handle_x = self.rect.x + (self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width
        handle_y = self.rect.y + self.rect.height // 2
        
        # Calculate distance from mouse to handle center
        distance = math.sqrt((pos[0] - handle_x) ** 2 + (pos[1] - handle_y) ** 2)
        return distance <= self.handle_radius
    
    def update_value(self, mouse_x):
        """Update slider value based on mouse position"""
        # Clamp mouse position to slider bounds
        normalized_x = max(self.rect.x, min(self.rect.x + self.rect.width, mouse_x))
        # Calculate value based on position within slider range
        self.value = self.min_val + (normalized_x - self.rect.x) / self.rect.width * (self.max_val - self.min_val)
        return self.value

# Create sliders for adjustable parameters
gravity_slider = Slider(50, 50, 200, 15, 100, 1500, GRAVITY, "Gravity", "{:.0f}")
elasticity_slider = Slider(50, 100, 200, 15, 0.1, 0.95, BALL_ELASTICITY, "Elasticity")
spawn_rate_slider = Slider(50, 150, 200, 15, 0.1, 5.0, SPAWN_RATE, "Spawn Rate")

sliders = [gravity_slider, elasticity_slider, spawn_rate_slider]

def create_zigzag_surface():
    """Create the zigzag surface physics objects and return drawing points"""
    segments = []
    points = []
    
    def create_zigzag(start_x, end_x, y, zigzag_count, amplitude):
        """Generate points for a zigzag pattern"""
        points = []
        total_width = end_x - start_x
        segment_width = total_width / zigzag_count
        
        # Create points alternating between peaks and valleys
        for i in range(zigzag_count + 1):
            x = start_x + i * segment_width
            # Alternate between positive and negative amplitude offsets
            offset = amplitude if i % 2 == 0 else -amplitude
            points.append((x, y + offset))
        
        return points
    
    # Create main zigzag section
    center_x = WIDTH // 2
    zigzag_section = create_zigzag(
        center_x - ZIGZAG_WIDTH//2,
        center_x + ZIGZAG_WIDTH//2,
        ZIGZAG_TOP_Y,
        ZIGZAG_FREQUENCY,
        ZIGZAG_AMPLITUDE
    )
    
    points.extend(zigzag_section)
    
    # Create physics segments between each zigzag point
    for i in range(len(zigzag_section) - 1):
        # Static bodies don't move (infinite mass)
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        # Create line segment between points
        shape = pymunk.Segment(body, zigzag_section[i], zigzag_section[i+1], ZIGZAG_THICKNESS)
        shape.elasticity = SURFACE_ELASTICITY
        shape.friction = SURFACE_FRICTION
        space.add(body, shape)
        segments.append(shape)
    
    # Create side walls to contain balls
    wall_height = 300
    
    # Left wall
    left_wall = pymunk.Body(body_type=pymunk.Body.STATIC)
    left_wall_shape = pymunk.Segment(
        left_wall,
        (center_x - ZIGZAG_WIDTH//2, ZIGZAG_TOP_Y - ZIGZAG_AMPLITUDE),
        (center_x - ZIGZAG_WIDTH//2, ZIGZAG_TOP_Y - wall_height),
        ZIGZAG_THICKNESS
    )
    left_wall_shape.elasticity = SURFACE_ELASTICITY
    left_wall_shape.friction = SURFACE_FRICTION
    space.add(left_wall, left_wall_shape)
    segments.append(left_wall_shape)
    
    # Right wall
    right_wall = pymunk.Body(body_type=pymunk.Body.STATIC)
    right_wall_shape = pymunk.Segment(
        right_wall,
        (center_x + ZIGZAG_WIDTH//2, ZIGZAG_TOP_Y - ZIGZAG_AMPLITUDE),
        (center_x + ZIGZAG_WIDTH//2, ZIGZAG_TOP_Y - wall_height),
        ZIGZAG_THICKNESS
    )
    right_wall_shape.elasticity = SURFACE_ELASTICITY
    right_wall_shape.friction = SURFACE_FRICTION
    space.add(right_wall, right_wall_shape)
    segments.append(right_wall_shape)
    
    return segments, points

def create_ball(position=None):
    """Create a new physics ball with random properties"""
    # Random size and mass (mass proportional to area)
    radius = random.uniform(BALL_SIZE_RANGE[0], BALL_SIZE_RANGE[1])
    mass = math.pi * radius**2 * 0.001  # Mass based on area with scaling factor
    color = random.choice(BALL_COLORS)
    
    # Position - either specified or random at top
    if position:
        x, y = position
    else:
        x = random.uniform(WIDTH//4, WIDTH*3//4)
        y = 50
    
    # Calculate moment of inertia for circular body
    moment = pymunk.moment_for_circle(mass, 0, radius)
    body = pymunk.Body(mass, moment)
    body.position = (x, y)
    
    # Small random initial velocity
    body.velocity = (random.uniform(-20, 20), random.uniform(-10, 10))
    
    # Create circular collision shape
    shape = pymunk.Circle(body, radius)
    shape.elasticity = BALL_ELASTICITY
    shape.friction = BALL_FRICTION
    shape.color = color  # Store color for drawing
    
    space.add(body, shape)
    
    return {
        'body': body,
        'shape': shape,
        'radius': radius,
        'color': color,
        'creation_time': pygame.time.get_ticks()
    }

def draw_zigzag_surface():
    """Draw the visible zigzag surface"""
    for i in range(len(zigzag_points) - 1):
        # Main surface line
        pygame.draw.line(
            screen, ZIGZAG_COLOR, 
            zigzag_points[i], zigzag_points[i+1], 
            ZIGZAG_THICKNESS * 2
        )
        
        # Highlight for 3D effect
        pygame.draw.line(
            screen, (120, 140, 160), 
            zigzag_points[i], zigzag_points[i+1], 
            2
        )

def draw_ui():
    """Draw all user interface elements"""
    # Timer display
    if simulation_running and start_time is not None:
        elapsed_time = (pygame.time.get_ticks() - start_time) / 1000
        timer_text = f"Time: {elapsed_time:.1f}s"
        font = pygame.font.SysFont('Arial', 24)
        text_surface = font.render(timer_text, True, TIME_COLOR)
        screen.blit(text_surface, (WIDTH - text_surface.get_width() - 20, 20))
    
    # Ball counter
    count_text = f"Balls: {len(balls)}"
    font = pygame.font.SysFont('Arial', 24)
    text_surface = font.render(count_text, True, TEXT_COLOR)
    screen.blit(text_surface, (WIDTH - text_surface.get_width() - 20, 50))
    
    # Draw all sliders
    for slider in sliders:
        slider.draw()
    
    # Start message
    if not simulation_running:
        message = "Press SPACE to start simulation"
        font = pygame.font.SysFont('Arial', 28, bold=True)
        text_surface = font.render(message, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
        
        # Draw background panel
        padding = 20
        bg_rect = pygame.Rect(text_rect.left - padding, text_rect.top - padding,
                             text_rect.width + padding*2, text_rect.height + padding*2)
        pygame.draw.rect(screen, (0, 0, 0, 128), bg_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), bg_rect, 2, border_radius=10)
        
        screen.blit(text_surface, text_rect)
    
    # Controls legend
    controls_text = [
        "Controls:",
        "SPACE: Start/Reset",
        "ESC: Exit",
        "R: Clear Balls"
    ]
    
    font = pygame.font.SysFont('Arial', 16)
    for i, text in enumerate(controls_text):
        text_surface = font.render(text, True, TEXT_COLOR)
        screen.blit(text_surface, (50, 200 + i * 25))

def reset_simulation():
    """Reset the simulation to initial state"""
    global balls, start_time, simulation_running, spawn_timer
    
    # Remove all balls from physics space
    for ball in balls:
        space.remove(ball['body'], ball['shape'])
    balls = []
    
    # Reset simulation state
    start_time = pygame.time.get_ticks()
    simulation_running = True
    spawn_timer = 0

# Create initial zigzag surface
surface_segments, zigzag_points = create_zigzag_surface()

# Main game loop
running = True
while running:
    # Fixed timestep for physics (1/FPS seconds)
    dt = 1 / FPS
    
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                reset_simulation()
            elif event.key == pygame.K_r:  # Clear all balls
                for ball in balls:
                    space.remove(ball['body'], ball['shape'])
                balls = []
        
        # Slider interaction
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                for slider in sliders:
                    if slider.is_over_handle(event.pos):
                        active_slider = slider
                        break
        
        elif event.type == pygame.MOUSEBUTTONUP:
            active_slider = None
            
        elif event.type == pygame.MOUSEMOTION:
            if active_slider:
                # Update slider value and apply changes
                active_slider.update_value(event.pos[0])
                
                if active_slider == gravity_slider:
                    GRAVITY = active_slider.value
                    space.gravity = (0, GRAVITY)
                elif active_slider == elasticity_slider:
                    BALL_ELASTICITY = active_slider.value
                elif active_slider == spawn_rate_slider:
                    SPAWN_RATE = active_slider.value
    
    # Physics update
    space.step(dt)
    
    # Remove balls that fall off screen
    for ball in balls[:]:
        if ball['body'].position.y > HEIGHT + 100:
            space.remove(ball['body'], ball['shape'])
            balls.remove(ball)
    
    # Spawn new balls according to spawn rate
    if simulation_running:
        spawn_timer += dt
        if spawn_timer >= 1.0 / SPAWN_RATE:
            balls.append(create_ball())
            spawn_timer = 0
    
    # Rendering
    screen.fill(BACKGROUND)
    
    # Gradient background
    for y in range(0, HEIGHT, 2):
        alpha = int(80 * (y / HEIGHT))
        pygame.draw.line(screen, (50, 50, 70, alpha), (0, y), (WIDTH, y))
    
    # Draw zigzag surface
    draw_zigzag_surface()
    
    # Draw all balls with shadows and highlights
    for ball in balls:
        position = ball['body'].position
        color = ball['color']
        radius = ball['radius']
        
        # Shadow effect
        shadow_offset = 3
        pygame.draw.circle(screen, (0, 0, 0, 100), 
                          (int(position.x + shadow_offset), int(position.y + shadow_offset)), 
                          int(radius))
        
        # Ball body
        pygame.draw.circle(screen, color, (int(position.x), int(position.y)), int(radius))
        
        # Highlight for 3D effect
        highlight_pos = (int(position.x - radius*0.3), int(position.y - radius*0.3))
        highlight_radius = radius * 0.3
        s = pygame.Surface((int(highlight_radius*2), int(highlight_radius*2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 255, 100), 
                          (int(highlight_radius), int(highlight_radius)), 
                          int(highlight_radius))
        screen.blit(s, (highlight_pos[0], highlight_pos[1]))
        
        # Velocity vector for large balls
        if radius > 20:
            vel = ball['body'].velocity
            vel_length = math.sqrt(vel.x**2 + vel.y**2)
            
            if vel_length > 10:
                scale = radius / vel_length
                end_x = position.x + vel.x * scale
                end_y = position.y + vel.y * scale
                
                pygame.draw.line(screen, (255, 255, 255), 
                                (int(position.x), int(position.y)), 
                                (int(end_x), int(end_y)), 2)
    
    # Draw UI elements
    draw_ui()
    
    # Update display
    pygame.display.flip()
    
    # Maintain framerate
    clock.tick(FPS)

pygame.quit()
sys.exit()