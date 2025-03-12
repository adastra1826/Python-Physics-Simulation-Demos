import pymunk
import pymunk.pygame_util
import pygame
import sys

# Global variables
WIDTH, HEIGHT = 800, 600
PLATFORM_WIDTH, PLATFORM_HEIGHT = 200, 20
STICK_WIDTH, STICK_HEIGHT = 10, 200
TARGET_SIZE = 20
FPS = 60

class StickBalanceGame:
    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = 0, 900
        self.platform_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.platform_shape = pymunk.Poly.create_box(self.platform_body, size=(PLATFORM_WIDTH, PLATFORM_HEIGHT))
        self.platform_shape.elasticity = 0.9
        self.space.add(self.platform_body, self.platform_shape)
        self.stick_body = pymunk.Body(mass=1, moment=100)
        self.stick_shape = pymunk.Poly.create_box(self.stick_body, size=(STICK_WIDTH, STICK_HEIGHT))
        self.stick_shape.elasticity = 0.9
        self.space.add(self.stick_body, self.stick_shape)
        self.target1_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.target1_shape = pymunk.Circle(self.target1_body, TARGET_SIZE)
        self.target1_body.position = WIDTH / 2 - TARGET_SIZE, HEIGHT - TARGET_SIZE
        self.space.add(self.target1_body, self.target1_shape)
        self.target2_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.target2_shape = pymunk.Circle(self.target2_body, TARGET_SIZE)
        self.target2_body.position = WIDTH / 2 + TARGET_SIZE, HEIGHT - TARGET_SIZE
        self.space.add(self.target2_body, self.target2_shape)
        self.platform_body.position = WIDTH / 2, HEIGHT / 2
        self.stick_body.position = WIDTH / 2, HEIGHT / 2 - STICK_HEIGHT / 2

    def draw_objects(self, screen):
        screen.fill((255, 255, 255))
        pygame.draw.polygon(screen, (0, 0, 255), self.platform_shape.get_vertices())
        pygame.draw.polygon(screen, (255, 0, 0), self.stick_shape.get_vertices())
        pygame.draw.circle(screen, (0, 255, 0), self.target1_body.position, TARGET_SIZE)
        pygame.draw.circle(screen, (0, 255, 0), self.target2_body.position, TARGET_SIZE)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
        mouse_pos = pygame.mouse.get_pos()
        if self.platform_shape.point_query(mouse_pos).distance < 0:
            self.platform_body.position = mouse_pos
        return None

    def run_simulation(self):
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        clock = pygame.time.Clock()
        running = True
        while running:
            self.space.step(1 / FPS)
            self.draw_objects(screen)
            pygame.display.flip()
            result = self.handle_events()
            if result is not None:
                running = not result
            clock.tick(FPS)
        pygame.quit()
        return not running

def main():
    game = StickBalanceGame()
    return game.run_simulation()

if __name__ == "__main__":
    if main():
        main()