"""
Boat and Wind Physics Simulation (Under Development).

This simulation attempts to model the interactions between a sailboat and wind.
It demonstrates principles of fluid dynamics, sail aerodynamics, and how forces
like thrust and drag affect watercraft motion. While marked as needing work,
the simulation aims to show how wind direction and strength influence sail
efficiency, how the boat's orientation relative to wind affects its speed and
movement direction, and the complex balance between wind power, water resistance,
and steering forces. Note that this implementation may have limitations or
inaccuracies in its current state.
"""

import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Set up some constants
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
WATER_COLOR = (64,192,255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
LIGHT_BLUE = (200, 235, 255)
GRID_SIZE = 40  # Space between wind particles
NUM_PARTICLES_X = WIDTH // GRID_SIZE + 2
NUM_PARTICLES_Y = HEIGHT // GRID_SIZE + 2   


# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Set up the font
font = pygame.font.Font(None, 24)

# Set up the sailboat
sailboat_x, sailboat_y = WIDTH / 2, HEIGHT / 2
sailboat_heading = 0
sailboat_speed = 0

#Scale parameters
time_step = 1/60.0
pixel_per_size = 5

#Set the boat drawing parameters
sail_width = 3
boom_length = 70
mast_offset = 30

# Set up the sail
sail_angle = 0

# Set up the wind
wind_speed = 0
wind_direction = 90
wind_coefficient = 0.06

# Set up the sliders
slider_width = 200
slider_height = 20
heading_slider_x = 20
heading_slider_y = 30
sail_slider_x = 20
sail_slider_y = 80
wind_slider_x = 20
wind_slider_y = 130

setting_heading = False
setting_sail = False
setting_wind = False

# Add this with other global variables
wind_particles = []
for i in range(NUM_PARTICLES_X):
    for j in range(NUM_PARTICLES_Y):
        wind_particles.append([i * GRID_SIZE, j * GRID_SIZE, 0])  # x, y, offset

#Draw the boat
def drawBoat(coords):
    '''Draws the boat polygon based on a 2D array of polar coordinates. The coordinates are mirrored, so only one pass of front to back is required'''
    points = []
    #Draw the first side
    for c in coords:
        r = c[0]*(1 - 0.2*math.sin(math.radians(c[1]))) #Transform to Make the boat a bit narrower
        point = (sailboat_x  + r * math.cos(math.radians(sailboat_heading - c[1])), sailboat_y  + r * math.sin(math.radians(sailboat_heading - c[1])))
        points.append(point)
    #Reverse the coordinates to draw the other side
    for c in coords[::-1]:
        r = c[0]*(1 - 0.2*math.sin(math.radians(c[1]))) #Transform to Make the boat a bit narrower
        point = (sailboat_x  + r * math.cos(math.radians(sailboat_heading + c[1])), sailboat_y   + r * math.sin(math.radians(sailboat_heading + c[1])))
        points.append(point)
    pygame.draw.polygon(screen, BLUE, points)

def drawSail():
    #Compute the angle of the boom
    if sailboat_heading + 90 < 180: angle = (180+sailboat_heading) - sail_angle
    else: angle = (sailboat_heading - 180) + sail_angle
    #Offset the mast from the boat
    mast_x, mast_y = sailboat_x + mast_offset*math.cos(math.radians(sailboat_heading)),  sailboat_y + mast_offset*math.sin(math.radians(sailboat_heading)) #Move the mast forward in the boat
    
    pygame.draw.line(screen, RED,  (mast_x, mast_y),  (mast_x + boom_length*math.cos(math.radians(angle)), mast_y + boom_length*math.sin(math.radians(angle))), width=sail_width )
    

def apparentWind():
    '''Returns the apparent wind as a polar vector'''
    #True Wind
    true_wind_x = wind_speed * math.cos(math.radians(wind_direction)) 
    true_wind_y = wind_speed * math.sin(math.radians(wind_direction))
    #Boat Speed
    boat_vx = sailboat_speed * math.cos(math.radians(sailboat_heading))
    boat_vy = sailboat_speed * math.sin(math.radians(sailboat_heading))
    #Apparent Wind
    app_wind_x = true_wind_x - boat_vx
    app_wind_y = true_wind_y - boat_vy
    #Convert to polar
    app_wind_mag = math.sqrt(math.pow(app_wind_x,2)+math.pow(app_wind_y,2))
    app_wind_dir = math.degrees(math.atan2(app_wind_y, app_wind_x))

    return (app_wind_mag, app_wind_dir)
    

def updateBoatSpeed():
    '''Returns the new x and y velocities of the boat, plus the new boatspeed'''
    app_wind, app_wind_dir = apparentWind()


    #Calculate angle of the sail to angle of the wind
    if sailboat_heading + 90 < 180: sail_wind_angle = (180+sailboat_heading) - sail_angle - app_wind_dir
    else: sail_wind_angle = (sailboat_heading - 180) + sail_angle - app_wind_dir
    
    #Calculate the flux of wind hitting the sail
    wind_hitting_sail = (wind_coefficient) * (app_wind) * abs(math.sin(math.radians(sail_wind_angle))) 
    
    sail_force = wind_hitting_sail / time_step #Vast oversimplification, but lets assume the lift is proportional to the flux of wind hitting the sail
    sail_force_direction = sail_angle #and that it is perfectly perpendicular to the boom
    #Check to see if sail is being backed
    if (sailboat_heading + 90 < 180) == (sail_wind_angle < 0) : sail_force *= -1
    
    #sail force components in the boat's frame
    sail_force_x = sail_force * math.sin(math.radians(sail_angle))
    sail_force_y = sail_force * math.cos(math.radians(sail_angle))
    #Keel keeps boat from moving sideways. Let's just assume it does its job perfectly
    keel_force_x = 0
    keel_force_y = -sail_force_y 
    #Water (and air) provide drag on the boat. Here's a crude model: the boat speed decays to 1/e time its present value after e times
    drag_force = -sailboat_speed * (1 - math.exp(-time_step) ) / time_step
    
    #Apply Forces to boat velocity. Still in Boat Frame
    _boat_speed_x = sailboat_speed + ( sail_force_x + drag_force )  * time_step
    _boat_speed_y = sail_force_y + keel_force_y
    
    #Convert back to global Frame
    boat_speed_x = _boat_speed_x * math.cos(math.radians(sailboat_heading)) - _boat_speed_y * math.sin(math.radians(sailboat_heading))
    boat_speed_y = _boat_speed_x * math.sin(math.radians(sailboat_heading)) + _boat_speed_y * math.cos(math.radians(sailboat_heading))
    
    return (boat_speed_x, boat_speed_y, _boat_speed_x)

def drawWind(wind_speed, wind_direction):
    """Draw a grid of moving lines to represent wind direction and speed."""
    if wind_speed <= 0:
        return
        
    # Fixed wind color
    wind_color = (200, 200, 200)
    
    # Calculate unit vector for wind direction (normalized)
    wind_dx = math.cos(math.radians(wind_direction))
    wind_dy = math.sin(math.radians(wind_direction))
    
    # Fixed line length
    line_length = 25
    
    # Update and draw each wind particle
    for particle in wind_particles:
        # Update particle position - speed affects movement rate only
        particle[2] = (particle[2] + wind_speed * 0.3) % GRID_SIZE
        
        # Calculate current position with offset
        curr_x = particle[0] + particle[2] * wind_dx
        curr_y = particle[1] + particle[2] * wind_dy
        
        # Calculate end point using normalized direction vector
        end_x = curr_x - wind_dx * line_length
        end_y = curr_y - wind_dy * line_length
        
        # Draw the line (fixed length)
        pygame.draw.line(screen, wind_color, (curr_x, curr_y), (end_x, end_y), 2)
        
        # Reset particles that move off screen
        if curr_x < -GRID_SIZE: particle[0] = WIDTH + GRID_SIZE
        elif curr_x > WIDTH + GRID_SIZE: particle[0] = -GRID_SIZE
        if curr_y < -GRID_SIZE: particle[1] = HEIGHT + GRID_SIZE
        elif curr_y > HEIGHT + GRID_SIZE: particle[1] = -GRID_SIZE

# Game loop
while True:
    #Adjust Controls
    for event in pygame.event.get():
        if pygame.mouse.get_pressed()[0] == True and event.type == pygame.MOUSEMOTION: #Adjust the current Slider
            if setting_heading: sailboat_heading = max(0,min(1, (event.pos[0] - heading_slider_x) / slider_width)) * 360 - 90
            elif setting_sail: sail_angle = max(0,min(1, (event.pos[0] - sail_slider_x) / slider_width)) * 90
            elif setting_wind: wind_speed = max(0,min(1, (event.pos[0] - wind_slider_x) / slider_width)) * 30
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: #Identify Slider that was clicked, if any
            if heading_slider_x < event.pos[0] < heading_slider_x + slider_width and heading_slider_y < event.pos[1] < heading_slider_y + slider_height: setting_heading = True
            elif sail_slider_x < event.pos[0] < sail_slider_x + slider_width and sail_slider_y < event.pos[1] < sail_slider_y + slider_height: setting_sail = True
            elif wind_slider_x < event.pos[0] < wind_slider_x + slider_width and wind_slider_y < event.pos[1] < wind_slider_y + slider_height: setting_wind = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1: #Stop adjusting sliders
            setting_heading, setting_sail, setting_wind = False, False, False
        elif event.type == pygame.QUIT: #Quit the Game
            pygame.quit()
            sys.exit()

    # Move the sailboat
    vx, vy, speed = updateBoatSpeed()
    sailboat_x += vx * time_step * pixel_per_size
    sailboat_y += vy * time_step * pixel_per_size
    sailboat_speed = speed

    # Keep the sailboat on the screen
    if sailboat_x < 0: sailboat_x = WIDTH
    elif sailboat_x > WIDTH: sailboat_x = 0
    if sailboat_y < 0: sailboat_y = HEIGHT
    elif sailboat_y > HEIGHT: sailboat_y = 0

    # Draw everything
    screen.fill(WATER_COLOR)

    # Draw the sailboat
    drawBoat([(60,0),(40,25),(30,60),(30,100),(50,155)])
    drawSail()

    # Draw wind visualization
    drawWind(wind_speed, wind_direction)

    # Draw the sliders
    pygame.draw.rect(screen, BLUE, (heading_slider_x, heading_slider_y, slider_width, slider_height))
    pygame.draw.rect(screen, BLACK, (heading_slider_x + (sailboat_heading+90)*slider_width/360, heading_slider_y, 2, slider_height))
    
    pygame.draw.rect(screen, RED, (sail_slider_x, sail_slider_y, slider_width, slider_height))
    pygame.draw.rect(screen, BLACK, (sail_slider_x + sail_angle*slider_width/90, sail_slider_y, 2, slider_height))
     
    pygame.draw.rect(screen, BLUE, (wind_slider_x, wind_slider_y, slider_width, slider_height))
    pygame.draw.rect(screen, BLACK, (wind_slider_x + wind_speed*slider_width/30, wind_slider_y, 2, slider_height))

    # Draw the text
    heading_text = font.render("Heading: " + str(int(sailboat_heading+90)), True, BLUE)
    sail_text = font.render("Sail: " + str(int(sail_angle)), True, RED)
    wind_text = font.render("Wind: " + str(int(wind_speed)), True, BLUE)
    screen.blit(heading_text, (heading_slider_x, heading_slider_y - 20))
    screen.blit(sail_text, (sail_slider_x, sail_slider_y - 20))
    screen.blit(wind_text, (wind_slider_x, wind_slider_y - 20))
    
    a_wind, a = apparentWind()
    a_wind_text = font.render("Apparent Wind: " + str(int(a_wind)), True, BLACK)
    speed_text = font.render("Boat Speed: " + str(int(sailboat_speed)), True, BLACK)
    screen.blit(a_wind_text, (wind_slider_x, wind_slider_y + 30))
    screen.blit(speed_text, (wind_slider_x, wind_slider_y + 50))

    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    pygame.time.delay(1000 // 60)