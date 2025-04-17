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
POCKET_RADIUS = BALL_RADIUS * 1.5

# Elasticity/friction/damping values
SPACE_DAMPING = 0.56
BALL_MASS = 1
BALL_FRICTION = 0.3
BALL_ELASTICITY = .95
WALL_FRICTION = 0.75
WALL_ELASTICITY = 0.8

# Collision types
BALL_COLLISION_TYPE = 1
WALL_COLLISION_TYPE = 2
POCKET_COLLISION_TYPE = 3

# Colors
BACKGROUND_COLOR = (21, 88, 67, 1)
CUE_BALL_COLOR = (245, 245, 245, 255)
BALL_COLOR = (200, 30, 30, 255)
POCKET_COLOR = (0, 0, 0, 255)

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
        # Add pocketed balls counter and list of pockets
        self.pocketed_balls = 0

    def create_table(self):        
        """Create the table body which the edges and pockets will be attached to."""
        self.table_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.table_body.position = (WIDTH / 2, HEIGHT - (TABLE_WIDTH / 2) - 50)
        self.space.add(self.table_body)
        
        # Add pockets at corners and middle of long edges
        pocket_positions = [
            (-HALF_TABLE_LENGTH, -HALF_TABLE_WIDTH),  # Top-left
            (0, -HALF_TABLE_WIDTH),                   # Top-middle
            (HALF_TABLE_LENGTH, -HALF_TABLE_WIDTH),   # Top-right
            (HALF_TABLE_LENGTH, HALF_TABLE_WIDTH),    # Bottom-right
            (0, HALF_TABLE_WIDTH),                    # Bottom-middle
            (-HALF_TABLE_LENGTH, HALF_TABLE_WIDTH)    # Bottom-left
        ]
        for pos in pocket_positions:
            pocket_body = pymunk.Body(body_type=pymunk.Body.STATIC)
            pocket_body.position = self.table_body.local_to_world(pos)
            pocket_shape = pymunk.Circle(pocket_body, POCKET_RADIUS)
            pocket_shape.sensor = True  # Sensor shape to detect collisions without physics response
            pocket_shape.color = POCKET_COLOR
            pocket_shape.collision_type = POCKET_COLLISION_TYPE
            self.space.add(pocket_body, pocket_shape)

        # Create the edges of the table, based on connection each pocket to the next
        # Create edges between pockets, leaving gaps for pocket entrances
        edges = []
        for i in range(len(pocket_positions)):
            current = pocket_positions[i]
            next_pocket = pocket_positions[(i + 1) % len(pocket_positions)]    
            angle = math.atan2(next_pocket[1] - current[1], next_pocket[0] - current[0])            
            # Calculate gap sizes for each end of the segment
            # Corner pockets are at indices 0, 2, 3, 5
            current_gap = POCKET_RADIUS * (2.0 if i in [0, 2, 3, 5] else 1.5)
            next_gap = POCKET_RADIUS * (2.0 if (i + 1) % len(pocket_positions) in [0, 2, 3, 5] else 1.5)
            start_x = current[0] + math.cos(angle) * current_gap
            start_y = current[1] + math.sin(angle) * current_gap
            end_x = next_pocket[0] - math.cos(angle) * next_gap
            end_y = next_pocket[1] - math.sin(angle) * next_gap
            edges.append(((start_x, start_y), (end_x, end_y)))
        
        for a, b in edges:
            segment = pymunk.Segment(self.table_body, a, b, 5)
            segment.friction = WALL_FRICTION
            segment.elasticity = WALL_ELASTICITY
            segment.collision_type = WALL_COLLISION_TYPE
            self.space.add(segment)
        
        # Set up collision handler for pockets
        handler = self.space.add_collision_handler(BALL_COLLISION_TYPE, POCKET_COLLISION_TYPE)
        # Use pre_solve for continuous collision detection
        handler.pre_solve = self.pocket_collision

    def pocket_collision(self, arbiter, space, data):
        """Handle collision between a ball and a pocket."""
        ball_shape = arbiter.shapes[0]
        pocket_shape = arbiter.shapes[1]
        distance = ball_shape.body.position.get_distance(pocket_shape.body.position)
        # If the ball center is within the pocket radius, remove the ball from the simulation
        if distance < POCKET_RADIUS:
            self.pocketed_balls += 1
            self.space.remove(ball_shape.body, ball_shape)
        return False  # No physical collision response

    # Create an instance of a pymunk pool ball. 
    # Since there are 15, the repetitive work is done in this function
    def create_ball(self):
        """Create and return a pymunk ball instance."""
        ball_body = pymunk.Body(BALL_MASS, self.moment)
        ball_shape = pymunk.Circle(ball_body, BALL_RADIUS)
        ball_shape.elasticity = BALL_ELASTICITY
        ball_shape.friction = BALL_FRICTION     
        ball_shape.collision_type = BALL_COLLISION_TYPE
        return ball_body, ball_shape

    # Adds all the balls to the simulation
    def add_balls(self):
        """Creates and adds all the balls to the simulation"""
        # Create and add the cue ball
        self.cue_ball_body, cue_ball_shape = self.create_ball()    
        cue_ball_shape.color = CUE_BALL_COLOR
        self.cue_ball_body.position = (-10, -10)
        self.space.add(self.cue_ball_body, cue_ball_shape)
        
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
            # Make special note of the first and last balls in the last row
            if ball == 11:
                self.top_ball_body = ball_body
            elif ball == 15:
                self.bottom_ball_body = ball_body

    # Main simulation function
    def simulate(self):
        """Run the simulation."""
        self.create_table()
        self.add_balls()

        # Variables for ball placement and aiming
        placing_ball = True
        aiming = False
        drag_start = None
        aim_angle = 0
        shot_power = 0
        max_power = MAX_SHOT_POWER
        
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
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if placing_ball:
                        # Convert screen coordinates to world coordinates
                        mouse_pos = self.table_body.world_to_local(event.pos)
                        # Check if position is within kitchen area
                        max_x = int(((TABLE_LENGTH) * KITCHEN_RATIO) - HALF_TABLE_LENGTH)
                        if (-HALF_TABLE_LENGTH + BALL_RADIUS <= mouse_pos[0] <= max_x and
                            -HALF_TABLE_WIDTH + BALL_RADIUS <= mouse_pos[1] <= HALF_TABLE_WIDTH - BALL_RADIUS):
                            self.cue_ball_body.position = event.pos
                            placing_ball = False
                    elif not placing_ball:
                        # Start aiming
                        aiming = True
                        drag_start = event.pos
                elif event.type == pygame.MOUSEBUTTONUP and aiming:
                    # Release shot
                    aiming = False
                    self.cue_ball_body.apply_impulse_at_local_point(
                        (shot_power * math.cos(aim_angle), shot_power * math.sin(aim_angle))
                    )
                    drag_start = None
                elif event.type == pygame.MOUSEMOTION:
                    if aiming:
                        # Calculate aim and power during drag
                        current_pos = event.pos
                        dx = drag_start[0] - current_pos[0]
                        dy = drag_start[1] - current_pos[1]
                        aim_angle = math.atan2(dy, dx)
                        # Calculate power based on drag distance (scaled to max_power)
                        drag_distance = math.sqrt(dx**2 + dy**2)
                        shot_power = min(drag_distance * 15, MAX_SHOT_POWER)
                    elif placing_ball:
                        mouse_pos = self.table_body.world_to_local(event.pos)
                        max_x = int(((TABLE_LENGTH) * KITCHEN_RATIO) - HALF_TABLE_LENGTH)
                        if (-HALF_TABLE_LENGTH + BALL_RADIUS <= mouse_pos[0] <= max_x and
                            -HALF_TABLE_WIDTH + BALL_RADIUS <= mouse_pos[1] <= HALF_TABLE_WIDTH - BALL_RADIUS):
                                self.cue_ball_body.position = event.pos

            if not paused:
                self.space.step(1 / FPS)

            # Draw the screen
            self.screen.fill(BACKGROUND_COLOR)
            self.space.debug_draw(self.draw_options)
            
            # Draw aiming line and power indicator
            if aiming and drag_start:
                cue_pos = self.cue_ball_body.position
                line_length = shot_power / 4
                end_x = cue_pos[0] + math.cos(aim_angle) * line_length
                end_y = cue_pos[1] + math.sin(aim_angle) * line_length
                pygame.draw.line(self.screen, (255, 0, 0), 
                               (int(cue_pos[0]), int(cue_pos[1])),
                               (int(end_x), int(end_y)), 2)
            
            # Display instructions and status
            font = pygame.font.Font(None, 30)
            if placing_ball:
                status_text = "Click to place cue ball in kitchen area"
            elif aiming:
                status_text = f"Aiming - Power: {format(shot_power, '.2f')} ({format(shot_power/max_power*100, '.1f')}%)"
            else:
                status_text = (f"Angle: {format(math.degrees(aim_angle), '.2f')}, "
                             f"Power: {format(shot_power, '.2f')}, "
                             f"Cue Position: [{int(self.cue_ball_body.position[0])}, {int(self.cue_ball_body.position[1])}], "
                             f"Pocketed: {self.pocketed_balls}")
            
            text = font.render(status_text, True, (0, 0, 0))
            self.screen.blit(text, (10, 10))
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