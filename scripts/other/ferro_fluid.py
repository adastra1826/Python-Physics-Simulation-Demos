"""
Ferrofluid Physics Simulation.

This simulation models the behavior of ferrofluid - a liquid that becomes
strongly magnetized in the presence of magnetic fields. It demonstrates
principles of magnetism, fluid dynamics, and how magnetic particles suspended
in a carrier fluid respond to external magnetic fields. The simulation shows
how ferrofluids form characteristic spikes when exposed to magnets (due to
the interplay between magnetic attraction, surface tension, and gravity),
how they flow while maintaining their magnetic properties, and how they can
be manipulated by changing magnetic field configurations.
"""

import pygame
import numpy as np

# Constants
WIDTH, HEIGHT = 800, 600
FERROFLUID_SIZE = 5
NUM_PARTICLES = 300
FORCE_CONSTANT = 500
MAX_FORCE = 10.0
MAX_VELOCITY = 5.0
GRID_SPACING = 100
MAGNET_SIZE = 20  # Size of user-placed magnets
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TRAIL_COLOR = (150, 150, 150)
TRAIL_LENGTH = 3
TRAIL_ALPHA = int(255 * 0.3)
GRID_COLOR = (50, 50, 50)
BORDER_COLOR = (100, 100, 100)
TEXT_COLOR = (200, 200, 200)
TEXT_SHADOW_COLOR = (50, 50, 50)
MAGNET_COLOR = (255, 0, 0)  # Red for user-placed magnets


def get_color(speed):
    """
    Map particle speed to a color gradient from dark blue (slow) to bright red (fast).

    Args:
        speed (float): Magnitude of the particle's velocity.

    """
    max_speed = 5.0
    ratio = min(speed / max_speed, 1.0)
    r = int(255 * ratio)
    b = int(255 * (1 - ratio))
    return (r, 0, b)


def create_background():
    """
    Create a background surface with a gradient and grid.

    """
    background = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        t = y / HEIGHT
        color = (int(20 * (1 - t)), int(20 * (1 - t)), int(20 * (1 - t)))
        background.fill(color, (0, y, WIDTH, 1))

    for x in range(0, WIDTH, GRID_SPACING):
        pygame.draw.line(background, GRID_COLOR, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, GRID_SPACING):
        pygame.draw.line(background, GRID_COLOR, (0, y), (WIDTH, y), 1)

    pygame.draw.rect(background, BORDER_COLOR, (0, 0, WIDTH, HEIGHT), 2)
    return background


class MagneticSource:
    """Represents a magnetic source in the background grid or user-placed."""

    def __init__(self, x, y, is_user_placed=False):
        """
        Initialize a magnetic source.

        """
        self.x = x
        self.y = y
        self.is_user_placed = is_user_placed

    def draw(self, screen):
        """Draw the magnet with a pulsing effect if user-placed."""
        if self.is_user_placed:
            size = MAGNET_SIZE + int(2 * np.sin(pygame.time.get_ticks() / 500.0))
            pygame.draw.circle(screen, MAGNET_COLOR, (int(self.x), int(self.y)), size)


class FerrofluidParticle:
    """Represents a single ferrofluid particle responding to magnetic sources."""

    def __init__(self, x, y):
        """
        Initialize a ferrofluid particle.

        """
        self.x = x
        self.y = y
        self.velocity_x = np.random.uniform(-0.1, 0.1)
        self.velocity_y = np.random.uniform(-0.1, 0.1)
        self.history = [(x, y)] * TRAIL_LENGTH

    def update(self, sources, field_strength, field_angle):
        """
        Update particle velocity, position, and trail based on magnetic sources.

        """
        accel_x, accel_y = 0, 0

        for source in sources:
            dx = self.x - source.x
            dy = self.y - source.y
            r = np.sqrt(dx**2 + dy**2) + 1e-6

            if r > GRID_SPACING * 2:
                continue

            B = field_strength / (r**2)
            angle = np.arctan2(dy, dx) + field_angle
            Bx = B * np.cos(angle)
            By = B * np.sin(angle)

            accel_x += FORCE_CONSTANT * Bx
            accel_y += FORCE_CONSTANT * By

        accel_magnitude = np.sqrt(accel_x**2 + accel_y**2)
        if accel_magnitude > MAX_FORCE:
            scale = MAX_FORCE / accel_magnitude
            accel_x *= scale
            accel_y *= scale

        self.velocity_x += accel_x * 0.005
        self.velocity_y += accel_y * 0.005

        velocity_magnitude = np.sqrt(self.velocity_x**2 + self.velocity_y**2)
        if velocity_magnitude > MAX_VELOCITY:
            scale = MAX_VELOCITY / velocity_magnitude
            self.velocity_x *= scale
            self.velocity_y *= scale

        self.velocity_x *= 0.95
        self.velocity_y *= 0.95

        self.x += self.velocity_x
        self.y += self.velocity_y

        self.history.append((self.x, self.y))
        if len(self.history) > TRAIL_LENGTH:
            self.history.pop(0)

        if self.x < 0 or self.x > WIDTH:
            self.velocity_x *= -1
            self.x = max(0, min(self.x, WIDTH))
        if self.y < 0 or self.y > HEIGHT:
            self.velocity_y *= -1
            self.y = max(0, min(self.y, HEIGHT))

        speed = np.sqrt(self.velocity_x**2 + self.velocity_y**2)
        return speed

    def draw(self, screen, trail_surface, speed):
        """
        Draw the particle and its trail.

        """
        if len(self.history) > 1:
            pygame.draw.lines(trail_surface, TRAIL_COLOR, False, self.history, 1)

        color = get_color(speed)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), FERROFLUID_SIZE)


