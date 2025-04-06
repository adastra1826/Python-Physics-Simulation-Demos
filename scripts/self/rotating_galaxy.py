"""
Rotating Galaxy Physics Simulation.

This simulation models a simplified version of galactic rotation, where
stars orbit around a central gravitational mass (representing a galactic core).
The simulation demonstrates orbital dynamics, gravitational attraction,
and the differential rotation of stellar objects at varying distances from 
the galactic center. Stars closer to the center orbit faster than those 
further away, creating the characteristic spiral arm patterns seen in galaxies.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from matplotlib.animation import FuncAnimation

# Constants for the simulation
# Gravitational constant in appropriate units
GRAVITY = 4.30091e-3

# Black Hole properties
BH_MASS = 4e6     # Mass of the black hole
BH_SIZE = 100     # Visual size for the black hole marker in the plot

# Stars properties
NUM_STARS = 1000            # Number of stars in the simulation
STAR_MIN_MASS = 0.1         # Minimum mass of a star
STAR_MAX_MASS = 2           # Maximum mass of a star
STAR_MIN_SIZE = 1           # Minimum visual size for a star marker
STAR_MAX_SIZE = 15          # Maximum visual size for a star marker
SPEED_NOISE = 0.2           # Variation in orbital speed (±20%)
VELOCITY_NOISE_DEGREES = 30 # Maximum random angular deviation in velocity direction in degrees
MAX_RADIUS = 20             # Maximum allowed radius for star initialization

# Time configuration for simulation and animation
FPS = 30                    # Frames per second for the animation
TIME_STEP_YEARS = 0.0001    # Time step used in the simulation updates (in years)

class Simulation:
    """
    Simulation class to handle the star orbit simulation around a black hole.
    
    This class sets up the plotting environment, initializes the simulation state,
    updates positions and velocities using a simplified Barnes-Hut approach for gravitational
    interactions (here only between the stars and the central black hole), and processes user input.
    """
    def __init__(self):
        """
        Initialize the simulation by setting up the plot, slider, and initial simulation state.
        """
        self.fig, self.ax = plt.subplots(figsize=(7, 7))
        plt.subplots_adjust(bottom=0.25)
        
        # Set background and axis colors to match a space theme
        self.fig.patch.set_facecolor("black")
        self.ax.set_facecolor("black")
        self.ax.tick_params(colors="grey")
        self.ax.xaxis.label.set_color("grey")
        self.ax.yaxis.label.set_color("grey")
        
        # Create slider to control simulation speed (number of steps per animation frame)
        self.ax_speed = plt.axes([0.35, 0.05, 0.3, 0.03])
        self.slider = Slider(self.ax_speed, "Speed ", 1, 100, valinit=10)
        self.slider.label.set_color("grey")
        self.slider.valtext.set_color("grey")
        
        # Configure the plot: title, aspect ratio, limits, and labels
        self.ax.set_title("Stars Orbiting a Black Hole", color="grey")
        self.ax.set_aspect("equal")
        self.ax.set_xlim(-MAX_RADIUS - 5, MAX_RADIUS + 5)
        self.ax.set_xlabel("Parsecs", color="grey")
        self.ax.set_ylim(-MAX_RADIUS - 5, MAX_RADIUS + 5)
        self.ax.set_ylabel("Parsecs", color="grey")
        
        # Plot the central black hole as a blue marker at the origin
        self.ax.scatter(0, 0, c='blue', s=BH_SIZE)
        
        # Create an empty scatter plot for the stars which will be updated dynamically
        self.scatter_stars = self.ax.scatter([], [], 0, c="white")
        
        # Set fixed properties for the black hole (position remains at origin)
        self.x_bh = 0
        self.y_bh = 0
        self.m_bh = BH_MASS
        
        # Control flag to pause the simulation
        self.paused = False        
        
        # Initialize the simulation state with star positions, velocities, etc.
        self.reset()
        
    def reset(self):
        """
        Initialize the simulation state.
        
        This method randomly generates the initial positions (in polar coordinates converted to Cartesian)
        for the stars, computes their orbital velocities with an added noise component to simulate variations,
        and sets their sizes based on their masses.
        """
        np.random.seed()
        # Generate random angles for star positions uniformly distributed between 0 and 2π
        angles = np.random.uniform(0, 2 * np.pi, NUM_STARS)
        # Generate random radii with a distribution that favors inner regions (using square root transformation)
        radii = np.sqrt(np.random.uniform(0, 1, NUM_STARS)) * MAX_RADIUS

        # Convert polar coordinates (radii and angles) to Cartesian coordinates (x, y)
        self.x = radii * np.cos(angles)
        self.y = radii * np.sin(angles)
        
        # Compute the perfect tangent (clockwise) angle at each star's position for a stable circular orbit
        tangent_angles = angles - np.pi / 2

        # Introduce noise to the velocity direction to simulate non-ideal orbits
        noise = np.radians(np.random.uniform(-VELOCITY_NOISE_DEGREES, VELOCITY_NOISE_DEGREES, NUM_STARS))
        final_angles = tangent_angles + noise

        # Calculate orbital speed based on gravitational force balance for circular orbits: v = sqrt(G*M / r)
        orbital_speed = np.sqrt(GRAVITY * BH_MASS / (radii + 0.01))
        
        # Introduce a random speed variation of ±SPEED_NOISE (±20%) to each star's orbital speed
        speed_variation = np.random.uniform(1 - SPEED_NOISE, 1 + SPEED_NOISE, NUM_STARS)
        final_speed = orbital_speed * speed_variation
    
        # Determine the initial velocity components for each star based on final speed and angle
        self.vx = final_speed * np.cos(final_angles)
        self.vy = final_speed * np.sin(final_angles)
        
        # Assign random masses to stars within the specified range
        self.m = np.random.uniform(STAR_MIN_MASS, STAR_MAX_MASS, NUM_STARS)
        
        # Map star masses to sizes for visualization (linearly scaling between STAR_MIN_SIZE and STAR_MAX_SIZE)
        star_sizes = STAR_MIN_SIZE + (self.m - STAR_MIN_MASS) * (STAR_MAX_SIZE - STAR_MIN_SIZE) / (STAR_MAX_MASS - STAR_MIN_MASS)
        self.scatter_stars.set_sizes(star_sizes)
        
        # Update the scatter plot with the newly calculated star positions
        self.scatter_stars.set_offsets(np.column_stack((self.x, self.y)))
    
    def handle_key_press(self, event):
        """
        Handle key press events for user interactions.
        
        Supported keys:
          - Space (' '): Pause or resume the simulation.
          - 'r': Reset the simulation to initial random state.
          - Other keys are forwarded to the default key press handler.
        
        Parameters:
            event: The key press event containing information about which key was pressed.
        """
        if event.key == ' ':
            self.paused = not self.paused
        elif event.key == 'r':
            self.reset()
        elif hasattr(self.fig.canvas.manager, 'key_press_handler'):
            # Forward the event to the default key press handler
            # Necessary because without forwarding, it is impossible to interact with the slider using the mouse
            self.fig.canvas.manager.key_press_handler(event)
        
    def calculate_movement(self, x, y, vx, vy, x_bh, y_bh, m_bh):
        """
        Compute the gravitational influence of the black hole on stars and update their positions and velocities.
        
        Calculates the acceleration for each star due to the central black hole,
        updates the velocities accordingly, and then updates the positions based on these velocities.
        
        Parameters:
            x, y: Arrays containing the current Cartesian positions of the stars.
            vx, vy: Arrays containing the current velocity components of the stars.
            x_bh, y_bh: Position of the black hole (fixed at the origin).
            m_bh: Mass of the black hole.
        
        Returns:
            Updated positions (x, y) and velocity components (vx, vy) for the stars.
        """
        # Calculate displacement of stars from the black hole
        dx = x - x_bh
        dy = y - y_bh
        # Compute distance from the black hole, adding a small offset (0.1) to avoid division by zero
        r = np.sqrt(dx**2 + dy**2) + 0.1
        
        # Compute the gravitational acceleration toward the black hole
        # The formula used is: a = G * M / r^2, adjusted to component form and normalized by r^3 for vector calculation
        ax = -GRAVITY * m_bh * dx / r**3
        ay = -GRAVITY * m_bh * dy / r**3

        # Update velocities using the computed acceleration and the time step
        vx += ax * TIME_STEP_YEARS
        vy += ay * TIME_STEP_YEARS

        # Update positions using the updated velocities and the time step
        x += vx * TIME_STEP_YEARS
        y += vy * TIME_STEP_YEARS

        return x, y, vx, vy

    def update(self, frame):
        """
        Update the simulation for each animation frame.
        
        This function:
          - Checks if the simulation is paused.
          - Updates the simulation state (positions and velocities) by calling the barnes_hut method multiple times
            according to the value selected on the speed slider.
          - Updates the positions of stars in the scatter plot.
        
        Parameters:
            frame: The current frame number (unused, but required by FuncAnimation).
        
        Returns:
            The updated scatter plot object for the animation.
        """
        if not self.paused:
            # Determine how many simulation steps to perform in this frame from the slider value
            steps_per_frame = int(self.slider.val)
            for _ in range(steps_per_frame):
                self.x, self.y, self.vx, self.vy = self.calculate_movement(
                    self.x, self.y, self.vx, self.vy,
                    self.x_bh, self.y_bh, self.m_bh
                )
            # Update the star positions in the scatter plot after simulation steps
            self.scatter_stars.set_offsets(np.column_stack((self.x, self.y)))
            return self.scatter_stars

def main():
    """
    The main function to run the simulation.
    
    This function:
      - Instantiates the Simulation class.
      - Connects the key press events to allow pausing and resetting.
      - Sets up the animation using FuncAnimation.
      - Displays the plot window.
    """
    sim = Simulation()
    sim.fig.canvas.mpl_connect("key_press_event", sim.handle_key_press)
    # Set up the animation to update based on the desired FPS (frames per second)
    anim = FuncAnimation(sim.fig, sim.update, interval=1000 / FPS, blit=False, cache_frame_data=False)
    plt.show()

if __name__ == "__main__":
    main()
