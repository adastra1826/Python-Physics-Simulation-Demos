import sys
import pygame
import math
import random
import Box2D  # Import Box2D physics engine
from Box2D import b2World, b2PolygonShape, b2CircleShape, b2EdgeShape, b2_staticBody, b2_dynamicBody, b2Vec2

"""
Marble Maze Game

A physics-based maze game where players tilt the maze to guide a marble to the goal.
Features realistic physics using Box2D and visual effects with Pygame.

Controls:
- Mouse drag: Tilt the maze
- Mouse wheel: Zoom in/out
- Space: Restart after completion

Physics properties:
- Realistic gravity and collision response
- Ball rotation and momentum
- Particle effects for movement feedback
"""

# Initialize Pygame and set up the game window
pygame.init()

# Game window dimensions and colors
WIDTH, HEIGHT = 800, 800  # Window size in pixels
BG_COLOR = (240, 245, 250)  # Light blue-gray background
WHITE = (255, 255, 255)
BLACK = (20, 20, 30)
RED = (255, 65, 65)
BLUE = (65, 105, 225)
GREEN = (50, 205, 50)

# Modern color palette for visual appeal
TEAL = (0, 168, 150)
PURPLE = (125, 60, 152)
ORANGE = (255, 126, 0)
PINK = (252, 108, 133)
DARK_BLUE = (41, 50, 65)
LIGHT_BLUE = (64, 200, 250)

# Maze dimensions and grid calculations
MAZE_WIDTH, MAZE_HEIGHT = 550, 550  # Size of the maze
GRID_WIDTH, GRID_HEIGHT = MAZE_WIDTH / 18, MAZE_HEIGHT / 18  # Size of each grid cell

# Game object colors
MAZE_COLOR = DARK_BLUE  # Color for maze walls
BALL_COLOR = ORANGE  # Primary ball color
HOLE_COLOR = TEAL  # Color for the goal/hole
BALL_HIGHLIGHT = (255, 200, 150)  # Highlight for the ball (creates 3D effect)
BALL_SHADOW = (200, 80, 0)  # Shadow color for the ball

# Wall thickness
WALL_THICKNESS = 8  # Thickness of maze walls in pixels

# Box2D physics constants
PPM = 20.0  # Pixels Per Meter - conversion factor between pixels and Box2D units
FPS = 60  # Frames per second
TIME_STEP = 1.0 / FPS  # Physics simulation time step
VELOCITY_ITERATIONS = 8  # Box2D velocity iterations (higher = more accurate)
POSITION_ITERATIONS = 8  # Box2D position iterations (higher = more accurate)

# Physics material properties
BALL_DENSITY = 10.0  # Ball density (affects mass)
BALL_FRICTION = 0.4  # Ball friction coefficient
BALL_RESTITUTION = 0.5  # Ball bounciness/elasticity
WALL_FRICTION = 0.8  # Wall friction coefficient
WALL_RESTITUTION = 0.5  # Wall bounciness/elasticity

# Visual effects settings
ENABLE_SHADOWS = True  # Enable shadow rendering
ENABLE_PARTICLE_EFFECTS = True  # Enable particle effects for movement
ENABLE_BLOOM = True  # Enable bloom/glow effects
MAX_PARTICLES = 30  # Maximum number of particles allowed
PARTICLE_LIFETIME = 30  # Particle lifetime in frames


def rotate_point(point, angle, center):
    """
    Rotate a point around a center point by a given angle in radians.

    This is used for rotating maze elements when the player tilts the maze.

    Args:
        point (tuple): (x, y) coordinates of the point to rotate
        angle (float): Rotation angle in radians
        center (tuple): (x, y) coordinates of the rotation center

    Returns:
        tuple: (x, y) coordinates of the rotated point
    """
    x, y = point
    cx, cy = center
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    x -= cx
    y -= cy
    new_x = x * cos_a - y * sin_a
    new_y = x * sin_a + y * cos_a
    return new_x + cx, new_y + cy


def create_gradient_surface(width, height, color1, color2, vertical=True):
    """
    Create a surface with a smooth gradient between two colors.

    Used for creating background and UI elements with depth.

    Args:
        width (int): Width of the surface in pixels
        height (int): Height of the surface in pixels
        color1 (tuple): RGB or RGBA values for the starting color
        color2 (tuple): RGB or RGBA values for the ending color
        vertical (bool): If True, gradient runs top to bottom; if False, left to right

    Returns:
        pygame.Surface: A new surface with the requested gradient
    """
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    for i in range(height if vertical else width):
        # Calculate blend factor (0.0 to 1.0)
        blend = i / (height if vertical else width)
        # Linear interpolation between colors
        r = int(color1[0] * (1 - blend) + color2[0] * blend)
        g = int(color1[1] * (1 - blend) + color2[1] * blend)
        b = int(color1[2] * (1 - blend) + color2[2] * blend)
        # Draw a line with the blended color
        if vertical:
            pygame.draw.line(surface, (r, g, b), (0, i), (width, i))
        else:
            pygame.draw.line(surface, (r, g, b), (i, 0), (i, height))
    return surface


# Initialize game window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Marble Maze")
clock = pygame.time.Clock()

# Create Box2D world with gravity
world = b2World(gravity=(0, 8), doSleep=True)