def main():
    """Run the ferrofluid simulation with a grid of magnetic sources and user-placed magnets."""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ferrofluid Simulation - Grid of Magnetic Sources")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)

    background = create_background()
    trail_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    trail_surface.set_alpha(TRAIL_ALPHA)

    # Create a grid of magnetic sources
    grid_sources = []
    for x in range(GRID_SPACING // 2, WIDTH, GRID_SPACING):
        for y in range(GRID_SPACING // 2, HEIGHT, GRID_SPACING):
            grid_sources.append(MagneticSource(x, y))

    # List for user-placed magnets
    user_sources = []

    field_strength = 10000000.0
    field_angle = 0.0
    input_text = ""
    input_active = False

    particles = [
        FerrofluidParticle(np.random.uniform(0, WIDTH), np.random.uniform(0, HEIGHT))
        for _ in range(NUM_PARTICLES)
    ]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:  # Right-click to place a magnet
                    user_sources.append(
                        MagneticSource(event.pos[0], event.pos[1], is_user_placed=True)
                    )
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    try:
                        new_strength = float(input_text)
                        if new_strength > 0:
                            field_strength = new_strength
                        input_text = ""
                        input_active = False
                    except ValueError:
                        input_text = ""
                        input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    input_text = ""
                    input_active = False
                elif event.unicode.isprintable() and len(input_text) < 10:
                    input_text += event.unicode
                    input_active = True

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            field_angle += 0.05
        if keys[pygame.K_RIGHT]:
            field_angle -= 0.05

        # Combine grid and user-placed sources
        all_sources = grid_sources + user_sources

        screen.blit(background, (0, 0))
        trail_surface.fill((0, 0, 0, 0))

        for particle in particles:
            speed = particle.update(all_sources, field_strength, field_angle)
            particle.draw(screen, trail_surface, speed)

        screen.blit(trail_surface, (0, 0))

        # Draw user-placed magnets
        for source in user_sources:
            source.draw(screen)

        # Display field parameters and input
        strength_text = font.render(
            f"Field Strength: {field_strength:.2f}", True, TEXT_COLOR
        )
        angle_text = font.render(
            f"Field Angle: {int(np.degrees(field_angle)) % 360}°", True, TEXT_COLOR
        )
        input_label = font.render(
            "Type Field Strength (Enter to set):", True, TEXT_COLOR
        )
        input_display = font.render(input_text, True, TEXT_COLOR)

        strength_shadow = font.render(
            f"Field Strength: {field_strength:.2f}", True, TEXT_SHADOW_COLOR
        )
        angle_shadow = font.render(
            f"Field Angle: {int(np.degrees(field_angle)) % 360}°",
            True,
            TEXT_SHADOW_COLOR,
        )
        input_label_shadow = font.render(
            "Type Field Strength (Enter to set):", True, TEXT_SHADOW_COLOR
        )
        input_display_shadow = font.render(input_text, True, TEXT_SHADOW_COLOR)

        screen.blit(strength_shadow, (12, 12))
        screen.blit(angle_shadow, (12, 42))
        screen.blit(input_label_shadow, (12, 72))
        screen.blit(input_display_shadow, (12, 102))
        screen.blit(strength_text, (10, 10))
        screen.blit(angle_text, (10, 40))
        screen.blit(input_label, (10, 70))
        screen.blit(input_display, (10, 100))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
