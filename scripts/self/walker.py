import pymunk
import pymunk.pygame_util
import pygame
import math

# Constants
# Simulation
WIDTH, HEIGHT = 800, 600
FPS = 60
SLOW_SPEED = 1 / 2

# Colors
WHITE = (255, 255, 255, 255)
GREEN = (60, 210, 22, 255)
BROWN = (139, 69, 19, 255)
GRAY = (128, 128, 128, 255)

SKY_TOP_COLOR = (50, 80, 120)
SKY_BOTTOM_COLOR = (135, 206, 235)

TEXT_COLOR = WHITE

# Ground
GROUND_THICKESS = 5
GROUND_FRICTION = 0.9
GROUND_ELASTICITY = 0.1
GROUND_DEBUG_COLOR = GREEN

# Walking machine
MACHINE_FRICTION = 0.9
MACHINE_ELASTICITY = 0.1

# Collision types
LEG_COLLISION_TYPE = 1
TORSO_COLLISION_TYPE = 2
GROUND_COLLISION_TYPE = 3

# World
GRAVITY = (0, 982)

# Game state
STATE = {"game_over": False}

class Machine:

    # Torso
    TORSO_MASS = 10
    TORSO_WIDTH = 100
    TORSO_HEIGHT = 150
    TORSO_VERTICES = [
        (0, 0),
        (TORSO_WIDTH, 0),
        (TORSO_WIDTH, -TORSO_HEIGHT),
        (0, -TORSO_HEIGHT)
    ]

    # General leg variables
    TOTAL_LEG_LENGTH = 250
    JOINT_OFFSET = 20
    LEG_THICKNESS = 10

    # Thigh
    THIGH_RATIO = 1 / 2
    THIGH_LENGTH = TOTAL_LEG_LENGTH * THIGH_RATIO
    THIGH_MASS = 5

    # Shin
    SHIN_LENGTH = TOTAL_LEG_LENGTH - THIGH_LENGTH - JOINT_OFFSET * 2
    SHIN_MASS = 4

    # Foot
    FOOT_LENGTH = 40
    FOOT_MASS = 30

    # Motors and limits
    HIP_MOTOR_RATE = 1
    HIP_MOTOR_MAX_FORCE = math.inf
    HIP_MIN_ANGLE = -1
    HIP_MAX_ANGLE = 1

    KNEE_MOTOR_RATE = 1
    KNEE_MOTOR_MAX_FORCE = math.inf
    KNEE_MIN_ANGLE = 0
    KNEE_MAX_ANGLE = 2.5

    ANKLE_MOTOR_RATE = 1
    ANKLE_MOTOR_MAX_FORCE = math.inf
    ANKLE_MIN_ANGLE = -0.8
    ANKLE_MAX_ANGLE = 1.5

    # Torso position starts at lowest left point of box
    TORSO_Y_POS = HEIGHT - GROUND_THICKESS - ( TOTAL_LEG_LENGTH + JOINT_OFFSET * 2 )


    def __init__(self, space):
        """Initialize the machine"""
        self.create_torso(space)
        self.create_leg(space)
        self.create_leg(space, False)


    def create_torso(self, space):
        """Create the torso for the machine"""
        moment = pymunk.moment_for_box(self.TORSO_MASS, (self.TORSO_WIDTH, self.TORSO_HEIGHT))
        torso_body = pymunk.Body(self.TORSO_MASS, moment)
        torso_body.position = 200, self.TORSO_Y_POS
        torso_shape = pymunk.Poly(torso_body, self.TORSO_VERTICES, None, 3)
        torso_shape.elasticity = MACHINE_ELASTICITY
        torso_shape.friction = MACHINE_FRICTION
        torso_shape.collision_type = TORSO_COLLISION_TYPE
        self.torso_body = torso_body
        self.torso_shape = torso_shape
        space.add(torso_body, torso_shape)

    
    def create_leg(self, space, right_leg = True):
        """Create a leg for the machine"""
        x_offset = self.TORSO_WIDTH if right_leg else 0

        # ================================================
        # ================= THIGH ========================
        # ================================================
        # Thigh body
        moment = pymunk.moment_for_segment(self.THIGH_MASS, (0, 0), (0, self.THIGH_LENGTH), self.LEG_THICKNESS)
        thigh_body = pymunk.Body(self.THIGH_MASS, moment)
        position = (
            self.torso_body.position.x + x_offset,
            self.torso_body.position.y + self.JOINT_OFFSET
        )
        thigh_body.position = position

        # Thigh shape
        thigh_shape = pymunk.Segment(thigh_body, (0, 0), (0, self.THIGH_LENGTH), self.LEG_THICKNESS)
        thigh_shape.elasticity = MACHINE_ELASTICITY
        thigh_shape.friction = MACHINE_FRICTION
        thigh_shape.collision_type = LEG_COLLISION_TYPE

        # Pivot joint between thigh and torso
        position = (
            thigh_body.position.x,
            thigh_body.position.y - self.JOINT_OFFSET / 2
        )
        hip_joint = pymunk.PivotJoint(self.torso_body, thigh_body, position)
        space.add(thigh_body, thigh_shape, hip_joint)

        # Motor between torso and thigh
        hip_motor = pymunk.SimpleMotor(self.torso_body, thigh_body, 0)
        hip_motor.max_force = self.HIP_MOTOR_MAX_FORCE

        # Limit the range of motion
        hip_limit = pymunk.RotaryLimitJoint(self.torso_body, thigh_body, self.HIP_MIN_ANGLE, self.HIP_MAX_ANGLE)
        hip_limit.max_force = math.inf
        space.add(hip_motor, hip_limit)

        # ================================================
        # ================= KNEE =========================
        # ================================================        
        # Shin body
        moment = pymunk.moment_for_segment(self.SHIN_MASS, (0, 0), (0, self.SHIN_LENGTH), self.LEG_THICKNESS)
        shin_body = pymunk.Body(self.SHIN_MASS, moment)
        position = (
            thigh_body.position.x,
            thigh_body.position.y + self.THIGH_LENGTH + self.JOINT_OFFSET
        )
        shin_body.position = position

        # Shin shape
        shin_shape = pymunk.Segment(shin_body, (0, 0), (0, self.SHIN_LENGTH), self.LEG_THICKNESS)
        shin_shape.elasticity = MACHINE_ELASTICITY
        shin_shape.friction = MACHINE_FRICTION
        shin_shape.collision_type = LEG_COLLISION_TYPE  

        # Pivot joint between thigh and knee
        position = (
            shin_body.position.x,
            shin_body.position.y - self.JOINT_OFFSET / 2
        )
        knee_joint = pymunk.PivotJoint(thigh_body, shin_body, position) 
        space.add(shin_body, shin_shape, knee_joint)

        # Motor between thigh and knee
        knee_motor = pymunk.SimpleMotor(thigh_body, shin_body, 0)
        knee_motor.max_force = self.KNEE_MOTOR_MAX_FORCE
        space.add(knee_motor)

        # Limit the range of motion
        knee_limit = pymunk.RotaryLimitJoint(thigh_body, shin_body, self.KNEE_MIN_ANGLE, self.KNEE_MAX_ANGLE)
        knee_limit.max_force = math.inf
        space.add(knee_limit)

        # ================================================
        # ================= ANKLE ========================
        # ================================================        
        # Foot body
        moment = pymunk.moment_for_segment(self.FOOT_MASS, (0, 0), (0, self.FOOT_LENGTH), self.LEG_THICKNESS)
        foot_body = pymunk.Body(self.FOOT_MASS, moment)
        position = (
            shin_body.position.x,
            shin_body.position.y + self.SHIN_LENGTH + self.JOINT_OFFSET
        )
        foot_body.position = position

        # Foot shape
        foot_shape = pymunk.Segment(foot_body, (0, 0), (self.FOOT_LENGTH, 0), self.LEG_THICKNESS)
        foot_shape.elasticity = MACHINE_ELASTICITY
        foot_shape.friction = MACHINE_FRICTION
        foot_shape.collision_type = LEG_COLLISION_TYPE  

        # Pivot joint between shin and foot
        position = (
            foot_body.position.x,
            foot_body.position.y - self.JOINT_OFFSET / 2
        )
        ankle_joint = pymunk.PivotJoint(shin_body, foot_body, position)
        space.add(foot_body, foot_shape, ankle_joint)

        # Motor between shin and foot
        ankle_motor = pymunk.SimpleMotor(shin_body, foot_body, 0)
        ankle_motor.max_force = self.ANKLE_MOTOR_MAX_FORCE
        space.add(ankle_motor)

        # Limit the range of motion
        ankle_limit = pymunk.RotaryLimitJoint(shin_body, foot_body, self.ANKLE_MIN_ANGLE, self.ANKLE_MAX_ANGLE)
        ankle_limit.max_force = math.inf
        space.add(ankle_limit)

        if right_leg:
            self.right_hip_motor = hip_motor
            self.right_knee_motor = knee_motor
            self.right_ankle_motor = ankle_motor
        else:
            self.left_hip_motor = hip_motor
            self.left_knee_motor = knee_motor
            self.left_ankle_motor = ankle_motor


    # Function to control the legs
    def control_legs(self):
        keys = pygame.key.get_pressed()

        # Right leg
        # Right/foreground hip
        if keys[pygame.K_u]:
            self.right_hip_motor.max_force = self.HIP_MOTOR_MAX_FORCE
            self.right_hip_motor.rate = self.HIP_MOTOR_RATE
        elif keys[pygame.K_j]:
            self.right_hip_motor.max_force = self.HIP_MOTOR_MAX_FORCE
            self.right_hip_motor.rate = -self.HIP_MOTOR_RATE
        elif self.right_hip_motor.rate != 0:
            self.right_hip_motor.rate = 0

        # Right/foreground knee
        if keys[pygame.K_i]:
            self.right_knee_motor.max_force = self.KNEE_MOTOR_MAX_FORCE
            self.right_knee_motor.rate = self.KNEE_MOTOR_RATE
        elif keys[pygame.K_k]:
            self.right_knee_motor.max_force = self.KNEE_MOTOR_MAX_FORCE
            self.right_knee_motor.rate = -self.KNEE_MOTOR_RATE
        elif self.right_knee_motor.rate != 0:
            self.right_knee_motor.rate = 0

        # Right/foreground ankle
        if keys[pygame.K_o]:
            self.right_ankle_motor.max_force = self.ANKLE_MOTOR_MAX_FORCE
            self.right_ankle_motor.rate = self.ANKLE_MOTOR_RATE
        elif keys[pygame.K_l]:
            self.right_ankle_motor.max_force = self.ANKLE_MOTOR_MAX_FORCE
            self.right_ankle_motor.rate = -self.ANKLE_MOTOR_RATE
        elif self.right_ankle_motor.rate != 0:
            self.right_ankle_motor.rate = 0

        # Left leg
        # Left/background hip
        if keys[pygame.K_q]:
            self.left_hip_motor.max_force = self.HIP_MOTOR_MAX_FORCE
            self.left_hip_motor.rate = self.HIP_MOTOR_RATE
        elif keys[pygame.K_a]:
            self.left_hip_motor.max_force = self.HIP_MOTOR_MAX_FORCE
            self.left_hip_motor.rate = -self.HIP_MOTOR_RATE
        elif self.left_hip_motor.rate != 0:
            self.left_hip_motor.rate = 0

        # Left/background knee  
        if keys[pygame.K_w]:
            self.left_knee_motor.max_force = self.KNEE_MOTOR_MAX_FORCE
            self.left_knee_motor.rate = self.KNEE_MOTOR_RATE
        elif keys[pygame.K_s]:
            self.left_knee_motor.max_force = self.KNEE_MOTOR_MAX_FORCE
            self.left_knee_motor.rate = -self.KNEE_MOTOR_RATE
        elif self.left_knee_motor.rate != 0:
            self.left_knee_motor.rate = 0

        # Left/background ankle
        if keys[pygame.K_e]:
            self.left_ankle_motor.max_force = self.ANKLE_MOTOR_MAX_FORCE
            self.left_ankle_motor.rate = self.ANKLE_MOTOR_RATE
        elif keys[pygame.K_d]:
            self.left_ankle_motor.max_force = self.ANKLE_MOTOR_MAX_FORCE
            self.left_ankle_motor.rate = -self.ANKLE_MOTOR_RATE
        elif self.left_ankle_motor.rate != 0:
            self.left_ankle_motor.rate = 0


