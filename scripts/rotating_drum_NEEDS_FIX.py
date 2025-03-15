import pygame
import random
import math

# Window dimensions
WIDTH, HEIGHT = 800, 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Ball properties
BALL_RADIUS = 10
GRAVITY = 0.1

# Maze properties
NUM_WALLS = 10
GAP_ANGLE = math.pi / 6  # Size of gaps in radians


class Ball:
    """Class representing a bouncing ball."""
    def __init__(self):
        self.x = WIDTH // 2 + random.randint(-100, 100)
        self.y = HEIGHT // 2 + random.randint(-100, 100)
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

    def update(self):
        """Update ball position with gravity."""
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy

        # Simple boundary collision
        if self.x - BALL_RADIUS < 0 or self.x + BALL_RADIUS > WIDTH:
            self.vx *= -1
        if self.y - BALL_RADIUS < 0 or self.y + BALL_RADIUS > HEIGHT:
            self.vy *= -0.9  # simulate energy loss on collision

    def draw(self, screen):
        """Draw ball on screen."""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), BALL_RADIUS)


class Maze:
    """Class representing the rotating maze."""
    def __init__(self):
        self.angle = 0
        self.radius = WIDTH // 3
        self.wall_width = 8
        self.center_x, self.center_y = WIDTH // 2, HEIGHT // 2

    def update(self):
        """Rotate maze by incrementing angle."""
        self.angle += 0.01

    def draw(self, screen):
        """Draw rotating walls of the maze."""
        for i in range(NUM_WALLS):
            start_angle = i * (2 * math.pi / NUM_WALLS) + self.angle
            end_angle = start_angle + (2 * math.pi / NUM_WALLS) - GAP_ANGLE

            # Calculate wall endpoints
            x1 = self.center_x + self.radius * math.cos(start_angle)
            y1 = self.center_y + self.radius * math.sin(start_angle)
            x2 = self.center_x + self.radius * math.cos(end_angle)
            y2 = self.center_y + self.radius * math.sin(end_angle)

            pygame.draw.line(screen, WHITE, (x1, y1), (x2, y2), self.wall_width)

    def check_collision(self, ball):
        """Check if a ball collides with any wall."""
        dx, dy = ball.x - self.center_x, ball.y - self.center_y
        distance_to_center = math.sqrt(dx**2 + dy**2)

        if distance_to_center > self.radius + BALL_RADIUS:
            return  # Ball is too far from the center to collide

        # Iterate through each wall segment
        for i in range(NUM_WALLS):
            start_angle = i * (2 * math.pi / NUM_WALLS) + self.angle
            end_angle = start_angle + (2 * math.pi / NUM_WALLS) - GAP_ANGLE

            # Normalize angles
            start_angle %= (2 * math.pi)
            end_angle %= (2 * math.pi)

            ball_angle = math.atan2(dy, dx) % (2 * math.pi)

            # Check if the ball is within the wall's angular span
            if start_angle <= ball_angle <= end_angle:
                # Calculate wall endpoints
                x1 = self.center_x + self.radius * math.cos(start_angle)
                y1 = self.center_y + self.radius * math.sin(start_angle)
                x2 = self.center_x + self.radius * math.cos(end_angle)
                y2 = self.center_y + self.radius * math.sin(end_angle)

                # Calculate distance from ball to wall segment
                distance = abs((x2 - x1) * (y1 - ball.y) - (x1 - ball.x) * (y2 - y1)) / math.sqrt(
                    (x2 - x1)**2 + (y2 - y1)**2)

                if distance <= BALL_RADIUS + self.wall_width / 2:
                    # Collision detected; reflect ball's velocity
                    normal_angle = (start_angle + end_angle) / 2
                    normal_x = math.cos(normal_angle)
                    normal_y = math.sin(normal_angle)

                    # Reflect velocity vector along wall normal
                    dot_product = ball.vx * normal_x + ball.vy * normal_y
                    ball.vx -= 2 * dot_product * normal_x
                    ball.vy -= 2 * dot_product * normal_y
                    return


def draw_gradient_background(screen):
    """Draw a gradient background for visual appeal."""
    for i in range(HEIGHT):
        color_value = int(255 * (i / HEIGHT))
        pygame.draw.line(screen, (color_value // 2, color_value // 3, color_value), (0, i), (WIDTH, i))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    balls = [Ball() for _ in range(10)]
    maze = Maze()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BLACK)
        draw_gradient_background(screen)

        maze.update()
        maze.draw(screen)

        for ball in balls:
            ball.update()
            maze.check_collision(ball)
            ball.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()