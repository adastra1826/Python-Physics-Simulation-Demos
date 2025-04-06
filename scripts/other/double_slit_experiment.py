"""
Double Slit Experiment Physics Simulation.

This simulation models the famous double-slit experiment, a cornerstone of quantum mechanics.
It demonstrates the wave-particle duality of light and matter, showing how particles
passing through two slits create an interference pattern characteristic of waves.
The simulation visualizes wave interference, diffraction patterns, and probabilistic
particle behavior. It illustrates one of the most profound quantum phenomena that
reveals the fundamental wavelike nature of quantum objects and the probabilistic
nature of quantum mechanics.
"""

import pygame
import numpy as np

# Window dimensions (we treat these as mm; 1 pixel = 1 mm)
WIDTH, HEIGHT = 800, 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

def create_hot_colormap():
    """
    Create a "hot" colormap (256x3) where low intensity is black and high intensity transitions
    from red to yellow to white.
    """
    colormap = np.zeros((256, 3), dtype=np.uint8)
    for i in range(256):
        norm = i / 255.0
        if norm < 1/3:
            # From black to red.
            r = int((norm / (1/3)) * 255)
            g = 0
            b = 0
        elif norm < 2/3:
            # From red to yellow.
            r = 255
            g = int(((norm - 1/3) / (1/3)) * 255)
            b = 0
        else:
            # From yellow to white.
            r = 255
            g = 255
            b = int(((norm - 2/3) / (1/3)) * 255)
        colormap[i] = (r, g, b)
    return colormap

# Precompute the colormap.
HOT_COLORMAP = create_hot_colormap()

def get_slit_positions(num_slits, slit_spacing, barrier_x, barrier_y):
    """
    Compute the x,y positions of the slits along a horizontal barrier.
    For a single slit, the slit is centered.
    For two slits, they are placed symmetrically at ±(slit_spacing/2) from center.
    For three slits, the center slit is at barrier_x and the outer slits at ±(slit_spacing).
    """
    if num_slits == 1:
        return [(barrier_x, barrier_y)]
    elif num_slits == 2:
        return [(barrier_x - slit_spacing / 2, barrier_y),
                (barrier_x + slit_spacing / 2, barrier_y)]
    elif num_slits == 3:
        return [(barrier_x - slit_spacing, barrier_y),
                (barrier_x, barrier_y),
                (barrier_x + slit_spacing, barrier_y)]
    else:
        return [(barrier_x, barrier_y)]

def draw_rounded_rect(surface, rect, color, radius):
    """
    Draw a rounded rectangle onto surface.
    """
    pygame.draw.rect(surface, color, rect, border_radius=radius)

class Slider:
    """
    A simple horizontal slider widget.
    """
    def __init__(self, x, y, width, min_val, max_val, initial, label, discrete=False):
        self.x = x
        self.y = y
        self.width = width
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial
        self.label = label
        self.discrete = discrete
        self.height = 20
        self.handle_radius = 10
        self.dragging = False
        # Define the bounding rect for the slider control (for drawing a rounded background)
        self.bg_rect = pygame.Rect(self.x - 5, self.y - 10, self.width + 10, self.height + 20)
        self.bg_color = (0, 0, 0, 150)  # Translucent dark

    def draw(self, surface, font):
        # Draw rounded background for slider.
        bg_surface = pygame.Surface((self.bg_rect.width, self.bg_rect.height), pygame.SRCALPHA)
        draw_rounded_rect(bg_surface, bg_surface.get_rect(), self.bg_color, 10)
        surface.blit(bg_surface, (self.bg_rect.x, self.bg_rect.y))
        
        # Draw the slider line.
        line_y = self.y + self.height // 2
        pygame.draw.line(surface, WHITE, (self.x, line_y), (self.x + self.width, line_y), 2)
        # Calculate handle position.
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        handle_x = self.x + int(ratio * self.width)
        pygame.draw.circle(surface, WHITE, (handle_x, line_y), self.handle_radius)
        # Draw the label with a solid background to stand out.
        if self.discrete:
            text = f"{self.label}: {int(round(self.value))}"
        else:
            text = f"{self.label}: {self.value:.1f}"
        img = font.render(text, True, WHITE, BLACK)
        surface.blit(img, (self.x, self.y - 25))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            line_y = self.y + self.height // 2
            ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
            handle_x = self.x + int(ratio * self.width)
            if np.sqrt((mx - handle_x) ** 2 + (my - line_y) ** 2) < self.handle_radius:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mx, _ = event.pos
                # Clamp mx to slider boundaries.
                mx = max(self.x, min(self.x + self.width, mx))
                ratio = (mx - self.x) / self.width
                new_val = self.min_val + ratio * (self.max_val - self.min_val)
                if self.discrete:
                    new_val = round(new_val)
                self.value = new_val

    def get_value(self):
        return self.value

