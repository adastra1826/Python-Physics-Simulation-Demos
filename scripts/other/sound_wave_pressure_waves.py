"""
Sound and Pressure Wave Physics Simulation.

This simulation models the propagation of sound and pressure waves through a medium.
It demonstrates principles of wave mechanics, including wave propagation, interference,
reflection, and diffraction. The simulation visualizes how sound waves travel through
space as longitudinal pressure waves, how they interact with obstacles and boundaries,
and how multiple waves combine through constructive and destructive interference.
It helps visualize the invisible pressure fluctuations that constitute sound waves
in a way that makes wave mechanics intuitive and observable.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.patches import Circle


class SoundRoomSimulation:
    """Simulates acoustic wave propagation in a 2D room with obstacles.
    
    Uses the finite difference method to solve the 2D wave equation.
    """

    def __init__(self):
        """Initialize simulation parameters and setup the environment."""
        # Simulation parameters
        self.room_width = 10.0  # meters
        self.room_height = 6.0  # meters
        self.c = 343.0  # speed of sound in air (m/s)
        self.grid_x = 200
        self.grid_y = 120
        self.dx = self.room_width / self.grid_x
        self.dy = self.room_height / self.grid_y
        # CFL stability condition
        self.dt = 0.5 * min(self.dx, self.dy) / self.c
        self.source_duration = 50  # time steps
        self.time_steps = 400  # Extended to show more wave propagation
        self.source_frequency = 5.0  # Hz
        
        # Source position (left side of room)
        self.source_x = int(self.grid_x * 0.1)
        self.source_y = int(self.grid_y * 0.5)
        
        # Initialize pressure fields
        self.p = np.zeros((self.grid_x, self.grid_y))
        self.p_prev = np.zeros((self.grid_x, self.grid_y))
        self.p_next = np.zeros((self.grid_x, self.grid_y))
        
        # Create obstacles (two parallel rows of circular pillars)
        self.obstacles = []
        for i in range(5):
            # Left row
            self.obstacles.append((
                int(self.grid_x * 0.3),
                int(self.grid_y * (0.2 + 0.15 * i)),
                int(self.grid_y * 0.05)
            ))
            # Right row
            self.obstacles.append((
                int(self.grid_x * 0.7),
                int(self.grid_y * (0.2 + 0.15 * i)),
                int(self.grid_y * 0.05)
            ))
        
        # Create mask for obstacles
        self.obstacle_mask = np.zeros((self.grid_x, self.grid_y), dtype=bool)
        for x, y, radius in self.obstacles:
            for i in range(max(0, x - radius), min(self.grid_x, x + radius + 1)):
                for j in range(max(0, y - radius),
                              min(self.grid_y, y + radius + 1)):
                    if ((i - x)**2 + (j - y)**2) <= radius**2:
                        self.obstacle_mask[i, j] = True
    
    def update_frame(self, frame):
        """Update the pressure field for a single time step.
        
        Args:
            frame: Current animation frame number.
        """
        # Add source term
        if frame < self.source_duration:
            self.p[self.source_x, self.source_y] = 3.0 * np.sin(
                2 * np.pi * self.source_frequency * frame * self.dt)
        
        # Create mask for non-obstacle points
        non_obstacle_mask = ~self.obstacle_mask
        
        # Apply finite difference method using vectorized operations
        laplacian = np.zeros_like(self.p)
        laplacian[1:-1, 1:-1] = (
            self.p[2:, 1:-1] + self.p[:-2, 1:-1] + 
            self.p[1:-1, 2:] + self.p[1:-1, :-2] - 
            4 * self.p[1:-1, 1:-1]
        ) / (self.dx**2)
        
        # Apply update only to non-obstacle points
        self.p_next[1:-1, 1:-1] = np.where(
            non_obstacle_mask[1:-1, 1:-1],
            2 * self.p[1:-1, 1:-1] - self.p_prev[1:-1, 1:-1] + 
            (self.c * self.dt)**2 * laplacian[1:-1, 1:-1],
            self.p_next[1:-1, 1:-1]
        )
        
        # Apply boundary conditions at walls (reflection)
        self.p_next[0, :] = self.p_next[1, :]
        self.p_next[-1, :] = self.p_next[-2, :]
        self.p_next[:, 0] = self.p_next[:, 1]
        self.p_next[:, -1] = self.p_next[:, -2]
        
        # Apply boundary conditions at obstacles - vectorized version
        obstacle_indices = np.where(self.obstacle_mask)
        if len(obstacle_indices[0]) > 0:
            for offset_i, offset_j in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                neighbor_i = np.clip(
                    obstacle_indices[0] + offset_i, 0, self.grid_x - 1)
                neighbor_j = np.clip(
                    obstacle_indices[1] + offset_j, 0, self.grid_y - 1)
                
                # Only consider valid neighbors outside obstacles
                valid_neighbors = ~self.obstacle_mask[neighbor_i, neighbor_j]
                if np.any(valid_neighbors):
                    self.p_next[
                        obstacle_indices[0][valid_neighbors], 
                        obstacle_indices[1][valid_neighbors]
                    ] = self.p_next[
                        neighbor_i[valid_neighbors], 
                        neighbor_j[valid_neighbors]
                    ]
        
        # Reduce damping to maintain wave intensity
        self.p_next *= 0.998  # Changed from 0.995
        
        # Update pressure fields
        self.p_prev = self.p.copy()
        self.p = self.p_next.copy()
        self.p_next = np.zeros_like(self.p)
    
    def reset_simulation(self):
        """Reset all pressure fields to zero."""
        self.p = np.zeros((self.grid_x, self.grid_y))
        self.p_prev = np.zeros((self.grid_x, self.grid_y))
        self.p_next = np.zeros((self.grid_x, self.grid_y))

    def run_simulation(self, output_file=None):
        """Run the acoustic wave simulation with visualization.
        
        Args:
            output_file: Optional path to save animation as MP4.
        
        Returns:
            Animation object.
        """
        # Use a clean, professional style
        plt.style.use('seaborn-v0_8-whitegrid')
        
        # Same figure size with better proportions and existing DPI
        fig, ax = plt.subplots(figsize=(12, 8), dpi=120)
        
        # Use a more professional colormap with better contrast
        img = ax.imshow(
            self.p.T, 
            cmap='RdBu_r',  # Professional red-blue colormap
            vmin=-0.03, 
            vmax=0.03,
            extent=[0, self.room_width, 0, self.room_height],
            origin='lower', 
            interpolation='bilinear'
        )
        
        # Professional typography and labels
        ax.set_xlabel('Distance (m)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Distance (m)', fontsize=11, fontweight='bold')
        ax.set_title(
            'Acoustic Wave Propagation Simulation', 
            fontsize=14, 
            fontweight='bold', 
            pad=10
        )
        
        # Add subtle grid for professional look
        ax.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.3)
        
        # Create obstacles with improved appearance
        obstacle_patches = []
        for x, y, radius in self.obstacles:
            # Use a better color that stands out professionally
            circle = Circle(
                (x * self.dx, y * self.dy), 
                radius * self.dx, 
                fill=True, 
                color='#444444', 
                alpha=0.8
            )
            ax.add_patch(circle)
            #Add edge for better definition
            edge = Circle(
                (x * self.dx, y * self.dy), 
                radius * self.dx,
                fill=False, 
                edgecolor='black', 
                linewidth=1
            )
            ax.add_patch(edge)
            obstacle_patches.append(circle)
            obstacle_patches.append(edge)
        
        # Enhanced source point
        source_point = ax.plot(
            self.source_x * self.dx, 
            self.source_y * self.dy, 
            'o', 
            color='yellow', 
            markersize=10, 
            markeredgecolor='black', 
            markeredgewidth=1,
            label='Sound Source'
        )[0]
        
        # Better colorbar with improved label
        cbar = plt.colorbar(img, ax=ax, pad=0.01)
        cbar.set_label('Pressure Variation (Pa)', fontsize=11, fontweight='bold')
        
        # Enhanced time counter
        time_box = dict(
            boxstyle='round,pad=0.4', 
            facecolor='white', 
            alpha=0.7, 
            edgecolor='gray'
        )
        time_text = ax.text(
            0.02, 
            0.95, 
            'Time: 0.000 s', 
            transform=ax.transAxes, 
            color='black', 
            fontsize=12, 
            fontweight='bold',
            bbox=time_box
        )
        
        # Add simulation parameters text
        params_text = ax.text(
            0.98, 
            0.02, 
            f'f = {self.source_frequency} Hz | c = {self.c} m/s', 
            transform=ax.transAxes, 
            fontsize=10,
            ha='right', 
            va='bottom',
            bbox=dict(facecolor='white', alpha=0.7, boxstyle='round')
        )
        
        # Add legend with better formatting
        ax.legend(loc='upper right', framealpha=0.8)
        
        # Add animation controls
        self.current_cycle = 0
        
        # Define the update function with dynamic source coloring
        def update(frame):
            """Update function for animation frames.
            
            Args:
                frame: Current frame number.
                
            Returns:
                List of artists to update.
            """
            # Check if we need to reset (for looping)
            if frame == 0 and self.current_cycle > 0:
                self.reset_simulation()
                
            self.update_frame(frame)
            img.set_array(self.p.T)
            
            # Update source point color based on emission status
            if frame < self.source_duration:
                source_point.set_color('red')  # Red when emitting
            else:
                source_point.set_color('gold')  # Yellow/gold when not emitting
            
            # Track which cycle we're on
            if frame == self.time_steps - 1:
                self.current_cycle += 1
                
            # Update time counter
            current_time = frame * self.dt
            time_text.set_text(f'Time: {current_time:.3f} s')
            
            return [img] + obstacle_patches + [source_point, time_text, params_text]
        
        # Create animation
        ani = FuncAnimation(
            fig, 
            update, 
            frames=self.time_steps, 
            blit=True, 
            interval=5
        )
        
        # Either save to file or display
        if output_file:
            # For MP4 output
            writer = FFMpegWriter(
                fps=30, 
                metadata=dict(artist='SoundRoomSimulation'),
                bitrate=3000
            )
            print(f"Saving animation to {output_file}...")
            ani.save(output_file, writer=writer)
            print(f"Animation saved successfully to {output_file}")
            plt.close(fig)
        else:
            # For display
            plt.tight_layout()
            plt.show()
        
        return ani


if __name__ == "__main__":
    simulation = SoundRoomSimulation()
    
    # Choose one:
    # For display:
    animation = simulation.run_simulation()
    
    # For saving to MP4:
    # animation = simulation.run_simulation("acoustic_wave_simulation.mp4")