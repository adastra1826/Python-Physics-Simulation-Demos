"""
Pool Table Physics Simulation.

This simulation models the physics of billiards/pool on a standard table.
It demonstrates principles of elastic collisions, conservation of momentum,
friction, and angular momentum as balls interact with each other and the table.
Users can control the cue ball with varying force and direction, experiencing
how initial conditions affect the entire system's evolution. The simulation
accurately models the characteristic behavior of pool balls, including how they
slow down due to rolling and sliding friction, and how they bounce off cushions.
"""

import pygame
import math
import random

# Window dimensions
WIDTH, HEIGHT = 1200, 720

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 128, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
BROWN = (139, 69, 19)

# Ball properties
BALL_RADIUS = 20
CUE_BALL_COLOR = WHITE
OBJECT_BALL_COLOR = YELLOW

# Physics constants
RESTITUTION = 0.985
CUSHION_FRICTION = 0.8

# Pocket locations
POCKETS = [
    [61, 61],
    [61, 339.5],
    [61, 658],
    [579.75, 61],
    [579.75, 658],
    [1138.5, 61],
    [1138.5, 339.5],
    [1138.5, 658]
]

RAIL_WIDTH = 40

# Game status flag
GAME_OVER = False

class Ball:
    def __init__(self, x, y, color):
        """
        Initializes a Ball object.

        Args:
            x (float): Initial x-coordinate.
            y (float): Initial y-coordinate.
            color (tuple): RGB color of the ball.
        """
        self.x = x
        self.y = y
        self.color = color
        self.velocity_x = 0
        self.velocity_y = 0
        self.potted = False

    def move(self):
        """
        Updates the ball's position based on its current velocity.
        Applies friction to gradually reduce the velocity.
        """
        self.x += self.velocity_x
        self.y += self.velocity_y

        self.velocity_x *= RESTITUTION
        self.velocity_y *= RESTITUTION

    def collide_with_ball(self, other_ball):
        """
        Handles elastic collision response between this ball and another ball.
        Uses vector projection to compute normal and tangential velocity components,
        then swaps normal components to simulate elastic collision.

        Physics:
            - Resolve velocities into normal and tangent directions.
            - Swap normal components for elastic collision.
            - Recombine to get resultant velocities.
            - Apply overlap correction to prevent balls sticking to each other.
        """
        dx = self.x - other_ball.x
        dy = self.y - other_ball.y
        distance = math.sqrt(dx**2 + dy**2)

        if distance < 2 * BALL_RADIUS:
            normal_x = dx / distance
            normal_y = dy / distance
            tangent_x = -normal_y
            tangent_y = normal_x

            v1n = self.velocity_x * normal_x + self.velocity_y * normal_y
            v1t = self.velocity_x * tangent_x + self.velocity_y * tangent_y

            v2n = other_ball.velocity_x * normal_x + other_ball.velocity_y * normal_y
            v2t = other_ball.velocity_x * tangent_x + other_ball.velocity_y * tangent_y

            v1n, v2n = v2n, v1n

            self.velocity_x = v1n * normal_x + v1t * tangent_x
            self.velocity_y = v1n * normal_y + v1t * tangent_y

            other_ball.velocity_x = v2n * normal_x + v2t * tangent_x
            other_ball.velocity_y = v2n * normal_y + v2t * tangent_y

            overlap = 2 * BALL_RADIUS - distance
            correction_x = normal_x * overlap / 2
            correction_y = normal_y * overlap / 2

            self.x += correction_x
            self.y += correction_y
            other_ball.x -= correction_x
            other_ball.y -= correction_y


    def collide_with_cushion(self):
        """
        Detects and responds to collisions with table boundaries.
        Reverses and reduces velocity using cushion friction.

        Physics:
            - Invert velocity on collision.
            - Clamp position to inside the play area.
        """
        if self.x - BALL_RADIUS < 40 or self.x + BALL_RADIUS > WIDTH - 40:
            self.velocity_x = -self.velocity_x * CUSHION_FRICTION
        if self.y - BALL_RADIUS < 40 or self.y + BALL_RADIUS > HEIGHT - 40:
            self.velocity_y = -self.velocity_y * CUSHION_FRICTION

        if self.x - BALL_RADIUS < 40:
            self.x = BALL_RADIUS + 40
        elif self.x + BALL_RADIUS > WIDTH - 40:
            self.x = WIDTH - BALL_RADIUS - 40
        if self.y - BALL_RADIUS < 40:
            self.y = BALL_RADIUS + 40
        elif self.y + BALL_RADIUS > HEIGHT - 40:
            self.y = HEIGHT - BALL_RADIUS - 40


    def fall_in_pocket(self):
        """
        Checks whether the ball has entered a pocket based on distance.

        If a yellow object ball falls in, it is marked as potted.
        If the cue ball falls in, the game is marked over.
        """
        for pocket_location in POCKETS:
            if math.hypot(self.x - pocket_location[0], self.y - pocket_location[1]) < 35:
                if self.color == YELLOW:
                    self.potted = True
                elif self.color == CUE_BALL_COLOR:
                    global GAME_OVER
                    GAME_OVER = True


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pool Table Game")
    clock = pygame.time.Clock()

    # Background is a solid color
    background = pygame.Surface((WIDTH, HEIGHT))
    background.fill(GREEN)

    # Draw pockets
    for pocket in POCKETS:
        pygame.draw.circle(background, BLACK, pocket, 35)

    # Draw rails
    pygame.draw.rect(background, BROWN, (0, 0, WIDTH, RAIL_WIDTH))
    pygame.draw.rect(background, BROWN, (0, HEIGHT - RAIL_WIDTH, WIDTH, RAIL_WIDTH))
    pygame.draw.rect(background, BROWN, (0, 0, RAIL_WIDTH, HEIGHT))
    pygame.draw.rect(background, BROWN, (WIDTH - RAIL_WIDTH, 0, RAIL_WIDTH, HEIGHT))


    object_ball_count = 5
    potted_ball_count = 0
    cue_ball = Ball(WIDTH // 2, HEIGHT // 2, CUE_BALL_COLOR)
    object_balls = [Ball(random.randint(BALL_RADIUS, WIDTH - BALL_RADIUS), random.randint(BALL_RADIUS, HEIGHT - BALL_RADIUS), OBJECT_BALL_COLOR) for _ in range(object_ball_count)]
    
    # Track which balls have been counted as potted
    counted_potted_balls = [False] * object_ball_count

    aiming = False # True when the player is aiming
    aim_start_pos = None # Starting location for hit drag

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                aiming = True
                aim_start_pos = event.pos
            elif event.type == pygame.MOUSEBUTTONUP:
                aiming = False
                if aim_start_pos:
                    # Impart initial velocity to cue ball when hit
                    aim_end_pos = event.pos
                    cue_ball.velocity_x = (aim_start_pos[0] - aim_end_pos[0]) / 10
                    cue_ball.velocity_y = (aim_start_pos[1] - aim_end_pos[1]) / 10
                    aim_start_pos = None

        if GAME_OVER == False and potted_ball_count < object_ball_count:
            screen.blit(background, (0, 0))

            # Update cue ball position, checking for collisions
            cue_ball.move()
            cue_ball.collide_with_cushion()
            cue_ball.fall_in_pocket()

            # Update object balls if the game is ongoing, checking for collisions
            for i, object_ball in enumerate(object_balls):
                if object_ball.potted == False:
                    object_ball.move()
                    object_ball.collide_with_cushion()
                    object_ball.fall_in_pocket()
                    cue_ball.collide_with_ball(object_ball)
                    for other_object_ball in object_balls:
                        if object_ball != other_object_ball:
                            object_ball.collide_with_ball(other_object_ball)
                else:
                    # Move potted balls off screen to hide them
                    object_ball.x = object_ball.y = -100
                    # Only increment the count once per ball
                    if not counted_potted_balls[i]:
                        potted_ball_count += 1
                        counted_potted_balls[i] = True


        else:
            font = pygame.font.Font(None, 50)
            game_over_text = font.render("GAME OVER", True, RED)
            screen.blit(game_over_text,
                        (WIDTH / 2 - game_over_text.get_width() / 2, HEIGHT / 2 - game_over_text.get_height() / 2)
                        )

        # Draw cue and yellow balls
        pygame.draw.circle(screen, cue_ball.color, (int(cue_ball.x), int(cue_ball.y)), BALL_RADIUS)
        for object_ball in object_balls:
            pygame.draw.circle(screen, object_ball.color, (int(object_ball.x), int(object_ball.y)), BALL_RADIUS)

        # Draw aiming line
        if aiming and aim_start_pos and not GAME_OVER:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            delta_x = aim_start_pos[0] - mouse_x
            delta_y = aim_start_pos[1] - mouse_y
            end_pos = (aim_start_pos[0] + delta_x, aim_start_pos[1] + delta_y)
            pygame.draw.line(screen, RED, aim_start_pos, end_pos, 2)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()