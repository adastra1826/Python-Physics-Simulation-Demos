import pygame
import pymunk
import pygame_gui
import random
import time
import numpy as np

# ---------------------------------------------------
# Configuration
# ---------------------------------------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 960
UI_HEIGHT = 100
MAZE_WIDTH, MAZE_HEIGHT = SCREEN_WIDTH, SCREEN_HEIGHT - UI_HEIGHT
CELL_SIZE = 64
FPS = 60

BALL_RADIUS = 10
POLE_RADIUS = 10
WALL_THICKNESS = 4

# Inverse-square magnet parameters:
FIELD_STRENGTH = 600000   # Increased base strength for a stronger effect at distance.
FIELD_CUTOFF = 500        # No magnetic effect beyond this distance

# Stability limits:
MAX_FORCE = 7500          # Cap net force for stability.
MAX_VELOCITY = 500

# Disable built-in damping/friction; we use our own constant kinetic friction.
DAMPING = 1.0             # 1.0 means no extra damping in Pymunk.
FRICTION = 0.0            # We'll override shape friction.
KINETIC_FRICTION_FORCE = 50.0  # Constant friction force opposing motion.

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
REPEL_COLOR = (255, 80, 80)  # Red for repel magnets.
ATTRACT_COLOR = (50, 200, 255)  # Blue for attract magnets.
OFF_COLOR = (180, 180, 180)     # Gray for inactive magnets.
GOAL_COLOR = (100, 255, 100)
BALL_COLOR = (50, 50, 50)
TRAIL_COLOR = (0, 0, 0)

# Colors for force-vector drawing.
FORCE_COLOR_INDIVIDUAL = (255, 165, 0)  # Orange for individual forces.
FORCE_COLOR_NET = (255, 0, 0)           # Red for net force.

# Magnet states
OFF, ATTRACT, REPEL = 0, 1, 2

# Initialize a font for labeling.
pygame.font.init()
FONT = pygame.font.SysFont("Arial", 14)


# ---------------------------------------------------
# MagneticPole Class
# ---------------------------------------------------
class MagneticPole:
    def __init__(self, x, y):
        """
        Initialize a magnetic pole at position (x, y).
        The pole's state cycles among:
          OFF (inactive), REPEL (red), and ATTRACT (blue).
        """
        self.pos = pymunk.Vec2d(x, y)
        self.state = OFF

    def toggle(self):
        """Cycle the magnet's state: OFF -> REPEL -> ATTRACT -> OFF."""
        self.state = (self.state + 1) % 3

    def get_force_on(self, ball_pos):
        """
        Compute the magnetic force exerted on a ball at ball_pos using an inverse-square law.
        If the magnet is OFF or the ball is beyond FIELD_CUTOFF, returns zero.
        
        For an ATTRACT magnet, the force pulls the ball toward the magnet.
        For a REPEL magnet, the force pushes the ball away.
        
        The magnitude is given by:
          F = FIELD_STRENGTH / (distance^2)
        with the distance clamped to a minimum value to avoid singularities.
        """
        if self.state == OFF:
            return pymunk.Vec2d(0, 0)
        vec = ball_pos - self.pos  # Vector from magnet to ball.
        dist = vec.length
        if dist > FIELD_CUTOFF:
            return pymunk.Vec2d(0, 0)
        dist = max(dist, 5.0)
        force_magnitude = FIELD_STRENGTH / (dist * dist)
        direction = vec.normalized()
        if self.state == REPEL:
            force = force_magnitude * direction  # Push away from magnet
        else:  # ATTRACT
            force = -force_magnitude * direction  # Pull toward magnet
        return force


# ---------------------------------------------------
# BallBearing Class
# ---------------------------------------------------
class BallBearing:
    def __init__(self, space, pos):
        """
        Create a dynamic ball-bearing with physical properties.
        The ball's trail is stored for visualization.
        """
        mass = 1
        moment = pymunk.moment_for_circle(mass, 0, BALL_RADIUS)
        self.body = pymunk.Body(mass, moment)
        self.body.position = pos
        self.body.velocity_func = self.limit_velocity
        self.shape = pymunk.Circle(self.body, BALL_RADIUS)
        self.shape.elasticity = 0.8
        self.shape.friction = FRICTION
        space.add(self.body, self.shape)
        self.trail = []  # Stores (x, y) positions.

    def limit_velocity(self, body, gravity, damping, dt):
        """
        Custom velocity update that:
          - Ignores gravity (we want top-down motion).
          - Uses our DAMPING value.
          - Clamps the velocity to MAX_VELOCITY.
        """
        pymunk.Body.update_velocity(body, (0, 0), DAMPING, dt)
        if body.velocity.length > MAX_VELOCITY:
            body.velocity = body.velocity.normalized() * MAX_VELOCITY

    def update_trail(self):
        """Append the current ball position to the trail."""
        self.trail.append(self.body.position.int_tuple)
        if len(self.trail) > 300:
            self.trail.pop(0)


