import sys
import math
import pymunk
import pygame

#Pygame Setup
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# Pymunk Setup
space = pymunk.Space()
space.gravity = (0, 1000)

# Create static boundaries: floor, left, right, and top walls
floor = pymunk.Segment(space.static_body, (0, 500), (800, 500), 5)
left_wall = pymunk.Segment(space.static_body, (0, 0), (0, 600), 5)
right_wall = pymunk.Segment(space.static_body, (800, 0), (800, 600), 5)
top_wall = pymunk.Segment(space.static_body, (0, 0), (800, 0), 5)
for wall in (floor, left_wall, right_wall, top_wall):
    wall.elasticity = 0.8
    wall.friction = 0.9
    space.add(wall)

# Simulation variables
spring_stiffness = 1000
spring_damping = 10
node_radius = 8
node_mass = 1
close_threshold = 20  # Snap-to threshold for closing the shape

# Storage for user-drawn points and simulation objects
blob_points = []
nodes = []         # List of (body, shape)
springs = []       # Perimeter springs
shear_springs = [] # soft-body behavior
blob_created = False
warning_message = ""

# Setup font for on-screen information
font = pygame.font.SysFont("Arial", 16)

# Slider definitions
slider_stiffness = {
    "x": 600, "y": 80, "width": 150, "height": 20,  # moved down to y=80
    "min": 500, "max": 2000, "value": spring_stiffness,
    "label": "Stiffness"
}
slider_damping = {
    "x": 600, "y": 130, "width": 150, "height": 20,  # moved down to y=130
    "min": 0, "max": 50, "value": spring_damping,
    "label": "Damping"
}
slider_active = None

def draw_background(screen):
    # blue sky and green ground
    screen.fill((135, 206, 235)) 
    pygame.draw.rect(screen, (34, 139, 34), (0, 500, 800, 100))

def draw_text(screen, text, x, y, color=(0, 0, 0)):
    label = font.render(text, True, color)
    screen.blit(label, (x, y))

