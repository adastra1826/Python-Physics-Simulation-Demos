import pymunk
import pymunk.pygame_util
import pygame
import random
import math

# Global variables
# Screen size
WIDTH, HEIGHT = 800, 600

# Ratio sizes
TABLE_WIDTH_RATIO, TABLE_LENGTH_RATIO = 1, 2
BALL_RADIUS_RATIO = 1 / 30
KITCHEN_RATIO = 1 / 4
FOOT_SPOT_RATIO = 3 / 4

# Scale factor
SCALE_FACTOR = int((WIDTH - 50) / TABLE_LENGTH_RATIO)

# Absolute sizes
TABLE_WIDTH = TABLE_WIDTH_RATIO * SCALE_FACTOR
TABLE_LENGTH = TABLE_LENGTH_RATIO * SCALE_FACTOR
HALF_TABLE_WIDTH = int(TABLE_WIDTH / 2)
HALF_TABLE_LENGTH = int(TABLE_LENGTH / 2)
BALL_RADIUS = int(BALL_RADIUS_RATIO * SCALE_FACTOR)
KITCHEN = int(KITCHEN_RATIO * SCALE_FACTOR)
FOOT_SPOT = int(FOOT_SPOT_RATIO * SCALE_FACTOR)
POCKET_RADIUS = int(BALL_RADIUS * 1.5)

# Elasticity/friction/damping values
SPACE_DAMPING = 0.56
BALL_MASS = 1
BALL_FRICTION = 0.3
BALL_ELASTICITY = .95
WALL_FRICTION = 0.75
WALL_ELASTICITY = 0.8

# Colors
BACKGROUND_COLOR = (21, 88, 67, 1)
CUE_BALL_COLOR = (245, 245, 245, 255)
BALL_COLOR = (200, 30, 30, 255)
POCKET_COLOR = (10, 10, 10, 255)

# FPS
FPS = 60

# Shot power
MIN_SHOT_POWER = 1000
MAX_SHOT_POWER = 2000

