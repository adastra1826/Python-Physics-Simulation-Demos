import tkinter as tk
import random
import math

# Window dimensions
WIDTH, HEIGHT = 800, 600

# Physical simulation parameters
# Defining a scaling system: 1 meter = 20 pixels, 1 second = 60 frames
METERS_TO_PIXELS = 20.0  # Conversion factor: 20 pixels = 1 meter
SECONDS_TO_FRAMES = 60.0  # Conversion factor: 60 frames = 1 second

# Real-world constants converted to simulation units
REAL_GRAVITY = 9.8  # m/s²
GRAVITY = REAL_GRAVITY * METERS_TO_PIXELS / (SECONDS_TO_FRAMES**2)  # px/frame²
DRAG = 0.99  # Air resistance factor (dimensionless)

# Particle properties
PARTICLE_SIZE = 2  # Base size in pixels
PARTICLE_COUNT = 500  # Number of particles per eruption

# Volcano and eruption properties
# Base eruption parameters (converted from typical volcanic velocities)
# Typical volcanic ejecta: 50-200 m/s
BASE_VELOCITY = 80.0  # m/s
BASE_ERUPTION_STRENGTH = BASE_VELOCITY * METERS_TO_PIXELS / SECONDS_TO_FRAMES  # px/frame

GROUND_HEIGHT = 50

# Pressure system
PRESSURE_BUILDUP_RATE = 0.05  # MPa/frame (simplified)
PRESSURE_THRESHOLD = 10.0     # MPa (typical volcanic eruption threshold: 5-25 MPa)
PRESSURE_RELEASE_FACTOR = 0.8 # Fraction of pressure released during eruption (dimensionless)

class Particle:
    """Represents a volcanic particle (ash, rock, or lava).
    
    Physical properties:
    - Position: Measured in pixels (1m = 20px)
    - Velocity: Measured in pixels/frame (1m/s = 20px/60frames)
    - Size: Varies from 1-6px (~5-30cm particles)
    - Heat: Dimensionless value 0-100 representing temperature
    """
    
    def __init__(self, x, y, vx, vy):
        self.x = x  # Horizontal position (px)
        self.y = y  # Vertical position (px)
        self.vx = vx  # Horizontal velocity (px/frame)
        self.vy = vy  # Vertical velocity (px/frame)
        self.heat = 100  # Initial heat value (0-100, dimensionless)
        
        # Random size based on typical volcanic ejecta
        # Convert from meters to pixels (volcanic ejecta: ~0.05-0.3m)
        size_in_meters = random.uniform(0.05, 0.3)
        self.size = size_in_meters * METERS_TO_PIXELS
        
    def update(self):
        """Update particle position and properties for next frame."""
        # Update position based on velocity
        self.x += self.vx
        self.y += self.vy
        
        # Apply physics
        self.vy += GRAVITY  # Apply gravity (px/frame²)
        self.vx *= DRAG     # Apply horizontal drag (dimensionless)
        self.vy *= DRAG     # Apply vertical drag (dimensionless)
        
        # Cooling effect - particles cool as they travel
        # Rate represents cooling of roughly 100°C/sec
        self.heat *= 0.99  # Decrease heat over time
    
    def is_out_of_bounds(self):
        """Check if particle has left the visible area."""
        return (self.y > HEIGHT - GROUND_HEIGHT or self.x < 0 or self.x > WIDTH)
        
    def draw(self, canvas):
        """Draw particle with heat-based color."""
        color = self.heat_to_color()
        canvas.create_oval(
            self.x - self.size, self.y - self.size,
            self.x + self.size, self.y + self.size,
            fill=color, outline=color
        )
        
    def heat_to_color(self):
        """Convert heat value to color gradient from white to yellow to orange to red.
        
        Approximate temperature mapping:
        - heat > 80: ~1000°C (red, lava)
        - heat > 50: ~800°C (orange, hot rocks)
        - heat > 20: ~600°C (yellow, cooling material)
        - heat <= 20: <400°C (white, ash/steam)
        """
        heat = int(self.heat)
        if heat > 80:
            return '#ff0000'  # Red (hottest, ~1000°C)
        elif heat > 50:
            return '#ffa000'  # Orange (~800°C)
        elif heat > 20:
            return '#ffff00'  # Yellow (~600°C)
        else:
            return '#ffffff'  # White (coolest, <400°C)

