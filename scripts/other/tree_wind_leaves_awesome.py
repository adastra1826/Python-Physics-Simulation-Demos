"""
Tree with Wind and Leaves Physics Simulation.

This simulation models the dynamics of a tree interacting with wind, including 
branch movements and leaf behaviors. It demonstrates principles of structural 
mechanics, fluid dynamics, and how forces propagate through connected systems.
The simulation shows how branches bend and sway under varying wind conditions,
how leaves are affected by both the wind directly and the movement of branches,
and how these complex interactions create the characteristic rustling and 
swaying patterns observed in real trees. The physics includes spring dynamics,
damping effects, and the interconnected nature of the tree's structure.

Autumn Tree Simulation - A calming physics-based visualization

This simulation creates a peaceful autumn scene with a procedurally generated tree
and falling leaves that respond to physics and wind. The scene includes a gradient sky,
rolling hills, and organic tree branches with leaves that fall naturally.

Controls:
    SPACE - Create a wind gust
    R - Reset/regenerate leaves
    Q - Quit the simulation
"""

import pygame
import random
import math
import sys

# Initialize pygame
pygame.init()

# Window dimensions
WIDTH, HEIGHT = 900, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Autumn Tree Simulation")

# Colors
WHITE = (255, 255, 255)
BROWN = (139, 69, 19)
DARK_BROWN = (101, 67, 33)
GREEN = (0, 128, 0)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GOLD = (255, 215, 0)
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (34, 139, 34)

# Autumn color palette
LEAF_COLORS = [
    (255, 69, 0),    # Red-Orange
    (255, 140, 0),   # Dark Orange
    (255, 165, 0),   # Orange
    (255, 215, 0),   # Gold
    (218, 165, 32),  # Goldenrod
    (210, 105, 30),  # Chocolate
    (178, 34, 34),   # Firebrick
    (139, 0, 0),     # Dark Red
]

# Physics constants
GRAVITY = 0.03  # Reduced gravity for slower falling
WIND_DAMPING = 0.98
BOUNCE_DAMPING = 0.6
MAX_WIND = 1.5
WIND_STEP = 0.2  # Step size for manual wind control