# Custom physics classes with Box2D integration
class Wall:
    """
    Represents a wall segment in the maze.

    Handles both physics (using Box2D fixtures) and rendering of wall segments.
    Walls can be rotated when the maze tilts, and they provide collision surfaces
    for the ball to interact with.

    Attributes:
        start_point (tuple): The (x,y) coordinates of the wall's starting point
        end_point (tuple): The (x,y) coordinates of the wall's ending point
        thickness (int): Thickness of the wall in pixels
        body (Box2D.b2Body): The Box2D physics body for this wall
        shape (Box2D.b2Fixture): The Box2D fixture attached to the body
    """

    def __init__(self, start_point, end_point, thickness=WALL_THICKNESS):
        """
        Initialize a wall segment.

        Args:
            start_point (tuple): Starting coordinates (x, y) in pixels
            end_point (tuple): Ending coordinates (x, y) in pixels
            thickness (int, optional): Wall thickness in pixels
        """
        self.start_point = start_point
        self.end_point = end_point
        self.thickness = thickness
        self.original_start = start_point  # Store original for rotation calculations
        self.original_end = end_point  # Store original for rotation calculations

        # Create Box2D body and shape
        self.body = world.CreateStaticBody(position=(0, 0))

        # Calculate wall center and dimensions
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        length = math.sqrt(dx * dx + dy * dy)

        if length < 0.001:  # Too small to create a fixture
            return

        # Create an edge shape for the wall
        self.shape = self.body.CreateFixture(
            shape=b2EdgeShape(vertices=[(start_point[0] / PPM, start_point[1] / PPM),
                                        (end_point[0] / PPM, end_point[1] / PPM)]),
            density=0.0,  # Static bodies have zero density
            friction=WALL_FRICTION,
            restitution=WALL_RESTITUTION,
            userData={"type": "wall"}
        )

    def rotate(self, angle, center):
        """
        Rotate the wall around a center point by a given angle.

        This recreates the Box2D fixture with the new rotated coordinates.

        Args:
            angle (float): The absolute angle in radians
            center (tuple): Center point (x, y) of rotation
        """
        # Remove old fixture
        self.body.DestroyFixture(self.shape)

        # Update rotated points
        self.start_point = rotate_point(self.original_start, angle, center)
        self.end_point = rotate_point(self.original_end, angle, center)

        # Create new edge shape for the rotated wall
        self.shape = self.body.CreateFixture(
            shape=b2EdgeShape(vertices=[(self.start_point[0] / PPM, self.start_point[1] / PPM),
                                        (self.end_point[0] / PPM, self.end_point[1] / PPM)]),
            density=0.0,
            friction=WALL_FRICTION,
            restitution=WALL_RESTITUTION,
            userData={"type": "wall"}
        )

    def draw(self, surface, zoom, offset_x, offset_y):
        """
        Draw the wall on the provided surface.

        Includes shadow effects for visual depth if enabled.

        Args:
            surface (pygame.Surface): Surface to draw on
            zoom (float): Current zoom level
            offset_x (float): X-offset for drawing
            offset_y (float): Y-offset for drawing
        """
        # Scale and transform coordinates based on zoom level and offsets
        start_x = self.start_point[0] * zoom + offset_x
        start_y = self.start_point[1] * zoom + offset_y
        end_x = self.end_point[0] * zoom + offset_x
        end_y = self.end_point[1] * zoom + offset_y

        # Draw shadow first (slightly offset)
        if ENABLE_SHADOWS:
            shadow_offset = 3
            pygame.draw.line(surface, (0, 0, 0, 100),
                             (start_x + shadow_offset, start_y + shadow_offset),
                             (end_x + shadow_offset, end_y + shadow_offset),
                             max(1, int(self.thickness * zoom)))

        # Draw main wall with slight gradient effect
        pygame.draw.line(surface, MAZE_COLOR, (start_x, start_y), (end_x, end_y),
                         max(1, int(self.thickness * zoom)))


class Particle:
    """
    Visual particle effect for ball movement.

    Particles are created when the ball moves quickly and gradually fade out.
    They provide visual feedback for ball movement and speed.

    Attributes:
        x (float): X-coordinate of particle
        y (float): Y-coordinate of particle
        color (tuple): RGB color of the particle
        size (float): Radius of the particle
        velocity (tuple): (vx, vy) velocity components
        lifetime (int): Remaining lifetime in frames
    """

    def __init__(self, x, y, color):
        """
        Initialize a new particle.

        Args:
            x (float): Starting X position
            y (float): Starting Y position
            color (tuple): RGB color values
        """
        self.x = x
        self.y = y
        self.color = color
        self.size = random.uniform(1, 3)  # Random size for variation
        self.velocity = (random.uniform(-1, 1), random.uniform(-1, 1))  # Random direction
        self.lifetime = PARTICLE_LIFETIME

    def update(self):
        """
        Update particle position and properties.

        Particles move according to their velocity and gradually shrink
        and fade as their lifetime decreases.
        """
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.lifetime -= 1
        self.size -= 0.05  # Gradually shrink
        if self.size < 0:
            self.size = 0

    def draw(self, surface):
        """
        Draw the particle on the given surface.

        Transparency is based on remaining lifetime.

        Args:
            surface (pygame.Surface): Surface to draw the particle on
        """
        alpha = int(255 * (self.lifetime / PARTICLE_LIFETIME))  # Fade based on lifetime
        if alpha > 0 and self.size > 0:
            color_with_alpha = (*self.color, alpha)
            pygame.draw.circle(surface, color_with_alpha, (int(self.x), int(self.y)), max(0, int(self.size)))