# ---------------------------------------------------
# Maze Generation
# ---------------------------------------------------
def generate_maze(cols, rows):
    """
    Generate a maze grid using DFS with backtracking.
    Each cell starts with four walls; walls are removed to create a path.
    
    Returns a 2D list of dictionaries representing cell walls.
    """
    grid = [[{"top": True, "bottom": True, "left": True, "right": True}
             for _ in range(rows)] for _ in range(cols)]
    stack = [(0, 0)]
    visited = [[False] * rows for _ in range(cols)]
    visited[0][0] = True

    def neighbors(x, y):
        n = []
        if x > 0: n.append((x - 1, y))
        if x < cols - 1: n.append((x + 1, y))
        if y > 0: n.append((x, y - 1))
        if y < rows - 1: n.append((x, y + 1))
        random.shuffle(n)
        return n

    while stack:
        x, y = stack[-1]
        for nx, ny in neighbors(x, y):
            if not visited[nx][ny]:
                if nx == x and ny == y + 1:
                    grid[x][y]["bottom"] = False
                    grid[nx][ny]["top"] = False
                elif nx == x and ny == y - 1:
                    grid[x][y]["top"] = False
                    grid[nx][ny]["bottom"] = False
                elif nx == x + 1 and ny == y:
                    grid[x][y]["right"] = False
                    grid[nx][ny]["left"] = False
                elif nx == x - 1 and ny == y:
                    grid[x][y]["left"] = False
                    grid[nx][ny]["right"] = False
                visited[nx][ny] = True
                stack.append((nx, ny))
                break
        else:
            stack.pop()
    return grid