def create_environment(space):
    """Create the static ground body"""
    ground_body = pymunk.Body(body_type = pymunk.Body.STATIC)
    ground_body.position = (-WIDTH / 2, HEIGHT - GROUND_THICKESS / 2)
    ground_shape = pymunk.Segment(ground_body, (0, 0), (WIDTH * 2, 0), GROUND_THICKESS)
    ground_shape.friction = GROUND_FRICTION
    ground_shape.elasticity = GROUND_ELASTICITY
    ground_shape.collision_type = GROUND_COLLISION_TYPE
    ground_shape.color = GROUND_DEBUG_COLOR
    space.add(ground_body, ground_shape)
    

def cache_background(screen):
    """Cache the background"""
    background = pygame.Surface(screen.get_size())
    for y in range(HEIGHT):
        # Interpolate between top and bottom colors
        ratio = y / HEIGHT
        r = int(SKY_TOP_COLOR[0] + (SKY_BOTTOM_COLOR[0] - SKY_TOP_COLOR[0]) * ratio)
        g = int(SKY_TOP_COLOR[1] + (SKY_BOTTOM_COLOR[1] - SKY_TOP_COLOR[1]) * ratio)
        b = int(SKY_TOP_COLOR[2] + (SKY_BOTTOM_COLOR[2] - SKY_TOP_COLOR[2]) * ratio)
        pygame.draw.line(background, (r, g, b), (0, y), (WIDTH, y))
    return background


