"""
Obstructed Fluid Flow Physics Simulation.

This simulation models the flow of fluid (liquid or gas) around obstacles in a channel.
It demonstrates principles of fluid dynamics including laminar and turbulent flow,
boundary layer formation, and how obstacles create disturbances in flow patterns.
The simulation shows how fluid particles navigate around obstructions, how vortices
form in certain flow conditions, and how the shape and arrangement of obstacles
affect the overall flow characteristics. It visualizes concepts like flow separation,
wake formation, and how pressure differences develop around objects in flowing fluids,
which are fundamental to understanding aerodynamics and hydrodynamics.
"""

import pygame
import numpy as np
import random
import math

# Window dimensions
WIDTH, HEIGHT = 800, 600

# Pipe dimensions
PIPE_WIDTH, PIPE_HEIGHT = 400, 100
PIPE_SPACING = 50

# Particle properties
PARTICLE_SIZE = 3

# Velocity gradient heatmap colors (blue to red)
VELOCITY_COLORS = [(0, 0, 255), (255, 0, 0)]


def get_particle_color(v, max_v):
    """
    Returns a color interpolated between blue (slow) and red (fast)
    based on the particle's horizontal velocity 'v' relative to max_v.
    """
    fraction = max(0, min(v / max_v, 1))
    r = int(fraction * 255)
    b = int((1 - fraction) * 255)
    return (r, 0, b)


class Particle:
    def __init__(self, x, y, vx, vy, pipe):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.pipe = pipe  # Particle is associated with a specific pipe

    def update(self, global_max_velocity):
        """
        Update the particle's velocity and position:
         - Compute a target horizontal velocity based on a parabolic profile
         - Use a dynamic relaxation facto
         - Dampen vy to keep the flow mostly horizontal
         - Enforce no-slip at the top and bottom boundaries
         - Repel the particle if its tentative new position is inside the obstruction
        """
        # Compute the target horizontal velocity (laminar profile)
        center_y = self.pipe.y + self.pipe.height / 2
        norm = (self.y - center_y) / (self.pipe.height / 2)
        base_vx = global_max_velocity * (1 - norm**2)

        # Determine relaxation factor
        relaxation = 0.2
        if self.pipe.obstruction:
            max_obs_x = max(p[0] for p in self.pipe.obstruction)
            if self.x > max_obs_x + 5:
                relaxation = 0.5

        # Relax current vx toward the parabolic target
        self.vx += relaxation * (base_vx - self.vx)

        # Dampen vertical velocity to keep flow mostly horizontal
        self.vy *= 0.9

        # Compute tentative new position
        new_x = self.x + self.vx
        new_y = self.y + self.vy

        # Enforce no-slip at the top and bottom walls:
        if new_y - PARTICLE_SIZE < self.pipe.y:
            new_y = self.pipe.y + PARTICLE_SIZE
            self.vy = 0
            self.vx = 0
        if new_y + PARTICLE_SIZE > self.pipe.y + self.pipe.height:
            new_y = self.pipe.y + self.pipe.height - PARTICLE_SIZE
            self.vy = 0
            self.vx = 0

        # Check collision with the obstruction (if any)
        if self.pipe.obstruction:
            if self.pipe.point_inside_polygon(new_x, new_y, self.pipe.obstruction):
                # Compute the centroid of the obstruction polygon
                pts = self.pipe.obstruction
                centroid_x = sum(p[0] for p in pts) / len(pts)
                centroid_y = sum(p[1] for p in pts) / len(pts)
                dx = new_x - centroid_x
                dy = new_y - centroid_y
                dist = math.hypot(dx, dy)
                if dist == 0:
                    dx, dy = 1, 0
                    dist = 1
                # Repel the particle away from the centroid
                nx, ny = dx / dist, dy / dist
                repulsion = 5  # strength of repulsion force
                new_x += repulsion * nx
                new_y += repulsion * ny
                # Slight head loss.
                self.vx *= 0.95
                self.vy *= 0.95
                # Iterate a few times if still inside
                iterations = 0
                while (
                    self.pipe.point_inside_polygon(new_x, new_y, self.pipe.obstruction)
                    and iterations < 10
                ):
                    new_x += repulsion * nx
                    new_y += repulsion * ny
                    iterations += 1

        # Update the particle's position.
        self.x = new_x
        self.y = new_y

    def draw(self, screen, global_max_velocity):
        # Compute color based on the current horizontal velocity
        color = get_particle_color(self.vx, global_max_velocity)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), PARTICLE_SIZE)