class Ball:
    """
    The player-controlled ball that navigates through the maze.

    Combines Box2D physics with visual rendering, including particle effects.
    The ball responds to gravity and collisions while also moving with the maze
    when it's tilted.

    Attributes:
        position (tuple): (x, y) position in pixels
        radius (float): Ball radius in pixels
        particles (list): List of active particles for visual effects
        original_position (tuple): Initial position for reference
        body (Box2D.b2Body): Box2D physics body
        fixture (Box2D.b2Fixture): Ball's circle fixture for physics
    """

    def __init__(self, x, y, radius=10):
        """
        Initialize the ball with physics properties.

        Args:
            x (float): Initial x-coordinate
            y (float): Initial y-coordinate
            radius (float, optional): Ball radius in pixels
        """
        self.position = (x, y)
        self.radius = radius
        self.particles = []
        self.original_position = (x, y)  # Store original position for rotation with maze

        # Create Box2D dynamic body for the ball
        self.body = world.CreateDynamicBody(
            position=(x / PPM, y / PPM),
            fixedRotation=False,  # Allow rotation for more realistic physics
            bullet=True,  # Enable continuous collision detection
            # linearDamping=0.2,
            # angularDamping=0.1
        )

        # Create circle fixture for the ball
        self.fixture = self.body.CreateFixture(
            shape=b2CircleShape(radius=radius / PPM),
            density=BALL_DENSITY,
            friction=BALL_FRICTION,
            restitution=BALL_RESTITUTION,
            userData={"type": "ball"}
        )

    def rotate_with_maze(self, angle_diff, center):
        """
        Rotate the ball with the maze to maintain relative position.

        This is critical for realistic maze tilting behavior. When the maze rotates,
        the ball should move with it, while still being affected by physics forces.
        This method adjusts both position and velocity to account for maze rotation.

        Args:
            angle_diff (float): Angle change in radians since last frame
            center (tuple): Center point (x, y) of rotation
        """
        # Calculate current position
        old_position = (self.body.position.x * PPM, self.body.position.y * PPM)

        # Rotate position around center
        rotated_position = rotate_point(old_position, angle_diff, center)

        # Apply new position
        self.body.position = b2Vec2(rotated_position[0] / PPM, rotated_position[1] / PPM)

        # Also rotate velocity to maintain direction relative to the maze
        vx, vy = self.body.linearVelocity
        new_vx = vx * math.cos(angle_diff) - vy * math.sin(angle_diff)
        new_vy = vx * math.sin(angle_diff) + vy * math.cos(angle_diff)
        self.body.linearVelocity = (new_vx, new_vy)

        # Apply additional angular velocity based on maze rotation
        self.body.angularVelocity += angle_diff * 30  # Scale factor to make rotation visible

    def update(self, gravity, walls, hole, angle):
        """
        Update ball physics and visual effects.

        Physics are primarily handled by Box2D, but this method manages
        particle effects and checks for goal/hole collision.

        Args:
            gravity: Not used directly (handled by Box2D world)
            walls: List of wall objects
            hole: The goal hole object
            angle: Current maze angle

        Returns:
            bool: True if ball is in the hole (game completed), False otherwise
        """
        # Position is updated by Box2D physics engine
        self.position = (self.body.position.x * PPM, self.body.position.y * PPM)

        # Add particles when ball is moving fast
        if ENABLE_PARTICLE_EFFECTS:
            velocity = self.body.linearVelocity
            speed = math.sqrt(velocity.x * velocity.x + velocity.y * velocity.y)
            if speed > 5 and random.random() < 0.3 and len(self.particles) < MAX_PARTICLES:
                # Create particle at ball position
                self.particles.append(Particle(self.position[0], self.position[1],
                                               (random.randint(200, 255),
                                                random.randint(100, 200),
                                                random.randint(0, 50))))

            # Update existing particles
            for particle in self.particles[:]:
                particle.update()
                if particle.lifetime <= 0:
                    self.particles.remove(particle)

        # Check if ball is in hole
        return self.check_hole_collision(hole)

    def check_hole_collision(self, hole):
        # Calculate distance from ball center to hole center
        dx = self.position[0] - hole.position[0]
        dy = self.position[1] - hole.position[1]
        distance = math.sqrt(dx * dx + dy * dy)

        # Check if ball is entirely inside hole
        return distance < hole.radius - self.radius

    def draw(self, surface, zoom, offset_x, offset_y):
        x = self.position[0] * zoom + offset_x
        y = self.position[1] * zoom + offset_y
        radius = self.radius * zoom

        # Draw particles first (they should appear behind the ball)
        if ENABLE_PARTICLE_EFFECTS:
            particle_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for particle in self.particles:
                particle.draw(particle_surface)
            surface.blit(particle_surface, (0, 0))

        # Get rotation angle from Box2D body for more realistic visualization
        angle = self.body.angle

        # Draw shadow
        if ENABLE_SHADOWS:
            shadow_offset = 4
            pygame.draw.circle(surface, (0, 0, 0, 100),
                               (int(x + shadow_offset), int(y + shadow_offset)),
                               int(radius))

        # Draw ball with gradient effect (3D look)
        gradient_offset = radius * 0.3
        pygame.draw.circle(surface, BALL_COLOR, (int(x), int(y)), int(radius))

        # Add highlight
        highlight_pos = (int(x - gradient_offset), int(y - gradient_offset))
        highlight_radius = int(radius * 0.6)
        pygame.draw.circle(surface, BALL_HIGHLIGHT, highlight_pos, highlight_radius)

        # Add rotation indicator
        end_x = x + math.cos(angle) * radius * 0.7
        end_y = y + math.sin(angle) * radius * 0.7
        pygame.draw.line(surface, BALL_SHADOW, (int(x), int(y)), (int(end_x), int(end_y)), 2)


