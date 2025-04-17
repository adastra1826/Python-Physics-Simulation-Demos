import pygame
import pygame_gui
import numpy as np
import random
import math
from pygame import gfxdraw

# Constants and colours
WIDTH, HEIGHT = 1000, 700
PLANET_RADIUS = 40
SPACECRAFT_RADIUS = 5
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# Initialising the simulation
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gravity Slingshot Simulator")
clock = pygame.time.Clock()

# UI Manager
manager = pygame_gui.UIManager((WIDTH, HEIGHT))
planet_mass_slider = pygame_gui.elements.UIHorizontalSlider(pygame.Rect((20, 20), (200, 20)), 10000, (1000, 50000), manager)
gravity_strength_slider = pygame_gui.elements.UIHorizontalSlider(pygame.Rect((20, 50), (200, 20)), 0.1, (0.01, 1.0), manager)
font = pygame.font.SysFont("arial", 16)


# helper function to add labels onto the screen
def draw_label(text, pos):
    label = font.render(text, True, WHITE)
    screen.blit(label, pos)


# helper function to draw the arrowhead for the velocity vectory
def draw_arrowhead(start, end, color=WHITE):
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    length = 10
    left = (end[0] - length * math.cos(angle - 0.5), end[1] - length * math.sin(angle - 0.5))
    right = (end[0] - length * math.cos(angle + 0.5), end[1] - length * math.sin(angle + 0.5))
    pygame.draw.polygon(screen, color, [end, left, right])


# star class (for the background) with occasional twinkling
class Star:
    def __init__(self, x, y, layer):
        self.x = x
        self.y = y
        self.layer = layer # Layer index for use in parallax
        self.phase = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(0.002, 0.005)
        self.offset = random.randint(0, 1000) # Phase offset for twinkling

    # For updating position
    def update(self, t):
        phase = (t * self.speed + self.offset) % (2 * math.pi)
        alpha = int(100 + 155 * (0.5 + 0.5 * math.sin(phase)))
        return alpha

    # For drawing
    def draw(self, t):
        alpha = self.update(t)
        s = pygame.Surface((2, 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 255, alpha), (1, 1), 1)
        offset_x = int((t * (self.layer + 1) * 0.05) % WIDTH)
        screen.blit(s, ((self.x - offset_x) % WIDTH, self.y))


# Generate twinkling stars across layers, layers help to add parallax effect
star_layers = []
for layer in range(3): # 3 Layers for parallax
    stars = [Star(random.randint(0, WIDTH), random.randint(0, HEIGHT), layer) for _ in range(75)]
    star_layers.append(stars)


# Particle class for explosion on impact
class Particle:
    def __init__(self, x, y, color):
        self.pos = np.array([x, y], dtype=np.float32)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 4)
        self.vel = np.array([np.cos(angle) * speed, np.sin(angle) * speed])
        self.life = 60  # Lifespan of particles in frames (in explosion animation), so 1 second
        self.color = color

    # For updating position
    def update(self):
        self.pos += self.vel
        self.life -= 1
        return self.life > 0

    # For drawing
    def draw(self):
        if 0 <= int(self.pos[0]) < WIDTH and 0 <= int(self.pos[1]) < HEIGHT:
            gfxdraw.filled_circle(screen, int(self.pos[0]), int(self.pos[1]), 2, self.color)