class Leaf:
    """
    Represents a leaf that can attach to the tree and fall with physics
    
    Attributes:
        x, y: Position coordinates
        attached: Whether the leaf is attached to the tree
        vel_x, vel_y: Velocity components
        spin: Rotation speed
        angle: Current rotation angle
        color: RGB color of the leaf
        size: Size of the leaf
        flutter: Random flutter factor for more natural movement
    """
    def __init__(self, x, y, attached=True):
        self.x = x
        self.y = y
        self.attached = attached
        self.vel_x = random.uniform(-0.3, 0.3)
        self.vel_y = random.uniform(-0.1, 0.1)
        self.spin = random.uniform(-1, 1)  # Slower rotation
        self.angle = random.uniform(0, 360)
        self.color = random.choice(LEAF_COLORS)
        self.size = random.uniform(5, 12)
        self.flutter = random.uniform(0.8, 1.2)
        self.detach_probability = random.uniform(0.0005, 0.002)  # Reduced chance to fall
        self.grounded = False
        # Add air resistance factor (higher = more resistance)
        self.air_resistance = random.uniform(0.92, 0.98)
    
    def update(self, wind_force):
        """
        Update leaf position and physics
        
        Args:
            wind_force: Current wind force affecting the leaf
        """
        if self.attached:
            # Random chance for leaf to detach
            if random.random() < self.detach_probability:
                self.attached = False
                self.vel_x = wind_force * random.uniform(0.5, 1.5)
        else:
            if not self.grounded:
                # Apply physics only if not grounded
                # Horizontal movement affected by wind
                self.vel_x += wind_force * self.flutter * 0.1
                # Apply gravity
                self.vel_y += GRAVITY
                
                # Simulate sideways flutter motion (left-right oscillation as they fall)
                self.vel_x += math.sin(pygame.time.get_ticks() * 0.001 * self.flutter) * 0.01
                
                # Add some randomness to simulate natural air currents
                random_flutter = random.uniform(-0.03, 0.03) * self.flutter
                self.vel_x += random_flutter
                self.vel_y += random_flutter * 0.3  # Less vertical randomness
                
                # Apply air resistance (terminal velocity)
                # Higher values for self.air_resistance mean more floating/drifting
                self.vel_x *= self.air_resistance
                self.vel_y *= self.air_resistance
                
                # Limit maximum falling speed for a more gentle descent
                max_fall_speed = 1.0
                if self.vel_y > max_fall_speed:
                    self.vel_y = max_fall_speed
                
                # Update position
                self.x += self.vel_x
                self.y += self.vel_y
                
                # Update rotation - slower, more gentle rotation
                self.angle += self.spin * (abs(wind_force) * 0.5 + 0.5)  # Wind affects rotation
                
                # Check for ground collision
                if self.y > HEIGHT - 50:
                    # Bounce with damping
                    self.y = HEIGHT - 50
                    self.vel_y = -self.vel_y * BOUNCE_DAMPING
                    
                    # Sometimes leaves come to rest
                    if abs(self.vel_y) < 0.3 and random.random() < 0.3:
                        self.grounded = True
                        self.vel_x = 0
                        self.vel_y = 0
                        self.spin = 0
                
                # Check for screen edges with gentle bounce
                if self.x < 0:
                    self.x = 0
                    self.vel_x = -self.vel_x * 0.5
                elif self.x > WIDTH:
                    self.x = WIDTH
                    self.vel_x = -self.vel_x * 0.5
    
    def draw(self, screen):
        """
        Draw the leaf on the screen
        
        Args:
            screen: Pygame screen surface to draw on
        """
        # Create a leaf shape using a transparent surface
        leaf_surface = pygame.Surface((self.size * 2, self.size), pygame.SRCALPHA)
        
        # Draw the leaf as an ellipse with a slight point at one end
        pygame.draw.ellipse(leaf_surface, self.color, (0, 0, self.size * 2, self.size))
        
        # Add a simple stem on the outside at one of the pointy ends
        stem_color = (DARK_BROWN[0], DARK_BROWN[1], DARK_BROWN[2], 200)
        # Draw stem at the left pointy end, extending outward
        pygame.draw.line(leaf_surface, stem_color, 
                         (self.size/2, self.size/2), (-self.size, self.size/2), 2)
        
        # Rotate and position
        rotated_leaf = pygame.transform.rotate(leaf_surface, self.angle)
        rect = rotated_leaf.get_rect(center=(self.x, self.y))
        screen.blit(rotated_leaf, rect)