class Hole:
    """
    The goal/destination hole that the player needs to get the ball into.

    Features visual effects like pulsating glow and shadows to make it
    visually distinctive. Uses a Box2D sensor to detect when the ball
    enters without creating physical collision.

    Attributes:
        position (tuple): Current (x, y) position in pixels
        radius (float): Hole radius in pixels
        original_position (tuple): Initial position for rotation calculations
        animation_time (float): Time counter for animation effects
        body (Box2D.b2Body): Box2D static body
        fixture (Box2D.b2Fixture): Sensor fixture for detecting ball entry
    """

    def __init__(self, x, y, radius=13):
        """
        Initialize the hole with position and visual properties.

        Args:
            x (float): X-coordinate of hole center
            y (float): Y-coordinate of hole center
            radius (float, optional): Radius of hole in pixels
        """
        self.position = (x, y)
        self.radius = radius
        self.original_position = (x, y)
        self.animation_time = 0

        # Add a sensor fixture for more accurate hole detection
        self.body = world.CreateStaticBody(position=(x / PPM, y / PPM))
        self.fixture = self.body.CreateFixture(
            shape=b2CircleShape(radius=radius / PPM),
            isSensor=True,  # This makes it a sensor that detects overlaps but doesn't collide
            userData={"type": "hole"}
        )

    def rotate(self, angle, center):
        """
        Rotate the hole when the maze is tilted.

        Args:
            angle (float): Current absolute angle in radians
            center (tuple): Center point (x, y) of rotation
        """
        # Update position
        self.position = rotate_point(self.original_position, angle, center)

        # Update Box2D body position
        self.body.position = b2Vec2(self.position[0] / PPM, self.position[1] / PPM)

    def update(self):
        """
        Update animation effects.

        Increments the animation timer used for pulsating visual effects.
        """
        # Update animation time for visual effects
        self.animation_time += 0.05

    def draw(self, surface, zoom, offset_x, offset_y):
        """
        Draw the hole with visual effects.

        Includes shadow, depth gradient, and pulsating inner glow.

        Args:
            surface (pygame.Surface): Surface to draw on
            zoom (float): Current zoom level
            offset_x (float): X-offset for drawing
            offset_y (float): Y-offset for drawing
        """
        x = self.position[0] * zoom + offset_x
        y = self.position[1] * zoom + offset_y
        radius = self.radius * zoom

        # Draw shadow (larger and darker at the bottom for 3D effect)
        if ENABLE_SHADOWS:
            shadow_radius = radius * 1.2
            shadow_surface = pygame.Surface((int(shadow_radius * 2), int(shadow_radius * 2)), pygame.SRCALPHA)
            for i in range(5):
                alpha = 150 - i * 30
                size_factor = 1.0 - i * 0.15
                pygame.draw.circle(shadow_surface, (0, 0, 0, alpha),
                                   (int(shadow_radius), int(shadow_radius)),
                                   int(radius * size_factor))
            surface.blit(shadow_surface, (int(x - shadow_radius), int(y - shadow_radius)))

        # Draw hole with gradient for depth effect
        dark_color = (HOLE_COLOR[0] // 2, HOLE_COLOR[1] // 2, HOLE_COLOR[2] // 2)

        # Outer circle (main hole color)
        pygame.draw.circle(surface, HOLE_COLOR, (int(x), int(y)), int(radius))

        # Inner circle (darker for depth)
        inner_radius = radius * 0.85
        pygame.draw.circle(surface, dark_color, (int(x), int(y)), int(inner_radius))

        # Pulsating inner glow
        glow_size = 0.4 + 0.1 * math.sin(self.animation_time)
        glow_radius = radius * glow_size
        glow_color = (HOLE_COLOR[0] + 40, HOLE_COLOR[1] + 40, HOLE_COLOR[2] + 40)
        pygame.draw.circle(surface, glow_color, (int(x), int(y)), int(glow_radius))


# Define maze segments (walls) - each tuple contains start and end points
maze_segments = [
    # Outer walls
    ((-MAZE_WIDTH / 2, -MAZE_HEIGHT / 2), (MAZE_WIDTH / 2, -MAZE_HEIGHT / 2)),
    ((MAZE_WIDTH / 2, -MAZE_HEIGHT / 2), (MAZE_WIDTH / 2, MAZE_HEIGHT / 2)),
    ((-MAZE_WIDTH / 2, MAZE_HEIGHT / 2), (MAZE_WIDTH / 2, MAZE_HEIGHT / 2)),
    ((-MAZE_WIDTH / 2, -MAZE_HEIGHT / 2), (-MAZE_WIDTH / 2, MAZE_HEIGHT / 2)),
    # Inner maze segments
    # Column 1
    ((MAZE_WIDTH / 2 - GRID_WIDTH, MAZE_HEIGHT / 2), (MAZE_WIDTH / 2 - GRID_WIDTH, MAZE_HEIGHT / 2 - GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - GRID_WIDTH, MAZE_HEIGHT / 2 - 3 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - GRID_WIDTH, MAZE_HEIGHT / 2 - 5 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - GRID_WIDTH, MAZE_HEIGHT / 2 - 17 * GRID_HEIGHT)),
    # Column 2
    ((MAZE_WIDTH / 2 - 2 * GRID_WIDTH, MAZE_HEIGHT / 2 - 4 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 2 * GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 2 * GRID_WIDTH, MAZE_HEIGHT / 2 - 14 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 2 * GRID_WIDTH, MAZE_HEIGHT / 2 - 16 * GRID_HEIGHT)),
    # Column 3
    ((MAZE_WIDTH / 2 - 3 * GRID_WIDTH, MAZE_HEIGHT / 2 - 4 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 3 * GRID_WIDTH, MAZE_HEIGHT / 2 - 5 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 3 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 3 * GRID_WIDTH, MAZE_HEIGHT / 2 - 11 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 3 * GRID_WIDTH, MAZE_HEIGHT / 2 - 14 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 3 * GRID_WIDTH, MAZE_HEIGHT / 2 - 17 * GRID_HEIGHT)),
    # Column 4
    ((MAZE_WIDTH / 2 - 4 * GRID_WIDTH, MAZE_HEIGHT / 2 - 4 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 4 * GRID_WIDTH, MAZE_HEIGHT / 2 - 5 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 4 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 4 * GRID_WIDTH, MAZE_HEIGHT / 2 - 11 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 4 * GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 4 * GRID_WIDTH, MAZE_HEIGHT / 2 - 17 * GRID_HEIGHT)),
    # Column 5
    ((MAZE_WIDTH / 2 - 5 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 5 * GRID_WIDTH, MAZE_HEIGHT / 2 - 9 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 5 * GRID_WIDTH, MAZE_HEIGHT / 2 - 10 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 5 * GRID_WIDTH, MAZE_HEIGHT / 2 - 11 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 5 * GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 5 * GRID_WIDTH, MAZE_HEIGHT / 2 - 17 * GRID_HEIGHT)),
    # Column 6
    ((MAZE_WIDTH / 2 - 6 * GRID_WIDTH, MAZE_HEIGHT / 2 - GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 6 * GRID_WIDTH, MAZE_HEIGHT / 2 - 2 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 6 * GRID_WIDTH, MAZE_HEIGHT / 2 - 4 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 6 * GRID_WIDTH, MAZE_HEIGHT / 2 - 5 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 6 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 6 * GRID_WIDTH, MAZE_HEIGHT / 2 - 9 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 6 * GRID_WIDTH, MAZE_HEIGHT / 2 - 10 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 6 * GRID_WIDTH, MAZE_HEIGHT / 2 - 11 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 6 * GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 6 * GRID_WIDTH, MAZE_HEIGHT / 2 - 16 * GRID_HEIGHT)),
    # Column 7
    ((MAZE_WIDTH / 2 - 7 * GRID_WIDTH, MAZE_HEIGHT / 2 - 3 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 7 * GRID_WIDTH, MAZE_HEIGHT / 2 - 5 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 7 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 7 * GRID_WIDTH, MAZE_HEIGHT / 2 - 9 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 7 * GRID_WIDTH, MAZE_HEIGHT / 2 - 10 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 7 * GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT)),
    # Column 8
    ((MAZE_WIDTH / 2 - 8 * GRID_WIDTH, MAZE_HEIGHT / 2 - 3 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 8 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 8 * GRID_WIDTH, MAZE_HEIGHT / 2 - 7 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 8 * GRID_WIDTH, MAZE_HEIGHT / 2 - 10 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 8 * GRID_WIDTH, MAZE_HEIGHT / 2 - 11 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 8 * GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 8 * GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 8 * GRID_WIDTH, MAZE_HEIGHT / 2 - 14 * GRID_HEIGHT)),
    # Column 9
    ((MAZE_WIDTH / 2 - 9 * GRID_WIDTH, MAZE_HEIGHT / 2 - 3 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 9 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 9 * GRID_WIDTH, MAZE_HEIGHT / 2 - 7 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 9 * GRID_WIDTH, MAZE_HEIGHT / 2 - 10 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 9 * GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 9 * GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT)),
    # Column 10
    ((MAZE_WIDTH / 2 - 10 * GRID_WIDTH, MAZE_HEIGHT / 2 - GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 10 * GRID_WIDTH, MAZE_HEIGHT / 2 - 3 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 10 * GRID_WIDTH, MAZE_HEIGHT / 2 - 8 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 10 * GRID_WIDTH, MAZE_HEIGHT / 2 - 9 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 10 * GRID_WIDTH, MAZE_HEIGHT / 2 - 10 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 10 * GRID_WIDTH, MAZE_HEIGHT / 2 - 11 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 10 * GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 10 * GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 10 * GRID_WIDTH, MAZE_HEIGHT / 2 - 14 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 10 * GRID_WIDTH, MAZE_HEIGHT / 2 - 15 * GRID_HEIGHT)),
    # Column 11
    ((MAZE_WIDTH / 2 - 11 * GRID_WIDTH, MAZE_HEIGHT / 2 - GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 11 * GRID_WIDTH, MAZE_HEIGHT / 2 - 2 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 11 * GRID_WIDTH, MAZE_HEIGHT / 2 - 3 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 11 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 11 * GRID_WIDTH, MAZE_HEIGHT / 2 - 10 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 11 * GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 11 * GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 11 * GRID_WIDTH, MAZE_HEIGHT / 2 - 14 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 11 * GRID_WIDTH, MAZE_HEIGHT / 2 - 15 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 11 * GRID_WIDTH, MAZE_HEIGHT / 2 - 17 * GRID_HEIGHT)),
    # Column 12
    ((MAZE_WIDTH / 2 - 12 * GRID_WIDTH, MAZE_HEIGHT / 2 - 3 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 12 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 12 * GRID_WIDTH, MAZE_HEIGHT / 2 - 10 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 12 * GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 12 * GRID_WIDTH, MAZE_HEIGHT / 2 - 14 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 12 * GRID_WIDTH, MAZE_HEIGHT / 2 - 17 * GRID_HEIGHT)),
    # Column 13
    ((MAZE_WIDTH / 2 - 13 * GRID_WIDTH, MAZE_HEIGHT / 2 - 2 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 13 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 13 * GRID_WIDTH, MAZE_HEIGHT / 2 - 8 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 13 * GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 13 * GRID_WIDTH, MAZE_HEIGHT / 2 - 15 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 13 * GRID_WIDTH, MAZE_HEIGHT / 2 - 17 * GRID_HEIGHT)),
    # Column 14
    ((MAZE_WIDTH / 2 - 14 * GRID_WIDTH, MAZE_HEIGHT / 2 - 3 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 14 * GRID_WIDTH, MAZE_HEIGHT / 2 - 5 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 14 * GRID_WIDTH, MAZE_HEIGHT / 2 - 8 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 14 * GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 14 * GRID_WIDTH, MAZE_HEIGHT / 2 - 15 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 14 * GRID_WIDTH, MAZE_HEIGHT / 2 - 16 * GRID_HEIGHT)),
    # Column 15
    ((MAZE_WIDTH / 2 - 15 * GRID_WIDTH, MAZE_HEIGHT / 2 - 7 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 15 * GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 15 * GRID_WIDTH, MAZE_HEIGHT / 2 - 14 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 15 * GRID_WIDTH, MAZE_HEIGHT / 2 - 17 * GRID_HEIGHT)),
    # Column 16
    ((MAZE_WIDTH / 2 - 16 * GRID_WIDTH, MAZE_HEIGHT / 2 - 2 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 16 * GRID_WIDTH, MAZE_HEIGHT / 2 - 5 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 16 * GRID_WIDTH, MAZE_HEIGHT / 2 - 8 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 16 * GRID_WIDTH, MAZE_HEIGHT / 2 - 10 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 16 * GRID_WIDTH, MAZE_HEIGHT / 2 - 11 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 16 * GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 16 * GRID_WIDTH, MAZE_HEIGHT / 2 - 14 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 16 * GRID_WIDTH, MAZE_HEIGHT / 2 - 15 * GRID_HEIGHT)),
    # Column 17
    ((MAZE_WIDTH / 2 - 17 * GRID_WIDTH, MAZE_HEIGHT / 2 - GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 17 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 17 * GRID_WIDTH, MAZE_HEIGHT / 2 - 9 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 17 * GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 17 * GRID_WIDTH, MAZE_HEIGHT / 2 - 14 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 17 * GRID_WIDTH, MAZE_HEIGHT / 2 - 17 * GRID_HEIGHT)),
    # Row 1
    ((MAZE_WIDTH / 2 - GRID_WIDTH, MAZE_HEIGHT / 2 - GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 10 * GRID_WIDTH, MAZE_HEIGHT / 2 - GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 11 * GRID_WIDTH, MAZE_HEIGHT / 2 - GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 17 * GRID_WIDTH, MAZE_HEIGHT / 2 - GRID_HEIGHT)),
    # Row 2
    ((MAZE_WIDTH / 2 - GRID_WIDTH, MAZE_HEIGHT / 2 - 2 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 6 * GRID_WIDTH, MAZE_HEIGHT / 2 - 2 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 7 * GRID_WIDTH, MAZE_HEIGHT / 2 - 2 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 10 * GRID_WIDTH, MAZE_HEIGHT / 2 - 2 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 11 * GRID_WIDTH, MAZE_HEIGHT / 2 - 2 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 16 * GRID_WIDTH, MAZE_HEIGHT / 2 - 2 * GRID_HEIGHT)),
    # Row 3
    ((MAZE_WIDTH / 2 - GRID_WIDTH, MAZE_HEIGHT / 2 - 3 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 7 * GRID_WIDTH, MAZE_HEIGHT / 2 - 3 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 11 * GRID_WIDTH, MAZE_HEIGHT / 2 - 3 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 12 * GRID_WIDTH, MAZE_HEIGHT / 2 - 3 * GRID_HEIGHT)),
    # Row 4
    ((MAZE_WIDTH / 2 - 2 * GRID_WIDTH, MAZE_HEIGHT / 2 - 4 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 6 * GRID_WIDTH, MAZE_HEIGHT / 2 - 4 * GRID_HEIGHT)),
    # Row 5
    ((MAZE_WIDTH / 2 - 4 * GRID_WIDTH, MAZE_HEIGHT / 2 - 5 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 5 * GRID_WIDTH, MAZE_HEIGHT / 2 - 5 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 6 * GRID_WIDTH, MAZE_HEIGHT / 2 - 5 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 7 * GRID_WIDTH, MAZE_HEIGHT / 2 - 5 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 14 * GRID_WIDTH, MAZE_HEIGHT / 2 - 5 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 16 * GRID_WIDTH, MAZE_HEIGHT / 2 - 5 * GRID_HEIGHT)),
    # Row 6
    ((MAZE_WIDTH / 2 - 5 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 6 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 8 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 11 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 12 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 13 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 14 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 17 * GRID_WIDTH, MAZE_HEIGHT / 2 - 6 * GRID_HEIGHT)),
    # Row 7-17 (remaining rows)
    # Row 7
    ((MAZE_WIDTH / 2 - 9 * GRID_WIDTH, MAZE_HEIGHT / 2 - 7 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 14 * GRID_WIDTH, MAZE_HEIGHT / 2 - 7 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 15 * GRID_WIDTH, MAZE_HEIGHT / 2 - 7 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 17 * GRID_WIDTH, MAZE_HEIGHT / 2 - 7 * GRID_HEIGHT)),
    # Row 8
    ((MAZE_WIDTH / 2 - 10 * GRID_WIDTH, MAZE_HEIGHT / 2 - 8 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 13 * GRID_WIDTH, MAZE_HEIGHT / 2 - 8 * GRID_HEIGHT)),
    # Row 9
    ((MAZE_WIDTH / 2 - 3 * GRID_WIDTH, MAZE_HEIGHT / 2 - 9 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 4 * GRID_WIDTH, MAZE_HEIGHT / 2 - 9 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 6 * GRID_WIDTH, MAZE_HEIGHT / 2 - 9 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 7 * GRID_WIDTH, MAZE_HEIGHT / 2 - 9 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 10 * GRID_WIDTH, MAZE_HEIGHT / 2 - 9 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 12 * GRID_WIDTH, MAZE_HEIGHT / 2 - 9 * GRID_HEIGHT)),
    # Row 10
    ((MAZE_WIDTH / 2 - 5 * GRID_WIDTH, MAZE_HEIGHT / 2 - 10 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 10 * GRID_WIDTH, MAZE_HEIGHT / 2 - 10 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 14 * GRID_WIDTH, MAZE_HEIGHT / 2 - 10 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 15 * GRID_WIDTH, MAZE_HEIGHT / 2 - 10 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 16 * GRID_WIDTH, MAZE_HEIGHT / 2 - 10 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 17 * GRID_WIDTH, MAZE_HEIGHT / 2 - 10 * GRID_HEIGHT)),
    # Row 11
    ((MAZE_WIDTH / 2 - 2 * GRID_WIDTH, MAZE_HEIGHT / 2 - 11 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 3 * GRID_WIDTH, MAZE_HEIGHT / 2 - 11 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 4 * GRID_WIDTH, MAZE_HEIGHT / 2 - 11 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 5 * GRID_WIDTH, MAZE_HEIGHT / 2 - 11 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 8 * GRID_WIDTH, MAZE_HEIGHT / 2 - 11 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 10 * GRID_WIDTH, MAZE_HEIGHT / 2 - 11 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 15 * GRID_WIDTH, MAZE_HEIGHT / 2 - 11 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 16 * GRID_WIDTH, MAZE_HEIGHT / 2 - 11 * GRID_HEIGHT)),
    # Row 12-17
    ((MAZE_WIDTH / 2 - GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 5 * GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 8 * GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 9 * GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 10 * GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 12 * GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 13 * GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 14 * GRID_WIDTH, MAZE_HEIGHT / 2 - 12 * GRID_HEIGHT)),
    # Row 13
    ((MAZE_WIDTH / 2 - GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 3 * GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 7 * GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 8 * GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 11 * GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 13 * GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 14 * GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 15 * GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 16 * GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 17 * GRID_WIDTH, MAZE_HEIGHT / 2 - 13 * GRID_HEIGHT)),
    # Row 14-17
    ((MAZE_WIDTH / 2 - 2 * GRID_WIDTH, MAZE_HEIGHT / 2 - 14 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 3 * GRID_WIDTH, MAZE_HEIGHT / 2 - 14 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 8 * GRID_WIDTH, MAZE_HEIGHT / 2 - 14 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 11 * GRID_WIDTH, MAZE_HEIGHT / 2 - 14 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 12 * GRID_WIDTH, MAZE_HEIGHT / 2 - 14 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 15 * GRID_WIDTH, MAZE_HEIGHT / 2 - 14 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 16 * GRID_WIDTH, MAZE_HEIGHT / 2 - 14 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 17 * GRID_WIDTH, MAZE_HEIGHT / 2 - 14 * GRID_HEIGHT)),
    # Row 15-17 (last rows)
    ((MAZE_WIDTH / 2 - 7 * GRID_WIDTH, MAZE_HEIGHT / 2 - 15 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 11 * GRID_WIDTH, MAZE_HEIGHT / 2 - 15 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 13 * GRID_WIDTH, MAZE_HEIGHT / 2 - 15 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 14 * GRID_WIDTH, MAZE_HEIGHT / 2 - 15 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 6 * GRID_WIDTH, MAZE_HEIGHT / 2 - 16 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 10 * GRID_WIDTH, MAZE_HEIGHT / 2 - 16 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - GRID_WIDTH, MAZE_HEIGHT / 2 - 17 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 3 * GRID_WIDTH, MAZE_HEIGHT / 2 - 17 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 4 * GRID_WIDTH, MAZE_HEIGHT / 2 - 17 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 12 * GRID_WIDTH, MAZE_HEIGHT / 2 - 17 * GRID_HEIGHT)),
    ((MAZE_WIDTH / 2 - 13 * GRID_WIDTH, MAZE_HEIGHT / 2 - 17 * GRID_HEIGHT),
     (MAZE_WIDTH / 2 - 17 * GRID_WIDTH, MAZE_HEIGHT / 2 - 17 * GRID_HEIGHT))
]

# Create walls from segments
walls = []
for segment in maze_segments:
    start_point = (segment[0][0] + WIDTH / 2, segment[0][1] + HEIGHT / 2)
    end_point = (segment[1][0] + WIDTH / 2, segment[1][1] + HEIGHT / 2)
    walls.append(Wall(start_point, end_point))

# Create hole
hole = Hole(WIDTH / 2 - 0.5 * GRID_WIDTH, HEIGHT / 2 - 1.5 * GRID_HEIGHT)

# Create ball at starting position
ball = Ball((WIDTH - MAZE_WIDTH) / 2 + MAZE_WIDTH - 17.5, (HEIGHT - (HEIGHT - MAZE_HEIGHT) / 2 - 20))


# Collision handler class
class ContactListener(Box2D.b2ContactListener):
    """
    Box2D contact listener for handling collision events.

    This can be extended to handle special collision effects,
    sounds, or gameplay mechanics when objects interact.
    """

    def __init__(self):
        """Initialize the contact listener."""
        Box2D.b2ContactListener.__init__(self)

    def BeginContact(self, contact):
        """
        Called when two fixtures begin to touch.

        Args:
            contact (Box2D.b2Contact): Contact object with information about the collision
        """
        # We can handle special collision effects here
        pass

    def EndContact(self, contact):
        """
        Called when two fixtures cease to touch.

        Args:
            contact (Box2D.b2Contact): Contact object with information about the collision
        """
        pass

    def PreSolve(self, contact, oldManifold):
        """
        Called before collision resolution.

        Args:
            contact (Box2D.b2Contact): Contact object
            oldManifold: Previous collision manifold
        """
        pass

    def PostSolve(self, contact, impulse):
        """
        Called after collision resolution.

        Args:
            contact (Box2D.b2Contact): Contact object
            impulse: Collision impulse data
        """
        # We can check collision impulses here for audio feedback
        pass


# Set up collision listener
contact_listener = ContactListener()
world.contactListener = contact_listener

# Game state variables
angle = 0
prev_angle = 0  # Store previous angle
angular_velocity = 0
max_angular_velocity = 10
game_over = False
start_time = pygame.time.get_ticks()
completion_time = 0  # Store the completion time when game is over

# Camera variables for zooming and panning
zoom = 1.0
offset_x = WIDTH / 2
offset_y = HEIGHT / 2

# Mouse drag variables
mouse_drag_start_x = 0
is_dragging = False
drag_sensitivity = 0.03  # Controls how responsive the rotation is to drag distance

# Create background gradient
background = create_gradient_surface(WIDTH, HEIGHT, (235, 244, 254), (208, 228, 254))

# Load fonts
try:
    title_font = pygame.font.SysFont('Arial', 50)
    stats_font = pygame.font.SysFont('Arial', 20)
    help_font = pygame.font.SysFont('Arial', 20)
except:
    # Fallback to default font if custom fonts fail to load
    title_font = pygame.font.Font(None, 50)
    stats_font = pygame.font.Font(None, 20)
    help_font = pygame.font.Font(None, 20)

# Main game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Start dragging and record the starting position
            is_dragging = True
            mouse_drag_start_x, mouse_drag_start_y = event.pos
            angular_velocity = 0  # Reset velocity when starting new drag
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # Stop dragging
            is_dragging = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 4:  # Mouse wheel up
            # Zoom in
            zoom = min(zoom * 1.1, 2.0)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 5:  # Mouse wheel down
            # Zoom out
            zoom = max(zoom / 1.1, 0.5)

    # Calculate angular velocity based on drag distance if dragging
    if is_dragging:
        current_mouse_x, current_mouse_y = pygame.mouse.get_pos()
        delta_x = current_mouse_x - mouse_drag_start_x
        delta_y = current_mouse_y - mouse_drag_start_y
        
        # Calculate drag distance
        drag_distance = math.sqrt(delta_x**2 + delta_y**2)
        
        # Get maze center
        maze_center_x, maze_center_y = maze_center
        
        # Calculate vectors from maze center to drag start and current position
        start_vector_x = mouse_drag_start_x - maze_center_x
        start_vector_y = mouse_drag_start_y - maze_center_y
        current_vector_x = current_mouse_x - maze_center_x
        current_vector_y = current_mouse_y - maze_center_y
        
        # Calculate the angle between these vectors
        # This gives us the rotation angle
        start_angle = math.atan2(start_vector_y, start_vector_x)
        current_angle = math.atan2(current_vector_y, current_vector_x)
        angle_diff = current_angle - start_angle
        
        # Normalize angle difference to be between -pi and pi
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        elif angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        
        # Calculate angular velocity based on angle difference and drag distance
        # The drag distance affects how fast the rotation happens
        angular_velocity = angle_diff * drag_sensitivity
        
        # Cap at maximum velocity
        angular_velocity = max(min(angular_velocity, max_angular_velocity), -max_angular_velocity)
    else:
        # Gradually reduce velocity when not dragging (simulates friction)
        angular_velocity *= 0.1  # Smooth deceleration

    # Update maze rotation
    prev_angle = angle  # Store previous angle
    angle += angular_velocity
    angle_diff = angular_velocity  # Difference since last frame

    # Rotate maze walls and hole
    maze_center = (WIDTH / 2, HEIGHT / 2)
    for wall in walls:
        wall.rotate(angle, maze_center)
    hole.rotate(angle, maze_center)
    hole.update()  # Update hole animation

    # Rotate ball with maze before physics step
    if not game_over:
        ball.rotate_with_maze(angle_diff, maze_center)

    # Step Box2D physics simulation
    world.Step(TIME_STEP, VELOCITY_ITERATIONS, POSITION_ITERATIONS)
    world.ClearForces()  # Important to clear forces after each step

    # Update game objects and check win condition
    if not game_over:
        new_game_over = ball.update(None, walls, hole, angle)
        if new_game_over and not game_over:
            # First frame when game is completed - record the completion time
            completion_time = (pygame.time.get_ticks() - start_time) / 1000
        game_over = new_game_over

    # -------------------------
    # Rendering section
    # -------------------------

    # Draw background
    screen.blit(background, (0, 0))

    # Create a semi-transparent surface for drawing the maze with shadows
    maze_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # Draw maze components on the surface
    for wall in walls:
        wall.draw(maze_surface, zoom, offset_x - WIDTH / 2, offset_y - HEIGHT / 2)
    hole.draw(maze_surface, zoom, offset_x - WIDTH / 2, offset_y - HEIGHT / 2)
    ball.draw(maze_surface, zoom, offset_x - WIDTH / 2, offset_y - HEIGHT / 2)

    # Apply the maze surface to the screen
    screen.blit(maze_surface, (0, 0))

    # -------------------------
    # UI Elements
    # -------------------------

    # Draw UI panel with stats at the top
    panel_height = 100
    panel_surface = pygame.Surface((WIDTH, panel_height), pygame.SRCALPHA)
    panel_surface.fill((41, 50, 65, 160))  # Semi-transparent dark blue

    # Add decorative line at the bottom of the panel
    pygame.draw.line(panel_surface, LIGHT_BLUE, (0, panel_height - 1), (WIDTH, panel_height - 1), 2)

    # Display game title
    title_text = title_font.render("MARBLE MAZE", True, WHITE)
    title_rect = title_text.get_rect(midtop=(WIDTH / 2, 5))
    panel_surface.blit(title_text, title_rect)

    # Display physics information
    velocity = ball.body.linearVelocity
    speed = math.sqrt(velocity.x * velocity.x + velocity.y * velocity.y) * PPM

    # Format texts with nice colors
    speed_text = stats_font.render(f"Speed: {speed:.1f} px/s", True, LIGHT_BLUE)
    panel_surface.blit(speed_text, (20, 70))

    angular_text = stats_font.render(f"Rotation: {ball.body.angularVelocity:.1f} rad/s", True, ORANGE)
    panel_surface.blit(angular_text, (175, 70))

    # Display time elapsed - only update if game isn't over
    if not game_over:
        elapsed_time = (pygame.time.get_ticks() - start_time) / 1000
    else:
        elapsed_time = completion_time
    time_text = stats_font.render(f"Time: {elapsed_time:.1f}s", True, PINK)
    panel_surface.blit(time_text, (350, 70))

    # Help text
    help_text = help_font.render("Drag to tilt | Mousewheel to zoom", True, WHITE)
    help_rect = help_text.get_rect(bottomright=(WIDTH - 20, panel_height - 5))
    panel_surface.blit(help_text, help_rect)

    # Apply the UI panel to the screen
    screen.blit(panel_surface, (0, 0))

    # -------------------------
    # Game Over State
    # -------------------------

    if game_over:
        # Create semi-transparent overlay with gradient
        overlay = create_gradient_surface(WIDTH, HEIGHT, (255, 255, 255, 200), (200, 230, 255, 200))
        screen.blit(overlay, (0, 0))

        # Create victory panel
        victory_panel = pygame.Surface((400, 300), pygame.SRCALPHA)
        victory_panel.fill((41, 50, 65, 220))

        # Add rounded corners and border effect
        pygame.draw.rect(victory_panel, LIGHT_BLUE, (0, 0, 400, 300), 3, border_radius=15)

        # Display victory message with shadow effect
        victory_font = pygame.font.Font(None, 48)
        shadow_text = victory_font.render("Congratulations!", True, BLACK)
        text = victory_font.render("Congratulations!", True, PINK)
        shadow_rect = shadow_text.get_rect(midtop=(202, 32))
        text_rect = text.get_rect(midtop=(200, 30))
        victory_panel.blit(shadow_text, shadow_rect)
        victory_panel.blit(text, text_rect)

        # Display "You Won!" text
        won_text = victory_font.render("You Won!", True, WHITE)
        won_rect = won_text.get_rect(midtop=(200, 80))
        victory_panel.blit(won_text, won_rect)

        # Draw decorative line
        pygame.draw.line(victory_panel, LIGHT_BLUE, (50, 130), (350, 130), 2)

        # Display completion time with fancy formatting
        time_label = stats_font.render("Your Time:", True, LIGHT_BLUE)
        time_text = title_font.render(f"{completion_time:.1f}s", True, WHITE)
        victory_panel.blit(time_label, (150, 150))
        time_rect = time_text.get_rect(center=(200, 190))
        victory_panel.blit(time_text, time_rect)

        # Display restart instructions with pulsing effect
        pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) * 0.5  # Value between 0 and 1
        restart_color = (
            int(WHITE[0] * pulse + ORANGE[0] * (1 - pulse)),
            int(WHITE[1] * pulse + ORANGE[1] * (1 - pulse)),
            int(WHITE[2] * pulse + ORANGE[2] * (1 - pulse))
        )
        restart_font = pygame.font.Font(None, 36)
        restart_text = restart_font.render("Press SPACE to play again", True, restart_color)
        restart_rect = restart_text.get_rect(midbottom=(200, 270))
        victory_panel.blit(restart_text, restart_rect)

        # Position and display the victory panel
        panel_rect = victory_panel.get_rect(center=(WIDTH / 2, HEIGHT / 2))
        screen.blit(victory_panel, panel_rect)

        # Handle restart
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            # Destroy all Box2D bodies first
            world.DestroyBody(ball.body)
            world.DestroyBody(hole.body)
            for wall in walls:
                world.DestroyBody(wall.body)

            # Recreate world and bodies
            world = b2World(gravity=(0, 6), doSleep=True)
            world.contactListener = contact_listener

            # Rebuild all game objects
            walls = []
            for segment in maze_segments:
                start_point = (segment[0][0] + WIDTH / 2, segment[0][1] + HEIGHT / 2)
                end_point = (segment[1][0] + WIDTH / 2, segment[1][1] + HEIGHT / 2)
                walls.append(Wall(start_point, end_point))

            # Create new hole and ball
            hole = Hole(WIDTH / 2 - 0.5 * GRID_WIDTH, HEIGHT / 2 - 1.5 * GRID_HEIGHT)
            ball = Ball((WIDTH - MAZE_WIDTH) / 2 + MAZE_WIDTH - 17.5, (HEIGHT - (HEIGHT - MAZE_HEIGHT) / 2 - 20))

            game_over = False
            angle = 0
            angular_velocity = 0
            start_time = pygame.time.get_ticks()

    # Update display
    pygame.display.flip()

    # Cap frame rate
    clock.tick(FPS)

pygame.quit()