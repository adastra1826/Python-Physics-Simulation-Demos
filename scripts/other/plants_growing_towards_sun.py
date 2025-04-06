import pygame
import random
import math
import time
from pygame import gfxdraw

# Initialize pygame
pygame.init()

# Constants for simulation window dimensions and colors
WIDTH, HEIGHT = 1200, 700
GROUND_HEIGHT = HEIGHT - 50
SKY_COLOR = (135, 206, 235)
GROUND_COLOR = (34, 139, 34)
SUN_COLOR = (255, 255, 0)
PLANT_COLORS = [
    (50, 205, 50),  # Lime Green
    (34, 139, 34),  # Forest Green
    (0, 128, 0),  # Green
    (107, 142, 35),  # Olive Drab
    (0, 100, 0)  # Dark Green
]
RAIN_COLOR = (174, 194, 224)
FONT_COLOR = (255, 255, 255)
FONT_BG_COLOR = (0, 0, 0, 128)

# Simulation parameters
MAX_PLANTS = 500
INITIAL_PLANTS = 50
SUN_RADIUS = 30
SUN_SPEED = 0.5
LIGHT_INTENSITY = 1.0
MAX_LIGHT_INTENSITY = 2.0
MIN_LIGHT_INTENSITY = 0.2
LIGHT_CHANGE_SPEED = 0.05
RAIN_DURATION = 5  # seconds
RAIN_PROBABILITY = 0.001  # per frame
STORM_PROBABILITY = 0.0005  # per frame

# Plant growth parameters - adjust these to control growth speed
ENERGY_GAIN_MULTIPLIER = 10
ENERGY_THRESHOLD = 0.2
ANGLE_RANDOMNESS = 0.15

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Plant Growth Simulation")
clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 16)
large_font = pygame.font.SysFont('Arial', 24)


class Plant:
    """
    Represents a plant that grows based on sunlight, weather, and its health.
    """
    def __init__(self, x):
        """
        Initializes a plant with position, growth properties, health, and random color.
        """
        self.x = x
        self.y = GROUND_HEIGHT
        self.segments = []
        self.growth_rate = random.uniform(0.3, 0.5)  # Increased growth rate
        self.max_height = random.randint(120, 200)
        self.color = random.choice(PLANT_COLORS)
        self.thickness = 2
        self.energy = 0
        self.health = 100
        self.age = 0
        self.leaf_probability = 0.25

        # Add initial segments to make plant visible
        self.add_segment(self.x, self.y, -math.pi / 2)  # First segment
        self.add_segment(self.x, self.y - 4, -math.pi / 2)  # Second segment to make it visible

    def add_segment(self, x, y, angle):
        """
        Adds a new segment to the plant, representing its growth.
        """
        length = random.uniform(2, 4)
        self.segments.append({
            'x': x,
            'y': y,
            'angle': angle,
            'length': length,
            'thickness': self.thickness
        })
        self.thickness = min(self.thickness + 0.15, 4)

    def grow(self, sun_x, sun_y, light_intensity, weather_effect):
        """
        Simulates the growth of the plant based on sunlight, light intensity, and weather.
        """
        if len(self.segments) == 0 or self.health <= 0:
            return

        self.age += 1

        last_segment = self.segments[-1]
        dx = sun_x - last_segment['x']
        dy = sun_y - last_segment['y']
        distance_to_sun = max(math.sqrt(dx * dx + dy * dy), 1)

        # Calculate the angle towards the sun and energy factor based on angle
        angle_to_sun = math.atan2(dy, dx)
        angle_diff = abs(last_segment['angle'] - angle_to_sun)
        energy_factor = (math.pi - angle_diff) / math.pi
        self.energy += light_intensity * energy_factor / distance_to_sun * (0.15 * ENERGY_GAIN_MULTIPLIER)

        # Modify growth based on weather effects
        growth_modifier = 1.0
        if weather_effect == "rain":
            growth_modifier = 1.6
        elif weather_effect == "storm":
            growth_modifier = 0.7
            self.health -= 0.1

        if self.energy > ENERGY_THRESHOLD and len(self.segments) < self.max_height:
            self.energy -= ENERGY_THRESHOLD

            current_angle = last_segment['angle']
            new_angle = current_angle + (angle_to_sun - current_angle) * 0.07 * light_intensity
            new_angle += random.uniform(-ANGLE_RANDOMNESS, ANGLE_RANDOMNESS) * (1.1 - light_intensity)

            new_x = last_segment['x'] + math.cos(new_angle) * last_segment['length']
            new_y = last_segment['y'] + math.sin(new_angle) * last_segment['length']

            self.add_segment(new_x, new_y, new_angle)

        self.health += random.uniform(-0.05, 0.05)
        self.health = max(0, min(self.health, 100))

    def draw(self, surface):
        """
        Draws the plant and its segments on the screen.
        """
        if len(self.segments) < 2:
            return

        last_seg = self.segments[-1]
        if len(self.segments) > 4 and random.random() < self.leaf_probability:
            leaf_size = random.randint(4, 8)
            leaf_color = (
                min(255, self.color[0] + 40),
                min(255, self.color[1] + 40),
                max(0, self.color[2] - 20)
            )
            pygame.draw.circle(surface, leaf_color,
                               (int(last_seg['x']), int(last_seg['y'])), leaf_size)

        for i in range(1, len(self.segments)):
            prev_seg = self.segments[i - 1]
            curr_seg = self.segments[i]

            stem_color = (
                max(0, self.color[0] + random.randint(-20, 0)),
                min(255, self.color[1] + random.randint(0, 20)),
                max(0, self.color[2] + random.randint(-20, 0))
            )

            if self.health < 50:
                darken = min(100, int(100 - self.health))
                stem_color = (
                    max(0, stem_color[0] - darken),
                    max(0, stem_color[1] - darken),
                    max(0, stem_color[2] - darken)
                )

            thickness = int(curr_seg['thickness'])
            pygame.draw.line(surface, stem_color,
                             (prev_seg['x'], prev_seg['y']),
                             (curr_seg['x'], curr_seg['y']),
                             max(2, thickness))