class Button:
    """
    A simple clickable button widget.
    """
    def __init__(self, x, y, width, height, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.clicked = False
        self.bg_color = (0, 0, 0, 150)  # Translucent dark

    def draw(self, surface, font):
        # Draw rounded background for the button.
        bg_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        draw_rounded_rect(bg_surface, bg_surface.get_rect(), self.bg_color, 10)
        surface.blit(bg_surface, (self.rect.x, self.rect.y))
        # Draw the button border.
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=10)
        img = font.render(self.label, True, WHITE, BLACK)
        text_rect = img.get_rect(center=self.rect.center)
        surface.blit(img, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.clicked = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.rect.collidepoint(event.pos) and self.clicked:
                self.clicked = False
                return True
            self.clicked = False
        return False

def draw_barrier(surface, slit_positions, slit_width, barrier_y, barrier_thickness=10):
    """
    Draw a horizontal barrier (with a semi-transparent dark overlay) that covers the entire
    width except at the slit openings. This visually marks the barrier and clearly shows the slit locations.
    """
    barrier_color = (50, 50, 50, 200)  # dark grey with alpha
    barrier_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    # Draw the barrier band.
    pygame.draw.rect(barrier_surface, barrier_color,
                     (0, barrier_y - barrier_thickness // 2, WIDTH, barrier_thickness))
    # "Cut out" the slit areas.
    for slit in slit_positions:
        slit_rect = (int(slit[0] - slit_width / 2), barrier_y - barrier_thickness // 2, int(slit_width), barrier_thickness)
        pygame.draw.rect(barrier_surface, (0, 0, 0, 0), slit_rect)
    surface.blit(barrier_surface, (0, 0))

def draw_instructions(surface, font):
    """
    Draw an instructions banner at the top of the screen with a solid background.
    """
    instructions = "Adjust sliders to change parameters. Click 'Reset' to clear the build-up."
    img = font.render(instructions, True, WHITE, BLACK)
    surface.blit(img, (20, 10))

def draw_control_panel(surface):
    """
    Draw a translucent dark control panel background at the bottom of the screen.
    """
    panel_height = 120
    panel = pygame.Surface((WIDTH, panel_height), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 180))  # Dark, translucent
    surface.blit(panel, (0, HEIGHT - panel_height))

def main():
    """
    Main simulation function.

    This program simulates the gradual build-up of diffraction and interference
    patterns produced by one, two, or three narrow slits. The simulation computes the
    superposition of waves (from each slit, modeled as a point source) over a 2D grid,
    using proper phase calculations. The instantaneous intensity (square of the amplitude)
    is accumulated over time to mimic a long-exposure image of the interference pattern.
    
    Physical parameters are given in mm (with 1 pixel = 1 mm) and the default values
    are chosen to be physically meaningful (scaled for visual clarity). Sliders let you
    interactively adjust the light wavelength, the slit spacing, and the number of slits.
    A reset button clears the accumulation when parameters change.
    """
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    # Simulation parameters (all in mm, where 1 pixel = 1 mm)
    wavelength = 50.0       # Default wavelength in mm.
    slit_spacing = 150.0    # Default center-to-center slit spacing in mm.
    num_slits = 1           # Default number of slits.
    slit_width = 20         # Fixed slit width in mm.
    amplitude = 1.0         # Base amplitude.
    wave_speed = 10.0       # Propagation speed in mm per frame.
    time_val = 0.0          # Simulation time.
    dt = 0.5                # Time step per frame.

    # Create a coordinate grid for the simulation area.
    xs = np.arange(WIDTH)
    ys = np.arange(HEIGHT)
    xx, yy = np.meshgrid(xs, ys)  # (HEIGHT, WIDTH)

    # Initialize the accumulated intensity field.
    accumulated_intensity = np.zeros((HEIGHT, WIDTH), dtype=np.float32)

    # Barrier parameters (placed at the center of the screen).
    barrier_x = WIDTH // 2
    barrier_y = HEIGHT // 2

    # Create sliders and a reset button.
    slider_wavelength = Slider(50, 520, 200, 10, 200, wavelength, "Wavelength (mm)")
    slider_slit_spacing = Slider(300, 520, 200, 10, 300, slit_spacing, "Slit Spacing (mm)")
    slider_num_slits = Slider(550, 520, 200, 1, 3, num_slits, "Number of Slits", discrete=True)
    reset_button = Button(50, 560, 100, 30, "Reset")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Pass event to sliders and button.
            slider_wavelength.handle_event(event)
            slider_slit_spacing.handle_event(event)
            slider_num_slits.handle_event(event)
            if reset_button.handle_event(event):
                accumulated_intensity.fill(0)
                time_val = 0.0

        # Update simulation parameters from sliders.
        wavelength = slider_wavelength.get_value()
        slit_spacing = slider_slit_spacing.get_value()
        num_slits = int(round(slider_num_slits.get_value()))

        # Recompute slit positions (in physical units) based on the current parameters.
        slit_positions = get_slit_positions(num_slits, slit_spacing, barrier_x, barrier_y)

        # Increment simulation time.
        time_val += dt

        # Compute the instantaneous wave field.
        field = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
        for slit_x, slit_y in slit_positions:
            # Compute distance from the slit to every point.
            distance = np.sqrt((xx - slit_x) ** 2 + (yy - slit_y) ** 2)
            # Only add the wave contribution where the wavefront has reached.
            mask = (wave_speed * time_val >= distance)
            # Compute the phase (radians) at each point.
            phase = 2 * np.pi * (distance - wave_speed * time_val) / wavelength
            contribution = amplitude * np.sin(phase)
            field += contribution * mask

        # Intensity is the square of the amplitude.
        intensity = field ** 2
        # Accumulate the intensity over time.
        accumulated_intensity += intensity

        # Normalize the accumulated intensity to the range [0, 255] for display.
        norm_intensity = accumulated_intensity.copy()
        max_val = norm_intensity.max()
        if max_val > 0:
            norm_intensity = norm_intensity / max_val * 255
        display_array = norm_intensity.astype(np.uint8)

        # Map the intensity to a hot colormap.
        display_rgb = HOT_COLORMAP[display_array]
        # Create a Pygame surface from the RGB array.
        sim_surface = pygame.surfarray.make_surface(display_rgb.swapaxes(0, 1))
        screen.blit(sim_surface, (0, 0))

        # Draw the barrier overlay (with clear slit openings).
        draw_barrier(screen, slit_positions, slit_width, barrier_y, barrier_thickness=10)

        # Draw the translucent control panel background at the bottom.
        draw_control_panel(screen)

        # Draw the instruction banner.
        draw_instructions(screen, font)

        # Draw the slider and button widgets.
        slider_wavelength.draw(screen, font)
        slider_slit_spacing.draw(screen, font)
        slider_num_slits.draw(screen, font)
        reset_button.draw(screen, font)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
