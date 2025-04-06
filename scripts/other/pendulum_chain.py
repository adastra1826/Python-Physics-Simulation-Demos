"""
Pendulum Chain Physics Simulation.

This simulation models a chain of connected pendulums, where each pendulum
is attached to the end of the previous one. It demonstrates principles of
coupled oscillators, energy transfer through a connected system, and how
initial conditions create complex motion patterns. The simulation shows
how energy propagates through the chain, creating fascinating wave-like motions
and chaotic behavior that emerges from simple physical rules. Each pendulum
affects and is affected by its neighbors, illustrating concepts of resonance,
energy conservation, and the complexity that arises in multi-body systems.
"""

import pygame
import math
import sys

# Window dimensions
WIDTH, HEIGHT = 800, 600

# Pendulum properties
NUM_PENDULUMS = 35
PENDULUM_LENGTH = 100
PENDULUM_SPACING = 20
LINE_WIDTH = 4

# Simulation properties
GRAVITY = 0.2
SLOW_MOTION = False

# Tuple of gradient of 35 rainbow colors from red to violet
colors = (
    (255, 0, 0),
    (255, 20, 0),
    (255, 40, 0),
    (255, 60, 0),
    (255, 80, 0),  # Red to Orange
    (255, 100, 0),
    (255, 120, 0),
    (255, 140, 0),
    (255, 160, 0),
    (255, 180, 0),  # Orange to Yellow
    (255, 200, 0),
    (255, 220, 0),
    (255, 255, 0),
    (228, 255, 0),
    (200, 255, 0),  # Yellow to Green
    (172, 255, 0),
    (144, 255, 0),
    (116, 255, 0),
    (88, 255, 0),
    (60, 255, 0),  # Green
    (0, 255, 0),
    (0, 255, 60),
    (0, 255, 120),
    (0, 255, 180),
    (0, 255, 255),  # Green to Cyan
    (0, 220, 255),
    (0, 180, 255),
    (0, 120, 255),
    (0, 60, 255),
    (0, 0, 255),  # Cyan to Blue
    (20, 0, 255),
    (40, 0, 255),
    (60, 0, 255),
    (80, 0, 255),
    (100, 0, 255),  # Blue to Violet
)


class Pendulum:
    """
    Represents a pendulum for simulation.

    Attributes:
        x (int): The x-coordinate of the pendulum's pivot point.
        y (int): The y-coordinate of the pendulum's pivot point.
        length (int): The length of the pendulum.
        angle (float): The current angle of the pendulum (in radians).
        color (tuple): The RGB color of the pendulum.
        angular_velocity (float): The current angular velocity of the pendulum.
    """

    def __init__(self, x, y, length, angle, color):
        """
        Initializes a new Pendulum instance.

        Args:
            x (int): The x-coordinate of the pendulum's pivot point.
            y (int): The y-coordinate of the pendulum's pivot point.
            length (int): The length of the pendulum.
            angle (float): The initial angle of the pendulum (in radians).
            color (tuple): The RGB color of the pendulum.
        """
        self.x = x
        self.y = y
        self.length = length
        self.angle = angle
        self.color = color
        self.angular_velocity = 0

    def update(self):
        """
        Updates the pendulum's angle and angular velocity based on gravitational forces.
        """
        self.angular_velocity += (GRAVITY / self.length) * math.sin(self.angle)
        self.angle += self.angular_velocity

        # Apply damping to the angular velocity
        self.angular_velocity *= 0.998

    def draw(self, screen):
        """
        Draws the pendulum on the given screen.

        Args:
            screen (pygame.Surface): The surface on which to draw the pendulum.
        """
        end_x = self.x + math.sin(self.angle) * self.length
        end_y = self.y - math.cos(self.angle) * self.length
        pygame.draw.line(screen, self.color, (self.x, self.y), (end_x, end_y), 1)
        pygame.draw.circle(screen, self.color, (end_x, end_y), 10)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # Create a list of pendulums with varying lengths and fixed initial angle
    pendulums = []
    for i in range(NUM_PENDULUMS):
        length = PENDULUM_LENGTH + i * 11
        angle = math.pi / 6
        color = colors[i]
        pendulums.append(Pendulum(WIDTH // 2, 50, length, angle, color))
    pendulums.reverse()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Toggle slow motion mode
                    global SLOW_MOTION
                    SLOW_MOTION = not SLOW_MOTION

        # Clear the screen for the next frame
        screen.fill((0, 0, 0))

        # Update and draw each pendulum
        for pendulum in pendulums:
            pendulum.update()
            pendulum.draw(screen)

        # Update the display and control frame rate
        pygame.display.flip()
        clock.tick(60 if not SLOW_MOTION else 30)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
