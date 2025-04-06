import pygame
import pymunk
import pymunk.pygame_util
import random
import math
from pygame import gfxdraw
from pygame.locals import *

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Raindrop Ripple Simulation - Enhanced")

# Colors
SKY_TOP = (50, 80, 120)  # Darker blue at top
SKY_BOTTOM = (135, 206, 235)  # Lighter blue at bottom
RAIN_COLOR = (220, 220, 255)
PUDDLE_COLOR = (70, 130, 180, 180)  # Semi-transparent
RIPPLE_COLOR = (180, 220, 255)
SPLASH_COLOR = (200, 230, 255)

# Physics space
space = pymunk.Space()
space.gravity = (0, 900)  # Gravity pointing downward

# Puddle parameters
PUDDLE_RADIUS = 180
PUDDLE_POSITION = (WIDTH // 2, HEIGHT - 40)

# Raindrop parameters
MIN_RAINDROP_RADIUS = 2
MAX_RAINDROP_RADIUS = 8
RAINDROP_SPAWN_RATE = 0.05  # Probability per frame
RAINDROP_ELASTICITY = 0.3

# Ripple parameters
MAX_RIPPLES = 30
RIPPLE_GROWTH_RATE = 2.0
RIPPLE_DECAY_RATE = 0.92

# Splash parameters
MAX_SPLASHES = 15
SPLASH_PARTICLES = 8
SPLASH_DURATION = 0.8  # seconds

# Simulation controls
running = True
clock = pygame.time.Clock()
FPS = 60

# Create puddle body (static)
puddle_body = pymunk.Body(body_type=pymunk.Body.STATIC)
puddle_body.position = PUDDLE_POSITION
puddle_shape = pymunk.Circle(puddle_body, PUDDLE_RADIUS)
puddle_shape.elasticity = 0.5
puddle_shape.friction = 0.3
puddle_shape.collision_type = 2
space.add(puddle_body, puddle_shape)

# Store raindrops, ripples, and splashes
raindrops = []
ripples = []
splashes = []

# UI controls
font = pygame.font.SysFont('Arial', 14)
rain_intensity = 0.05  # 0 to 1
min_radius = 2
max_radius = 6


def create_raindrop():
    """Create a new raindrop with random properties"""
    radius = random.uniform(min_radius, max_radius)
    mass = radius * 0.1  # Heavier raindrops

    # Random starting position at top of screen
    x = random.randint(50, WIDTH - 50)
    y = random.randint(-100, -10)

    # Random angle and speed
    angle = random.uniform(-0.25, 0.25)  # Slight angle variation
    speed = random.uniform(200, 400)

    # Create physics body
    body = pymunk.Body(mass, pymunk.moment_for_circle(mass, 0, radius))
    body.position = x, y
    body.velocity = speed * math.sin(angle), speed * math.cos(angle)

    # Create shape
    shape = pymunk.Circle(body, radius)
    shape.elasticity = RAINDROP_ELASTICITY
    shape.friction = 0.2
    shape.collision_type = 1  # For collision handling

    space.add(body, shape)

    # Store for drawing
    raindrops.append({
        'body': body,
        'radius': radius,
        'shape': shape,
        'alpha': 255  # For fade effects
    })


def create_ripple(position):
    """Create a new ripple at the impact position"""
    ripples.append({
        'position': position,
        'radius': 3,
        'width': 2,
        'intensity': 1.0,
        'alpha': 200,
        'growth_rate': random.uniform(1.5, 2.5)
    })


def create_splash(position):
    """Create splash particles when raindrop hits water"""
    splash = {
        'position': position,
        'particles': [],
        'time': 0,
        'duration': SPLASH_DURATION
    }

    # Create particles
    for _ in range(SPLASH_PARTICLES):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(50, 150)
        lifetime = random.uniform(0.3, SPLASH_DURATION)

        splash['particles'].append({
            'position': [position.x, position.y],
            'velocity': [speed * math.cos(angle), speed * math.sin(angle)],
            'radius': random.uniform(1, 3),
            'lifetime': lifetime,
            'age': 0,
            'alpha': 255
        })

    splashes.append(splash)


def handle_collision(arbiter, space, data):
    """Callback for raindrop-puddle collisions"""
    for shape in arbiter.shapes:
        if shape != puddle_shape:
            # This is the raindrop shape
            body = shape.body
            position = body.position

            # Create effects
            create_ripple(position)
            create_splash(position)

            # Remove the raindrop from simulation
            space.remove(body, shape)

            # Remove from drawing list
            for i, drop in enumerate(raindrops):
                if drop['body'] == body:
                    raindrops.pop(i)
                    break

    return True


# Set up collision handler
handler = space.add_collision_handler(1, 2)  # raindrop vs puddle
handler.begin = handle_collision


def draw_gradient_background():
    """Draw gradient sky background"""
    for y in range(HEIGHT):
        # Interpolate between top and bottom colors
        ratio = y / HEIGHT
        r = int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * ratio)
        g = int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * ratio)
        b = int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))