# ---------------------------------------------------
# Game Class
# ---------------------------------------------------
class Game:
    def __init__(self):
        """
        Initialize the game:
         - Set up Pygame display and clock.
         - Create a Pymunk physics space with no gravity and disabled sleeping.
         - Initialize UI elements using pygame_gui.
         - Build the maze (walls and magnetic poles) and spawn the ball.
         - Prepare data structures for force-vector visualization.
        """
        pygame.init()
        pygame.display.set_caption("Magnetic Maze - Inverse-Square & Constant Friction")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))

        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        self.space.sleep_time_threshold = float('inf')

        self.cols = MAZE_WIDTH // CELL_SIZE
        self.rows = MAZE_HEIGHT // CELL_SIZE

        self.static_lines = []  # Maze walls for rendering.
        self.poles = []         # Magnetic poles in the maze.

        # UI Elements.
        self.slider_label = pygame_gui.elements.UILabel(
            pygame.Rect(20, 0, 100, 20), "Initial Speed", self.manager)
        self.slider = pygame_gui.elements.UIHorizontalSlider(
            pygame.Rect(20, 20, 200, 25), 300, (100, 600), self.manager)
        self.launch_btn = pygame_gui.elements.UIButton(
            pygame.Rect(240, 20, 80, 25), "Launch", self.manager)
        self.reset_btn = pygame_gui.elements.UIButton(
            pygame.Rect(330, 20, 80, 25), "Reset", self.manager)
        self.newmaze_btn = pygame_gui.elements.UIButton(
            pygame.Rect(420, 20, 100, 25), "New Maze", self.manager)
        self.instructions = pygame_gui.elements.UILabel(
            pygame.Rect((550, 5), (460, 80)),
            "🧲 Magnet Controls:\nGrey = Off | Blue = Attract | Red = Repel\nClick magnets to toggle.",
            self.manager
        )
        self.time_label = pygame_gui.elements.UILabel(
            pygame.Rect((20, 55), (150, 30)),
            "Time: 0.00s",
            self.manager
        )

        self.start_time = None
        self.win_shown = False
        self.ball = None
        self.goal_pos = None
        self.ball_active = False
        self.running = True

        # Data for visualizing force vectors.
        self.individual_forces = []
        self.net_force = pymunk.Vec2d(0, 0)

        self.build_maze()

    def build_maze(self):
        """
        Build (or rebuild) the maze:
         - Remove any existing wall segments.
         - Generate a new maze grid.
         - Create wall segments and place magnetic poles (in every other cell).
         - Create boundary walls.
         - Spawn a new ball and define the goal position.
        """
        for s in self.space.shapes[:]:
            if isinstance(s, pymunk.Segment):
                self.space.remove(s)
        self.static_lines.clear()
        self.poles.clear()

        self.maze = generate_maze(self.cols, self.rows)
        for x in range(self.cols):
            for y in range(self.rows):
                cell = self.maze[x][y]
                cx, cy = x * CELL_SIZE, y * CELL_SIZE + UI_HEIGHT
                if cell["top"]:
                    self._add_wall((cx, cy), (cx + CELL_SIZE, cy))
                if cell["left"]:
                    self._add_wall((cx, cy), (cx, cy + CELL_SIZE))
                if cell["bottom"]:
                    self._add_wall((cx, cy + CELL_SIZE), (cx + CELL_SIZE, cy + CELL_SIZE))
                if cell["right"]:
                    self._add_wall((cx + CELL_SIZE, cy), (cx + CELL_SIZE, cy + CELL_SIZE))
                if (x + y) % 2 == 0:
                    self.poles.append(MagneticPole(cx + CELL_SIZE // 2, cy + CELL_SIZE // 2))
        # Boundary walls
        self._add_wall((0, UI_HEIGHT), (SCREEN_WIDTH, UI_HEIGHT))
        self._add_wall((0, SCREEN_HEIGHT), (SCREEN_WIDTH, SCREEN_HEIGHT))
        self._add_wall((0, UI_HEIGHT), (0, SCREEN_HEIGHT))
        self._add_wall((SCREEN_WIDTH, UI_HEIGHT), (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.spawn_ball()
        self.goal_pos = pymunk.Vec2d(SCREEN_WIDTH - CELL_SIZE // 2, SCREEN_HEIGHT - CELL_SIZE // 2)

    def _add_wall(self, start, end):
        """
        Create a static wall segment in the physics space and store it for rendering.
        """
        seg = pymunk.Segment(self.space.static_body, start, end, WALL_THICKNESS)
        seg.elasticity = 0.8
        seg.friction = 0.5
        self.space.add(seg)
        self.static_lines.append((start, end))

    def spawn_ball(self):
        """
        Remove any existing ball and spawn a new one at the maze start.
        """
        if self.ball:
            self.space.remove(self.ball.body, self.ball.shape)
        self.ball = BallBearing(self.space, (CELL_SIZE // 2, UI_HEIGHT + CELL_SIZE // 2))
        self.ball.body.sleeping_allowed = False
        self.ball_active = False
        self.start_time = None
        self.win_shown = False

    def apply_forces(self):
        """
        Calculate and apply the net force on the ball:
          - Uses NumPy to vectorize the calculation from all magnetic poles.
          - Each active magnet contributes a force following the inverse-square law.
          - A constant kinetic friction force opposes the ball's velocity.
          - The net force is capped to MAX_FORCE.
          - The computed individual forces and net force are stored for visualization.
        """
        if not self.ball_active:
            self.net_force = pymunk.Vec2d(0, 0)
            self.individual_forces = []
            return

        ball_pos = self.ball.body.position
        ball_np = np.array([ball_pos.x, ball_pos.y])
        magnet_positions = np.array([[pole.pos.x, pole.pos.y] for pole in self.poles])
        magnet_states = np.array([pole.state for pole in self.poles])
        vecs = ball_np - magnet_positions  # shape (N, 2)
        dists = np.linalg.norm(vecs, axis=1)
        active_mask = (magnet_states != OFF) & (dists < FIELD_CUTOFF)
        dists_clamped = np.maximum(dists, 5.0)
        force_magnitudes = FIELD_STRENGTH / (dists_clamped ** 2)
        directions = np.divide(vecs, dists_clamped[:, None], out=np.zeros_like(vecs), where=dists_clamped[:, None]!=0)
        forces = np.zeros_like(vecs)
        attract_mask = active_mask & (magnet_states == ATTRACT)
        forces[attract_mask] = -(force_magnitudes[attract_mask][:, None] * directions[attract_mask])
        repel_mask = active_mask & (magnet_states == REPEL)
        forces[repel_mask] = (force_magnitudes[repel_mask][:, None] * directions[repel_mask])
        net_force_np = np.sum(forces, axis=0)
        net_force = pymunk.Vec2d(net_force_np[0], net_force_np[1])
        individual_forces = []
        for i in range(len(forces)):
            if active_mask[i]:
                fvec = pymunk.Vec2d(forces[i][0], forces[i][1])
                individual_forces.append(fvec)
        vel = self.ball.body.velocity
        if vel.length > 1e-5:
            friction_force = -vel.normalized() * KINETIC_FRICTION_FORCE
            net_force += friction_force
            individual_forces.append(friction_force)
        if net_force.length > MAX_FORCE:
            net_force = net_force.normalized() * MAX_FORCE

        self.ball.body.apply_force_at_local_point(net_force)
        self.net_force = net_force
        self.individual_forces = individual_forces

    def update(self, dt):
        """
        Update the simulation:
          - Process UI updates.
          - If the ball is active, apply forces and step the physics simulation with substeps.
          - Check if the goal is reached.
        """
        self.manager.update(dt)
        if self.ball_active:
            if self.start_time is not None and not self.win_shown:
                elapsed = time.time() - self.start_time
                self.time_label.set_text(f"Time: {elapsed:.2f}s")
            self.apply_forces()
            self.ball.update_trail()
            substeps = 4
            for _ in range(substeps):
                self.space.step((1 / FPS) / substeps)
            if not self.win_shown and (self.ball.body.position - self.goal_pos).length < 25:
                self.win_shown = True
                elapsed = time.time() - self.start_time
                # Corrected call: HTML message is second argument, followed by manager.
                pygame_gui.windows.UIMessageWindow(
                    pygame.Rect((SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 100), (300, 200)),
                    f"You reached the goal in <b>{elapsed:.2f} seconds!</b>",
                    self.manager,
                    window_title="🎉 Goal Reached!"
                )

    def draw(self):
        """
        Render the scene:
          - Draw background, walls, goal, ball trail, ball, and magnets.
          - Visualize force vectors (individual and net).
          - Annotate active magnets with force magnitude.
        """
        self.screen.fill(WHITE)
        for start, end in self.static_lines:
            pygame.draw.line(self.screen, BLACK, start, end, WALL_THICKNESS)
        pygame.draw.circle(self.screen, GOAL_COLOR, self.goal_pos.int_tuple, 20)
        if len(self.ball.trail) > 1:
            trail_arr = np.array(self.ball.trail, dtype=np.int32)
            pygame.draw.lines(self.screen, TRAIL_COLOR, False, trail_arr.tolist(), 2)
        pygame.draw.circle(self.screen, BALL_COLOR, self.ball.body.position.int_tuple, BALL_RADIUS)
        for pole in self.poles:
            color = [OFF_COLOR, ATTRACT_COLOR, REPEL_COLOR][pole.state]
            pygame.draw.circle(self.screen, color, pole.pos.int_tuple, POLE_RADIUS)
            force = pole.get_force_on(self.ball.body.position)
            if force.length > 1e-3:
                label = FONT.render(f"{force.length:.0f}", True, BLACK)
                label_pos = (pole.pos.x + POLE_RADIUS, pole.pos.y - POLE_RADIUS)
                self.screen.blit(label, label_pos)
        ball_pos = self.ball.body.position
        for fvec in self.individual_forces:
            if fvec.length < 1e-3:
                continue
            scaled = fvec * 0.03  # Scale factor for visibility.
            start = ball_pos.int_tuple
            end = (ball_pos + scaled).int_tuple
            pygame.draw.line(self.screen, FORCE_COLOR_INDIVIDUAL, start, end, 2)
        if self.net_force.length > 1e-3:
            scaled_net = self.net_force * 0.03
            net_end = (ball_pos + scaled_net).int_tuple
            pygame.draw.line(self.screen, FORCE_COLOR_NET, ball_pos.int_tuple, net_end, 3)
        self.manager.draw_ui(self.screen)
        pygame.display.flip()

    def handle_events(self, dt):
        """
        Process input events:
          - Quit event.
          - Mouse clicks to toggle magnet state (only below the UI area).
          - UI button presses to launch/reset/build maze.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = pygame.mouse.get_pos()
                if pos[1] >= UI_HEIGHT:
                    for pole in self.poles:
                        if (pole.pos - pymunk.Vec2d(*pos)).length < POLE_RADIUS:
                            pole.toggle()

            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.launch_btn and not self.ball_active:
                    self.ball.body.velocity = (self.slider.get_current_value(), 0)
                    self.ball_active = True
                    self.start_time = time.time()
                elif event.ui_element == self.reset_btn:
                    self.spawn_ball()
                elif event.ui_element == self.newmaze_btn:
                    self.build_maze()
            self.manager.process_events(event)

    def run(self):
        """Main game loop: process events, update simulation, render scene."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events(dt)
            self.update(dt)
            self.draw()
        pygame.quit()


# ---------------------------------------------------
# Entry Point
# ---------------------------------------------------
if __name__ == "__main__":
    Game().run()
