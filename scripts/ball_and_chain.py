import pymunk
import pymunk.pygame_util
import pygame
import sys

# Global variables
WIDTH, HEIGHT = 800, 600
CHAIN_LINK_LENGTH = 20
CHAIN_LINK_RADIUS = 2
CHAIN_LINK_COLOR = (255, 255, 255)
BALL_RADIUS = 20
BALL_COLOR = (255, 0, 0)
GRAVITY = 1000

class BallAndChain:
    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = 0, GRAVITY
        self.chain = []
        self.ball = None
        self.draw_options = pymunk.pygame_util.DrawOptions(pygame.display.get_surface())
        self.paused = False
        self.grabbed = None

        pygame.init()
        pygame.display.set_caption("Ball and Chain")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.create_chain()
        self.create_ball()

    def create_chain(self):
        for i in range(10):
            x = WIDTH / 2
            y = HEIGHT / 2 - i * CHAIN_LINK_LENGTH
            body = pymunk.Body(1, 1666)
            body.position = x, y
            shape = pymunk.Segment(body, (0, CHAIN_LINK_LENGTH / 2), (0, -CHAIN_LINK_LENGTH / 2), CHAIN_LINK_RADIUS)
            shape.elasticity = 0.95
            shape.friction = 1
            self.space.add(body, shape)
            self.chain.append((body, shape))

        for i in range(len(self.chain) - 1):
            body1 = self.chain[i][0]
            body2 = self.chain[i + 1][0]
            joint = pymunk.PivotJoint(body1, body2, (0, -CHAIN_LINK_LENGTH / 2))
            self.space.add(joint)

    def create_ball(self):
        x = WIDTH / 2
        y = HEIGHT / 2 - len(self.chain) * CHAIN_LINK_LENGTH
        body = pymunk.Body(1, 1666)
        body.position = x, y
        shape = pymunk.Circle(body, BALL_RADIUS)
        shape.elasticity = 0.95
        shape.friction = 1
        self.space.add(body, shape)
        self.ball = (body, shape)

        joint = pymunk.PivotJoint(self.chain[-1][0], body, (0, -CHAIN_LINK_LENGTH / 2))
        self.space.add(joint)

    def draw(self):
        self.screen.fill((0, 0, 0))
        for _, shape in self.chain:
            pygame.draw.line(self.screen, CHAIN_LINK_COLOR, shape.a, shape.b, CHAIN_LINK_RADIUS * 2)
        pygame.draw.circle(self.screen, BALL_COLOR, (int(self.ball[0].position.x), int(self.ball[0].position.y)), BALL_RADIUS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    return False
                elif event.key == pygame.K_q:
                    sys.exit(0)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for body, shape in self.chain + [self.ball]:
                    if shape.point_query(event.pos).distance < 0:
                        self.grabbed = body
                        break
            elif event.type == pygame.MOUSEBUTTONUP:
                self.grabbed = None
            elif event.type == pygame.MOUSEMOTION and self.grabbed:
                self.grabbed.position = event.pos

        return True

    def update(self):
        if not self.paused:
            self.space.step(1 / 60)

    def run(self):
        while True:
            if not self.handle_events():
                return
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

def main():
    game = BallAndChain()
    game.run()

if __name__ == "__main__":
    main()