def draw_puddle():
    """Draw the puddle with transparency"""
    # Create a surface with per-pixel alpha
    puddle_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # Draw main puddle
    pygame.draw.circle(
        puddle_surface,
        PUDDLE_COLOR,
        PUDDLE_POSITION,
        PUDDLE_RADIUS
    )

    # Draw subtle highlights
    highlight_pos = (PUDDLE_POSITION[0] - 30, PUDDLE_POSITION[1] - 30)
    pygame.draw.circle(
        puddle_surface,
        (200, 230, 255, 30),
        highlight_pos,
        PUDDLE_RADIUS - 20
    )

    screen.blit(puddle_surface, (0, 0))


def draw_ripple(surface, ripple):
    """Draw a single ripple with fading effect"""
    alpha = int(min(255, max(0, ripple['alpha'] * ripple['intensity'])))  # Clamped
    width = max(1, ripple['width'] * ripple['intensity'])
    color = (*RIPPLE_COLOR[:3], alpha)

    # Create a surface for the ripple
    ripple_surface = pygame.Surface((ripple['radius'] * 2, ripple['radius'] * 2), pygame.SRCALPHA)

    # Draw the ripple circle
    pygame.draw.circle(
        ripple_surface,
        color,
        (ripple['radius'], ripple['radius']),
        ripple['radius'],
        int(width)
    )

    # Blit onto main surface
    surface.blit(
        ripple_surface,
        (ripple['position'].x - ripple['radius'], ripple['position'].y - ripple['radius'])
    )


def draw_splash(splash, dt):
    """Draw and update splash particles"""
    splash['time'] += dt

    for particle in splash['particles']:
        # Update position
        particle['position'][0] += particle['velocity'][0] * dt
        particle['position'][1] += particle['velocity'][1] * dt

        # Update age
        particle['age'] += dt
        progress = min(1, particle['age'] / particle['lifetime'])

        # Update alpha (fade out)
        particle['alpha'] = int(min(255, max(0, 255 * (1 - progress))))  # Fixed parentheses

        # Draw particle
        if particle['alpha'] > 0:
            gfxdraw.filled_circle(
                screen,
                max(0, min(WIDTH-1, int(particle['position'][0]))),  # Clamped x
                max(0, min(HEIGHT-1, int(particle['position'][1]))),  # Clamped y
                max(1, min(100, int(particle['radius']))),  # Clamped radius
                (*SPLASH_COLOR[:3], min(255, max(0, particle['alpha'])))  # Clamped alpha
            )


def draw_control_panel():
    """Draw the control panel with sliders"""
    panel_rect = pygame.Rect(10, 10, 200, 150)
    pygame.draw.rect(screen, (40, 40, 60, 200), panel_rect, border_radius=5)

    # Draw title
    title = font.render("Rain Controls", True, (240, 240, 255))
    screen.blit(title, (panel_rect.x + 10, panel_rect.y + 10))

    # Draw sliders
    draw_slider(panel_rect.x + 10, panel_rect.y + 40, "Intensity", rain_intensity, 0.01, 0.2)
    draw_slider(panel_rect.x + 10, panel_rect.y + 80, "Min Size", min_radius, 1, 5)
    draw_slider(panel_rect.x + 10, panel_rect.y + 120, "Max Size", max_radius, 3, 10)


