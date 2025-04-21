import tkinter as tk
import random
import math

# Constants
WIDTH, HEIGHT = 800, 600
CELL_SIZE = 10
WIND_DIRECTIONS = ['N', 'S', 'E', 'W']

class Cell:
    """
    Represents a single cell in the wildfire simulation.
    
    Attributes:
        x, y: Grid coordinates
        vegetation_density: Value between 0-1 representing how much fuel is available
        moisture_level: Value between 0-1 representing how wet the cell is
        on_fire: Boolean indicating if the cell is currently burning
        burnt: Boolean indicating if the cell has been consumed by fire
        burn_time: Number of simulation steps the cell will burn before becoming burnt
    """
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vegetation_density = random.random()
        self.moisture_level = random.random()
        self.on_fire = False
        self.burnt = False
        self.burn_time = 0
    
    def start_fire(self):
        """Start a fire in this cell if it's not already burnt."""
        if not self.burnt and not self.on_fire:
            self.on_fire = True
            # Cells with more vegetation burn longer (3-10 steps)
            self.burn_time = int(3 + self.vegetation_density * 7)
    
    def can_catch_fire(self):
        """
        Determine if this cell can catch fire based on its properties.
        Cells with high vegetation and low moisture are more likely to burn.
        """
        if self.burnt or self.on_fire:
            return False
        
        # Flammability factor: higher vegetation and lower moisture increases chance of burning
        flammability = self.vegetation_density - self.moisture_level
        return random.random() < (flammability + 0.1)  # +0.1 gives a small base chance