class Sun:
    """
    Represents the sun and its movement, affecting the light intensity that plants receive.
    """
    def __init__(self):
        self.x = 0
        self.y = HEIGHT // 3
        self.direction = 1  # 1 for right, -1 for left
        self.speed = SUN_SPEED
        self.light_intensity = LIGHT_INTENSITY

    def update(self):
        """
        Updates the sun's position and light intensity based on its distance from the center.
        """
        self.x += self.direction * self.speed

        if self.x > WIDTH + SUN_RADIUS:
            self.direction = -1
        elif self.x < -SUN_RADIUS:
            self.direction = 1

        midday = WIDTH / 2
        distance_to_midday = abs(self.x - midday)
        self.light_intensity = max(MIN_LIGHT_INTENSITY,
                                   MIN_LIGHT_INTENSITY + (MAX_LIGHT_INTENSITY - MIN_LIGHT_INTENSITY) *
                                   (1 - distance_to_midday / midday))

    def draw(self, surface):
        """
        Draws the sun on the screen with a glowing effect.
        """
        for i in range(5, 0, -1):
            alpha = 50 - i * 10
            radius = SUN_RADIUS + i * 2
            temp_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, (*SUN_COLOR, alpha), (radius, radius), radius)
            surface.blit(temp_surface, (self.x - radius, self.y - radius))

        pygame.draw.circle(surface, SUN_COLOR, (int(self.x), int(self.y)), SUN_RADIUS)