class Branch:
    """
    Represents a branch of the tree with position and direction
    
    Attributes:
        start_pos: Starting position (x, y)
        end_pos: Ending position (x, y)
        thickness: Branch thickness
        angle: Branch angle in radians
        length: Branch length
        children: List of child branches
        leaves: List of leaves attached to this branch
    """
    def __init__(self, start_pos, angle, length, thickness):
        self.start_pos = start_pos
        self.angle = angle
        self.length = length
        self.thickness = thickness
        
        # Calculate end position
        end_x = start_pos[0] + math.cos(angle) * length
        end_y = start_pos[1] + math.sin(angle) * length
        self.end_pos = (end_x, end_y)
        
        self.children = []
        self.leaves = []
        self.original_end = self.end_pos  # Store original position for swaying
        self.sway_offset = 0
        self.sway_speed = random.uniform(0.02, 0.04)
    
    def generate_children(self, depth, branch_angle_var=0.3, length_factor=0.7):
        """
        Recursively generate child branches
        
        Args:
            depth: Current recursion depth
            branch_angle_var: Variation in branch angles
            length_factor: Factor to reduce length for child branches
        """
        if depth <= 0:
            return
        
        # Number of branches increases with depth to create denser foliage at the ends
        num_branches = random.randint(2, 3) if depth > 2 else random.randint(1, 2)
        
        for i in range(num_branches):
            # Calculate new angle with variation
            angle_offset = random.uniform(-branch_angle_var, branch_angle_var)
            if i == 0:
                new_angle = self.angle + angle_offset - 0.2  # Tend left
            else:
                new_angle = self.angle + angle_offset + 0.2  # Tend right
            
            # Calculate new length with some variation
            new_length = self.length * length_factor * random.uniform(0.9, 1.1)
            
            # Calculate new thickness (decrease as we go deeper)
            new_thickness = max(1, self.thickness * 0.7)
            
            # Create new branch
            new_branch = Branch(self.end_pos, new_angle, new_length, new_thickness)
            self.children.append(new_branch)
            
            # Generate children for this branch
            new_branch.generate_children(depth - 1, branch_angle_var, length_factor)
            
            # Add leaves to end branches
            if depth <= 2:
                num_leaves = random.randint(3, 7)
                for _ in range(num_leaves):
                    leaf_x = new_branch.end_pos[0] + random.uniform(-10, 10)
                    leaf_y = new_branch.end_pos[1] + random.uniform(-10, 10)
                    new_branch.leaves.append(Leaf(leaf_x, leaf_y))
    
    def update_sway(self, time, wind_force):
        """
        Update the swaying motion of branches
        
        Args:
            time: Current time for oscillation
            wind_force: Current wind force affecting sway
        """
        # Sway amount depends on thickness (thinner branches sway more)
        sway_amount = (5 / self.thickness) * wind_force * 10
        
        # Calculate sway offset using sine function
        self.sway_offset = math.sin(time * self.sway_speed) * sway_amount
        
        # Apply sway to end position
        sway_angle = self.angle + math.pi/2  # Perpendicular to branch direction
        self.end_pos = (
            self.original_end[0] + math.cos(sway_angle) * self.sway_offset,
            self.original_end[1] + math.sin(sway_angle) * self.sway_offset
        )
        
        # Update children
        for child in self.children:
            child.start_pos = self.end_pos
            child.update_sway(time, wind_force * 1.2)  # Wind increases effect higher in tree
        
        # Update leaves
        for leaf in self.leaves:
            if leaf.attached:
                leaf_sway_x = math.cos(sway_angle) * self.sway_offset * 1.2
                leaf_sway_y = math.sin(sway_angle) * self.sway_offset * 1.2
                leaf.x = self.end_pos[0] + random.uniform(-1, 1) * (wind_force / MAX_WIND) + leaf_sway_x
                leaf.y = self.end_pos[1] + random.uniform(-1, 1) * (wind_force / MAX_WIND) + leaf_sway_y
    
    def draw(self, screen):
        """
        Draw the branch and its children
        
        Args:
            screen: Pygame screen surface to draw on
        """
        # Draw this branch
        pygame.draw.line(screen, BROWN, self.start_pos, self.end_pos, int(self.thickness))
        
        # Draw children
        for child in self.children:
            child.draw(screen)
        
        # Draw attached leaves
        for leaf in self.leaves:
            if leaf.attached:
                leaf.draw(screen)