class SmokeParticle:
    """
    Represents a smoke particle in the simulation.
    
    Attributes:
        x, y: Position coordinates
        age: How long the particle has existed
        max_age: Maximum lifecycle of the particle
        size: Visual size of the particle
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.age = 0
        self.max_age = random.randint(20, 50)
        self.size = random.uniform(1.0, 3.0)
    
    def update(self, wind_direction, wind_speed):
        """Update particle position based on wind and physics."""
        # Basic heat rise effect (smoke always rises somewhat)
        self.y -= 0.5 + random.uniform(0, 1.0)
        
        # Apply wind force
        if wind_direction == 'N':
            self.y -= wind_speed
        elif wind_direction == 'S':
            self.y += wind_speed * 0.5  # Reduced effect as smoke tends to rise
        elif wind_direction == 'E':
            self.x += wind_speed
        elif wind_direction == 'W':
            self.x -= wind_speed
            
        # Add some random movement to simulate air currents
        self.x += random.uniform(-0.5, 0.5)
        self.y += random.uniform(-0.3, 0.3)
        
        # Age the particle
        self.age += 1
        
        # Particles get slightly smaller as they age
        self.size = max(0.5, self.size - 0.02)
    
    def is_expired(self):
        """Check if the particle has reached the end of its lifecycle."""
        return self.age >= self.max_age or self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT

class WildfireSimulation:
    """
    Main simulation class that handles the wildfire cellular automaton.
    
    The simulation models fire spread based on:
    - Vegetation density (more vegetation = more fuel)
    - Moisture levels (wetter cells are harder to ignite)
    - Wind direction and speed (affects fire spread pattern and speed)
    """
    def __init__(self, master):
        self.master = master
        self.master.title("Wildfire Simulation")
        
        # Initialize grid of cells
        self.cells = [[Cell(x, y) for y in range(HEIGHT // CELL_SIZE)] for x in range(WIDTH // CELL_SIZE)]
        self.wind_direction = 'N'
        self.wind_speed = 1
        self.smoke_particles = []
        self.is_running = True
        
        # Set up UI
        self.canvas = tk.Canvas(self.master, width=WIDTH, height=HEIGHT, bg='lightgreen')
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", self.place_fire)
        
        # Control panel
        self.controls_frame = tk.Frame(self.master)
        self.controls_frame.pack(pady=10)
        
        # Wind direction control
        self.wind_direction_label = tk.Label(self.controls_frame, text="Wind Direction:")
        self.wind_direction_label.pack(side=tk.LEFT, padx=5)
        
        self.wind_direction_var = tk.StringVar(self.controls_frame)
        self.wind_direction_var.set(self.wind_direction)
        self.wind_direction_option = tk.OptionMenu(self.controls_frame, self.wind_direction_var, *WIND_DIRECTIONS, command=self.update_wind_direction)
        self.wind_direction_option.pack(side=tk.LEFT, padx=5)
        
        # Wind speed control
        self.wind_speed_label = tk.Label(self.controls_frame, text="Wind Speed:")
        self.wind_speed_label.pack(side=tk.LEFT, padx=5)
        
        self.wind_speed_scale = tk.Scale(self.controls_frame, from_=0, to=10, orient=tk.HORIZONTAL, command=self.update_wind_speed)
        self.wind_speed_scale.set(self.wind_speed)
        self.wind_speed_scale.pack(side=tk.LEFT, padx=5)
        
        # Buttons for simulation control
        self.start_fire_button = tk.Button(self.controls_frame, text="Random Fire", command=self.start_random_fire)
        self.start_fire_button.pack(side=tk.LEFT, padx=5)
        
        self.reset_button = tk.Button(self.controls_frame, text="Reset Simulation", command=self.reset_simulation)
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
        self.pause_button = tk.Button(self.controls_frame, text="Pause", command=self.toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        # Instructions
        instructions = "Click on the map to place fires. Adjust wind direction and speed to see effects."
        self.instructions_label = tk.Label(self.master, text=instructions)
        self.instructions_label.pack(pady=5)
        
        # Initialize the visualization
        self.draw()
        self.update()
    
    def update(self):
        """Main simulation update loop."""
        if self.is_running:
            self.spread_fire()
            self.update_smoke_particles()
            self.draw()
        self.master.after(100, self.update)
    
    def spread_fire(self):
        """
        Update the fire spread across cells based on physics rules:
        - Fire burns for several steps based on vegetation density
        - Fire spreads to neighbors based on wind, vegetation, and moisture
        - Wind direction and speed influence spread probability and direction
        """
        # Copy the current state to avoid immediate propagation affecting neighbors
        new_fires = []
        update_burn_times = []
        
        # First pass: determine fire spread
        for x in range(len(self.cells)):
            for y in range(len(self.cells[x])):
                cell = self.cells[x][y]
                
                if cell.on_fire:
                    # Generate smoke from burning cells
                    if random.random() < 0.3:  # 30% chance to generate smoke per step
                        center_x = x * CELL_SIZE + CELL_SIZE // 2
                        center_y = y * CELL_SIZE + CELL_SIZE // 2
                        self.smoke_particles.append(SmokeParticle(center_x, center_y))
                    
                    # Handle burn time
                    update_burn_times.append((x, y))
                    
                    # Attempt to spread fire to neighbors with weighted probabilities
                    neighbors = self.get_neighbors(x, y)
                    for nx, ny, spread_chance in neighbors:
                        if 0 <= nx < len(self.cells) and 0 <= ny < len(self.cells[0]):
                            neighbor = self.cells[nx][ny]
                            # Check if this neighbor can catch fire
                            if neighbor.can_catch_fire():
                                # Adjust chance based on wind
                                adjusted_chance = spread_chance * (1 + self.wind_speed/10)
                                if random.random() < adjusted_chance:
                                    new_fires.append((nx, ny))
        
        # Second pass: update burn times
        for x, y in update_burn_times:
            cell = self.cells[x][y]
            cell.burn_time -= 1
            if cell.burn_time <= 0:
                cell.on_fire = False
                cell.burnt = True
        
        # Third pass: set new fires
        for x, y in new_fires:
            self.cells[x][y].start_fire()
    
    def get_neighbors(self, x, y):
        """
        Get neighboring cells with spread probabilities adjusted for wind direction.
        Returns: List of tuples (x, y, probability)
        """
        neighbors = []
        
        # Base spread chances in each direction
        north = (x, y-1, 0.1)
        south = (x, y+1, 0.1)
        east = (x+1, y, 0.1)
        west = (x-1, y, 0.1)
        ne = (x+1, y-1, 0.05)
        nw = (x-1, y-1, 0.05)
        se = (x+1, y+1, 0.05)
        sw = (x-1, y+1, 0.05)
        
        # Adjust probabilities based on wind direction
        wind_factor = 0.1 * self.wind_speed
        
        if self.wind_direction == 'N':
            north = (north[0], north[1], north[2] + wind_factor)
            ne = (ne[0], ne[1], ne[2] + wind_factor/2)
            nw = (nw[0], nw[1], nw[2] + wind_factor/2)
        elif self.wind_direction == 'S':
            south = (south[0], south[1], south[2] + wind_factor)
            se = (se[0], se[1], se[2] + wind_factor/2)
            sw = (sw[0], sw[1], sw[2] + wind_factor/2)
        elif self.wind_direction == 'E':
            east = (east[0], east[1], east[2] + wind_factor)
            ne = (ne[0], ne[1], ne[2] + wind_factor/2)
            se = (se[0], se[1], se[2] + wind_factor/2)
        elif self.wind_direction == 'W':
            west = (west[0], west[1], west[2] + wind_factor)
            nw = (nw[0], nw[1], nw[2] + wind_factor/2)
            sw = (sw[0], sw[1], sw[2] + wind_factor/2)
        
        neighbors.extend([north, south, east, west, ne, nw, se, sw])
        return neighbors
    
    def update_smoke_particles(self):
        """Update all smoke particles in the simulation."""
        # Create a new list to hold particles that are still active
        active_particles = []
        
        for particle in self.smoke_particles:
            particle.update(self.wind_direction, self.wind_speed)
            if not particle.is_expired():
                active_particles.append(particle)
        
        # Replace the old list with only active particles
        self.smoke_particles = active_particles
    
    def draw(self):
        """Render the current state of the simulation to the canvas."""
        self.canvas.delete("all")
        
        # Draw cells
        for x in range(len(self.cells)):
            for y in range(len(self.cells[x])):
                cell = self.cells[x][y]
                
                # Visualization based on cell state
                if cell.burnt:
                    # Black for burnt cells
                    self.canvas.create_rectangle(
                        x * CELL_SIZE, y * CELL_SIZE, 
                        (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE, 
                        fill="black", outline=""
                    )
                elif cell.on_fire:
                    # Red-orange gradient for fire, intensity based on remaining burn time
                    fire_intensity = min(255, int(255 * (cell.burn_time / 10)))
                    color = f"#{fire_intensity:02x}{fire_intensity//3:02x}00"
                    self.canvas.create_rectangle(
                        x * CELL_SIZE, y * CELL_SIZE, 
                        (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE, 
                        fill=color, outline=""
                    )
                else:
                    # Green for normal vegetation, shade based on density and moisture
                    # More vegetation = darker green, more moisture = bluer tint
                    green = int(100 + (1 - cell.vegetation_density) * 155)
                    blue = int(cell.moisture_level * 100)
                    color = f"#00{green:02x}{blue:02x}"
                    self.canvas.create_rectangle(
                        x * CELL_SIZE, y * CELL_SIZE, 
                        (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE, 
                        fill=color, outline=""
                    )
        
        # Draw smoke particles
        for particle in self.smoke_particles:
            # Smoke fades from dark gray to transparent as it ages
            alpha = 1.0 - (particle.age / particle.max_age)
            gray_value = int(100 + 155 * alpha)
            size = particle.size
            
            self.canvas.create_oval(
                particle.x - size, particle.y - size,
                particle.x + size, particle.y + size,
                fill=f"#{gray_value:02x}{gray_value:02x}{gray_value:02x}",
                outline=""
            )
        
        # Draw wind direction indicator
        self.draw_wind_indicator()
    
    def draw_wind_indicator(self):
        """Draw an arrow showing current wind direction and strength."""
        # Position at bottom-right corner
        center_x, center_y = WIDTH - 50, HEIGHT - 50
        arrow_length = 20 + self.wind_speed * 2  # Length based on wind speed
        
        # Calculate end point based on direction
        end_x, end_y = center_x, center_y
        if self.wind_direction == 'N':
            end_y = center_y - arrow_length
        elif self.wind_direction == 'S':
            end_y = center_y + arrow_length
        elif self.wind_direction == 'E':
            end_x = center_x + arrow_length
        elif self.wind_direction == 'W':
            end_x = center_x - arrow_length
            
        # Draw the arrow
        self.canvas.create_line(center_x, center_y, end_x, end_y, 
                               arrow=tk.LAST, width=3, fill="blue")
        self.canvas.create_text(center_x, center_y + 20, 
                               text=f"{self.wind_direction} ({self.wind_speed})", fill="blue")
    
    def update_wind_direction(self, value):
        """Update wind direction based on user selection."""
        self.wind_direction = value
    
    def update_wind_speed(self, value):
        """Update wind speed based on user selection."""
        self.wind_speed = int(value)
    
    def start_random_fire(self):
        """Start a fire at a random location."""
        x = random.randint(0, len(self.cells) - 1)
        y = random.randint(0, len(self.cells[0]) - 1)
        self.cells[x][y].start_fire()
    
    def place_fire(self, event):
        """Start a fire at the clicked location."""
        # Convert mouse coordinates to grid coordinates
        x = event.x // CELL_SIZE
        y = event.y // CELL_SIZE
        
        # Check if coordinates are within bounds
        if 0 <= x < len(self.cells) and 0 <= y < len(self.cells[0]):
            self.cells[x][y].start_fire()
    
    def reset_simulation(self):
        """Reset the entire simulation to initial state."""
        self.cells = [[Cell(x, y) for y in range(HEIGHT // CELL_SIZE)] for x in range(WIDTH // CELL_SIZE)]
        self.smoke_particles = []
        self.draw()
    
    def toggle_pause(self):
        """Pause or resume the simulation."""
        self.is_running = not self.is_running
        if self.is_running:
            self.pause_button.config(text="Pause")
        else:
            self.pause_button.config(text="Resume")

# Run the simulation
if __name__ == "__main__":
    root = tk.Tk()
    simulation = WildfireSimulation(root)
    root.mainloop()