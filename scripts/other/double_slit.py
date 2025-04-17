import pygame
import numpy as np
import math

# Window dimensions
WIDTH, HEIGHT = 800, 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
TEXTCOLOR = (200, 200, 200)
SLIDER_COLOR = (100, 100, 255)
SLIDER_BG = (200, 200, 200)

# Default parameters
SLIT_DISTANCE = 100e-6
SCREEN_DISTANCE = 1.0
WAVELENGTH = 500e-9

# Simulation grid
pattern_height = HEIGHT - 150
pattern_width = WIDTH
screen_center = np.array([pattern_width / 2, pattern_height / 2])

# Autoscroll wavelength feature
AUTOSCROLL_WAVELENGTH = False

pygame.init()
font = pygame.font.SysFont("Arial", 16)

# Sliders
class Slider:
    """A UI component that allows the user to adjust a parameter value via dragging."""

    def __init__(self, x, y, min_val, max_val, start_val, label, unit, scale=1e0):
        """
        Initialize a slider.

        Args:
            x, y: Position of the slider on screen.
            min_val: Minimum slider value.
            max_val: Maximum slider value.
            start_val: Initial value.
            label: Label shown above the slider.
            unit: Display unit (e.g., "nm", "µm").
            scale: Scaling factor to convert internal value to display value.
        """
        self.x = x
        self.y = y
        self.w = 200
        self.h = 20
        self.min_val = min_val
        self.max_val = max_val
        self.val = start_val
        self.scale = scale
        self.label = label
        self.unit = unit
        self.dragging = False

    def draw(self, surface):
        """Render the slider and its label onto the given surface."""
        pygame.draw.rect(surface, SLIDER_BG, (self.x, self.y, self.w, self.h))
        ratio = (self.val - self.min_val) / (self.max_val - self.min_val)
        handle_x = self.x + ratio * self.w
        pygame.draw.circle(surface, SLIDER_COLOR, (int(handle_x), self.y + self.h // 2), 10)
        label_surf = font.render(
            f"{self.label}: {self.val / self.scale:.2f} {self.unit}", True, TEXTCOLOR
        )
        surface.blit(label_surf, (self.x, self.y - 20))

    def handle_event(self, event):
        """Update slider state in response to mouse events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if self.x <= mx <= self.x + self.w and self.y <= my <= self.y + self.h:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mx = event.pos[0]
            ratio = (mx - self.x) / self.w
            ratio = max(0, min(1, ratio))
            self.val = self.min_val + ratio * (self.max_val - self.min_val)

class Button:
    """A clickable toggle button UI component."""
    def __init__(self, x, y, w, h, text, callback):
        """
        Initialize the button.

        Args:
            x, y, w, h: Position and size.
            text: Button label.
            callback: Function called when button is toggled.
        """
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.active = False

    def draw(self, surface):
        """Render the button on the given surface."""
        color = (100, 255, 100) if self.active else (180, 180, 180)
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, SLIDER_COLOR, self.rect, 2, border_radius=6)
        label = font.render(self.text, True, BLACK)
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)

    def handle_event(self, event):
        """Toggle the button state on click and call the callback."""
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.active = not self.active
            self.callback(self.active)


class DoubleSlitSimulation:
    """Main simulation class for visualizing 2D double-slit interference."""
    def __init__(self):
        """Initialize the simulation window, parameters, sliders, and button."""
        pygame.display.set_caption("2D Double-Slit Interference Pattern")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.slit_distance = SLIT_DISTANCE
        self.screen_distance = SCREEN_DISTANCE
        self.wavelength = WAVELENGTH
        self.last_slit_distance = 0
        self.last_screen_distance = 0
        self.last_wavelength = 0

        self.autoscroll_wavelength = AUTOSCROLL_WAVELENGTH

        self.sliders = [
            Slider(50, HEIGHT - 100, 200e-9, 800e-9, self.wavelength, "Wavelength", "nm", 1e-9),
            Slider(300, HEIGHT - 100, 10e-6, 200e-6, self.slit_distance, "Slit Distance", "µm", 1e-6),
            Slider(550, HEIGHT - 100, 0.1, 2.0, self.screen_distance, "Screen Distance", "m"),
        ]

        self.toggle_button = Button(x=WIDTH // 2 - 90, y=HEIGHT - 50, w=180, h=30, text="Autoscroll Wavelength", callback=self.toggle_autoscroll)

        self.screen.fill(BLACK)
    
    def draw_2d_pattern(self):
        """
        Compute and draw the 2D interference pattern.

        - For each point on the screen, we calculate the distance to each slit.
        - The path difference between the two waves determines the phase difference.
        - Intensity at that point is proportional to cos²(phase difference).
        - The final image shows bright and dark fringes due to constructive/destructive interference.
        """
        lam = self.wavelength
        d = self.slit_distance
        L = self.screen_distance

        # Coordinate grid (in meters)
        x = np.linspace(-pattern_width / 2, pattern_width / 2, pattern_width) * 1e-3 # Convert screen coordinates (pixels) to meters (using 1 pixel = 1e-3 m for visualization).
        y = np.linspace(-pattern_height / 2, pattern_height / 2, pattern_height) * 1e-3
        X, Y = np.meshgrid(x, y)
        Z = L

        # Define positions of the slits in the y-direction (symmetrical)
        slit_y_offset = d / 2

        # Calculate distance from each screen point to each slit
        distance1 = np.sqrt((X**2) + (Y + slit_y_offset)**2 + Z**2)  # from slit 1
        distance2 = np.sqrt((X**2) + (Y - slit_y_offset)**2 + Z**2)  # from slit 2

        # Path difference between the two waves arriving at the screen point
        path_diff = distance1 - distance2

        # Phase difference corresponding to the path difference
        phase_diff = 2 * np.pi * path_diff / lam

        # Interference intensity formula: I ∝ cos²(Δϕ)
        intensity = (np.cos(phase_diff))**2  # Range: [0, 1]

        # Normalize intensity
        norm_intensity = (intensity - intensity.min()) / (intensity.max() - intensity.min())

        # Jet-style colormap mapping
        def jet_colormap(val):
            """Maps a float in [0, 1] to an RGB tuple using a Jet-like style."""
            four_val = 4 * val
            r = np.clip(np.minimum(four_val - 1.5, -four_val + 4.5), 0, 1)
            g = np.clip(np.minimum(four_val - 0.5, -four_val + 3.5), 0, 1)
            b = np.clip(np.minimum(four_val + 0.5, -four_val + 2.5), 0, 1)
            return (r * 255, g * 255, b * 255)

        r, g, b = jet_colormap(norm_intensity)
        rgb_array = np.stack([r, g, b], axis=-1).astype(np.uint8)

        # Convert to Pygame surface
        surface = pygame.surfarray.make_surface(np.transpose(rgb_array, (1, 0, 2)))
        self.screen.blit(surface, (0, 0))
    
    def toggle_autoscroll(self, state):
        """
        Enable or disable wavelength autoscroll.

        Args:
            state: True to enable autoscroll, False to disable.
        """
        self.autoscroll_wavelength = state

    def update(self):
        """Handle input events, update simulation state, and render the scene."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            for slider in self.sliders:
                slider.handle_event(event)
            self.toggle_button.handle_event(event)

        if self.autoscroll_wavelength:
            self.wavelength += 0.2e-9
            if self.wavelength > 800e-9:
                self.wavelength = 200e-9
            self.sliders[0].val = self.wavelength  # keep slider in sync

        self.wavelength = self.sliders[0].val
        self.slit_distance = self.sliders[1].val
        self.screen_distance = self.sliders[2].val

        if not (self.wavelength == self.last_wavelength and self.slit_distance == self.last_slit_distance and self.screen_distance == self.last_screen_distance):
            self.screen.fill(BLACK)
            self.draw_2d_pattern()
        
        for slider in self.sliders:
            slider.draw(self.screen)
        self.toggle_button.draw(self.screen)

        self.last_wavelength = self.wavelength
        self.last_slit_distance = self.slit_distance
        self.last_screen_distance = self.screen_distance


        pygame.display.flip()
        self.clock.tick(60)

if __name__ == "__main__":
    simulation = DoubleSlitSimulation()
    while True:
        simulation.update()