def draw_slider(x, y, label, value, min_val, max_val):
    """Draw a slider control"""
    slider_width = 180
    slider_height = 6
    handle_radius = 8

    # Draw label
    label_text = font.render(f"{label}: {value:.1f}", True, (220, 220, 255))
    screen.blit(label_text, (x, y - 15))

    # Draw track
    pygame.draw.rect(screen, (80, 80, 100), (x, y, slider_width, slider_height), border_radius=3)

    # Draw filled progress
    progress_width = int((value - min_val) / (max_val - min_val) * slider_width)
    pygame.draw.rect(screen, (120, 180, 220), (x, y, progress_width, slider_height), border_radius=3)

    # Draw handle
    handle_x = x + progress_width
    pygame.draw.circle(screen, (200, 230, 255), (handle_x, y + slider_height // 2), handle_radius)

    return pygame.Rect(x, y, slider_width, slider_height + handle_radius)


def update_slider_value(mouse_pos, value, min_val, max_val, slider_rect):
    """Update slider value based on mouse position"""
    if slider_rect.collidepoint(mouse_pos):
        rel_x = mouse_pos[0] - slider_rect.x
        new_value = min_val + (rel_x / slider_rect.width) * (max_val - min_val)
        return max(min_val, min(max_val, new_value))
    return value


# Main game loop
dragging_slider = None
intensity_slider_rect = None
min_radius_slider_rect = None
max_radius_slider_rect = None

while running:
    dt = 1.0 / FPS

    # Handle events
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                # Check if clicking on any slider
                mouse_pos = pygame.mouse.get_pos()
                if intensity_slider_rect.collidepoint(mouse_pos):
                    dragging_slider = 'intensity'
                elif min_radius_slider_rect.collidepoint(mouse_pos):
                    dragging_slider = 'min_radius'
                elif max_radius_slider_rect.collidepoint(mouse_pos):
                    dragging_slider = 'max_radius'
        elif event.type == MOUSEBUTTONUP:
            if event.button == 1:
                dragging_slider = None
        elif event.type == MOUSEMOTION and dragging_slider:
            mouse_pos = pygame.mouse.get_pos()
            if dragging_slider == 'intensity':
                rain_intensity = update_slider_value(mouse_pos, rain_intensity, 0.01, 0.2, intensity_slider_rect)
            elif dragging_slider == 'min_radius':
                min_radius = update_slider_value(mouse_pos, min_radius, 1, 5, min_radius_slider_rect)
            elif dragging_slider == 'max_radius':
                max_radius = update_slider_value(mouse_pos, max_radius, 3, 10, max_radius_slider_rect)

    # Spawn new raindrops
    if random.random() < rain_intensity:
        create_raindrop()

    # Update physics
    space.step(dt)

    # Update ripples
    for ripple in ripples:
        ripple['radius'] += ripple['growth_rate']
        ripple['intensity'] *= RIPPLE_DECAY_RATE
        ripple['alpha'] *= 0.98

    # Remove dead ripples
    ripples = [r for r in ripples if r['intensity'] > 0.05 and r['alpha'] > 5]

    # Remove raindrops that accumulate at the bottom of the screen
    for i, drop in enumerate(raindrops):
        if drop['body'].position.y > HEIGHT + 10:
            space.remove(drop['body'], drop['shape'])
            raindrops.pop(i)

    # Draw everything
    draw_gradient_background()
    draw_puddle()

    # Draw ripples
    for ripple in ripples:
        draw_ripple(screen, ripple)

    # Update splashes
    for splash in splashes[:]:
        draw_splash(splash, dt)
        if splash['time'] >= splash['duration']:
            splashes.remove(splash)

    # Draw raindrops
    for drop in raindrops:
        alpha = max(0, min(255, drop['alpha']))  # Clamped alpha value
        gfxdraw.filled_circle(
            screen,
            max(0, min(WIDTH-1, int(drop['body'].position.x))),  # Clamped x position
            max(0, min(HEIGHT-1, int(drop['body'].position.y))),  # Clamped y position
            max(1, min(100, int(drop['radius']))),  # Clamped radius
            (*RAIN_COLOR[:3], min(255, max(0, alpha)))  # Clamped alpha
        )

    # Draw control panel
    intensity_slider_rect = draw_slider(20, 40, "Rain Intensity", rain_intensity, 0.01, 0.2)
    min_radius_slider_rect = draw_slider(20, 80, "Min Drop Size", min_radius, 1, 5)
    max_radius_slider_rect = draw_slider(20, 120, "Max Drop Size", max_radius, 3, 10)

    # Display FPS
    fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, (240, 240, 255))
    screen.blit(fps_text, (WIDTH - 80, 20))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()