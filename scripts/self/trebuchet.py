import pymunk
import pymunk.pygame_util
import pygame
import math

# Initialize Pygame
pygame.init()

# Simulation constants
WIDTH, HEIGHT = 1000, 600
GROUND_THICKNESS = 15

# Colors
SKY_TOP_COLOR = (50, 80, 120)
SKY_BOTTOM_COLOR = (135, 206, 235)
GROUND_COLOR = (34, 139, 34)
TREBUCHET_COLOR = (139, 69, 19)
PROJECTILE_COLOR = (169, 169, 169)
COUNTERWEIGHT_COLOR = (69, 69, 69)
TEXT_COLOR = (255, 0, 0)
OUTLINE_COLOR = (0, 0, 0)


# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))

def draw_gradient_background():
    """Draw gradient sky background"""
    for y in range(HEIGHT):
        # Interpolate between top and bottom colors
        ratio = y / HEIGHT
        r = int(SKY_TOP_COLOR[0] + (SKY_BOTTOM_COLOR[0] - SKY_TOP_COLOR[0]) * ratio)
        g = int(SKY_TOP_COLOR[1] + (SKY_BOTTOM_COLOR[1] - SKY_TOP_COLOR[1]) * ratio)
        b = int(SKY_TOP_COLOR[2] + (SKY_BOTTOM_COLOR[2] - SKY_TOP_COLOR[2]) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

class ShotStats:
    """Class to store and manage shot statistics"""
    
    def __init__(self):
        self.furthest_shot = 0
        self.last_shot = 0
        self.shot_history = []
    
    def update_shot(self, distance):
        """Update the shot statistics with a new distance"""
        self.last_shot = max(self.last_shot, distance)
        self.furthest_shot = max(self.furthest_shot, self.last_shot)
        self.shot_history.append(self.last_shot)
    
    def reset_current_shot(self):
        """Reset the current shot distance but keep the furthest shot"""
        self.last_shot = 0

class Projectile:

    # Mass properties
    MIN_MASS = 1
    MAX_MASS = 50
    DEFAULT_MASS = 25
    DELTA_MASS = 1

    # Poly side vertices
    RADIUS = 10
    VERTICES = [
        (RADIUS, 0),  # Right point
        (RADIUS * 0.8, RADIUS * 0.6),  # Upper right
        (RADIUS * 0.4, RADIUS * 0.9),  # Upper middle right
        (-RADIUS * 0.2, RADIUS),  # Upper middle left
        (-RADIUS * 0.7, RADIUS * 0.7),  # Upper left
        (-RADIUS, 0),  # Left point
        (-RADIUS * 0.7, -RADIUS * 0.7),  # Lower left
        (-RADIUS * 0.2, -RADIUS),  # Lower middle left
        (RADIUS * 0.4, -RADIUS * 0.9),  # Lower middle right
        (RADIUS * 0.8, -RADIUS * 0.6),  # Lower right
    ]

    def __init__(self, space):
        self.space = space
        self.mass = self.DEFAULT_MASS
        self.moment = pymunk.moment_for_poly(self.mass, self.VERTICES)
        self.body = pymunk.Body(self.mass, self.moment)
        self.body.position = 200, 200
        self.shape = pymunk.Poly(self.body, self.VERTICES)
        self.shape.elasticity = 0.95
        self.shape.friction = 0.3
        # Add angular damping to help the projectile stop rotating eventually
        self.body.angular_damping = 0.5
        # Add linear damping to help the projectile stop moving eventually
        self.body.damping = 0.5
        self.space.add(self.body, self.shape)

    def change_mass(self, increase = True):
        if increase and self.mass + self.DELTA_MASS <= self.MAX_MASS:
            self.mass += self.DELTA_MASS
        elif self.mass - self.DELTA_MASS >= self.MIN_MASS:
            self.mass -= self.DELTA_MASS
        self.body.mass = self.mass
        self.moment = pymunk.moment_for_poly(self.mass, self.VERTICES)
        self.body.moment = self.moment

    def draw_projectile(self):
        # Get the current position and rotation of the projectile
        pos = self.body.position
        angle = self.body.angle
        
        # Transform vertices based on position and rotation
        transformed_vertices = []
        for v in self.VERTICES:
            # Rotate vertex
            rotated_x = v[0] * math.cos(angle) - v[1] * math.sin(angle)
            rotated_y = v[0] * math.sin(angle) + v[1] * math.cos(angle)
            
            # Translate to position
            transformed_vertices.append((pos[0] + rotated_x, pos[1] + rotated_y))
        
        # Draw the projectile
        if len(transformed_vertices) >= 3:
            pygame.draw.polygon(screen, PROJECTILE_COLOR, transformed_vertices)
            pygame.draw.polygon(screen, OUTLINE_COLOR, transformed_vertices, 1)



# Set up the trebuchet
class Trebuchet:
    
    # Size properties
    TREBUCHET_HEIGHT = 150
    BASE_WIDTH = 100
    TREBUCHET_X_POS_OFFSET = BASE_WIDTH + 50

    BEAM_LENGTH = 250
    BEAM_THICKNESS = 10
    BEAM_MASS = 10

    BEAM_PIVOT_RATIO = 0.7
    BEAM_PIVOT_POSITION = BEAM_LENGTH * BEAM_PIVOT_RATIO
    COUNTERWEIGHT_SIZE = 20
    COUNTERWEIGHT_HANG_OFFSET = 30

    # Counterweight properties
    MIN_COUNTERWEIGHT_MASS = 1
    MAX_COUNTERWEIGHT_MASS = 1000
    DEFAULT_COUNTERWEIGHT_MASS = 200
    DELTA_COUNTERWEIGHT_MASS = 10

    beams = []
    resting = False
    holding_projectile = False

    def __init__(self, space, shot_stats):
        self.space = space
        self.counterweight_mass = self.DEFAULT_COUNTERWEIGHT_MASS
        self.counterweight_moment = pymunk.moment_for_box(self.counterweight_mass, (self.COUNTERWEIGHT_SIZE, self.COUNTERWEIGHT_SIZE))
        self.release_point = 100
        
        # Use the provided shot statistics object
        self.shot_stats = shot_stats
        
        # Create base trebuchet body with position at the bottom center of the flat part
        self.trebuchet_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.trebuchet_body.position = (self.TREBUCHET_X_POS_OFFSET, HEIGHT - GROUND_THICKNESS)
        
        # Calculate pivot position (at the top point of triangle)
        self.pivot_position = (self.trebuchet_body.position[0], self.trebuchet_body.position[1] - self.TREBUCHET_HEIGHT)
        
        # Calculate beam lengths on each side of pivot
        # Swap the lengths to make the short side face left
        self.launch_arm_length = self.BEAM_PIVOT_POSITION
        self.counterweight_arm_length = self.BEAM_LENGTH - self.BEAM_PIVOT_POSITION
        
        # Initialize beam body at the pivot point
        moment = pymunk.moment_for_segment(self.BEAM_MASS, (-self.launch_arm_length, 0), (self.counterweight_arm_length, 0), self.BEAM_THICKNESS)
        self.beam_body = pymunk.Body(self.BEAM_MASS, moment)
        self.beam_body.position = self.pivot_position
        
        # Create beam shape relative to beam body (from launch end to counterweight end)
        self.beam_shape = pymunk.Segment(self.beam_body, (-self.launch_arm_length, 0), (self.counterweight_arm_length, 0), self.BEAM_THICKNESS)

        # Create pivot joint at the pivot point
        self.pivot_joint = pymunk.PivotJoint(self.trebuchet_body, self.beam_body, self.pivot_position)
        self.pivot_joint.max_force = math.inf

        # Rotate the beam so the long end rests on the ground
        self.beam_body.angle = 7 * math.pi * 0.25

        # Add all the bodies and joints to the space
        self.space.add(self.trebuchet_body, self.beam_body, self.pivot_joint, self.beam_shape)
        self.beams = [self.beam_shape]

        # Create counterweight
        self.counterweight_body = pymunk.Body(self.counterweight_mass, self.counterweight_moment)
        self.counterweight_body.position = (
            self.beam_body.position[0] + self.counterweight_arm_length * math.cos(self.beam_body.angle),
            self.beam_body.position[1] + self.counterweight_arm_length * math.sin(self.beam_body.angle) + self.COUNTERWEIGHT_HANG_OFFSET
        )
        
        # Create counterweight shape
        self.counterweight_shape = pymunk.Circle(self.counterweight_body, self.COUNTERWEIGHT_SIZE / 2)
        
        # Create pin joint between counterweight and beam end
        self.counterweight_pivot = pymunk.PinJoint(
            self.counterweight_body, 
            self.beam_body, 
            (0, 0), 
            (self.counterweight_arm_length, 0)
        )
        self.counterweight_pivot.max_force = math.inf
        self.space.add(self.counterweight_body, self.counterweight_shape, self.counterweight_pivot)

        self.reset()

        # Create triangular base with 3 points
        segments = [
            pymunk.Segment(self.trebuchet_body, (-self.BASE_WIDTH / 2, 0), (0, -self.TREBUCHET_HEIGHT), self.BEAM_THICKNESS),
            pymunk.Segment(self.trebuchet_body, (-self.BASE_WIDTH / 2, 0), (self.BASE_WIDTH / 2, 0), self.BEAM_THICKNESS),
            pymunk.Segment(self.trebuchet_body, (self.BASE_WIDTH / 2, 0), (0, -self.TREBUCHET_HEIGHT), self.BEAM_THICKNESS)
        ]
        self.beams.extend(segments)

    def reset(self):
        # If the trebuchet is already resting, don't reset it
        if self.resting:
            return
        self.resting = True

        # Reset the beam body so the long end rests on the ground
        self.beam_body.angle = 7 * math.pi * 0.25
        self.beam_body.angular_velocity = 0
        
        # Create the ground pin joint
        if not hasattr(self, 'ground_pin_joint') or self.ground_pin_joint not in self.space.constraints:
            # Calculate the position of the launch end of the beam
            launch_end_x = self.beam_body.position[0] - self.launch_arm_length * math.cos(self.beam_body.angle)
            launch_end_y = self.beam_body.position[1] - self.launch_arm_length * math.sin(self.beam_body.angle)
            
            # Create a static body for the ground at the launch end position
            self.ground_pin_body = pymunk.Body(body_type=pymunk.Body.STATIC)
            self.ground_pin_body.position = (launch_end_x, HEIGHT - GROUND_THICKNESS)
            
            # Create the pin joint between the ground and the launch end of the beam
            self.ground_pin_joint = pymunk.PinJoint(
                self.ground_pin_body,
                self.beam_body,
                (0, 0),
                (-self.launch_arm_length, 0)
            )
            self.ground_pin_joint.max_force = math.inf
            self.space.add(self.ground_pin_body, self.ground_pin_joint)

    def release(self):
        # If the trebuchet is already released, don't release it again
        if not self.resting:
            return
        self.resting = False
        
        # Remove the ground pin joint to release the trebuchet
        if hasattr(self, 'ground_pin_joint'):
            self.space.remove(self.ground_pin_joint)
            self.space.remove(self.ground_pin_body)
        
        # Reset the current shot distance
        self.shot_stats.reset_current_shot()

    def add_projectile(self, projectile):
        if self.holding_projectile:
            return
        self.holding_projectile = True
        # Calculate the position of the launch end of the beam
        launch_end_x = self.beam_body.position[0] - self.launch_arm_length * math.cos(self.beam_body.angle)
        launch_end_y = self.beam_body.position[1] - self.launch_arm_length * math.sin(self.beam_body.angle)
        
        # Set the projectile's initial position to the launch end
        projectile.body.position = (launch_end_x + 20, launch_end_y)
        
        # Create a pin joint between the launch end and projectile
        self.projectile_pin_joint = pymunk.PinJoint(
            self.beam_body,
            projectile.body,
            (-self.launch_arm_length, 0),  # Anchor point on beam
            (0, 0)  # Anchor point on projectile's center
        )
        self.projectile_pin_joint.max_force = math.inf
        self.space.add(self.projectile_pin_joint)

    def release_projectile(self):
        if not self.holding_projectile:
            return
        self.holding_projectile = False
        self.space.remove(self.projectile_pin_joint)

    def draw(self):
        # Draw base trebuchet (static triangular base)
        for i in range(1, len(self.beams)):
            beam = self.beams[i]
            pos = self.trebuchet_body.position
            start = pos + beam.a
            end = pos + beam.b
            pygame.draw.line(screen, TREBUCHET_COLOR, start, end, self.BEAM_THICKNESS)
        
        # Draw beam with proper rotation
        beam_pos = self.beam_body.position
        beam_angle = self.beam_body.angle
        
        # Calculate rotated beam endpoints
        launch_end = (
            beam_pos[0] - self.launch_arm_length * math.cos(beam_angle),
            beam_pos[1] - self.launch_arm_length * math.sin(beam_angle)
        )
        
        counterweight_end = (
            beam_pos[0] + self.counterweight_arm_length * math.cos(beam_angle),
            beam_pos[1] + self.counterweight_arm_length * math.sin(beam_angle)
        )
        
        # Draw the beam
        pygame.draw.line(screen, TREBUCHET_COLOR, launch_end, counterweight_end, self.BEAM_THICKNESS)        
        # Draw pivot point
        pygame.draw.circle(screen, (0, 0, 0), beam_pos, 5)        
        # Draw counterweight
        pygame.draw.circle(screen, COUNTERWEIGHT_COLOR, self.counterweight_body.position, self.COUNTERWEIGHT_SIZE / 2)

    def change_counterweight_mass(self, increase = True):
        if increase and self.counterweight_mass + self.DELTA_COUNTERWEIGHT_MASS <= self.MAX_COUNTERWEIGHT_MASS:
            self.counterweight_mass += self.DELTA_COUNTERWEIGHT_MASS
        elif self.counterweight_mass - self.DELTA_COUNTERWEIGHT_MASS >= self.MIN_COUNTERWEIGHT_MASS:
            self.counterweight_mass -= self.DELTA_COUNTERWEIGHT_MASS
        self.counterweight_body.mass = self.counterweight_mass
        self.counterweight_moment = pymunk.moment_for_box(self.counterweight_mass, (self.COUNTERWEIGHT_SIZE, self.COUNTERWEIGHT_SIZE))


class Ground:
    def __init__(self, space):
        self.space = space
        self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.body.position = 0, HEIGHT
        self.shape = pymunk.Segment(self.body, (0, 0), (1e6, 0), GROUND_THICKNESS)
        self.shape.elasticity = 0.3
        self.shape.friction = 0.7
        self.space.add(self.body, self.shape)

    def draw(self):
        pygame.draw.line(screen, GROUND_COLOR, (0, HEIGHT - GROUND_THICKNESS / 2), (WIDTH, HEIGHT - GROUND_THICKNESS / 2), GROUND_THICKNESS)

def simulate(space, shot_stats):
    clock = pygame.time.Clock()

    # Initialize font
    font = pygame.font.Font(None, 24)

    ground = Ground(space)
    trebuchet = Trebuchet(space, shot_stats)
    projectile = Projectile(space)
    trebuchet.add_projectile(projectile)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if trebuchet.holding_projectile and trebuchet.resting:
                        trebuchet.release()
                    elif trebuchet.holding_projectile and not trebuchet.resting:
                        trebuchet.release_projectile()
                elif event.key == pygame.K_w:
                    trebuchet.change_counterweight_mass(increase=True)
                elif event.key == pygame.K_s:
                    trebuchet.change_counterweight_mass(increase=False)
                elif event.key == pygame.K_d:
                    projectile.change_mass(increase=True)
                elif event.key == pygame.K_a:
                    projectile.change_mass(increase=False)
                elif event.key == pygame.K_r:
                    return True

        # Update last shot distance for tracking
        distance = projectile.body.position[0] - trebuchet.trebuchet_body.position[0]
        trebuchet.shot_stats.update_shot(distance)    

        # Draw the scene
        draw_gradient_background()
        ground.draw()
        trebuchet.draw()
        projectile.draw_projectile()
            
        space.step(1 / 60.0)
        
        # Create background panel for UI
        ui_panel = pygame.Surface((WIDTH, 175), pygame.SRCALPHA)
        ui_panel.fill((100, 100, 100, 128))
        screen.blit(ui_panel, (0, 0))
        
        # Write and draw all UI text
        ui_text = [
            f"Furthest shot: {int(trebuchet.shot_stats.furthest_shot)}",
            f"Last shot: {int(trebuchet.shot_stats.last_shot)}",
            f"Counterweight mass: {trebuchet.counterweight_mass}",
            f"Projectile mass: {projectile.mass}",
            "Controls:",
            "Space - Release trebuchet",
            "Space - Release projectile",
            "W/S - Adjust counterweight",
            "A/D - Adjust projectile mass",
            "R - Reset trebuchet"
        ]
        
        for i, text in enumerate(ui_text):
            text_surface = font.render(text, True, TEXT_COLOR)
            # Position stats on left, controls on right
            x_pos = 10 if i < 4 else WIDTH - 300
            y_pos = 10 + i * 25 if i < 4 else 10 + (i - 4) * 25
            screen.blit(text_surface, (x_pos, y_pos))

        pygame.display.flip()
        clock.tick(60)

def main():   
    # Create a persistent shot stats object
    shot_stats = ShotStats()
    
    reset = True
    while reset:
        # Set up the Pymunk space
        space = pymunk.Space()
        space.gravity = 0, 981
        space.damping = 0.9
        space.iterations = 10

        reset = simulate(space, shot_stats)

if __name__ == "__main__":
    main()