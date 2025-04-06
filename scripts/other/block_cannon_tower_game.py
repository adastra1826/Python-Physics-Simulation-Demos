import pygame
import pymunk
import pymunk.pygame_util
import random
import math

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tower Destruction Simulator")

# Colors for background, blocks, and cannon
BACKGROUND = (240, 240, 240)  # Background color (light gray)
BLACK = (0, 0, 0)  # Color for outlines (black)
WHITE = (255, 255, 255)  # Color for text (white)
RED = (255, 0, 0)  # Color for cannonballs or damage (red)
CANNON_COLOR = (100, 100, 100)  # Cannon color (dark gray)

# Physics space
space = pymunk.Space()
space.gravity = (0, 981)  # 981 pixels/s² ~ earth gravity

# Draw options for debugging
draw_options = pymunk.pygame_util.DrawOptions(screen)

# Cannon parameters
cannon_pos = (100, HEIGHT - 100)  # Position of the cannon
cannon_length = 60  # Length of the cannon
cannon_min_angle = 10  # Minimum firing angle (degrees)
cannon_max_angle = 80  # Maximum firing angle (degrees)
cannon_min_power = 200  # Minimum cannonball power (initial speed)
cannon_max_power = 1000  # Maximum cannonball power (initial speed)

# Game parameters
fps = 60  # Frames per second
dt = 1.0 / fps  # Time step for physics updates (1/60th of a second)
cannonball_radius = 10  # Radius of the cannonball
cannonball_mass = 20  # Mass of the cannonball
block_density = 0.1  # Default density of the blocks (controls weight)
block_elasticity = 0.2  # Elasticity of the blocks (how bouncy they are)
block_friction = 0.7  # Friction of the blocks (controls stickiness)

# Debris parameters
debris_count = 5  # Number of pieces when a block breaks
min_debris_size = 5  # Minimum size of debris (shattered pieces)
max_debris_size = 15  # Maximum size of debris (shattered pieces)


def draw_background(surface):
    """
    Draws the background of the simulation, creating a sky gradient effect.
    
    Args:
        surface (pygame.Surface): The surface on which to draw the background.
    """
    for y in range(HEIGHT):
        # Calculate gradient ratio (0 at top, 1 at bottom)
        ratio = y / HEIGHT
        # Blend from dark blue (30, 30, 100) to light blue (135, 206, 250)
        r = int(30 + (135 - 30) * ratio)
        g = int(30 + (206 - 30) * ratio)
        b = int(100 + (250 - 100) * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))


