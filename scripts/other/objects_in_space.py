"""
Objects in Space Physics Simulation.

This simulation models the motion of celestial bodies under the influence of gravity.
It demonstrates principles of orbital mechanics, including how objects follow paths
determined by gravitational forces according to Newton's laws. The simulation shows
how multiple bodies interact gravitationally, creating complex orbital patterns,
stable systems, or chaotic trajectories depending on initial conditions and mass
distributions. It visualizes concepts like orbital velocity, escape velocity,
gravitational slingshots, and how conservation of angular momentum governs the
movement of objects in space.
"""

import pygame
import pygame_gui
from pygame.locals import QUIT
from Box2D import (b2World, b2CircleShape, b2_dynamicBody, b2Vec2)
import numpy as np

# Constants
PPM = 2e-2  # Pixels per meter (adjusted for simulation)
TARGET_FPS = 120  # Target frames per second
TIME_STEP = 1.0 / TARGET_FPS  # Time step for the simulation
VELOCITY_ITERATIONS = 8  # Number of velocity iterations for Box2D
POSITION_ITERATIONS = 3  # Number of position iterations for Box2D
G = 4.416e-12  # Gravitational constant, adjusted to prevent overflow

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
LIME_GREEN = (0, 255, 0)

# Pygame initialization
pygame.init()
screen = pygame.display.set_mode((1000, 1000), 0, 32)
pygame.display.set_caption('Gravity Simulation')
clock = pygame.time.Clock()

# Pygame GUI initialization
ui_manager = pygame_gui.UIManager((1000, 1000))

# Box2D world initialization
world = b2World(gravity=(0, 0), doSleep=True)

# Create reset button
reset_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, 10), (100, 50)),
                                            text='Reset',
                                            manager=ui_manager)

class Object:
    def __init__(self, x, y, mass, radius, color, label, initial_velocity=0):
        """
        Initialize an object with given parameters.
        """
        self.body = world.CreateBody(
            type=b2_dynamicBody,
            position=(x / PPM, y / PPM)
        )
        self.fixture = self.body.CreateFixture(
            shape=b2CircleShape(radius=radius * PPM),
            density=mass / (np.pi * (radius * PPM) ** 2),
            friction=0
        )
        self.mass = mass
        self.color = color
        self.label = label
        self.trail = []  # List to store the trail of the object
        self.velocity = b2Vec2(initial_velocity, 0)  # Initial velocity in m/s
        self.acceleration = b2Vec2(0, 0)  # Initial acceleration

        if initial_velocity != 0:
            self.body.ApplyLinearImpulse((-initial_velocity * mass, 0), self.body.position, True)

    def update_trail(self):
        """
        Update the trail of the object to show its path.
        """
        self.trail.append(self.body.position * PPM)
        if len(self.trail) > TARGET_FPS * 5:  # Limit the trail length to 5 seconds
            self.trail.pop(0)

    def apply_force(self, force):
        """
        Apply a force to the object, updating its acceleration.
        """
        self.acceleration += force / self.mass

    def update_velocity(self):
        """
        Update the velocity of the object based on its acceleration.
        """
        self.velocity += self.acceleration * TIME_STEP
        self.body.linearVelocity = self.velocity
        self.acceleration = b2Vec2(0, 0)  # Reset acceleration after applying it

    def get_velocity_kms(self):
        """
        Get the velocity of the object in km/s.
        """
        return self.velocity.length / 1000  # Convert m/s to km/s

def calculate_gravitational_force(obj1, obj2):
    """
    Calculate the gravitational force between two objects.
    """
    distance_vec = obj2.body.position - obj1.body.position
    distance = distance_vec.length
    if distance == 0:
        return b2Vec2(0, 0)  # Avoid division by zero
    # Newton's law of universal gravitation: F = G * (m1 * m2) / r^2
    force_magnitude = G * obj1.mass * obj2.mass / distance**2
    force_direction = distance_vec
    force_direction.Normalize()
    return force_magnitude * force_direction

def main():
    """
    Main function to run the simulation.
    """
    running = True
    object_count = {'big': 0, 'small': 0}  # Dictionary to count objects
    objects = []  # List to store objects

    while running:
        time_delta = clock.tick(TARGET_FPS) / 1000.0  # Time elapsed since last frame

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False  # Exit the loop if the window is closed
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    object_count['big'] += 1
                    objects.append(
                        Object(event.pos[0], event.pos[1], 2e25, 4.4646e4, YELLOW, f'big{object_count["big"]}')
                    )
                elif event.button == 3:  # Right mouse button
                    radius = 6.378e3
                    initial_velocity = -radius * 0.01 * 1000  # Convert km/s to m/s and negate for left direction
                    object_count['small'] += 1
                    objects.append(
                        Object(event.pos[0], event.pos[1], 6e19, radius, LIME_GREEN, f'small{object_count["small"]}', initial_velocity)
                    )
            ui_manager.process_events(event)  # Process GUI events

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == reset_button:
                    objects.clear()  # Clear all objects
                    object_count = {'big': 0, 'small': 0}  # Reset object count

        screen.fill(BLACK)

        # Calculate gravity for each object
        for i, obj1 in enumerate(objects):
            for obj2 in objects[i+1:]:
                force = calculate_gravitational_force(obj1, obj2)
                obj1.apply_force(force)
                obj2.apply_force(-force)

        # Update and draw each object
        for obj in objects:
            obj.update_velocity()
            obj.update_trail()
            pygame.draw.circle(screen, obj.color, (int(obj.body.position.x * PPM), int(obj.body.position.y * PPM)), int(obj.fixture.shape.radius * PPM))
            for i in range(len(obj.trail) - 1):
                pygame.draw.line(screen, obj.color, obj.trail[i], obj.trail[i + 1], 1)

            # Display velocity readout
            velocity_text = f'{obj.label}: {obj.get_velocity_kms():.2f} km/s'
            font = pygame.font.Font(None, 18)  # Smaller font size
            text_surface = font.render(velocity_text, True, WHITE)
            screen.blit(text_surface, (int(obj.body.position.x * PPM), int(obj.body.position.y * PPM) - 30))

        world.Step(TIME_STEP, VELOCITY_ITERATIONS, POSITION_ITERATIONS)  # Step the Box2D world
        ui_manager.update(time_delta)  # Update the UI manager
        ui_manager.draw_ui(screen)  # Draw the UI elements

        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    main()