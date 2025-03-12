import pymunk
import pymunk.pygame_util
import pygame

# Global variables
# Sizes
WIDTH, HEIGHT = 800, 600
TARGET_SIZE = 20

# Platform
PLATFORM_WIDTH, PLATFORM_HEIGHT = 100, 5
PLATFORM_ELASTICITY = 0.0
PLATFORM_FRICTION = 1.0

# Stick
STICK_WIDTH, STICK_HEIGHT = 5, 100
STICK_RADIUS = STICK_WIDTH / 2
STICK_MASS = 1
STICK_ELASTICITY = 0.0
STICK_FRICTION = 1.0

# Colors
BACKGROUND_COLOR = (100, 100, 100, 255)
PLATFORM_COLOR = (200, 0, 0, 255)
STICK_COLOR = (0, 200, 200, 255)
TARGET_AREA_COLOR = (0, 0, 200, 255)

# Space
FPS = 60
GRAVITY = 0, 981
DAMPING = 0.9
SUBSTEPS = 10

# Main simulation class
class StickBalanceGame:
    def __init__(self):
        self.space = pymunk.Space()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.space.gravity = GRAVITY
        self.space.damping = DAMPING
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        self.clock = pygame.time.Clock()
        self.grabbed = False
        self.grab_position = None
        self.add_objects()   
        
    def add_objects(self):
        """Add all the required objects to the simulation."""
        # Controllable platform
        self.platform_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.platform_body.position = WIDTH / 2, HEIGHT * 2 / 3
        self.platform_shape = pymunk.Segment(self.platform_body, (-PLATFORM_WIDTH / 2, 0), (PLATFORM_WIDTH / 2, 0), PLATFORM_HEIGHT)      
        self.platform_shape.color = PLATFORM_COLOR
        self.platform_stop_1 = pymunk.Segment(self.platform_body, (-STICK_WIDTH * 2, 0), ( -STICK_WIDTH * 2, -STICK_WIDTH * 3), PLATFORM_HEIGHT)
        self.platform_stop_1.color = PLATFORM_COLOR
        self.platform_stop_2 = pymunk.Segment(self.platform_body, (STICK_WIDTH * 2, 0), (STICK_WIDTH * 2, -STICK_WIDTH * 3), PLATFORM_HEIGHT)
        self.platform_stop_2.color = PLATFORM_COLOR
        self.space.add(self.platform_body, self.platform_shape, self.platform_stop_1, self.platform_stop_2)
        # Balancing stick
        moment = pymunk.moment_for_box(STICK_MASS, (STICK_WIDTH, STICK_HEIGHT))
        self.stick_body = pymunk.Body(STICK_MASS, moment) 
        self.stick_shape = pymunk.Poly.create_box(self.stick_body, size=(STICK_WIDTH, STICK_HEIGHT), radius = STICK_RADIUS)
        self.stick_body.position = WIDTH / 2, (HEIGHT  * (2 / 3)) - STICK_HEIGHT / 2   
        self.stick_shape.elasticity = STICK_ELASTICITY
        self.stick_shape.friction = STICK_FRICTION
        self.stick_shape.color = STICK_COLOR
        self.space.add(self.stick_body, self.stick_shape)
        # Target 1
        self.target1_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.target1_shape = pymunk.Circle(self.target1_body, TARGET_SIZE)
        self.target1_body.position = 0 + TARGET_SIZE, TARGET_SIZE
        self.space.add(self.target1_body, self.target1_shape)
        # Target 2
        self.target2_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.target2_shape = pymunk.Circle(self.target2_body, TARGET_SIZE)
        self.target2_body.position = WIDTH - TARGET_SIZE, TARGET_SIZE
        self.space.add(self.target2_body, self.target2_shape)
        

    def draw_objects(self):
        self.screen.fill(BACKGROUND_COLOR)
        self.space.debug_draw(self.draw_options)
        pygame.draw.circle(self.screen, (0, 255, 0), self.target1_body.position, TARGET_SIZE)
        pygame.draw.circle(self.screen, (0, 255, 0), self.target2_body.position, TARGET_SIZE)

    def handle_events(self):
        """Handle all Pygame events/input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
                elif event.key == pygame.K_q:
                    return False
        mouse_pos = pygame.mouse.get_pos()
        if self.grabbed:
            self.platform_body.position = (mouse_pos[0] + self.grab_position[0], mouse_pos[1] + self.grab_position[1])
        elif self.platform_shape.point_query(mouse_pos).distance < 0:
            self.grabbed = True
            # When the platform is grabbed, set its position relative to where the mouse first contacts it
            # This prevents the platform center from snapping to the mouse and throwing the stick
            self.grab_position = (self.platform_body.position[0] - mouse_pos[0], self.platform_body.position[1] - mouse_pos[1])
        return None

    def run_simulation(self):
        while True:
            result = self.handle_events()
            if result is not None:
                return result
            dt = 1 / (FPS * SUBSTEPS)  # Smaller time step
            for _ in range(SUBSTEPS):  
                self.space.step(dt) 
            self.draw_objects()
            pygame.display.flip()
            self.clock.tick(FPS)

def main():
    pygame.init()
        
    # Dispatch simulation loop
    reset = True
    while reset:
        game = StickBalanceGame()
        reset = game.run_simulation()    
    
    pygame.quit()

if __name__ == "__main__":
    main()