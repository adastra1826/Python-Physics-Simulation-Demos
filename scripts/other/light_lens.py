"""
Light and Lens Physics Simulation.

This simulation models the behavior of light rays as they interact with optical lenses.
It demonstrates principles of geometric optics, including refraction, focal points,
and image formation. The simulation shows how different lens shapes (convex, concave)
affect light paths according to Snell's Law, how parallel rays converge or diverge
based on lens properties, and how the index of refraction influences the bending
of light. Users can visualize the fundamental optical principles that explain how
lenses in cameras, eyeglasses, telescopes, and microscopes manipulate light to form
images or correct vision.
"""

import pygame
import math
import pygame.freetype

# Window dimensions
WIDTH, HEIGHT = 800, 600

# Colors
BACKGROUND_TOP = (30, 30, 50)  # Darker blue at the top
BACKGROUND_BOTTOM = (10, 10, 30)  # Even darker at the bottom
WHITE = (220, 220, 240)  # Softer white for text
YELLOW = (255, 220, 100)  # Warm glowing yellow for light source
LENS_COLOR = (100, 150, 255, 128)  # Semi-transparent blue for lens
RAY_COLOR = (180, 200, 255)  # Light blue for rays
REFERENCE_COLOR = (80, 80, 120, 100)  # Subtle dashed lines
GLOW_COLORS = [
    (255, 255, 200),
    (255, 200, 150),
    (200, 150, 100),
    (150, 100, 50),
]  # Gradient for glow

# Lens properties
MIN_RADIUS = 20
MAX_RADIUS = 200

# Light source properties
LIGHT_SOURCE_RADIUS = 10

# Ray properties
RAY_WIDTH = 1


class LightSource:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Lens:
    def __init__(self, x, y, radius1, radius2):
        """Initialize lens with position and separate radii of curvature for each surface."""
        self.x = x
        self.y = y
        self.radius1 = radius1  # Radius of curvature for left surface
        self.radius2 = radius2  # Radius of curvature for right surface
        self.display_radius = max(radius1, radius2)  # For visual representation


def draw_gradient_background(screen):
    """Draw a vertical gradient background from top to bottom."""
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(BACKGROUND_TOP[0] + t * (BACKGROUND_BOTTOM[0] - BACKGROUND_TOP[0]))
        g = int(BACKGROUND_TOP[1] + t * (BACKGROUND_BOTTOM[1] - BACKGROUND_TOP[1]))
        b = int(BACKGROUND_TOP[2] + t * (BACKGROUND_BOTTOM[2] - BACKGROUND_TOP[2]))
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))


def draw_rays(screen, light_source, lens, focal_length):
    """Draw light rays from the source, refracted by the lens using the thin-lens approximation.

    Rays are modeled using the paraxial approximation. For each ray:
    1. Compute intersection with the lens plane (x = lens.x).
    2. Calculate incident slope m = dy/dx.
    3. Calculate height y relative to optical axis.
    4. Compute refracted slope m' = m - y/f, where f is the focal length.
    5. Draw incident ray from source to intersection.
    6. Draw refracted ray from intersection to screen edge.
    """
    for angle in range(-45, 46):
        dx = math.cos(math.radians(angle))
        dy = math.sin(math.radians(angle))

        if dx != 0:
            t = (lens.x - light_source.x) / dx
            if t > 0:
                ix = lens.x
                iy = light_source.y + t * dy
                y_rel = iy - lens.y
                m_inc = dy / dx if dx != 0 else float("inf")
                if m_inc != float("inf"):
                    m_ref = m_inc - y_rel / focal_length
                    pygame.draw.line(
                        screen,
                        RAY_COLOR,
                        (light_source.x, light_source.y),
                        (ix, iy),
                        RAY_WIDTH,
                    )
                    ref_x = WIDTH
                    ref_y = iy + m_ref * (WIDTH - ix)
                    pygame.draw.line(
                        screen, RAY_COLOR, (ix, iy), (ref_x, ref_y), RAY_WIDTH
                    )


def calculate_image_position(light_source, lens, focal_length):
    """Calculate the image position using the thin-lens formula: 1/f = 1/d + 1/d'."""
    d = lens.x - light_source.x
    if d > 0 and d != focal_length:
        try:
            d_prime = 1 / (1 / focal_length - 1 / d)
            m = -d_prime / d
            image_x = lens.x + d_prime
            image_y = lens.y + m * (light_source.y - lens.y)
            return image_x, image_y
        except ZeroDivisionError:
            return None
    return None


def draw_glow(screen, pos, time):
    """Draw a pronounced glow effect at the convergence point with animated gradient."""
    for i, color in enumerate(GLOW_COLORS):
        radius = 6 + i * 5 + 3 * math.sin(time / 300 + i)  # Smoother pulsing
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, color + (128 - i * 20,), (radius, radius), radius)
        screen.blit(surf, (int(pos[0]) - radius, int(pos[1]) - radius))


def draw_dashed_line(screen, color, start_pos, end_pos, dash_length=5):
    """Draw a dashed line between two points."""
    dx = end_pos[0] - start_pos[0]
    dy = end_pos[1] - start_pos[1]
    distance = math.hypot(dx, dy)
    if distance == 0:
        return
    dx /= distance
    dy /= distance
    pos = start_pos
    total_dist = 0
    while total_dist < distance:
        next_pos = (pos[0] + dx * dash_length, pos[1] + dy * dash_length)
        pygame.draw.line(screen, color, pos, next_pos)
        pos = (next_pos[0] + dx * dash_length, next_pos[1] + dy * dash_length)
        total_dist += 2 * dash_length


