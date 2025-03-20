from vpython import *
import numpy as np

# Create the scene for 2D simulation. VPython does 3D simulation by default.
scene = canvas(title="2D Water Surface Simulation", width=800, height=600)
scene.userzoom = False  # Disable zooming
scene.userpan = False  # Disable panning
scene.userspin = False  # Disable rotation

# Define the size of the pond
grid_size = 100
pond_size = 10  # Scaled display size
spacing = pond_size / grid_size

time_step = 0.1  # Time step for wave update
damping = 0.999  # Attenuation factor 0.99
wave_speed = 5.0  # Speed of wave propagation

# Add captions
caption1 = label(
    pos=vector(0.0, pond_size / 1.85, 0),
    text="Ripples on a pond",
    height=15,
    box=False,
    color=color.white,
)
caption2 = label(
    pos=vector(-pond_size / 2.9, -pond_size / 1.85, 0),
    text="Click to create a splash!",
    height=15,
    box=False,
    color=color.yellow,
)
caption2 = label(
    pos=vector(pond_size / 4.0, -pond_size / 1.85, 0),
    text="Click several times to create bigger splash!",
    height=15,
    box=False,
    color=color.yellow,
)

# Add timer display
timer = label(
    pos=vector(-pond_size / 2.5, pond_size / 1.85, 0),
    text="Time: 0.00 s",
    height=15,
    box=False,
    color=color.white,
)

# Create a 2D grid representing the water surface
water_height = np.zeros((grid_size, grid_size))
velocity = np.zeros((grid_size, grid_size))

# Create the pond surface
surface = []
for i in range(grid_size):
    row = []
    for j in range(grid_size):
        box_color = vector(0, 0, 0.5)  # Initial blue color
        b = box(
            pos=vector(i * spacing - pond_size / 2, j * spacing - pond_size / 2, 0),
            size=vector(spacing, spacing, 0.1),
            color=box_color,
            emissive=True,
        )  # Set emissive to remove shading
        row.append(b)
    surface.append(row)

# Create boundary walls
boundary_thickness = 0.2
boundary_color = color.gray(0.5)
boundaries = [
    box(
        pos=vector(0, pond_size / 2 + boundary_thickness / 2, 0),
        size=vector(pond_size, boundary_thickness, 0.5),
        color=boundary_color,
        emissive=True,
    ),  # Top
    box(
        pos=vector(0, -pond_size / 2 - boundary_thickness / 2, 0),
        size=vector(pond_size, boundary_thickness, 0.5),
        color=boundary_color,
        emissive=True,
    ),  # Bottom
    box(
        pos=vector(pond_size / 2 + boundary_thickness / 2, 0, 0),
        size=vector(boundary_thickness, pond_size, 0.5),
        color=boundary_color,
        emissive=True,
    ),  # Right
    box(
        pos=vector(-pond_size / 2 - boundary_thickness / 2, 0, 0),
        size=vector(boundary_thickness, pond_size, 0.5),
        color=boundary_color,
        emissive=True,
    ),  # Left
]


# Function to create a ripple
def create_ripple(x, y):
    i, j = int((x + pond_size / 2) / spacing), int((y + pond_size / 2) / spacing)
    if 0 <= i < grid_size and 0 <= j < grid_size:
        water_height[i, j] = 2.0  # Initial displacement
        velocity[i, j] = 1.0  # Initial velocity


# Mouse click event to generate ripples
def mouse_click(evt):
    create_ripple(evt.pos.x, evt.pos.y)


scene.bind("mousedown", mouse_click)


# Update function for wave propagation
def update_water():
    global water_height, velocity
    """Wave equation is Laplacian*f(x) = speed^2 * acceleration"""
    """Laplacian is calculated using: \nabla^2 f(i, j) = f(i+1, j) + f(i-1, j) + f(i, j+1) + f(i, j-1) - 4f(i, j)"""
    laplacian = (
        np.roll(water_height, 1, axis=0)
        + np.roll(water_height, -1, axis=0)
        + np.roll(water_height, 1, axis=1)
        + np.roll(water_height, -1, axis=1)
        - 4 * water_height
    )
    acceleration = wave_speed * laplacian
    velocity += acceleration * time_step
    velocity *= damping  # Damping effect
    water_height += velocity * time_step

    # Boundary reflection
    """These are hard boundary conditions, where the wave amplitude is zero"""
    water_height[0, :] = 0.0
    water_height[-1, :] = 0.0
    water_height[:, 0] = 0.0
    water_height[:, -1] = 0.0

    # Update the surface color based on water_height
    for i in range(grid_size):
        for j in range(grid_size):
            h = water_height[i, j]
            surface[i][j].pos.z = 0.0  # Doing 2D simulation, set to zero
            surface[i][j].color = vector(0.0, 3 * abs(h), 0.5)  # Greenish waves


# Animation loop
t = 0  # Set timer to zero
while True:
    rate(60)
    update_water()
    # Update timer display
    timer.text = f"Time: {t:.2f} s"
    t += time_step