class Block:
    """
    Represents a block in the tower. Blocks are physical objects that can interact with the cannonball and debris.

    Attributes:
        width (float): The width of the block.
        height (float): The height of the block.
        color (tuple): The color of the block (R, G, B).
        density (float): The density of the block.
        elasticity (float): How bouncy the block is when hit.
        friction (float): The friction of the block surface.
        body (pymunk.Body): The pymunk physics body associated with the block.
        shape (pymunk.Poly): The pymunk collision shape for the block.
    """

    def __init__(self, x, y, width, height, color=None, density=None, elasticity=None, friction=None, debris=False):
        """
        Initializes the Block object with given position, size, and physical properties.
        
        Args:
            x (float): The x-coordinate of the block.
            y (float): The y-coordinate of the block.
            width (float): The width of the block.
            height (float): The height of the block.
            color (tuple, optional): The color of the block. Defaults to a random color.
            density (float, optional): The density of the block. Defaults to a random value.
            elasticity (float, optional): The elasticity of the block. Defaults to a random value.
            friction (float, optional): The friction of the block. Defaults to a random value.
        """
        self.width = width
        self.height = height
        self.color = color or self.random_color()  # Random color if not specified
        self.density = density or random.uniform(block_density * 0.5, block_density * 1.5)  # Random density
        self.elasticity = elasticity or random.uniform(block_elasticity * 0.5, block_elasticity * 1.5)  # Random elasticity
        self.friction = friction or random.uniform(block_friction * 0.5, block_friction * 1.5)  # Random friction
        self.debris = debris

        # Create the physics body for the block (mass and moment of inertia)
        mass = self.density * width * height  # Mass = density * area
        moment = pymunk.moment_for_box(mass, (width, height))  # Moment of inertia for a box shape
        self.body = pymunk.Body(mass, moment)  # Create the body with mass and moment
        self.body.position = x, y  # Set the initial position of the block

        # Create the collision shape for the block (box shape)
        self.shape = pymunk.Poly.create_box(self.body, (width, height))
        self.shape.elasticity = self.elasticity  # Set the elasticity (bounciness)
        self.shape.friction = self.friction  # Set the friction (stickiness)
        self.shape.color = self.color  # Set the color for visual representation

        # Add the body and shape to the pymunk space
        space.add(self.body, self.shape)

    def random_color(self):
        """
        Returns a random color for the block, used if no color is specified.

        Returns:
            tuple: A random RGB color value.
        """
        return (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))

    def draw(self, surface):
        """
        Draws the block on the given surface using its current position and shape.
        
        Args:
            surface (pygame.Surface): The surface on which to draw the block.
        """
        vertices = self.shape.get_vertices()  # Get the vertices of the block shape
        # Convert the vertices from pymunk coordinates to pygame coordinates
        points = [v.rotated(self.body.angle) + self.body.position for v in vertices]
        pygame.draw.polygon(surface, self.color, points)  # Draw the block with its color
        pygame.draw.polygon(surface, BLACK, points, 1)  # Draw the border with black

    def break_apart(self):
        """
        Breaks the block into debris and removes the original block from the simulation.
        Creates smaller debris pieces, adds them to the simulation, and applies random velocities.
        
        Returns:
            list: List of debris Block objects created from the broken block
        """

        # Do not allow breaking of debris pieces to prevent infinite breaking
        if self.debris:
            return

        # Remove the original block from the space
        space.remove(self.body, self.shape)
        
        debris_pieces = []
        # Create debris from the broken block
        for _ in range(debris_count):  # Number of debris pieces
            size = random.uniform(min_debris_size, max_debris_size)  # Random size for each piece
            debris = Block(
                self.body.position.x + random.uniform(-self.width / 2, self.width / 2),
                self.body.position.y + random.uniform(-self.height / 2, self.height / 2),
                size, size,
                color=self.color,
                density=self.density,
                elasticity=self.elasticity * 1.5,  # Debris is bouncier
                friction=self.friction * 0.8,  # Debris is less sticky
                debris=True
            )

            # Apply some random velocity to the debris pieces
            debris.body.velocity = (
                random.uniform(-150, 150),  # Random horizontal velocity
                random.uniform(-250, 0)  # Random vertical velocity (upwards or downwards)
            )
            debris_pieces.append(debris)
        
        return debris_pieces


class Cannonball:
    def __init__(self, x, y, velocity_x, velocity_y):
        self.radius = cannonball_radius
        self.mass = cannonball_mass
        self.color = BLACK

        # Create physics body
        self.body = pymunk.Body()
        self.body.position = x, y
        self.body.velocity = velocity_x, velocity_y

        # Create collision shape
        self.shape = pymunk.Circle(self.body, self.radius)
        self.shape.mass = self.mass
        self.shape.elasticity = 0.8
        self.shape.friction = 0.5
        self.shape.color = self.color

        # Add to space
        space.add(self.body, self.shape)

    def draw(self, surface):
        pos = int(self.body.position.x), int(self.body.position.y)
        pygame.draw.circle(surface, self.color, pos, self.radius)

    def should_remove(self):
        # Remove if off-screen or below ground
        return (self.body.position.x < -100 or self.body.position.x > WIDTH + 100 or
                self.body.position.y > HEIGHT + 100)


def create_tower(base_x, base_y, width, height, num_blocks_x=5, num_blocks_y=10):
    blocks = []
    block_width = width / num_blocks_x
    block_height = height / num_blocks_y

    for row in range(num_blocks_y):
        for col in range(num_blocks_x):
            # Alternate pattern for more stability
            x = base_x + col * block_width
            if row % 2 == 1:
                x += block_width / 2

            # Randomize block dimensions slightly
            w = block_width * random.uniform(0.9, 1.1)
            h = block_height * random.uniform(0.9, 1.1)

            # Create block
            block = Block(
                x, base_y - row * block_height,
                w, h
            )
            blocks.append(block)

    return blocks


def create_ground():
    ground = pymunk.Segment(space.static_body, (0, HEIGHT), (WIDTH, HEIGHT), 5)
    ground.elasticity = 0.8
    ground.friction = 1.0
    space.add(ground)

    # Left wall
    left_wall = pymunk.Segment(space.static_body, (0, 0), (0, HEIGHT), 5)
    left_wall.elasticity = 0.8
    space.add(left_wall)

    # Right wall
    right_wall = pymunk.Segment(space.static_body, (WIDTH, 0), (WIDTH, HEIGHT), 5)
    right_wall.elasticity = 0.8
    space.add(right_wall)