def draw_text(texts, screen, left = 10, top = 10):
    """Draw text on the screen"""
    font = pygame.font.Font(None, 24)
    for i, text in enumerate(texts):
        screen.blit(font.render(text, True, TEXT_COLOR), (left, top + i * 20))


def on_collision(arbiter, space, data):
    """Prevent legs from colliding with each other"""
    return False


def on_ground_collision(arbiter, space, data):
    """Reset the simulation if the machine falls on the ground"""
    STATE["game_over"] = True
    return True


def simulate(slow_motion = False):
    """Set up the simulation and run it."""

    # Initialize control flags
    slow_motion = slow_motion
    paused = False

    # Set up the display
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    debug_draw = pymunk.pygame_util.DrawOptions(screen)
    background = cache_background(screen)

    # Set up the Pymunk space
    space = pymunk.Space()
    space.gravity = GRAVITY
    space.damping = 0.9

    # Create the static ground body
    create_environment(space)

    # Create the machine
    machine = Machine(space)

    # Create the collision handlers
    # Prevent legs from colliding with each other
    self_collision_handler = space.add_collision_handler(LEG_COLLISION_TYPE, LEG_COLLISION_TYPE)
    self_collision_handler.pre_solve = on_collision

    # Reset the simulation if the machine falls on the ground
    ground_collision_handler = space.add_collision_handler(TORSO_COLLISION_TYPE, GROUND_COLLISION_TYPE)
    ground_collision_handler.post_solve = on_ground_collision

    # Set up clock and fixed timestep parameters
    clock = pygame.time.Clock()
    fixed_dt = 1.0 / 60.0  # Fixed time step (60 Hz physics)
    if slow_motion:
        fixed_dt *= SLOW_SPEED
    time_accumulator = 0
    substeps = 3

    # Main loop
    while True:

        # Restart the simulation if the machine falls
        if STATE["game_over"]:
            return True, slow_motion

        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, slow_motion
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True, slow_motion
                elif event.key == pygame.K_f:
                    slow_motion = not slow_motion
                    fixed_dt = 1.0 / 60.0 * (SLOW_SPEED if slow_motion else 1.0)
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_ESCAPE:
                    return False, slow_motion

        # Get actual time elapsed since last frame
        dt = clock.tick(FPS) / 1000.0
        
        # Step the simulation if not paused
        if not paused:
            machine.control_legs()
            
            # Accumulate time and step physics at fixed intervals
            time_accumulator += dt
            while time_accumulator >= fixed_dt / substeps:
                space.step(fixed_dt / substeps)
                time_accumulator -= fixed_dt / substeps

        # Draw background
        screen.blit(background, (0, 0))

        # Draw machine
        space.debug_draw(debug_draw)

        # Draw help texts
        texts = [
            f"Toggle speed: F",
            f"Toggle pause: Space",
            f"Reset: R",
            f"Quit: Esc"
        ]
        draw_text(texts, screen, left = 10, top = 10)
        texts = [
            f"1 / 2 Speed" if slow_motion else "1x Speed",
            f"Paused" if paused else ""
        ]
        draw_text(texts, screen, left = WIDTH - 150, top = 10)
        texts = [
            f"Left leg:",
            f"Thigh: <- Q / A ->",
            f"Shin: <- W / S ->",
            f"Foot: ^ E / D v"
        ]
        draw_text(texts, screen, left = 10, top = 100)
        texts = [
            f"Right leg:",
            f"Thigh: <- U / J ->",
            f"Shin: <- I / K ->",
            f"Foot: ^ O / L v"
        ]
        draw_text(texts, screen, left = WIDTH - 150, top = 100)

        pygame.display.flip()


def main():

    pygame.init()

    slow_motion = False

    reset = True
    while reset:
        STATE["game_over"] = False
        reset, slow_motion = simulate(slow_motion)

    pygame.quit()


if __name__ == "__main__":
    main()