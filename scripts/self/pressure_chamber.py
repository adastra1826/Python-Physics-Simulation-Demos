import pymunk
import pygame
import pymunk.pygame_util
import random
from collections import deque

# Constants for screen and chamber dimensions
WIDTH, HEIGHT = 800, 600
CHAMBER_X = WIDTH // 3
CHAMBER_Y = HEIGHT - HEIGHT // 7
CHAMBER_SCALE = WIDTH // 8
CHAMBER_WALL_WIDTH = CHAMBER_SCALE // 20
PARTICLE_RADIUS = CHAMBER_SCALE // 30

# Collision groups for different physics objects
PRESSURE_CHAMBER_COLLISION_GROUP = 1
PARTICLE_COLLISION_GROUP = 2
VALVE_COLLISION_GROUP = 3
VOID_COLLISION_GROUP = 4

# Simulation parameters
FPS = 60

class PressureChamber:
    """Simulates a pressure chamber with inlet/outlet valves and particle physics."""
    
    # Chamber geometry defined as relative coordinates
    # Each segment is defined by start point, end point, and collision group
    # Void collision group is used for the walls that are not part of the pressure chamber, to avoid them being used for the pressure calculation
    SEGMENTS = [
        [(0, 0), (2, 0), VOID_COLLISION_GROUP],
        [(2, 0), (5, 0), PRESSURE_CHAMBER_COLLISION_GROUP],
        [(5, 0), (5, -4), PRESSURE_CHAMBER_COLLISION_GROUP],
        [(5, -4), (4, -4), PRESSURE_CHAMBER_COLLISION_GROUP],
        [(4, -4), (4, -5), VOID_COLLISION_GROUP],
        [(3, -5), (3, -4), VOID_COLLISION_GROUP],
        [(3, -4), (2, -4), PRESSURE_CHAMBER_COLLISION_GROUP],
        [(2, -4), (2, -1), PRESSURE_CHAMBER_COLLISION_GROUP],
        [(2, -1), (0, -1), VOID_COLLISION_GROUP],
        [(0, -1), (0, 0), VOID_COLLISION_GROUP]
    ]

    # Chamber dimensions for visual representation
    CHAMBER_WIDTH = 3
    CHAMBER_HEIGHT = 4
    CHAMBER_X_OFFSET = 2
    CHAMBER_Y_OFFSET = -4

    # Valve control parameters
    INLET_VALVE_POSITION = (2, -0.5)
    OUTLET_VALVE_POSITION = (3.5, -4)
    MAX_VALVE_ANGLE = 1.5
    MIN_VALVE_ANGLE = 0
    VALVE_ROTATION_SPEED = 0.3

    # Particle system parameters
    PARTICLE_SPAWN_POSITION = (0.5, -0.5)
    PARTICLE_SPAWN_RATE = 2 # Particles per frame
    PARTICLE_VELOCITY_RANGE = 300

    def __init__(self, space):
        """Initialize pressure chamber with physics space."""
        self.space = space

        # Create static body for the chamber
        self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.body.position = (CHAMBER_X, CHAMBER_Y)
        self.body_background = pygame.Rect(self.body.position.x + self.CHAMBER_X_OFFSET * CHAMBER_SCALE, self.body.position.y + self.CHAMBER_Y_OFFSET * CHAMBER_SCALE, self.CHAMBER_WIDTH * CHAMBER_SCALE, self.CHAMBER_HEIGHT * CHAMBER_SCALE)
        space.add(self.body)

        # Create chamber walls from segments
        for SEGMENT in self.SEGMENTS:
            segment = pymunk.Segment(self.body,
                                     (SEGMENT[0][0] * CHAMBER_SCALE, SEGMENT[0][1] * CHAMBER_SCALE),
                                     (SEGMENT[1][0] * CHAMBER_SCALE, SEGMENT[1][1] * CHAMBER_SCALE),
                                     CHAMBER_WALL_WIDTH
                                    )
            segment.collision_type = SEGMENT[2]
            segment.elasticity = 1
            segment.friction = 0
            space.add(segment)

        # Create inlet valve
        self.inlet = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.inlet.position = (self.INLET_VALVE_POSITION[0] * CHAMBER_SCALE + CHAMBER_X, self.INLET_VALVE_POSITION[1] * CHAMBER_SCALE + CHAMBER_Y)
        self.inlet_segment = pymunk.Segment(self.inlet, (0, -0.5 * CHAMBER_SCALE), (0, 0.5 * CHAMBER_SCALE), CHAMBER_WALL_WIDTH // 2)
        self.inlet_segment.collision_type = VALVE_COLLISION_GROUP
        self.inlet_segment.elasticity = 1
        self.inlet_segment.friction = 0

        # Create outlet valve
        self.outlet = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.outlet.position = (self.OUTLET_VALVE_POSITION[0] * CHAMBER_SCALE + CHAMBER_X, self.OUTLET_VALVE_POSITION[1] * CHAMBER_SCALE + CHAMBER_Y)
        self.outlet_segment = pymunk.Segment(self.outlet, (-0.5 * CHAMBER_SCALE, 0), (0.5 * CHAMBER_SCALE, 0), CHAMBER_WALL_WIDTH // 2)
        self.outlet_segment.collision_type = VALVE_COLLISION_GROUP
        self.outlet_segment.elasticity = 1
        self.outlet_segment.friction = 0

        # Add valves to physics space
        space.add(self.inlet, self.inlet_segment, self.outlet, self.outlet_segment)

        # Initialize particle system
        self.particle_spawn_position = (self.PARTICLE_SPAWN_POSITION[0] * CHAMBER_SCALE + CHAMBER_X, self.PARTICLE_SPAWN_POSITION[1] * CHAMBER_SCALE + CHAMBER_Y)
        self.particles = []

        # Configure particle physics properties
        self.particle_mass = 1.0
        self.particle_moment = pymunk.moment_for_circle(self.particle_mass, 0, PARTICLE_RADIUS)

        # Set up collision handling for pressure calculation
        self.particle_to_pressure_chamber_collision_handler = space.add_collision_handler(PARTICLE_COLLISION_GROUP, PRESSURE_CHAMBER_COLLISION_GROUP)
        self.particle_to_pressure_chamber_collision_handler.begin = self.particle_to_pressure_chamber_collision_handler_begin
        
        # Initialize pressure monitoring system
        self.pressure_window_seconds = 1.0
        self.pressure_window_frames = int(self.pressure_window_seconds * FPS)
        self.collision_history = deque([0] * self.pressure_window_frames, maxlen=self.pressure_window_frames)
        self.current_frame_collisions = 0
        self.frame_counter = 0

        # Set pressure thresholds
        self.ideal_pressure = 20
        self.failure_pressure = 25

    def particle_to_pressure_chamber_collision_handler_begin(self, arbiter, space, data):
        """Handle particle collisions with chamber walls."""
        self.current_frame_collisions += 1
        return True
    
    def get_pressure(self):
        """Calculate current pressure based on particle collisions."""
        total_collisions = sum(self.collision_history)
        avg_collisions_per_window = total_collisions / self.pressure_window_frames
        return avg_collisions_per_window
    
    def reset_pressure(self):
        """Reset pressure history and current collision count."""
        self.collision_history = deque([0] * self.pressure_window_frames, maxlen=self.pressure_window_frames)
        self.current_frame_collisions = 0

    def update(self, dt):
        """Update chamber state and pressure calculations."""
        self.collision_history.append(self.current_frame_collisions)
        self.current_frame_collisions = 0
        self.frame_counter += 1

    def draw(self, screen):
        """Draw chamber background with color based on pressure."""
        color = self.get_color()
        pygame.draw.rect(screen, color, self.body_background)

    def get_color(self):
        """Get chamber color based on current pressure level."""
        pressure = self.get_pressure()
        
        # Color transition from green to red based on pressure
        if pressure > self.ideal_pressure:
            # Calculate pressure scale between ideal and failure
            scale = (pressure - self.ideal_pressure) / (self.failure_pressure - self.ideal_pressure + 1e-6)
            scale = min(1.0, max(0.0, scale))
            
            # Transition from green to yellow to red
            if scale < 0.5:
                adjusted_scale = scale * 2
                return (255 * adjusted_scale, 255, 0)
            else:
                adjusted_scale = (scale - 0.5) * 2
                return (255, 255 * (1 - adjusted_scale), 0)
        else:
            # Color for pressure below ideal
            green_threshold = max(self.ideal_pressure - 5, 0)
            
            if pressure < green_threshold:
                scale = pressure / green_threshold
                return (0, 255 * scale, 255 * (1 - scale))
            else:
                return (0, 255, 0)
        
    def spawn_particle(self):
        """Spawn new particles with random velocities."""
        for _ in range(self.PARTICLE_SPAWN_RATE):
            # Create particle physics body
            particle_body = pymunk.Body(self.particle_mass, self.particle_moment)
            particle_body.position = self.particle_spawn_position
            
            # Configure particle shape and properties
            particle_shape = pymunk.Circle(particle_body, PARTICLE_RADIUS)
            particle_shape.collision_type = PARTICLE_COLLISION_GROUP
            particle_shape.elasticity = 1
            particle_shape.friction = 0
            particle_shape.color = (0, 0, 0, 255)
            
            # Set random initial velocity
            particle_body.velocity = (random.uniform(-self.PARTICLE_VELOCITY_RANGE, self.PARTICLE_VELOCITY_RANGE), random.uniform(-self.PARTICLE_VELOCITY_RANGE, self.PARTICLE_VELOCITY_RANGE))
            
            # Add particle to simulation
            self.space.add(particle_body, particle_shape)
            self.particles.append(particle_body)
        
    def rotate_inlet(self, clockwise=True):
        """Rotate inlet valve in specified direction."""
        if clockwise and self.inlet.angle < self.MAX_VALVE_ANGLE:
            self.inlet.angle  = min(self.inlet.angle + self.VALVE_ROTATION_SPEED, self.MAX_VALVE_ANGLE)
        elif not clockwise and self.inlet.angle > self.MIN_VALVE_ANGLE:
            self.inlet.angle = max(self.inlet.angle - self.VALVE_ROTATION_SPEED, self.MIN_VALVE_ANGLE)
        
    def rotate_outlet(self, clockwise=True):
        """Rotate outlet valve in specified direction."""
        if clockwise and self.outlet.angle < self.MAX_VALVE_ANGLE:
            self.outlet.angle = min(self.outlet.angle + self.VALVE_ROTATION_SPEED, self.MAX_VALVE_ANGLE)
        elif not clockwise and self.outlet.angle > self.MIN_VALVE_ANGLE:
            self.outlet.angle = max(self.outlet.angle - self.VALVE_ROTATION_SPEED, self.MIN_VALVE_ANGLE)

class Visualization:
    """Handles visualization of the pressure chamber simulation."""
    
    def __init__(self, width, height):
        """Initialize visualization with screen dimensions."""
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        self.debug_draw = pymunk.pygame_util.DrawOptions(self.screen)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        
        # Initialize pressure history tracking
        self.pressure_history = []
        self.max_pressure_history = 100
        self.graph_rect = pygame.Rect(width - 220, 10, 200, 100)

    def draw(self, chamber, space):
        """Draw chamber, physics space, and gauges."""
        self.screen.fill((255, 255, 255))
        chamber.draw(self.screen)
        space.debug_draw(self.debug_draw)
        self.draw_gauges(chamber)
        pygame.display.flip()

    def draw_gauges(self, chamber):
        """Draw pressure gauges and control information."""
        # Update pressure history
        pressure = chamber.get_pressure()
        
        if chamber.frame_counter % 10 == 0:  # Update every 10 frames
            self.pressure_history.append(pressure)
            if len(self.pressure_history) > self.max_pressure_history:
                self.pressure_history.pop(0)

        # Display simulation information
        texts = [
            f"Pressure: {pressure:.2f} PSI",
            f"Target Pressure: {chamber.ideal_pressure} PSI",
            f"Failure Pressure: {chamber.failure_pressure} PSI",
            "",
            "Open/Close Valves: Arrow Keys",
            "Change Target Pressures: WASD",
            "Turn On/Off Particle Spawning: F",
            "Pause: Spacebar; Reset: R"
        ]

        self.draw_text(texts)        

    def draw_text(self, texts):
        """Draw text lines with vertical spacing."""
        vertical_spacing = 40
        for i, line in enumerate(texts):
            text_surface = self.font.render(line, True, (0, 0, 0))
            self.screen.blit(text_surface, (10, 10 + i * vertical_spacing))
            
        
def simulate():
    """Run the pressure chamber simulation."""
    visualization = Visualization(WIDTH, HEIGHT)

    # Initialize physics space
    space = pymunk.Space()
    space.gravity = 0, 0
    space.damping = 0.9999

    chamber = PressureChamber(space)

    clock = pygame.time.Clock()

    # Simulation state
    game_over = False
    spawning = False
    paused = False
    
    # Configure physics simulation
    substeps = 3
    dt = 1.0 / (FPS * substeps)
    
    while True:
        # Handle user input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    return True
                elif event.key == pygame.K_q:
                    return False
                elif event.key == pygame.K_d:
                    chamber.ideal_pressure = min(50, chamber.ideal_pressure + 1)
                elif event.key == pygame.K_a:
                    chamber.ideal_pressure = max(1, chamber.ideal_pressure - 1)
                elif event.key == pygame.K_w:
                    chamber.failure_pressure = min(75, chamber.failure_pressure + 1)
                elif event.key == pygame.K_s:
                    chamber.failure_pressure = max(1, chamber.ideal_pressure, chamber.failure_pressure - 1)
                elif event.key == pygame.K_f:
                    spawning = not spawning
                elif event.key == pygame.K_LEFT:
                    chamber.rotate_inlet(clockwise=False)
                elif event.key == pygame.K_RIGHT:
                    chamber.rotate_inlet(clockwise=True)
                elif event.key == pygame.K_UP:
                    chamber.rotate_outlet(clockwise=True)
                elif event.key == pygame.K_DOWN:
                    chamber.rotate_outlet(clockwise=False)                  
        
        # Update visualization
        visualization.draw(chamber, space)

        if not paused:
            # Update simulation state
            if spawning:
                chamber.spawn_particle()
            
            chamber.update(1 / FPS)
            
            # Advance physics simulation
            for _ in range(substeps):
                space.step(dt)

            # Check for failure condition
            if chamber.get_pressure() > chamber.failure_pressure:
                return True

        clock.tick(FPS)
    

def main():
    """Main entry point for the pressure chamber simulation."""
    pygame.init()

    reset = True
    while reset:
        reset = simulate()

    pygame.quit()

if __name__ == "__main__":
    main()