class Tree:
    """
    Represents the entire tree with trunk, branches and leaves
    
    Attributes:
        x, y: Position of the tree base
        branches: List of all branches
        fallen_leaves: List of leaves that have fallen
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.branches = []
        self.fallen_leaves = []
        self.time = 0
        
        # Create the trunk
        trunk_length = random.uniform(120, 150)
        trunk_thickness = random.uniform(12, 16)
        trunk = Branch((x, y), -math.pi/2, trunk_length, trunk_thickness)  # Straight up
        self.branches.append(trunk)
        
        # Generate branches
        trunk.generate_children(5)  # 5 levels of branching
        
        # Get all leaves for easy access
        self.collect_all_leaves()
    
    def collect_all_leaves(self):
        """Collect references to all leaves from all branches"""
        self.all_leaves = []
        
        def collect_from_branch(branch):
            for leaf in branch.leaves:
                self.all_leaves.append(leaf)
            for child in branch.children:
                collect_from_branch(child)
        
        for branch in self.branches:
            collect_from_branch(branch)
    
    def update(self, wind_force):
        """
        Update tree state including branches and leaves
        
        Args:
            wind_force: Current wind force affecting the tree
        """
        self.time += 0.01
        
        # Update branch sway
        for branch in self.branches:
            branch.update_sway(self.time, wind_force)
        
        # Update all leaves
        for leaf in self.all_leaves:
            leaf.update(wind_force)
            
            # Move detached leaves to fallen_leaves list
            if not leaf.attached and leaf not in self.fallen_leaves:
                self.fallen_leaves.append(leaf)
        
        # Update fallen leaves
        for leaf in self.fallen_leaves:
            leaf.update(wind_force)
    
    def draw(self, screen):
        """
        Draw the entire tree including branches and leaves
        
        Args:
            screen: Pygame screen surface to draw on
        """
        # Draw fallen leaves first (on the ground)
        for leaf in self.fallen_leaves:
            if not leaf.attached:
                leaf.draw(screen)
        
        # Draw branches (which also draws attached leaves)
        for branch in self.branches:
            branch.draw(screen)

def draw_background(screen):
    """
    Draw the background with sky gradient and hills
    
    Args:
        screen: Pygame screen surface to draw on
    """
    # Sky gradient
    for y in range(HEIGHT):
        # Create gradient from light blue to darker blue
        blue_val = max(80, 235 - int((y / HEIGHT) * 100))
        color = (135, 206, blue_val)
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))
    
    # Draw hills in background
    hill_color1 = (34, 139, 34)  # Forest green
    hill_color2 = (85, 107, 47)  # Dark olive green
    
    # First hill
    points = [(0, HEIGHT)]
    for x in range(0, WIDTH + 50, 50):
        y_offset = math.sin(x * 0.01) * 50 + math.sin(x * 0.02) * 30
        points.append((x, HEIGHT - 150 + y_offset))
    points.append((WIDTH, HEIGHT))
    pygame.draw.polygon(screen, hill_color1, points)
    
    # Second hill (closer)
    points = [(0, HEIGHT)]
    for x in range(0, WIDTH + 30, 30):
        y_offset = math.sin(x * 0.02 + 1) * 40 + math.sin(x * 0.03) * 20
        points.append((x, HEIGHT - 80 + y_offset))
    points.append((WIDTH, HEIGHT))
    pygame.draw.polygon(screen, hill_color2, points)
    
    # Ground
    pygame.draw.rect(screen, GRASS_GREEN, (0, HEIGHT - 50, WIDTH, 50))

def draw_instructions(screen, font, wind_force, tree):
    """
    Draw instruction text overlay and data visualization
    
    Args:
        screen: Pygame screen surface to draw on
        font: Pygame font object for rendering text
        wind_force: Current wind force value
        tree: Tree object to get stats from
    """
    instructions = [
        "SPACE - Create wind gust",
        "LEFT/RIGHT - Decrease/Increase wind",
        "UP/DOWN - Fine wind adjustment",
        "R - Reset leaves",
        "D - Toggle data overlay",
        "Q - Quit"
    ]
    
    # Calculate needed height for background (instruction lines + wind display line)
    lines_count = len(instructions) + 1  # +1 for the wind display
    panel_height = 30 + (lines_count * 30)  # 30px top padding + height for each line
    
    # Draw semi-transparent background for text
    info_surface = pygame.Surface((380, panel_height), pygame.SRCALPHA)
    info_surface.fill((0, 0, 0, 128))
    screen.blit(info_surface, (10, 10))
    
    # Draw text
    for i, text in enumerate(instructions):
        text_surface = font.render(text, True, WHITE)
        screen.blit(text_surface, (20, 20 + i * 30))
    
    # Draw current wind force indicator
    wind_text = font.render(f"Current Wind: {wind_force:.2f}", True, 
                          (255, 255, 100) if abs(wind_force) > 0.5 else WHITE)
    screen.blit(wind_text, (20, 20 + len(instructions) * 30))

def draw_data_overlay(screen, font, wind_force, tree, time):
    """
    Draw real-time physics data overlays
    
    Args:
        screen: Pygame screen surface to draw on
        font: Pygame font object for rendering text
        wind_force: Current wind force value
        tree: Tree object to get stats from
        time: Current simulation time
    """
    # Data panel background
    panel_width = 280
    panel_height = 600
    data_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    data_surface.fill((20, 20, 50, 180))  # Dark blue, semi-transparent
    screen.blit(data_surface, (WIDTH - panel_width - 10, 10))
    
    # Title
    title_font = pygame.font.SysFont('Arial', 24, bold=True)
    title = title_font.render("Simulation Data", True, (220, 220, 255))
    screen.blit(title, (WIDTH - panel_width + 10, 20))
    
    # Data sections
    y_pos = 60
    section_spacing = 25
    
    # Physics data
    draw_section_title(screen, font, "Physics Parameters", WIDTH - panel_width + 10, y_pos)
    y_pos += 30
    
    physics_data = [
        f"Wind Force: {wind_force:.2f} N",
        f"Gravity: {GRAVITY:.2f} m/s²",
        f"Time: {time:.1f} s",
    ]
    
    for item in physics_data:
        text = font.render(item, True, WHITE)
        screen.blit(text, (WIDTH - panel_width + 20, y_pos))
        y_pos += section_spacing
    
    y_pos += 10
    
    # Leaf statistics
    draw_section_title(screen, font, "Leaf Statistics", WIDTH - panel_width + 10, y_pos)
    y_pos += 30
    
    # Count leaves
    attached_leaves = sum(1 for leaf in tree.all_leaves if leaf.attached)
    falling_leaves = len(tree.fallen_leaves)
    grounded_leaves = sum(1 for leaf in tree.fallen_leaves if leaf.grounded)
    
    leaf_data = [
        f"Total Leaves: {len(tree.all_leaves)}",
        f"Attached: {attached_leaves}",
        f"Falling: {falling_leaves - grounded_leaves}",
        f"Grounded: {grounded_leaves}"
    ]
    
    for item in leaf_data:
        text = font.render(item, True, WHITE)
        screen.blit(text, (WIDTH - panel_width + 20, y_pos))
        y_pos += section_spacing
    
    y_pos += 10
    
    # Wind graph
    draw_section_title(screen, font, "Wind Force Over Time", WIDTH - panel_width + 10, y_pos)
    y_pos += 30
    
    # Wind history graph
    graph_width = panel_width - 40
    graph_height = 80
    pygame.draw.rect(screen, (50, 50, 70), (WIDTH - panel_width + 20, y_pos, graph_width, graph_height))
    
    # Draw zero line
    zero_y = y_pos + graph_height // 2
    pygame.draw.line(screen, (100, 100, 100), 
                     (WIDTH - panel_width + 20, zero_y), 
                     (WIDTH - panel_width + 20 + graph_width, zero_y), 1)
    
    # Get wind data from global history
    if hasattr(draw_data_overlay, 'wind_history'):
        draw_data_overlay.wind_history.append(wind_force)
        # Keep only the most recent points
        if len(draw_data_overlay.wind_history) > graph_width:
            draw_data_overlay.wind_history.pop(0)
    else:
        draw_data_overlay.wind_history = [0] * 10  # Initialize with zeros
        draw_data_overlay.wind_history.append(wind_force)
    
    # Draw the wind graph
    max_wind = MAX_WIND * 1.2  # Allow some extra room
    points = []
    for i, w in enumerate(draw_data_overlay.wind_history):
        x = WIDTH - panel_width + 20 + i * (graph_width / len(draw_data_overlay.wind_history))
        y = zero_y - (w / max_wind) * (graph_height // 2)
        points.append((x, y))
    
    if len(points) > 1:
        pygame.draw.lines(screen, (100, 200, 255), False, points, 2)
    
    y_pos += graph_height + 20
    
    # Leaf velocity histogram
    draw_section_title(screen, font, "Leaf Velocity Distribution", WIDTH - panel_width + 10, y_pos)
    y_pos += 30
    
    # Create velocity buckets
    hist_width = panel_width - 40
    hist_height = 80
    pygame.draw.rect(screen, (50, 50, 70), (WIDTH - panel_width + 20, y_pos, hist_width, hist_height))
    
    # Get velocity data for falling leaves
    falling_velocities = [abs(leaf.vel_x) for leaf in tree.fallen_leaves 
                        if not leaf.grounded and not leaf.attached]
    
    # Create histogram buckets
    if falling_velocities:
        max_vel = max(max(falling_velocities), 1)
        buckets = [0] * 10
        
        for vel in falling_velocities:
            bucket_idx = min(int((vel / max_vel) * 9), 9)
            buckets[bucket_idx] += 1
        
        # Normalize buckets
        if max(buckets) > 0:
            buckets = [b / max(buckets) * hist_height for b in buckets]
            
            # Draw the histogram bars
            bar_width = hist_width / len(buckets)
            for i, height in enumerate(buckets):
                bar_x = WIDTH - panel_width + 20 + i * bar_width
                bar_y = y_pos + hist_height - height
                pygame.draw.rect(screen, (255, 165, 0), 
                                (bar_x, bar_y, bar_width - 2, height))
    
    # Draw x-axis labels
    min_label = font.render("0", True, WHITE)
    max_label = font.render(f"{max_vel:.1f} m/s", True, WHITE) if falling_velocities else font.render("5.0 m/s", True, WHITE)
    screen.blit(min_label, (WIDTH - panel_width + 20, y_pos + hist_height + 5))
    screen.blit(max_label, (WIDTH - panel_width + 20 + hist_width - 70, y_pos + hist_height + 5))

def draw_section_title(screen, font, title, x, y):
    """Helper function to draw section titles with consistent styling"""
    section_font = pygame.font.SysFont('Arial', 18, bold=True)
    title_text = section_font.render(title, True, (255, 220, 150))
    screen.blit(title_text, (x, y))

def main():
    """Main function to run the simulation"""
    # Setup
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Arial', 20)
    
    # Create tree in middle bottom of screen
    tree = Tree(WIDTH // 2, HEIGHT - 50)
    
    # Wind variables
    wind_force = 0
    target_wind = 0
    
    # Manual wind control
    manual_wind_control = False
    
    # Simulation time
    simulation_time = 0
    
    # Data overlay toggle
    show_data = True
    
    # Main loop
    running = True
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Create wind gust (random direction)
                    direction = 1 if random.random() > 0.5 else -1
                    target_wind = direction * random.uniform(0.5, MAX_WIND)
                    manual_wind_control = False
                elif event.key == pygame.K_RIGHT:
                    # Increase wind (right direction)
                    target_wind += WIND_STEP
                    manual_wind_control = True
                elif event.key == pygame.K_LEFT:
                    # Decrease wind (left direction)
                    target_wind -= WIND_STEP
                    manual_wind_control = True
                elif event.key == pygame.K_UP:
                    # Fine increase of wind (current direction)
                    if target_wind > 0:
                        target_wind += WIND_STEP * 0.25
                    else:
                        target_wind -= WIND_STEP * 0.25
                    manual_wind_control = True
                elif event.key == pygame.K_DOWN:
                    # Fine decrease of wind (current direction)
                    if target_wind > 0:
                        target_wind -= WIND_STEP * 0.25
                    else:
                        target_wind += WIND_STEP * 0.25
                    manual_wind_control = True
                elif event.key == pygame.K_r:
                    # Reset tree
                    tree = Tree(WIDTH // 2, HEIGHT - 50)
                    target_wind = 0
                    manual_wind_control = False
                elif event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_d:
                    # Toggle data overlay
                    show_data = not show_data
        
        # Limit wind to maximum
        target_wind = max(min(target_wind, MAX_WIND), -MAX_WIND)
        
        # Update wind (gradually approach target wind)
        wind_force = wind_force * 0.95 + target_wind * 0.05
        
        # Wind gradually dies down if not in manual control
        if not manual_wind_control:
            target_wind *= 0.99
            
            # Add some natural wind variation
            target_wind += random.uniform(-0.01, 0.01)
        
        # Update tree and leaves
        tree.update(wind_force)
        
        # Update simulation time
        simulation_time += 1/60  # Assuming 60 FPS
        
        # Drawing
        draw_background(screen)
        tree.draw(screen)
        draw_instructions(screen, font, wind_force, tree)
        
        # Draw data overlay if enabled
        if show_data:
            draw_data_overlay(screen, font, wind_force, tree, simulation_time)
        
        # Update display
        pygame.display.update()
        clock.tick(60)
    
    # Clean up
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()