def draw_slider(slider):
    # Draw the slider track
    track_rect = pygame.Rect(slider["x"], slider["y"] + slider["height"] // 2 - 2,
                             slider["width"], 4)
    pygame.draw.rect(screen, (200, 200, 200), track_rect)
    # Determine knob position
    ratio = (slider["value"] - slider["min"]) / (slider["max"] - slider["min"])
    knob_x = slider["x"] + int(ratio * slider["width"])
    knob_y = slider["y"] + slider["height"] // 2
    # Draw knob
    pygame.draw.circle(screen, (255, 255, 255), (knob_x, knob_y), slider["height"] // 2 + 2)
    pygame.draw.circle(screen, (0, 0, 0), (knob_x, knob_y), slider["height"] // 2 + 2, 2)
    # Draw label above the slider
    draw_text(screen, f"{slider['label']}: {int(slider['value'])}",
              slider["x"] + slider["width"]//2 - 40, slider["y"] - 20)

def update_slider(slider, mouse_x):
    # Calculate new value based on mouse x
    rel = mouse_x - slider["x"]
    rel = max(0, min(rel, slider["width"]))
    ratio = rel / slider["width"]
    slider["value"] = slider["min"] + ratio * (slider["max"] - slider["min"])
    return slider["value"]

def create_blob(points):
    global nodes, springs, shear_springs, spring_stiffness, spring_damping
    n = len(points)
    # Create a dynamic body for each point
    for pos in points:
        body = pymunk.Body(node_mass, pymunk.moment_for_circle(node_mass, 0, node_radius))
        body.position = pos
        shape = pymunk.Circle(body, node_radius)
        shape.elasticity = 0.95
        shape.friction = 1
        space.add(body, shape)
        nodes.append((body, shape))
    
    # Connect adjacent nodes with perimeter springs (closed loop)
    for i in range(n):
        body_a = nodes[i][0]
        body_b = nodes[(i + 1) % n][0]
        rest_length = math.dist(body_a.position, body_b.position)
        spring = pymunk.DampedSpring(body_a, body_b, (0, 0), (0, 0),
                                     rest_length, spring_stiffness, spring_damping)
        space.add(spring)
        springs.append(spring)
    
    # Add shear springs
    if n >= 4:
        for i in range(n):
            body_a = nodes[i][0]
            body_b = nodes[(i + 2) % n][0]
            rest_length = math.dist(body_a.position, body_b.position)
            shear = pymunk.DampedSpring(body_a, body_b, (0, 0), (0, 0),
                                        rest_length, spring_stiffness * 0.5, spring_damping)
            space.add(shear)
            shear_springs.append(shear)

def update_existing_springs():
    # Update parameters of existing springs to match current slider values
    global springs, shear_springs, spring_stiffness, spring_damping
    for spring in springs:
        spring.stiffness = spring_stiffness
        spring.damping = spring_damping
    for shear in shear_springs:
        shear.stiffness = spring_stiffness * 0.5
        shear.damping = spring_damping

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit(0)

        # Slider events
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            # Check if click is inside slider regions
            rect1 = pygame.Rect(slider_stiffness["x"], slider_stiffness["y"],
                                slider_stiffness["width"], slider_stiffness["height"])
            rect2 = pygame.Rect(slider_damping["x"], slider_damping["y"],
                                slider_damping["width"], slider_damping["height"])
            if rect1.collidepoint(pos):
                slider_active = slider_stiffness
            elif rect2.collidepoint(pos):
                slider_active = slider_damping
            # Only process blob creation if click isn't on a slider
            elif not blob_created and event.button == 1:
                click_pos = event.pos
                if not blob_points:
                    blob_points.append(click_pos)
                else:
                    if math.dist(click_pos, blob_points[0]) < close_threshold and len(blob_points) >= 3:
                        blob_created = True
                        create_blob(blob_points)
                    elif math.dist(click_pos, blob_points[-1]) < close_threshold:
                        warning_message = "Clicked too close to the last node. Click elsewhere or near the starting node to close."
                    else:
                        blob_points.append(click_pos)
                        
        elif event.type == pygame.MOUSEMOTION:
            if slider_active is not None:
                new_val = update_slider(slider_active, event.pos[0])
                if slider_active is slider_stiffness:
                    spring_stiffness = new_val
                elif slider_active is slider_damping:
                    spring_damping = new_val
                update_existing_springs()
                        
        elif event.type == pygame.MOUSEBUTTONUP:
            slider_active = None

        # Contingencies
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and not blob_created:
                if len(blob_points) >= 3 and math.dist(blob_points[0], blob_points[-1]) < close_threshold:
                    blob_created = True
                    create_blob(blob_points)
                else:
                    warning_message = "Shape not closed. Click near the starting node to close the shape."
        elif event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                space.gravity = (space.gravity[0], space.gravity[1] - 100)
            else:
                space.gravity = (space.gravity[0], space.gravity[1] + 100)
    
    # Apply arrow key impulses to each node if the blob exists
    keys = pygame.key.get_pressed()
    if blob_created:
        impulse = [0, 0]
        if keys[pygame.K_LEFT]:
            impulse[0] -= 100
        if keys[pygame.K_RIGHT]:
            impulse[0] += 100
        if keys[pygame.K_UP]:
            impulse[1] -= 100
        if keys[pygame.K_DOWN]:
            impulse[1] += 100
        if impulse != [0, 0]:
            for body, _ in nodes:
                body.apply_impulse_at_local_point(impulse)
    
    # Draw text
    draw_background(screen)
    draw_text(screen, "Click to add nodes. Close shape by clicking near the starting node.", 10, 10)
    draw_text(screen, "Press Enter when done. Arrow keys apply forces, scroll wheel adjusts gravity.", 10, 30)
    draw_text(screen, f"Gravity: {space.gravity[1]}", 10, 50)
    if warning_message:
        draw_text(screen, warning_message, 10, 90, (255, 0, 0))
    
    # Draw sliders
    draw_slider(slider_stiffness)
    draw_slider(slider_damping)
    
    if not blob_created:
        if len(blob_points) > 1:
            pygame.draw.lines(screen, (0, 0, 0), False, blob_points, 2)
        for pos in blob_points:
            pygame.draw.circle(screen, (255, 0, 0), pos, 5)
    else:
        for i in range(len(nodes)):
            body_a = nodes[i][0]
            body_b = nodes[(i + 1) % len(nodes)][0]
            pygame.draw.line(screen, (0, 255, 0),
                             (int(body_a.position.x), int(body_a.position.y)),
                             (int(body_b.position.x), int(body_b.position.y)), 3)
        for body, _ in nodes:
            pos = (int(body.position.x), int(body.position.y))
            pygame.draw.circle(screen, (0, 0, 255), pos, node_radius + 4)
            pygame.draw.circle(screen, (255, 255, 255), pos, node_radius)
    
    pygame.display.flip()
    clock.tick(60)
    space.step(1 / 60.0)