class Weather:
    """
    Handles weather events like rain or storms that affect plant growth and the environment.
    """
    def __init__(self):
        self.active = False
        self.type = None
        self.start_time = 0
        self.duration = 0
        self.particles = []

    def start(self, weather_type):
        """
        Starts a new weather event (rain or storm) with specific properties.
        """
        self.active = True
        self.type = weather_type
        self.start_time = time.time()

        if weather_type == "rain":
            self.duration = RAIN_DURATION
            self.particles = [{'x': random.randint(0, WIDTH),
                               'y': random.randint(0, GROUND_HEIGHT),
                               'speed': random.uniform(5, 10)}
                              for _ in range(200)]
        elif weather_type == "storm":
            self.duration = RAIN_DURATION * 1.5
            self.particles = [{'x': random.randint(0, WIDTH),
                               'y': random.randint(0, GROUND_HEIGHT),
                               'speed': random.uniform(10, 15),
                               'angle': random.uniform(-0.2, 0.2)}
                              for _ in range(300)]
        else:
            self.duration = 0

    def update(self):
        """
        Updates the state of the weather event, either continuing or ending it.
        """
        if not self.active:
            if random.random() < RAIN_PROBABILITY:
                self.start("rain")
            elif random.random() < STORM_PROBABILITY:
                self.start("storm")
            return

        if time.time() - self.start_time > self.duration:
            self.active = False
            self.type = None
            return

        if self.type in ["rain", "storm"]:
            for p in self.particles:
                if self.type == "rain":
                    p['y'] += p['speed']
                    if p['y'] > GROUND_HEIGHT:
                        p['x'] = random.randint(0, WIDTH)
                        p['y'] = random.randint(-50, 0)
                elif self.type == "storm":
                    p['x'] += math.sin(p['angle']) * 5
                    p['y'] += p['speed']
                    if p['y'] > GROUND_HEIGHT or p['x'] < 0 or p['x'] > WIDTH:
                        p['x'] = random.randint(0, WIDTH)
                        p['y'] = random.randint(-50, 0)
                        p['angle'] = random.uniform(-0.2, 0.2)

    def draw(self, surface):
        """
        Draws the weather particles (rain or storm) on the screen.
        """
        if not self.active or self.type not in ["rain", "storm"]:
            return

        for p in self.particles:
            if self.type == "rain":
                pygame.draw.line(surface, RAIN_COLOR,
                                 (p['x'], p['y']),
                                 (p['x'], p['y'] + 10), 1)
            elif self.type == "storm":
                angle = p['angle']
                end_x = p['x'] + math.sin(angle) * 15
                end_y = p['y'] + 15
                pygame.draw.line(surface, RAIN_COLOR,
                                 (p['x'], p['y']),
                                 (end_x, end_y), 1)


def draw_text_with_background(surface, text, pos, font, color=FONT_COLOR, bg_color=FONT_BG_COLOR):
    """
    Draws text on the screen with a background for better visibility.
    """
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(topleft=pos)

    bg_surface = pygame.Surface((text_rect.width + 4, text_rect.height + 4), pygame.SRCALPHA)
    bg_surface.fill(bg_color)

    surface.blit(bg_surface, (pos[0] - 2, pos[1] - 2))
    surface.blit(text_surface, pos)


def main():
    """
    Main game loop for the plant growth simulation.
    """
    running = True
    paused = False
    plants = [Plant(random.randint(50, WIDTH - 50)) for _ in range(INITIAL_PLANTS)]
    sun = Sun()
    weather = Weather()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    sun.direction *= -1
                elif event.key == pygame.K_UP:
                    sun.light_intensity = min(sun.light_intensity + LIGHT_CHANGE_SPEED, MAX_LIGHT_INTENSITY)
                elif event.key == pygame.K_DOWN:
                    sun.light_intensity = max(sun.light_intensity - LIGHT_CHANGE_SPEED, MIN_LIGHT_INTENSITY)
                elif event.key == pygame.K_n and len(plants) < MAX_PLANTS:
                    plants.append(Plant(random.randint(50, WIDTH - 50)))

        if paused:
            screen.fill(SKY_COLOR)
            sun.draw(screen)
            weather.draw(screen)
            pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_HEIGHT, WIDTH, HEIGHT - GROUND_HEIGHT))

            for plant in plants:
                plant.draw(screen)

            paused_text = large_font.render("PAUSED", True, (255, 0, 0))
            screen.blit(paused_text, (WIDTH // 2 - paused_text.get_width() // 2, 20))

            pygame.display.flip()
            clock.tick(60)
            continue

        sun.update()
        weather.update()

        for plant in plants[:]:
            plant.grow(sun.x, sun.y, sun.light_intensity, weather.type if weather.active else None)

            if plant.health <= 0 and random.random() < 0.01:
                plants.remove(plant)
                if random.random() < 0.3 and len(plants) < MAX_PLANTS:
                    plants.append(Plant(random.randint(50, WIDTH - 50)))

        screen.fill(SKY_COLOR)
        sun.draw(screen)
        weather.draw(screen)
        pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_HEIGHT, WIDTH, HEIGHT - GROUND_HEIGHT))

        for plant in sorted(plants, key=lambda p: len(p.segments)):
            plant.draw(screen)

        stats = [
            f"Plants: {len(plants)}/{MAX_PLANTS}",
            f"Sunlight: {sun.light_intensity:.2f}",
            f"Weather: {weather.type if weather.active else 'clear'}",
            f"Controls: SPACE=Pause, UP/DOWN=Light, R=Reverse Sun, N=New Plant"
        ]

        for i, stat in enumerate(stats):
            draw_text_with_background(screen, stat, (10, 10 + i * 25), font)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