class PoolSimulation:
    """Class which creates and runs the simulation."""
    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = 0, 0
        self.space.damping = SPACE_DAMPING
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        self.moment = pymunk.moment_for_circle(BALL_MASS, 0, BALL_RADIUS)
        self.cue_ball_body = None
        self.top_ball_body = None
        self.bottom_ball_body = None
        self.table_body = None
        self.balls = []
        self.pockets = []
        self.balls_in_pocket = 0
        
        # Set up collision handler for pockets
        self.collision_handler = self.space.add_collision_handler(1, 2)
        self.collision_handler.begin = self.ball_in_pocket
        
    def ball_in_pocket(self, arbiter, space, data):
        ball_shape = arbiter.shapes[0]
        self.space.remove(ball_shape, ball_shape.body)
        self.balls.remove(ball_shape.body)
        self.balls_in_pocket += 1
        return False

    def create_table(self):        
        """Create the table body which the edges will be attatched to."""
        self.table_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        
        # The position is set relative to the center
        self.table_body.position = (WIDTH / 2, HEIGHT - (TABLE_WIDTH / 2) - 50)
        self.space.add(self.table_body)
        
        # Create pockets - positions are relative to table corners
        pocket_positions = [
            (-HALF_TABLE_LENGTH, -HALF_TABLE_WIDTH),  # bottom left
            (0, -HALF_TABLE_WIDTH),                  # bottom middle
            (HALF_TABLE_LENGTH, -HALF_TABLE_WIDTH),   # bottom right
            (HALF_TABLE_LENGTH, HALF_TABLE_WIDTH),    # top right
            (0, HALF_TABLE_WIDTH),                   # top middle
            (-HALF_TABLE_LENGTH, HALF_TABLE_WIDTH)    # top left
        ]
        
        for pos in pocket_positions:
            pocket_body = pymunk.Body(body_type=pymunk.Body.STATIC)
            pocket_body.position = self.table_body.local_to_world(pos)
            pocket_shape = pymunk.Circle(pocket_body, POCKET_RADIUS)
            pocket_shape.collision_type = 1
            pocket_shape.sensor = True
            self.space.add(pocket_body, pocket_shape)
            self.pockets.append((pocket_body, pocket_shape))
        
        # Since the position is relative to center, define segment edges related to the center
        edges = [
            ((-HALF_TABLE_LENGTH, -HALF_TABLE_WIDTH), (-POCKET_RADIUS, -HALF_TABLE_WIDTH)),
            ((POCKET_RADIUS, -HALF_TABLE_WIDTH), (HALF_TABLE_LENGTH - POCKET_RADIUS, -HALF_TABLE_WIDTH)),
            ((HALF_TABLE_LENGTH, -HALF_TABLE_WIDTH), (HALF_TABLE_LENGTH, HALF_TABLE_WIDTH - POCKET_RADIUS)),
            ((HALF_TABLE_LENGTH, -HALF_TABLE_WIDTH + POCKET_RADIUS), (HALF_TABLE_LENGTH, HALF_TABLE_WIDTH - POCKET_RADIUS)),
            ((HALF_TABLE_LENGTH, HALF_TABLE_WIDTH), (POCKET_RADIUS, HALF_TABLE_WIDTH)),
            ((-POCKET_RADIUS, HALF_TABLE_WIDTH), (-HALF_TABLE_LENGTH + POCKET_RADIUS, HALF_TABLE_WIDTH)),
            ((-HALF_TABLE_LENGTH, HALF_TABLE_WIDTH), (-HALF_TABLE_LENGTH, -HALF_TABLE_WIDTH + POCKET_RADIUS)),
            ((-HALF_TABLE_LENGTH, HALF_TABLE_WIDTH - POCKET_RADIUS), (-HALF_TABLE_LENGTH, -HALF_TABLE_WIDTH + POCKET_RADIUS))
        ]
        
        # Attatch all segments
        for a, b in edges:
            segment = pymunk.Segment(self.table_body, a, b, 5)
            segment.friction = WALL_FRICTION
            segment.elasticity = WALL_ELASTICITY
            self.space.add(segment)

    # Create an instance of a pymunk pool ball. 
    # Since there are 15, the repetitive work is done in this function
    def create_ball(self):
        """Create and return a pymunk ball instance."""
        ball_body = pymunk.Body(BALL_MASS, self.moment)
        ball_shape = pymunk.Circle(ball_body, BALL_RADIUS)
        ball_shape.elasticity = BALL_ELASTICITY
        ball_shape.friction = BALL_FRICTION
        ball_shape.collision_type = 2
        return ball_body, ball_shape

    # Adds all the balls to the simulation
    def add_balls(self):
        """Creates and adds all the balls to the simulation"""
        # Create and add the cue ball
        self.cue_ball_body, cue_ball_shape = self.create_ball()    
        cue_ball_shape.color = CUE_BALL_COLOR
        max_x = int(((TABLE_LENGTH) * KITCHEN_RATIO) - HALF_TABLE_LENGTH)
        self.cue_ball_body.position = (
            random.randint(-HALF_TABLE_LENGTH + BALL_RADIUS, max_x),
            random.randint(-HALF_TABLE_WIDTH + BALL_RADIUS, HALF_TABLE_WIDTH - BALL_RADIUS)
        )
        self.cue_ball_body.position = self.table_body.local_to_world(self.cue_ball_body.position)
        self.space.add(self.cue_ball_body, cue_ball_shape)
        self.balls.append(self.cue_ball_body)
        
        # Find the relative coordinates for each object ball in its racked position
        rack_coords = []
        next_row = [BALL_RADIUS * math.sqrt(3), -BALL_RADIUS]
        next_ball = BALL_RADIUS * 2
        for ball in range(5):
            curr_x = int(next_row[0] * ball)
            for j in range(ball + 1):
                curr_y = int((next_row[1] * ball) + (next_ball * j))
                rack_coords.append([curr_x, curr_y])
        
        # Normalize the position of the rack to the appropriate spot on the table        
        rack_position = (((TABLE_LENGTH) * FOOT_SPOT_RATIO) - HALF_TABLE_LENGTH, 0)
        rack_position = self.table_body.local_to_world(rack_position)
        
        # Create and place each ball in position such that they are racked
        for ball, coord in enumerate(rack_coords, start=1):
            x, y = coord[0] + rack_position[0], coord[1] + rack_position[1]
            ball_body, ball_shape = self.create_ball()
            ball_body.position = x, y
            ball_shape.color = BALL_COLOR
            self.space.add(ball_body, ball_shape)
            self.balls.append(ball_body)
            # Make special note of the first and last balls in the last row
            # to ensure the cue ball is always aimed between them
            if ball == 11:
                self.top_ball_body = ball_body
            elif ball == 15:
                self.bottom_ball_body = ball_body
            
    # Main simulation function
    def simulate(self):
        """Run the simulation."""
        self.create_table()
        self.add_balls()

        # Determine shot angle and power randomly
        # The shot always aims such that it will hit the racked balls
        x, y = self.cue_ball_body.position
        tx, ty = self.top_ball_body.position
        bx, by = self.bottom_ball_body.position
        top_range = math.atan2(ty - y, tx - x)
        bottom_range = math.atan2(by - y, bx - x)        
        aim_angle = random.uniform(top_range, bottom_range)        
        shot_power = random.uniform(MIN_SHOT_POWER, MAX_SHOT_POWER)
        # Apply the shot force
        self.cue_ball_body.apply_impulse_at_local_point((shot_power * math.cos(aim_angle), shot_power * math.sin(aim_angle)))

        # Main simulation loop
        paused = False
        while True:
            # Handle input events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        paused = not paused
                    elif event.key == pygame.K_q:
                        return False
                    elif event.key == pygame.K_r:
                        return True

            if not paused:
                self.space.step(1 / FPS)

            # Draw the screen
            self.screen.fill(BACKGROUND_COLOR)
            
            # Draw pockets manually (because they're sensors)
            for pocket_body, pocket_shape in self.pockets:
                pygame.draw.circle(
                    self.screen, 
                    POCKET_COLOR, 
                    (int(pocket_body.position.x), int(pocket_body.position.y)),
                    POCKET_RADIUS
                )
                
            self.space.debug_draw(self.draw_options)
            
            # Draw text info
            font = pygame.font.Font(None, 30)
            text = font.render(f"Angle: {format(math.degrees(aim_angle), '.2f')}, Power: {format(shot_power, '.2f')}", True, (0, 0, 0))
            self.screen.blit(text, (10, 10))
            
            # Draw ball counter
            ball_text = font.render(f"Balls in pockets: {self.balls_in_pocket}", True, (0, 0, 0))
            self.screen.blit(ball_text, (10, 40))
            
            pygame.display.flip()
            self.clock.tick(FPS)


# Main entry point of the program
def main():
    """Main function which handles creating and resetting the simulation."""
    pygame.init()
    # Easily handle resetting the simulation with a boolean return value from the simulation
    reset = True
    while reset:
        simulation = PoolSimulation()
        reset = simulation.simulate()
    pygame.quit()


# Run the simulation
if __name__ == "__main__":
    main()