def main():
    """Simulate light rays passing through a lens, with adjustable lens position and radii of curvature.

    The simulation uses a thin-lens model for ray refraction, allows the user to move the light source
    and lens with mouse controls, and adjust the radii of curvature with keyboard inputs (UP/DOWN for left surface,
    LEFT/RIGHT for right surface).

    The focal length is calculated using the lensmaker's equation:
    1/f = (n-1)(1/R1 - 1/R2), where n is the refractive index, R1 and R2 are radii of curvature.
    """
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.freetype.Font(None, 20)

    light_source = LightSource(100, 100)
    lens = Lens(WIDTH // 2, HEIGHT // 2, 50, 50)

    light_dragging = False
    lens_dragging = False
    time = 0

    n = 1.5  # Refractive index of glass

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    light_dragging = True
                elif event.button == 3:
                    lens_dragging = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    light_dragging = False
                elif event.button == 3:
                    lens_dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if light_dragging:
                    light_source.x, light_source.y = event.pos
                elif lens_dragging:
                    lens.x, lens.y = event.pos
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    lens.radius1 += 5
                    if lens.radius1 > MAX_RADIUS:
                        lens.radius1 = MAX_RADIUS
                elif event.key == pygame.K_DOWN:
                    lens.radius1 -= 5
                    if lens.radius1 < MIN_RADIUS:
                        lens.radius1 = MIN_RADIUS
                elif event.key == pygame.K_LEFT:
                    lens.radius2 -= 5
                    if lens.radius2 < MIN_RADIUS:
                        lens.radius2 = MIN_RADIUS
                elif event.key == pygame.K_RIGHT:
                    lens.radius2 += 5
                    if lens.radius2 > MAX_RADIUS:
                        lens.radius2 = MAX_RADIUS
                lens.display_radius = max(lens.radius1, lens.radius2)

        # Calculate focal length using the lensmaker's equation
        R1 = lens.radius1 if lens.radius1 > 0 else float("inf")
        R2 = -lens.radius2 if lens.radius2 > 0 else -float("inf")
        if R1 != float("inf") and R2 != -float("inf"):
            try:
                focal_length = 1 / ((n - 1) * (1 / R1 - 1 / R2))
                focal_length = max(focal_length, 10)
            except ZeroDivisionError:
                focal_length = float("inf")
        else:
            focal_length = float("inf")

        # Draw background and faint grid
        draw_gradient_background(screen)
        for y in range(0, HEIGHT, 50):
            pygame.draw.line(screen, (50, 50, 70, 50), (0, y), (WIDTH, y))
        for x in range(0, WIDTH, 50):
            pygame.draw.line(screen, (50, 50, 70, 50), (x, 0), (x, HEIGHT))

        # Draw reference lines (dashed)
        draw_dashed_line(screen, REFERENCE_COLOR, (0, lens.y), (WIDTH, lens.y))
        focal_left = lens.x - focal_length if focal_length != float("inf") else lens.x
        focal_right = lens.x + focal_length if focal_length != float("inf") else lens.x
        draw_dashed_line(
            screen,
            REFERENCE_COLOR,
            (focal_left, lens.y - 10),
            (focal_left, lens.y + 10),
        )
        draw_dashed_line(
            screen,
            REFERENCE_COLOR,
            (focal_right, lens.y - 10),
            (focal_right, lens.y + 10),
        )
        draw_dashed_line(screen, REFERENCE_COLOR, (lens.x, 0), (lens.x, HEIGHT))

        draw_rays(screen, light_source, lens, focal_length)

        # Calculate and draw glow at image position
        image_pos = calculate_image_position(light_source, lens, focal_length)
        if image_pos:
            draw_glow(screen, image_pos, time)

        # Draw light source with glow
        surf = pygame.Surface(
            (LIGHT_SOURCE_RADIUS * 4, LIGHT_SOURCE_RADIUS * 4), pygame.SRCALPHA
        )
        pygame.draw.circle(
            surf,
            YELLOW + (128,),
            (LIGHT_SOURCE_RADIUS * 2, LIGHT_SOURCE_RADIUS * 2),
            LIGHT_SOURCE_RADIUS * 2,
        )
        pygame.draw.circle(
            surf,
            YELLOW,
            (LIGHT_SOURCE_RADIUS * 2, LIGHT_SOURCE_RADIUS * 2),
            LIGHT_SOURCE_RADIUS,
        )
        screen.blit(
            surf,
            (
                int(light_source.x) - LIGHT_SOURCE_RADIUS * 2,
                int(light_source.y) - LIGHT_SOURCE_RADIUS * 2,
            ),
        )

        # Draw lens with transparency
        surf = pygame.Surface(
            (lens.display_radius * 2, lens.display_radius * 2), pygame.SRCALPHA
        )
        pygame.draw.circle(
            surf,
            LENS_COLOR,
            (lens.display_radius, lens.display_radius),
            lens.display_radius,
        )
        pygame.draw.circle(
            surf,
            WHITE + (200,),
            (lens.display_radius, lens.display_radius),
            lens.display_radius,
            2,
        )
        screen.blit(
            surf, (int(lens.x) - lens.display_radius, int(lens.y) - lens.display_radius)
        )

        # Draw labels with shadows
        texts = [
            f"Focal length: {focal_length:.1f} pixels",
            f"R1: {lens.radius1:.1f}, R2: {lens.radius2:.1f}",
            "Left-click: Move light | Right-click: Move lens | Up/Down: R1 | Left/Right: R2",
        ]
        for i, text in enumerate(texts):
            y = 10 + i * 25 if i < 2 else HEIGHT - 30
            # Shadow
            font.render_to(screen, (12, y + 2), text, (50, 50, 50))
            # Text
            font.render_to(screen, (10, y), text, WHITE)

        pygame.display.flip()
        clock.tick(60)
        time += clock.get_time()

    pygame.quit()


if __name__ == "__main__":
    main()