class Volcano:
    """Models a volcano with pressure buildup and eruption mechanics.
    
    Physical properties:
    - Width: ~200px (represents ~10m crater width)
    - Height: ~100px (represents ~5m visible height)
    - Pressure: Represented in MPa (megapascals), typical volcanic eruption: 5-25 MPa
    """
    
    def __init__(self, x, y):
        self.x = x  # Horizontal center position (px)
        self.y = y  # Vertical base position (px)
        self.particles = []
        self.eruption_strength = BASE_ERUPTION_STRENGTH  # Initial velocity multiplier (px/frame)
        self.pressure = 0.0  # Current pressure level (MPa)
        self.erupting = False
        
        # Volcano shape parameters (converted from meters to pixels)
        volcano_width_meters = 10.0  # Typical small volcanic crater: 10-100m
        volcano_height_meters = 5.0   # Visible volcano height
        self.width = volcano_width_meters * METERS_TO_PIXELS
        self.height = volcano_height_meters * METERS_TO_PIXELS
        
    def update_pressure(self):
        """Update internal pressure, trigger eruption if threshold exceeded.
        
        Typical pressure buildup rates vary widely in real volcanoes,
        from days to weeks to reach eruption threshold.
        This is accelerated for simulation purposes.
        """
        if not self.erupting:
            self.pressure += PRESSURE_BUILDUP_RATE
            
            # Check if pressure triggers eruption
            if self.pressure >= PRESSURE_THRESHOLD:
                self.erupt()
                self.pressure *= (1.0 - PRESSURE_RELEASE_FACTOR)  # Release pressure
                self.erupting = False
    
    def erupt(self):
        """Generate particles in an eruption pattern.
        
        The eruption velocity is scaled by pressure, simulating more
        violent eruptions when pressure is high.
        
        Typical volcanic ejecta velocities: 50-200 m/s
        """
        self.erupting = True
        
        # Scale eruption strength with pressure
        # Converts to velocity in px/frame
        pressure_factor = 0.7 + 0.3 * (self.pressure / PRESSURE_THRESHOLD)
        actual_strength = self.eruption_strength * pressure_factor
        
        # Calculate crater position (top of volcano)
        crater_x = self.x
        crater_y = self.y - self.height
        
        for _ in range(PARTICLE_COUNT):
            # Create directional eruption (mostly upward with some spread)
            # Typical volcanic eruption angles: within ~40° of vertical
            angle = random.uniform(-0.4 * math.pi, 0.4 * math.pi) - math.pi/2  # Mostly upward
            
            # Velocity in px/frame
            velocity = random.uniform(0.5 * actual_strength, actual_strength)
            vx = velocity * math.cos(angle)
            vy = velocity * math.sin(angle)
            
            # Add some randomness to eruption point
            # Crater width variation scaled to meters
            crater_width_meters = 0.75  # ~75cm spread
            offset_x = random.uniform(-crater_width_meters, crater_width_meters) * METERS_TO_PIXELS
            
            particle = Particle(crater_x + offset_x, crater_y, vx, vy)
            
            # Initial temperature varies by particle (800-1200°C range)
            particle.heat = random.uniform(80, 100)
            self.particles.append(particle)
    
    def update(self):
        """Update volcano state and all particles."""
        self.update_pressure()
        
        # Update all particles and remove those out of bounds
        self.particles = [p for p in self.particles if not p.is_out_of_bounds()]
        for particle in self.particles:
            particle.update()
    
    def draw(self, canvas):
        """Draw volcano and all particles."""
        # Draw volcano shape
        canvas.create_polygon(
            self.x - self.width/2, self.y,
            self.x, self.y - self.height,
            self.x + self.width/2, self.y,
            fill='#555555', outline='#333333'
        )
        
        # Draw pressure indicator
        pressure_height = 50 * (self.pressure / PRESSURE_THRESHOLD)
        canvas.create_rectangle(
            20, HEIGHT - 20 - pressure_height,
            50, HEIGHT - 20,
            fill='#ff0000', outline='#000000'
        )
        canvas.create_text(35, HEIGHT - 60, text=f"Pressure\n{self.pressure:.1f} MPa", fill="white")
        
        # Draw all particles
        for particle in self.particles:
            particle.draw(canvas)