def draw_cannon(surface, pos, angle, power_percent):
    # Cannon base
    pygame.draw.circle(surface, CANNON_COLOR, pos, 20)

    # Cannon barrel
    end_x = pos[0] + math.cos(math.radians(angle)) * cannon_length
    end_y = pos[1] - math.sin(math.radians(angle)) * cannon_length
    pygame.draw.line(surface, CANNON_COLOR, pos, (end_x, end_y), 10)

    # Power meter
    meter_width = 100
    meter_height = 10
    meter_x = pos[0] - meter_width // 2
    meter_y = pos[1] + 30

    # Background
    pygame.draw.rect(surface, (200, 200, 200), (meter_x, meter_y, meter_width, meter_height))
    # Fill
    fill_width = int(meter_width * power_percent)
    pygame.draw.rect(surface, (255, 0, 0), (meter_x, meter_y, fill_width, meter_height))


def fire_cannon(pos, angle, power):
    angle_rad = math.radians(angle)
    velocity_x = math.cos(angle_rad) * power
    velocity_y = -math.sin(angle_rad) * power

    # Start position slightly in front of cannon to avoid self-collision
    start_x = pos[0] + math.cos(angle_rad) * (cannon_length + cannonball_radius)
    start_y = pos[1] - math.sin(angle_rad) * (cannon_length + cannonball_radius)

    return Cannonball(start_x, start_y, velocity_x, velocity_y)


def collision_handler(arbiter, space, data):
    # Get the shapes involved in the collision
    shape1, shape2 = arbiter.shapes

    # Check if a cannonball hit a block
    if isinstance(shape1, pymunk.Circle) and isinstance(shape2, pymunk.Poly):
        cannonball_shape, block_shape = shape1, shape2
    elif isinstance(shape2, pymunk.Circle) and isinstance(shape1, pymunk.Poly):
        cannonball_shape, block_shape = shape2, shape1
    else:
        return True  # Not a cannonball-block collision

    # Find the block object
    for block in blocks:
        if block.shape == block_shape:
            # Break the block apart and add debris to blocks list
            debris_pieces = block.break_apart()
            blocks.extend(debris_pieces)
            blocks.remove(block)
            break

    return True  # Process the collision normally


def main():
    global blocks

    # Create physics objects
    create_ground()
    blocks = create_tower(WIDTH // 2, HEIGHT - 50, 300, 500, num_blocks_x=6, num_blocks_y=12)

    # Set up collision handler
    handler = space.add_default_collision_handler()
    handler.post_solve = collision_handler

    # Game objects
    cannonballs = []
    clock = pygame.time.Clock()
    running = True

    # Initialize cannon variables
    cannon_angle = 45  # Starting angle
    power_percent = 0.5
    power_direction = 1
    cannon_power = cannon_min_power + (cannon_max_power - cannon_min_power) * power_percent

    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    cannonballs.append(fire_cannon(cannon_pos, cannon_angle, cannon_power))

        # Handle key presses for cannon control
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            cannon_angle = min(cannon_max_angle, cannon_angle + 1)
        if keys[pygame.K_RIGHT]:
            cannon_angle = max(cannon_min_angle, cannon_angle - 1)

        # Animate power meter
        power_percent += 0.01 * power_direction
        if power_percent >= 1.0:
            power_percent = 1.0
            power_direction = -1
        elif power_percent <= 0.0:
            power_percent = 0.0
            power_direction = 1

        cannon_power = cannon_min_power + (cannon_max_power - cannon_min_power) * power_percent

        # Update physics
        space.step(dt)

        # Remove cannonballs that are off-screen
        cannonballs = [cb for cb in cannonballs if not cb.should_remove()]

        # Draw everything
        draw_background(screen)

        # Draw blocks
        for block in blocks:
            block.draw(screen)

        # Draw cannonballs
        for cannonball in cannonballs:
            cannonball.draw(screen)

        # Draw cannon
        draw_cannon(screen, cannon_pos, cannon_angle, power_percent)

        # Draw UI
        font = pygame.font.SysFont('Arial', 16)
        angle_text = font.render(f"Angle: {cannon_angle}°", True, BLACK)
        power_text = font.render(f"Power: {int(cannon_power)}", True, BLACK)
        screen.blit(angle_text, (10, 10))
        screen.blit(power_text, (10, 30))

        instructions = font.render("Use LEFT/RIGHT arrows to adjust angle. Click to fire.", True, BLACK)
        screen.blit(instructions, (10, HEIGHT - 30))

        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()


if __name__ == "__main__":
    main()