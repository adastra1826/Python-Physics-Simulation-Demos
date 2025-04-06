"""
Planetary Orbits Physics Simulation.

This simulation models the orbital mechanics of planets around a central star,
based on Newtonian gravitational physics. It demonstrates principles of elliptical
orbits, conservation of angular momentum, and how gravitational forces maintain
planetary systems. The simulation shows how different initial conditions affect
orbital characteristics, how multi-body systems evolve over time, and the stable
configurations that can emerge from gravitational interactions in space.
"""

import pygame
import math
from scipy import integrate

# Window size
WIDTH, HEIGHT = 800, 600

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)

# Slider 1 shape
slider_1 = pygame.Rect(25, 50, 200, 20)
slider_1_border = pygame.Rect(
    slider_1.left - 1, slider_1.top - 1, slider_1.width + 2, slider_1.height + 2
)

# Slider 2 shape
slider_2 = pygame.Rect(
    slider_1.left, slider_1_border.top + slider_1_border.height, 200, 20
)
slider_2_border = pygame.Rect(
    slider_2.left - 1, slider_2.top - 1, slider_2.width + 2, slider_2.height + 2
)

# Star properties
STAR_MASS = 1e5  # very heavy, relative to planets
STAR_RADIUS = 20


def area_calc(r_1: float, r_2: float, d: float) -> float:
    """
    Calculates the area being intersected between two circles
    Args:
        r_1 : radius of the first circle
        r_2 : radius of the second circle
        d : distance between the two circles' centers

    Returns:
        The area of the section that both circle intersect
    """

    # Define the circles as semicircle functions.
    def f(x):
        return math.sqrt(r_1**2 - x**2)

    def g(x):
        return -math.sqrt(r_2**2 - x**2) + d

    # Define the function which determines the intersecting are when integrated
    def h(x):
        return f(x) - g(x)

    # Find the zeroes of h, to use as definite interval points
    zeros = math.sqrt(
        (-1 * ((r_1**2 - r_2**2) ** 2) / (4 * d**2)) + (r_1**2 + r_2**2) / 2 - d**2 / 4
    )
    return integrate.quad(h, -zeros, zeros)[0]


class Planet:
    """
    A Class that represents a Planet orbiting around the star

    Attributes
    ----------
    x : float
        x-position of the planet
    y : float
        y-position of the planet
    mass : float
        mass of the planet
    velocity : list[float]
        velocity of the electron - [x_velocity, y_velocity]
    trail : list[tuple[float, float]]
        list of coordinates to draw the trail of the planet
    exists : bool
        Value to use in main program to check whether the object should be removed from the system

    Methods
    -------
    update(planets, star):
        updates the position and velocity of the planet from the gravitational forces generated from the
        surrounding planets and star.
        Additionally, updates the mass, radius, velocity and exists attributes depending on the
        collisions between the other planets or the star.
    """

    def __init__(self, x: float, y: float, mass: float, velocity: list[float]):
        """Construction of a Planet's attributes"""
        self.x = x
        self.y = y
        self.mass = mass
        self.velocity = velocity
        self.radius = math.sqrt(mass)
        self.trail = []
        self.exists = True

    def update(self, planets: list["Planet"], star: tuple[float, float]):
        """
        Updates the position and velocity of the planet from the gravitational forces generated from the
        surrounding planets and star.
        Additionally, updates the mass, radius, velocity and exists attributes depending on the
        collisions between the other planets or the star.

        Parameters
        ----------
        planets : list[Planet], required
            list of all the planet objects in the system, for collision and gravity calculations
        star : list[float], required
            center star's position

        Returns
        -------
        None
        """
        # Update velocity from planets
        for planet in planets:
            if planet != self:
                dx = planet.x - self.x
                dy = planet.y - self.y
                angle = math.atan2(dy, dx)
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 0:
                    force = 0.1 * self.mass * planet.mass / dist**2
                    self.velocity[0] += force * math.cos(angle) / self.mass
                    self.velocity[1] += force * math.sin(angle) / self.mass

        # Update Velocity from star
        dx = star[0] - self.x
        dy = star[1] - self.y
        angle = math.atan2(dy, dx)
        dist = math.sqrt(dx**2 + dy**2)
        if dist > 0:
            force = 0.1 * self.mass * STAR_MASS / dist**2
            self.velocity[0] += force * math.cos(angle) / self.mass
            self.velocity[1] += force * math.sin(angle) / self.mass

        # Update position
        self.x += self.velocity[0]
        self.y += self.velocity[1]

        dx = star[0] - self.x
        dy = star[1] - self.y
        dist = math.sqrt(dx**2 + dy**2)

        # Collision with star
        if dist < STAR_RADIUS + self.radius:
            if dist > STAR_RADIUS:
                overlap_area = area_calc(self.radius, STAR_RADIUS, dist)
                old_area = math.pi * self.radius**2
                new_area = old_area - overlap_area
                self.radius = math.sqrt(new_area / math.pi)
                self.mass = self.mass * (new_area / old_area)
            else:
                self.exists = False

        # Collision with other planets
        for planet in planets:
            if planet != self:
                dx = planet.x - self.x
                dy = planet.y - self.y
                dist = math.sqrt(dx**2 + dy**2)
                if dist < self.radius + planet.radius:
                    # Calculate new velocities
                    v1x, v1y = self.velocity
                    v2x, v2y = planet.velocity
                    m1, m2 = self.mass, planet.mass
                    v1x_new = (v1x * (m1 - m2) + 2 * m2 * v2x) / (m1 + m2)
                    v1y_new = (v1y * (m1 - m2) + 2 * m2 * v2y) / (m1 + m2)
                    v2x_new = (v2x * (m2 - m1) + 2 * m1 * v1x) / (m1 + m2)
                    v2y_new = (v2y * (m2 - m1) + 2 * m1 * v1y) / (m1 + m2)

                    # Update velocities
                    self.velocity = [v1x_new, v1y_new]
                    planet.velocity = [v2x_new, v2y_new]

                    # Check if velocities are similar
                    if abs(v1x_new - v2x_new) < 0.1 and abs(v1y_new - v2y_new) < 0.1:
                        # Merge planets
                        self.mass += planet.mass
                        self.radius = math.sqrt(self.mass)
                        planets.remove(planet)

        # Update trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > 100:
            self.trail.pop(0)