def main():
    """Initialize and run the simulation."""
    root = tk.Tk()
    root.title("Volcanic Eruption Simulation")

    canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='#000033')  # Dark blue background
    canvas.pack()

    # Create volcano at bottom center of screen
    volcano = Volcano(WIDTH // 2, HEIGHT - 50)

    # UI controls
    controls_frame = tk.Frame(root)
    controls_frame.pack(side=tk.BOTTOM, fill=tk.X)
    
    # Add simulation info
    info_frame = tk.Frame(root)
    info_frame.pack(side=tk.TOP, fill=tk.X)
    tk.Label(info_frame, text="Simulation scale: 1m = 20px, 1s = 60 frames", 
             bg='#333333', fg='white', font=('Arial', 10)).pack(fill=tk.X)
    
    eruption_strength_var = tk.DoubleVar()
    eruption_strength_var.set(BASE_ERUPTION_STRENGTH)

    def update_eruption_strength(value):
        """Update the volcano's eruption strength (velocity scaling)."""
        volcano.eruption_strength = float(value)
        # Calculate approximate real-world velocity
        real_velocity = float(value) * SECONDS_TO_FRAMES / METERS_TO_PIXELS
        strength_label.config(text=f"Eruption Strength: {real_velocity:.1f} m/s")

    # Eruption strength slider
    strength_label = tk.Label(controls_frame, text=f"Eruption Strength: {BASE_VELOCITY:.1f} m/s")
    strength_label.pack(side=tk.LEFT, padx=5)
    
    tk.Scale(controls_frame, from_=1, to=15, resolution=0.1, variable=eruption_strength_var,
             orient=tk.HORIZONTAL, command=update_eruption_strength, length=200).pack(side=tk.LEFT)

    # Pressure buildup rate slider
    pressure_rate_var = tk.DoubleVar()
    pressure_rate_var.set(PRESSURE_BUILDUP_RATE)
    
    def update_pressure_rate(value):
        """Update the pressure buildup rate (MPa per frame)."""
        global PRESSURE_BUILDUP_RATE
        PRESSURE_BUILDUP_RATE = float(value)
        # Convert to real-world units (MPa per second)
        real_rate = float(value) * SECONDS_TO_FRAMES
        rate_label.config(text=f"Pressure Rate: {real_rate:.2f} MPa/s")
    
    rate_label = tk.Label(controls_frame, text=f"Pressure Rate: {PRESSURE_BUILDUP_RATE * SECONDS_TO_FRAMES:.2f} MPa/s")
    rate_label.pack(side=tk.LEFT, padx=5)
    
    tk.Scale(controls_frame, from_=0.01, to=0.2, resolution=0.01, variable=pressure_rate_var,
             orient=tk.HORIZONTAL, command=update_pressure_rate, length=200).pack(side=tk.LEFT)

    # Manual eruption button
    def manual_erupt():
        """Force an eruption by setting pressure to threshold."""
        volcano.pressure = PRESSURE_THRESHOLD
    
    tk.Button(controls_frame, text="Force Eruption", command=manual_erupt).pack(side=tk.LEFT, padx=10)

    def draw_background(canvas):
        """Draw night sky and ground."""
        # Draw a few stars
        for _ in range(50):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT - 150)
            size = random.uniform(0.5, 1.5)
            brightness = random.randint(150, 255)
            color = f'#{brightness:02x}{brightness:02x}{brightness:02x}'
            canvas.create_oval(x-size, y-size, x+size, y+size, fill=color, outline='')
            
        # Draw ground (representing ~2.5m of ground)
        canvas.create_rectangle(0, HEIGHT - GROUND_HEIGHT, WIDTH, HEIGHT, fill='#332211', outline='')
    
    def animate():
        """Main animation loop."""
        canvas.delete('all')
        
        draw_background(canvas)
        volcano.update()
        volcano.draw(canvas)
        
        # Display particle count and physics info
        real_velocity = volcano.eruption_strength * SECONDS_TO_FRAMES / METERS_TO_PIXELS
        info_text = (
            f"Particles: {len(volcano.particles)}\n"
            f"Time scale: 1 sec = {SECONDS_TO_FRAMES} frames\n"
            f"Eruption velocity: {real_velocity:.1f} m/s"
        )
        canvas.create_text(WIDTH - 200, 40, text=info_text, fill="white", anchor="nw")
        
        root.after(16, animate)  # ~60 FPS

    animate()
    root.mainloop()

if __name__ == '__main__':
    main()