"""
Entropy Physics Simulation (Under Development).

This simulation attempts to model entropy increase in physical systems.
It demonstrates principles of statistical mechanics and the second law of 
thermodynamics - that isolated systems spontaneously evolve toward states of
higher entropy. While marked as needing work, the simulation aims to show how
ordered systems naturally progress toward disorder, how microscopic randomness
leads to macroscopic predictability, and how irreversible processes emerge
from reversible microscopic physics. Note that this implementation may have
limitations or simplifications in its current state that affect its accuracy
or comprehensiveness.
"""

import pygame
import numpy as np
import random
import math


# Simulation Settings

WIDTH, HEIGHT = 900, 700   # Increased resolution for better visuals
GRID_SIZE = 40             # Grid resolution for entropy heatmap
PARTICLE_COUNT = 200       # Number of gas-like particles
PARTICLE_RADIUS = 4        # Visual size of particles
FONT_SIZE = 22             # UI text size
FPS = 60                   # Smooth frame rate
NOISE_LEVEL = 0.1          # Probability of bit flips in transmission
MESSAGE_LENGTH = 50        # Length of the binary message

# Colors
WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
RED = (255, 70, 70)        # High entropy (errors)
GREEN = (50, 200, 50)      # Low entropy (correct data)
BLUE = (50, 50, 255)       # Particles representing physical entropy
GRAY = (100, 100, 100)     # Background grid
YELLOW = (255, 255, 100)   # Noise-affected areas


# Pygame Initialization

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🔢 Entropy & Data Transmission Simulation")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", FONT_SIZE, bold=True)


# Particle Class (Gas-Like Behavior)

class Particle:
    """Represents a gas-like particle that moves randomly in the system."""
    
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.vx = random.uniform(-2, 2)  
        self.vy = random.uniform(-2, 2)

    def move(self):
        """Moves the particle and applies boundary collisions."""
        self.x += self.vx
        self.y += self.vy

        # Reflect off walls
        if self.x < 0 or self.x > WIDTH:
            self.vx = -self.vx
        if self.y < 0 or self.y > HEIGHT:
            self.vy = -self.vy


# Data Transmission Functions

def generate_message(length):
    """Generates a random binary message (0s and 1s)."""
    return np.random.choice([0, 1], size=length)

def add_noise(message, noise_level):
    """Simulates bit flips caused by noise in a communication channel."""
    noise_mask = np.random.choice([0, 1], size=len(message), p=[1 - noise_level, noise_level])
    return np.logical_xor(message, noise_mask)

def calculate_ber(original, noisy):
    """Computes the Bit Error Rate (BER) based on incorrect bits."""
    errors = np.sum(original != noisy)
    return errors / len(original)


# Shannon Entropy Calculation

def calculate_entropy(particles):
    """Computes entropy based on particle density distribution."""
    grid = np.zeros((GRID_SIZE, GRID_SIZE))
    
    for p in particles:
        grid_x = min(GRID_SIZE - 1, max(0, int((p.x / WIDTH) * GRID_SIZE)))
        grid_y = min(GRID_SIZE - 1, max(0, int((p.y / HEIGHT) * GRID_SIZE)))
        grid[grid_x, grid_y] += 1  

    # Normalize probabilities
    total_particles = len(particles)
    probabilities = grid / total_particles

    # Compute entropy safely 
    entropy = -np.nansum(probabilities * np.log2(probabilities, where=probabilities > 0))
    return entropy, grid


#  Visualization Functions

def draw_heatmap(screen, entropy_grid):
    """Draws the entropy heatmap."""
    cell_width = WIDTH // GRID_SIZE
    cell_height = HEIGHT // GRID_SIZE

    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            intensity = int(255 * (entropy_grid[i, j] / np.max(entropy_grid) if np.max(entropy_grid) > 0 else 0))
            color = (intensity, intensity // 2, 255 - intensity)  
            pygame.draw.rect(screen, color, (i * cell_width + cell_width // 2, j * cell_height + cell_height // 2, cell_width, cell_height))

def draw_particles(screen, particles):
    """Draws particles as small blue circles."""
    for p in particles:
        pygame.draw.circle(screen, BLUE, (int(p.x), int(p.y)), PARTICLE_RADIUS)

def draw_ui(screen, entropy_value, noise_level, bit_error_rate, elapsed_time):
    """Displays entropy, noise level, and transmission accuracy as text UI."""
    pygame.draw.rect(screen, BLACK, (0, HEIGHT - 150, WIDTH, 150)) 

    entropy_text = font.render(f"Entropy: {entropy_value:.3f} bits", True, WHITE)
    noise_text = font.render(f"Noise Level: {noise_level:.2f}", True, WHITE)
    ber_text = font.render(f"Bit Error Rate (BER): {bit_error_rate:.3f}", True, WHITE)
    time_text = font.render(f"Elapsed Time: {elapsed_time:.1f}s", True, WHITE)

    screen.blit(entropy_text, (20, HEIGHT - 120))
    screen.blit(noise_text, (20, HEIGHT - 90))
    screen.blit(ber_text, (20, HEIGHT - 60))
    screen.blit(time_text, (20, HEIGHT - 30))

def draw_message(screen, message, noisy_message, y_offset, label):
    """Draws transmitted vs. received message using colored rectangles."""
    text = font.render(label, True, WHITE)
    screen.blit(text, (20, y_offset - 30))

    for i, (bit, noisy_bit) in enumerate(zip(message, noisy_message)):
        color = GREEN if bit == noisy_bit else RED  
        pygame.draw.rect(screen, color, (20 + i * 10, y_offset, 8, 20))


# Main Simulation Loop

def main():
    """Runs the entropy and data transmission simulation."""
    particles = [Particle() for _ in range(PARTICLE_COUNT)]
    message = generate_message(MESSAGE_LENGTH)
    start_time = pygame.time.get_ticks()

    running = True
    while running:
        screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        for p in particles:
            p.move()

        entropy_value, entropy_grid = calculate_entropy(particles)
        noisy_message = add_noise(message, NOISE_LEVEL)
        bit_error_rate = calculate_ber(message, noisy_message)

        draw_heatmap(screen, entropy_grid)
        draw_particles(screen, particles)
        draw_message(screen, message, noisy_message, HEIGHT - 70, "Transmission Status:")
        draw_ui(screen, entropy_value, NOISE_LEVEL, bit_error_rate, (pygame.time.get_ticks() - start_time) / 1000)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

# run simulation
if __name__ == "__main__":
    main()