def main():

    # Initialize and title the simulation screen
    pygame.init()
    pygame.display.set_caption("Solar System Simulation")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # Create star position
    star = (WIDTH // 2, HEIGHT // 2)

    # Initialize all variables that need to be reassigned during simulation
    planets = []
    mass_slider = 10
    velocity_slider = 5
    slider_1_click, slider_2_click = False, False
    running = True

    # Start simulation
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Adjust Slider 1: Mass
                if slider_1.collidepoint(event.pos):
                    slider_1_click = True
                    x_position = event.pos[0]

                # Adjust Slider 2: Mass
                elif slider_2.collidepoint(event.pos):
                    slider_2_click = True
                    x_position = event.pos[0]

                # Create new planet at mouse position
                else:
                    x, y = event.pos
                    dist = star[0] - x, star[1] - y
                    perp_angle = math.atan2(dist[1], dist[0]) - (math.pi / 2)
                    mag = velocity_slider
                    planets.append(
                        Planet(
                            x,
                            y,
                            mass_slider,
                            [mag * math.cos(perp_angle), mag * math.sin(perp_angle)],
                        )
                    )

            # Keep track of mouse position in case slider is held down
            elif event.type == pygame.MOUSEMOTION:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                x_position = mouse_x

            # Stop changing slider if mouse button is released
            elif event.type == pygame.MOUSEBUTTONUP:
                slider_1_click = False
                slider_2_click = False

        # Change the mass and velocity to the slider values
        if slider_1_click:
            mass_slider = int(
                min(
                    max(((x_position - slider_1.left) / slider_1.width * 20) + 1, 1), 20
                )
            )
        elif slider_2_click:
            velocity_slider = int(
                min(
                    max(((x_position - slider_2.left) / slider_2.width * 41) - 20, -20),
                    20,
                )
            )

        # Empty space background
        screen.fill((0, 0, 0))

        # Update all planets motion and size in the system
        for planet in planets:
            planet.update(planets, star)
            if planet.exists:
                pygame.draw.circle(
                    screen, WHITE, (int(planet.x), int(planet.y)), int(planet.radius)
                )

                # Draw planet trail
                for i, (x, y) in enumerate(planet.trail):
                    opacity = (
                        255 * (i + 1) // len(planet.trail)
                    )  # such that closest trail coord will be opaque,
                    # and furthest will be close to transparent
                    pygame.draw.circle(
                        screen, (opacity, opacity, opacity), (int(x), int(y)), 1
                    )
            else:
                planets.remove(planet)

        # Draw the star, with brighter colors near center to increase visual appeal
        pygame.draw.circle(screen, RED, star, STAR_RADIUS)
        pygame.draw.circle(screen, YELLOW, star, STAR_RADIUS - 3)
        pygame.draw.circle(screen, WHITE, star, STAR_RADIUS - 6)

        # Draw the sliders and text
        pygame.draw.rect(screen, WHITE, slider_1_border)
        pygame.draw.rect(screen, GRAY, slider_1)
        pygame.draw.rect(
            screen,
            BLACK,
            (
                slider_1.left + (mass_slider - 1) / 20 * slider_1.width,
                slider_1.top,
                10,
                slider_1.height,
            ),
        )
        pygame.draw.rect(screen, WHITE, slider_2_border)
        pygame.draw.rect(screen, GRAY, slider_2)
        pygame.draw.rect(
            screen,
            BLACK,
            (
                slider_2.left + (velocity_slider + 20) / 41 * slider_2.width,
                slider_2.top,
                5,
                slider_2.height,
            ),
        )

        font = pygame.font.Font(None, 36)
        text = font.render(
            f"Mass: {mass_slider}, Velocity: {velocity_slider:.1f}", True, WHITE
        )
        screen.blit(text, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