class Pipe:
    def __init__(self, x, y, width, height, obstructed=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        # Generate an obstruction if required
        self.obstruction = generate_obstruction(self) if obstructed else None

    def draw(self, screen, label, font):
        # Draw the pipe boundary
        pygame.draw.rect(
            screen, (0, 0, 0), (self.x, self.y, self.width, self.height), 2
        )
        # Draw the label centered above the pipe
        label_surf = font.render(label, True, (0, 0, 0))
        label_rect = label_surf.get_rect(center=(self.x + self.width / 2, self.y - 20))
        screen.blit(label_surf, label_rect)
        # Draw the obstruction if present
        if self.obstruction:
            pygame.draw.polygon(screen, (0, 0, 0), self.obstruction)

    def point_inside_polygon(self, x, y, polygon):
        """
        Ray-casting algorithm to test if a point (x,y) is inside the polygon.
        """
        n = len(polygon)
        inside = False
        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside


def generate_obstruction(pipe):
    """
    Generates a random polygon with 5–9 sides that fits inside the pipe.
    The polygon is centered in the pipe with variable vertex positions.
    """
    center_x = pipe.x + pipe.width / 2
    center_y = pipe.y + pipe.height / 2
    num_sides = random.randint(5, 9)
    avg_radius = pipe.height / 4
    points = []
    for i in range(num_sides):
        angle = 2 * math.pi * i / num_sides
        factor = random.uniform(0.7, 1.3)
        radius = avg_radius * factor
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        points.append((x, y))
    return points


def enforce_separation(particles, min_distance):
    for i in range(len(particles)):
        for j in range(i + 1, len(particles)):
            p1, p2 = particles[i], particles[j]
            dx = p1.x - p2.x
            dy = p1.y - p2.y
            dist = math.hypot(dx, dy)
            if dist < min_distance and dist > 0:
                # Normalize the vector between particles
                nx, ny = dx / dist, dy / dist
                # Calculate overlap amount, dividing by 2 to push both particles equally
                overlap = (min_distance - dist) / 2
                # Adjust positions to separate them
                p1.x += nx * overlap
                p1.y += ny * overlap
                p2.x -= nx * overlap
                p2.y -= ny * overlap


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2D Pipe Flow Simulation")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 20)
    instr_font = pygame.font.SysFont("Arial", 16)

    # Center the pipes within the window
    pipe_x = (WIDTH - PIPE_WIDTH) // 2
    total_height = 2 * PIPE_HEIGHT + PIPE_SPACING
    pipe_y1 = (HEIGHT - total_height) // 2
    pipe_y2 = pipe_y1 + PIPE_HEIGHT + PIPE_SPACING

    # Create two horizontal pipes: one clear and one with an obstruction
    pipe1 = Pipe(pipe_x, pipe_y1, PIPE_WIDTH, PIPE_HEIGHT, obstructed=False)
    pipe2 = Pipe(pipe_x, pipe_y2, PIPE_WIDTH, PIPE_HEIGHT, obstructed=True)
    pipes = [pipe1, pipe2]

    particles = []
    global_max_velocity = 5.0  # Maximum velocity at the center

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEWHEEL:
                # Adjust the global max velocity for the entire flow
                global_max_velocity += event.y / 10.0
                if global_max_velocity < 0.1:
                    global_max_velocity = 0.1
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Reset the obstruction in the obstructed pipe
                    pipe2.obstruction = generate_obstruction(pipe2)

        screen.fill((255, 255, 255))

        # Draw an instruction banner at the top
        instructions = (
            "Scroll to adjust flow velocity | Press Space to change obstruction"
        )
        instr_surf = instr_font.render(instructions, True, (0, 0, 0))
        instr_rect = instr_surf.get_rect(center=(WIDTH / 2, 20))
        screen.blit(instr_surf, instr_rect)

        # Draw pipes with labels
        pipe1.draw(screen, "Clear Flow", font)
        pipe2.draw(screen, "Obstructed Flow", font)

        for pipe in pipes:
            for i in range(5):  # spawn 5 particles per pipe per frame
                spawn_y = random.randint(
                    int(pipe.y + PARTICLE_SIZE),
                    int(pipe.y + pipe.height - PARTICLE_SIZE),
                )
                particle = Particle(pipe.x + PARTICLE_SIZE, spawn_y, 0, 0, pipe)
                # Initialize vx based on the parabolic profile at the spawn point
                center_y = pipe.y + pipe.height / 2
                norm = (spawn_y - center_y) / (pipe.height / 2)
                particle.vx = global_max_velocity * (1 - norm**2)
                particles.append(particle)

        # Enforce a minimum separation between particles
        min_distance = 7
        enforce_separation(particles, min_distance)

        # Update and draw particles; remove them once they exit the right edge
        for particle in particles[:]:
            particle.update(global_max_velocity)

            particle.draw(screen, global_max_velocity)
            if particle.x > particle.pipe.x + particle.pipe.width - PARTICLE_SIZE:
                particles.remove(particle)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
