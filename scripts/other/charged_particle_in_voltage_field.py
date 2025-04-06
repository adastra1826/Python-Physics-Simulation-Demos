import pygame
import numpy as np
import matplotlib.pyplot as plt

# Window size
WIDTH, HEIGHT = 800, 600

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Particle properties
PARTICLE_RADIUS = 5
PARTICLE_CHARGE = 1

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0

    def update(self, t):
        # Update velocity based on electric field
        Ex = np.cos(self.x/50)*np.sin(t/50)
        Ey = np.cos(self.y/50)*np.sin(t/50)
        self.vx += Ex * PARTICLE_CHARGE / 10
        self.vy += Ey * PARTICLE_CHARGE / 10

        # Update position based on velocity
        self.x += self.vx
        self.y += self.vy

        # Boundary checking
        if self.x < 0 or self.x > WIDTH:
            self.vx *= -1
        if self.y < 0 or self.y > HEIGHT:
            self.vy *= -1

    def draw(self, screen):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), PARTICLE_RADIUS)

def draw_voltage_field(screen, t):
    for x in range(0, WIDTH, 10):
        for y in range(0, HEIGHT, 10):
            voltage = np.sin(y/50)*np.sin(t/50) + np.sin(x/50)*np.sin(t/50)
            color = int((voltage + 2) / 4 * 255)
            if color >=255: print(voltage, ':', color)
            pygame.draw.rect(screen, (color, color, color), (x, y, 10, 10))

def draw_graphs(screen, kinetic_history, potential_history):
    # Draw both graphs at the bottom on the same axis
    pygame.draw.rect(screen, WHITE, (0, 600, 800, 200))
    for i in range(len(kinetic_history)):
        pygame.draw.circle(screen, (0, 255, 0), (10 + i, 790 - 10*kinetic_history[i]), 2)
        pygame.draw.circle(screen, (0, 0, 255), (10 + i, 700 + 40*potential_history[i]), 2)

    font = pygame.font.Font(None, 24)
    text = font.render("Kinetic Energy", True, (0, 255, 0))
    screen.blit(text, (10, 610))
    text = font.render("Potential Energy", True, (0, 0, 255))
    screen.blit(text, (210, 610))

    # Draw angular velocity graph
    #for i, velocity in enumerate(stick.velocity_history):
    #    pygame.draw.circle(screen, RED, (10 + i, 105 - int(velocity * 1000)), 2)
    #font = pygame.font.Font(None, 24)
    #text = font.render("Angular Velocity", True, RED)
    #screen.blit(text, (10, 240))



def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT+200))
    clock = pygame.time.Clock()
    particle = Particle(WIDTH // 2, HEIGHT // 2)
    running = True
    t = 0

    kinetic_energy_history = []
    potential_energy_history = []

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(WHITE)

        draw_voltage_field(screen, t)
        particle.update(t)
        particle.draw(screen)

        kinetic_energy = 0.5 * (particle.vx**2 + particle.vy**2)
        potential_energy = np.sin(particle.y/50)*np.sin(t/50) + np.sin(particle.x/50)*np.sin(t/50)

        kinetic_energy_history.append(kinetic_energy)
        potential_energy_history.append(potential_energy)
        while len(kinetic_energy_history) > WIDTH-20:
            kinetic_energy_history = kinetic_energy_history[1:]
            potential_energy_history = potential_energy_history[1:]

        draw_graphs(screen, kinetic_energy_history, potential_energy_history)
        
        pygame.display.flip()
        t += 1
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
