import pymunk
import pygame
import math
import random

# Window size
WIDTH, HEIGHT = 800, 600

# Chamber dimensions
CHAMBER_WIDTH, CHAMBER_HEIGHT = 400, 400

# Piston dimensions (match chamber height so there’s no gap)
PISTON_WIDTH = 50
PISTON_HEIGHT = CHAMBER_HEIGHT

# Particle properties
PARTICLE_SIZE = 5
PARTICLE_COUNT = 100

# Gas law parameters
GAS_CONSTANT = 0.1
TEMPERATURE = 100
INITIAL_VOLUME = CHAMBER_WIDTH * CHAMBER_HEIGHT

# Colors
SKY_BLUE = (135, 206, 235)
IRON_GREY = (105, 105, 105)
BLACK = (0, 0, 0)


class Particle:
    def __init__(self, space, x, y, vx=0, vy=0):
        self.body = pymunk.Body(mass=1, moment=10)
        self.body.position = (x, y)
        self.body.velocity = (vx, vy)
        # Use a circle with full elasticity and zero friction so particles bounce well.
        self.shape = pymunk.Circle(self.body, PARTICLE_SIZE)
        self.shape.elasticity = 1.0
        self.shape.friction = 0.0
        space.add(self.body, self.shape)
        # Store recent positions for trail drawing.
        self.trail = []

    def update_trail(self):
        self.trail.append(self.body.position)
        if len(self.trail) > 10:
            self.trail.pop(0)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Piston Gas Simulation")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 24)

    # Create a separate surface for trails with per-pixel alpha.
    trail_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # Create the pymunk space.
    space = pymunk.Space()
    space.gravity = (0, 0)

    # Create chamber boundaries (left, top, bottom) in iron grey.
    wall_bottom = pymunk.Segment(space.static_body, (0, 0), (CHAMBER_WIDTH, 0), 1)
    wall_bottom.friction = 0.0
    wall_bottom.elasticity = 1.0
    wall_top = pymunk.Segment(
        space.static_body, (0, CHAMBER_HEIGHT), (CHAMBER_WIDTH, CHAMBER_HEIGHT), 1
    )
    wall_top.friction = 0.0
    wall_top.elasticity = 1.0
    wall_left = pymunk.Segment(space.static_body, (0, 0), (0, CHAMBER_HEIGHT), 1)
    wall_left.friction = 0.0
    wall_left.elasticity = 1.0
    for w in (wall_bottom, wall_top, wall_left):
        space.add(w)

    # Create a kinematic piston so it acts as a solid, non-movable barrier.
    piston_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
    # Start fully to the right: left edge at CHAMBER_WIDTH (so center = CHAMBER_WIDTH + PISTON_WIDTH/2)
    piston_body.position = (CHAMBER_WIDTH + PISTON_WIDTH / 2, CHAMBER_HEIGHT / 2)
    piston_shape = pymunk.Poly.create_box(piston_body, (PISTON_WIDTH, PISTON_HEIGHT))
    piston_shape.friction = 0.0
    piston_shape.elasticity = 1.0
    space.add(piston_body, piston_shape)

    # Create particles inside the chamber.
    particles = []
    for _ in range(PARTICLE_COUNT):
        x = random.uniform(50, CHAMBER_WIDTH - 50)
        y = random.uniform(50, CHAMBER_HEIGHT - 50)
        vx = random.uniform(-50, 50)
        vy = random.uniform(-50, 50)
        particles.append(Particle(space, x, y, vx, vy))

    # Piston movement: track the piston’s LEFT edge.
    # It oscillates between piston_min_edge (when the piston is 3/4 in)
    # and piston_max_edge (when the piston is fully outside the chamber).
    piston_speed = 50.0
    piston_min_edge = (
        0.25 * CHAMBER_WIDTH
    )  # When left edge is at 100 px (for a 400 px chamber).
    piston_max_edge = CHAMBER_WIDTH  # When left edge is at 400 px.
    piston_left_edge = piston_max_edge
    piston_direction = -1  # Start moving left.

    # Physics substeps to help with collision accuracy.
    SUBSTEPS = 5
    dt = 1 / 60

    paused = True
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused

        if not paused:
            # Update piston position.
            piston_left_edge += piston_direction * piston_speed * dt
            if piston_left_edge < piston_min_edge:
                piston_left_edge = piston_min_edge
                piston_direction = 1
            elif piston_left_edge > piston_max_edge:
                piston_left_edge = piston_max_edge
                piston_direction = -1
            piston_body.position = (
                piston_left_edge + PISTON_WIDTH / 2,
                CHAMBER_HEIGHT / 2,
            )

            # Step the physics multiple times per frame.
            sub_dt = dt / SUBSTEPS
            for _ in range(SUBSTEPS):
                space.step(sub_dt)

            # Calculate pressure and scale particle velocities (simulate PV=nRT).
            current_volume = max(piston_left_edge, 1) * CHAMBER_HEIGHT
            pressure = GAS_CONSTANT * PARTICLE_COUNT * TEMPERATURE / current_volume
            scaling_factor = math.sqrt(INITIAL_VOLUME / current_volume)
            scaling_factor = min(scaling_factor, 3.0)
            for p in particles:
                vx, vy = p.body.velocity
                p.body.velocity = (vx * scaling_factor, vy * scaling_factor)
            # Clamp maximum speed.
            max_speed = 500
            for p in particles:
                vx, vy = p.body.velocity
                speed = math.hypot(vx, vy)
                if speed > max_speed:
                    factor = max_speed / speed
                    p.body.velocity = (vx * factor, vy * factor)

        # DRAWING

        # Fill the background with sky blue.
        screen.fill(SKY_BLUE)

        # Draw the chamber boundaries in iron grey.
        pygame.draw.line(screen, IRON_GREY, (0, 0), (CHAMBER_WIDTH, 0), 2)
        pygame.draw.line(
            screen, IRON_GREY, (0, CHAMBER_HEIGHT), (CHAMBER_WIDTH, CHAMBER_HEIGHT), 2
        )
        pygame.draw.line(screen, IRON_GREY, (0, 0), (0, CHAMBER_HEIGHT), 2)

        # Draw the piston in iron grey.
        piston_rect = pygame.Rect(
            piston_body.position.x - PISTON_WIDTH / 2,
            piston_body.position.y - PISTON_HEIGHT / 2,
            PISTON_WIDTH,
            PISTON_HEIGHT,
        )
        pygame.draw.rect(screen, IRON_GREY, piston_rect)

        # Draw a hydraulic arm attached to the back (right side) of the piston.
        # The arm is a narrow rectangle extending from the piston.
        arm_width = 10
        arm_length = 40
        arm_rect = pygame.Rect(
            piston_rect.right,  # attach at the right edge
            piston_rect.centery - arm_width / 2,
            arm_length,
            arm_width,
        )
        pygame.draw.rect(screen, IRON_GREY, arm_rect)

        # Clear the trail surface.
        trail_surface.fill((0, 0, 0, 0))
        # Draw particle trails as thin lines that fade to transparent.
        for p in particles:
            p.update_trail()
            if len(p.trail) > 1:
                # Draw line segments between consecutive trail points.
                for i in range(len(p.trail) - 1):
                    start = p.trail[i]
                    end = p.trail[i + 1]
                    # Older segments get lower alpha.
                    alpha = int(255 * (i + 1) / len(p.trail))
                    color = (0, 0, 0, alpha)
                    start_int = (int(start[0]), int(start[1]))
                    end_int = (int(end[0]), int(end[1]))
                    pygame.draw.line(trail_surface, color, start_int, end_int, 2)
        # Blit the trail surface (with alpha) onto the main screen.
        screen.blit(trail_surface, (0, 0))

        # Draw particles as black circles.
        for p in particles:
            pos = (int(p.body.position.x), int(p.body.position.y))
            pygame.draw.circle(screen, BLACK, pos, PARTICLE_SIZE)

        # Draw UI text in black.
        msg_surface = font.render("Press SPACE to Start/Pause", True, BLACK)
        screen.blit(msg_surface, (10, CHAMBER_HEIGHT + 5))
        if not paused:
            current_volume = max(piston_left_edge, 1) * CHAMBER_HEIGHT
            pressure = GAS_CONSTANT * PARTICLE_COUNT * TEMPERATURE / current_volume
            p_surf = font.render(f"Pressure: {pressure:.4f}", True, BLACK)
            screen.blit(p_surf, (10, CHAMBER_HEIGHT + 35))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