# Planet class
class Planet:
    def __init__(self, x, y, mass):
        self.x, self.y = x, y
        self.mass = mass
        self.radius = PLANET_RADIUS
        # Creates a 300 pixel wide strip to simulate a spinning texture
        self.texture_width = 300
        self.texture_height = self.radius * 2
        self.scroll_offset = 0
        self.texture_strip = pygame.Surface((self.texture_width, self.texture_height))
        self.generate_tileable_texture()
        # Views and masking for rendering texture
        self.scroll_texture_view = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.mask = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.mask, (255, 255, 255, 255), (self.radius, self.radius), self.radius)
        # Atmospheric glow generation
        self.glow_radius = self.radius * 2.5
        glow_size = int(self.glow_radius * 2)
        self.glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        center = self.glow_radius
        for y in range(glow_size):
            for x in range(glow_size):
                dx = x - center
                dy = y - center
                dist = math.hypot(dx, dy)
                if dist <= self.glow_radius:
                    alpha = int(80 * (1 - dist / self.glow_radius))
                    self.glow.set_at((x, y), (100, 180, 255, alpha))

        # Cloud layer setup
        self.cloud_scroll = 0
        self.cloud_texture = pygame.Surface((self.texture_width, self.texture_height), pygame.SRCALPHA)
        self.generate_cloud_texture()
        self.cloud_view = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)

    # Helper function go generate the texture that gets scrolled through
    def generate_tileable_texture(self):
        for y in range(self.texture_height):
            for x in range(self.texture_width):
                phase = (x / self.texture_width) * 2 * math.pi
                band = int(127 + 80 * math.sin(phase + y * 0.1))
                base_blue = 160 + int(math.sin(phase * 3) * 10)
                base_green = int(band * 0.6)
                self.texture_strip.set_at((x, y), (0, base_green, base_blue))

    # Similar thing for but the cloud texture
    def generate_cloud_texture(self):
        for y in range(self.texture_height):
            for x in range(self.texture_width):
                fx = (2 * math.pi * x) / self.texture_width
                fy = (2 * math.pi * y) / self.texture_height

                # Composite wave function
                value = (
                        math.sin(fx) * math.sin(fy) +
                        0.5 * math.sin(2 * fx + fy) +
                        0.3 * math.sin(fx - 2 * fy)
                )
                normalized = (value + 2.0) / 4.0  # Normalize to [0, 1]

                # Apply threshold to introduce cloud gaps
                if normalized > 0.5:  # Only draw clouds in higher value regions
                    alpha = int(50 + 100 * (normalized - 0.5) * 2)  # Fade in more dense areas
                    self.cloud_texture.set_at((x, y), (255, 255, 255, alpha))
                else:
                    self.cloud_texture.set_at((x, y), (0, 0, 0, 0))  # Transparent (no cloud)

    # Called to draw planet
    def draw(self):
        # Scrolls base texture
        self.scroll_offset = (self.scroll_offset + 1) % self.texture_width
        self.scroll_texture_view.fill((0, 0, 0, 0))
        self.scroll_texture_view.blit(self.texture_strip, (0, 0), area=pygame.Rect(self.scroll_offset, 0, self.radius * 2, self.radius * 2))
        if self.scroll_offset + self.radius * 2 > self.texture_width:
            remaining = (self.scroll_offset + self.radius * 2) - self.texture_width
            self.scroll_texture_view.blit(self.texture_strip, (self.texture_width - self.scroll_offset, 0), area=pygame.Rect(0, 0, remaining, self.radius * 2))
        self.surface.blit(self.scroll_texture_view, (0, 0))
        self.surface.blit(self.mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # Glow and base surface
        glow_rect = self.glow.get_rect(center=(self.x, self.y))
        screen.blit(self.glow, glow_rect.topleft)
        planet_rect = self.surface.get_rect(center=(self.x, self.y))
        screen.blit(self.surface, planet_rect.topleft)

        # Draw cloud layer
        self.cloud_scroll = (self.cloud_scroll + 0.5) % self.texture_width
        self.cloud_view.fill((0, 0, 0, 0))
        self.cloud_view.blit(self.cloud_texture, (0, 0), area=pygame.Rect(self.cloud_scroll, 0, self.radius * 2, self.radius * 2))
        if self.cloud_scroll + self.radius * 2 > self.texture_width:
            remaining = (self.cloud_scroll + self.radius * 2) - self.texture_width
            self.cloud_view.blit(self.cloud_texture, (self.texture_width - self.cloud_scroll, 0), area=pygame.Rect(0, 0, remaining, self.radius * 2))
        self.cloud_view.blit(self.mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(self.cloud_view, planet_rect.topleft)


# Spacecraft class
class Spacecraft:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.radius = SPACECRAFT_RADIUS
        self.mass = 1
        self.velocity = np.array([0.0, 0.0])
        self.trail = [] # List of previous positions

    # Draws spacecraft as a simple red circle
    def draw(self):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius)
        for pos in self.trail:
            pygame.draw.circle(screen, (200, 0, 0), pos, 1)

    # Updating position and trail
    def update(self, planet, gravity_strength):
        dx = planet.x - self.x
        dy = planet.y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return False
        if dist < planet.radius:
            return True # Collision
        force_mag = gravity_strength * planet.mass * self.mass / dist**2
        force_dir = np.array([dx, dy]) / dist
        acceleration = force_mag * force_dir / self.mass
        self.velocity += acceleration
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        if 0 <= self.x <= WIDTH and 0 <= self.y <= HEIGHT:
            self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 300:
            self.trail.pop(0)
        return False


# Function for drawing starfield
def draw_parallax_stars(star_layers, t):
    for layer in star_layers:
        for star in layer:
            star.draw(t)


def main():
    # Initialising
    spacecraft, planet = None, None
    dragging, sim_running, slowmode = False, False, False
    drag_start, current_mouse_pos = None, None
    particles = []
    explosion_timer = 0

    running = True
    while running:
        # Set 60fps for animation
        dt = clock.tick(60)
        time_delta = dt / 1000.0
        ticks = pygame.time.get_ticks()

        # Handles inputs
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            manager.process_events(event)   # Handling UI interactions
            # User attempting to interact with planet mass and gravity slider
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if planet_mass_slider.get_abs_rect().collidepoint(event.pos) or gravity_strength_slider.get_abs_rect().collidepoint(event.pos):
                    continue
                # Creates spacecraft if the spacecraft doesn't exist and initialises the velocity vector
                if spacecraft is None:
                    spacecraft = Spacecraft(*event.pos)
                    drag_start = event.pos
                    current_mouse_pos = event.pos
                    dragging = True
                # Creates planet if planet does not already exist and then starts the simulation
                elif planet is None and not sim_running:
                    planet = Planet(*event.pos, planet_mass_slider.get_current_value())
                    sim_running = True
                    dragging = False
                    current_mouse_pos = None
            # Mouse release finalises velocity vector
            elif event.type == pygame.MOUSEBUTTONUP and dragging:
                dx = event.pos[0] - drag_start[0]
                dy = event.pos[1] - drag_start[1]
                spacecraft.velocity = np.array([dx, dy]) * 0.05
                dragging = False
            # Otherwise updates drag preview if mouse is still held down
            elif event.type == pygame.MOUSEMOTION and dragging:
                current_mouse_pos = event.pos
            elif event.type == pygame.KEYDOWN:
                # Activates slowmode with S
                if event.key == pygame.K_s:
                    slowmode = not slowmode
                # Restarts simulation with R
                elif event.key == pygame.K_r:
                    spacecraft, planet = None, None
                    sim_running, dragging = False, False
                    drag_start, current_mouse_pos = None, None
                    particles.clear()
                    explosion_timer = 0

        # Draws background
        screen.fill(BLACK)
        draw_parallax_stars(star_layers, ticks)

        # Adds labels
        draw_label("Planet Mass", (230, 20))
        draw_label("Gravity Strength", (230, 50))
        draw_label("S = Toggle Slowmode    R = Reset Simulation", (20, HEIGHT - 30))
        manager.update(time_delta)
        manager.draw_ui(screen)

        # If planet exists, draws the planet at its location
        if planet:
            planet.mass = planet_mass_slider.get_current_value()
            planet.draw()

        # Same for spacecraft
        if spacecraft:
            spacecraft.draw()
            # Physics update if the sim is running
            if sim_running and planet and explosion_timer == 0:
                collided = spacecraft.update(planet, gravity_strength_slider.get_current_value())
                if collided:
                    # When the spacecraft and planet collide, plays the explosion animation and then resets simulation
                    explosion_timer = pygame.time.get_ticks()
                    for _ in range(100):
                        particles.append(Particle(spacecraft.x, spacecraft.y, (255, 100, 0)))
            # Draw velocity vector preview
            if not sim_running and drag_start and current_mouse_pos:
                pygame.draw.line(screen, WHITE, drag_start, current_mouse_pos, 2)
                draw_arrowhead(drag_start, current_mouse_pos)

        # Draw and update particles
        particles[:] = [p for p in particles if p.update()]
        for p in particles:
            p.draw()

        # Resets explosion after animation completes
        if explosion_timer and pygame.time.get_ticks() - explosion_timer > 1000:
            spacecraft, planet = None, None
            sim_running, dragging = False, False
            drag_start, current_mouse_pos = None, None
            explosion_timer = 0
            particles.clear()

        pygame.display.flip()
        if slowmode:
            pygame.time.delay(100)


if __name__ == "__main__":
    main()
