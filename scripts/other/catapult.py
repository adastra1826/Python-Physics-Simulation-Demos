import pygame
import pymunk
import pymunk.pygame_util
import random
import math
import numpy as np 

# Window size
WIDTH, HEIGHT = 1000, 600

# Game constants 
FPS = 60 
DELTA_TIME = 1/FPS 
SCALE_FACTOR = 1/20 
COLLIDER_TYPE_PROJECTILE = 1
COLLIDER_TYPE_GOAL = 2
COLLIDER_TYPE_GROUND = 3 

# Game Dynamic Variables 
SCORE = 10000
NUM_SHOTS = 0 
GAME_PROJECTILES = []
CURRENT_LEVEL = None
COMPLETE_LEVEL_ON = False 
CATAPULT_OBJECT = None 

# UI 
pygame.font.init()
UI_FONT = pygame.font.SysFont('Helvetica', 20)
COMPLETE_FONT = pygame.font.SysFont('Helvetica', 80)
RESTART_FONT = pygame.font.SysFont('Helvetica', 40)
FIRE_POS = (100, HEIGHT - 35)
ARM_LENGTH_POS = (42, 50)
PROJECTILE_RADIUS_POS = (20, 130)
PROJECTILE_X_OFFSET = 40
STRENGTH_POS = (20, 210)
STRENGTH_X_OFFSET = 40 
FIRING_ANGLE_POS = (42, 290)
FIRING_ANGLE_X_OFFSET = 20
MATERIAL_POS = (20, 370)
MATERIAL_X_OFFSET = 20 

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)
DARK_BROWN = (119, 49, 9)
METAL = (128, 128, 128)
DARK_METAL = (90, 90, 90)
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (17, 124, 19)
DARK_GREEN = (10, 80, 5)
IRON = (78, 79, 85)
ALUMINUM = (163, 167, 169)
STONE = (185, 176, 164)
GOLD = (255, 215, 0)


# Catapult settings
PROJECTILE_MATERIAL = "stone"
CATAPULT_X_POS = FIRE_POS[0]
CATAPULT_Y_POS = HEIGHT - 50
MAX_TORQUE = 4000000

# Materials
MATERIALS = {
    "stone": {'density': 1600, 'color': STONE},
    "wood": {'density': 500, 'color': BROWN},
    "aluminum": {'density': 2700, 'color': ALUMINUM},
    "iron": {'density': 7870, 'color': IRON}
}

# Helper functions 

def rotate_point_by_angle(p0, angle):
    # Convert to numpy array 
    rotated_point = np.array([p0[0], p0[1]])
    c, s = np.cos(angle), np.sin(angle)
    rotation_matrix = np.array(((c,-s), (s, c)))
    # Rotate position based on current arm angle 
    rotated_point = np.dot(rotation_matrix, rotated_point)
    # Return as tuple 
    return (rotated_point[0],rotated_point[1])

# Game Functions 

def handle_goal_collision(arbiter, space, data):
    complete_level()
    return True 

def complete_level():
    global COMPLETE_LEVEL_ON
    global GAME_PROJECTILES
    global CATAPULT_OBJECT
    global CURRENT_LEVEL
    if not COMPLETE_LEVEL_ON: 
        COMPLETE_LEVEL_ON = True 
        GAME_PROJECTILES = []
        CURRENT_LEVEL.objects = []
        
def reset_game(): 
    global NUM_SHOTS
    global SCORE 
    global COMPLETE_LEVEL_ON
    COMPLETE_LEVEL_ON = False 
    SCORE = 10000
    NUM_SHOTS = 0 
    main()    

# Game Classes 
class Catapult:
    def __init__(self):
        self.position = (130, HEIGHT - 50)
        self.arm_length = 80 # in 20ths of a meter (4 m default) 
        self.arm_width = 7 
        self.arm_mass = 100
        self.arm_angle = 0
        self.firing_angle = math.pi / 2
        self.firing = False 
        self.resetting = False 
        self.torque = 500000
        self.projectile_released = False 
        self.projectile_radius = self.arm_length / 8
        self.projectile_material = PROJECTILE_MATERIAL
        self.projectile_mass = self.compute_projectile_mass()
        self.angular_acceleration = self.compute_angular_acceleration()
        self.angular_velocity = 0 
        self.projectile = None 
        
    def increment_arm_length(self):
        self.arm_length = min(120, self.arm_length + 10)
        self.angular_acceleration = self.compute_angular_acceleration()
    
    def decrement_arm_length(self):
        self.arm_length = max(20, self.arm_length - 10)
        self.angular_acceleration = self.compute_angular_acceleration()
        
    def increment_projectile_radius(self):
        self.projectile_radius = min(int(self.arm_length / 4), self.projectile_radius + 5)
        self.projectile_mass = self.compute_projectile_mass()
        self.angular_acceleration = self.compute_angular_acceleration()
    
    def decrement_projectile_radius(self):
        self.projectile_radius = max(int(self.arm_length / 12), self.projectile_radius - 5)
        self.projectile_mass = self.compute_projectile_mass()
        self.angular_acceleration = self.compute_angular_acceleration()
        
    def increment_catapult_strength(self):
        self.torque = min(MAX_TORQUE, self.torque + 100000)
        self.angular_acceleration = self.compute_angular_acceleration()
    
    def decrement_catapult_strength(self):
        self.torque = max(0, self.torque - 100000)
        self.angular_acceleration = self.compute_angular_acceleration()
        
    def increment_firing_angle(self):
        self.firing_angle = min(math.pi/2, self.firing_angle + 5*(math.pi/180))
    
    def decrement_firing_angle(self):
        self.firing_angle = max(math.pi/6, self.firing_angle - 5*(math.pi/180))
        
    def increment_material(self):
        keys = list(MATERIALS.keys()) 
        index = keys.index(self.projectile_material)
        if index == len(keys) - 1: 
            index = 0 
        else:
            index += 1 
        self.projectile_material = keys[index]
        self.projectile_mass = self.compute_projectile_mass()
        self.angular_acceleration = self.compute_angular_acceleration()
    
    def decrement_material(self):
        keys = list(MATERIALS.keys())
        index = keys.index(self.projectile_material)
        if index == 0: 
            index = len(keys) - 1 
        else:
            index -= 1 
        self.projectile_material = keys[index]
        self.projectile_mass = self.compute_projectile_mass()
        self.angular_acceleration = self.compute_angular_acceleration()
        
    def compute_projectile_mass(self):
        return (4/3) * math.pow(self.projectile_radius*SCALE_FACTOR,3) * math.pi * MATERIALS[self.projectile_material]['density']
        
    def compute_angular_acceleration(self):
         # Compute moment of inertia for catapult arm + projectile 
         I_arm = (1/3) * self.arm_mass * (self.arm_length*SCALE_FACTOR)**2
         I_projectile = self.projectile_mass * (self.arm_length*SCALE_FACTOR)**2
         return self.torque / (I_arm + I_projectile) 
        
    def trigger_fire(self):
        global NUM_SHOTS
        global SCORE 
        if self.resetting: 
            return 
        if not self.firing:
            self.firing = True
            # Update stat 
            NUM_SHOTS += 1 
            SCORE = 10000 - ((NUM_SHOTS - 1) * 500)
        
    def tick_fire(self, space):
        # Update angular velocity and arm angle 
        self.angular_velocity += self.angular_acceleration * DELTA_TIME 
        next_arm_angle = self.arm_angle + self.angular_velocity * DELTA_TIME 
        if next_arm_angle < self.firing_angle: 
            self.arm_angle = next_arm_angle
        else: 
            self.launch_projectile(space)
            
    def tick_reset(self, space):
        # Update arm angle  
        next_arm_angle = self.arm_angle + self.angular_velocity * DELTA_TIME 
        if next_arm_angle > 0:  
            self.arm_angle = next_arm_angle
        else: 
            self.arm_angle = 0 
            self.projectile_released = False 
            self.resetting = False 
            
    def launch_projectile(self, space):
        global SCORE
        self.arm_angle = self.firing_angle 
        self.firing = False  
        if self.angular_velocity < 35: 
            self.projectile_released = True
            new_projectile = Projectile(self, space) 
            new_projectile.launch(self.angular_velocity * self.arm_length, self.firing_angle)
            GAME_PROJECTILES.append(new_projectile)
        else: 
            # Angular velocity too great 
            # Reduce by an additional 500 points and do not fire catapult as it is temporarily broken
            SCORE -= 500
        self.trigger_reset()
        
    def trigger_reset(self):
        self.resetting = True 
        self.angular_velocity = -0.5
            
    # Draws the firing arm and returns the location of the point where projectile contacts firing arm and the polygon
    # for the firing bucket 
    def draw_firing_arm(self, screen):
        half_width = self.arm_width / 2 
        sin_angle = math.sin(self.arm_angle)
        cos_angle = math.cos(self.arm_angle)
        # Arm polygon point names based on position @ arm angle = 0 
        bottom_right = (self.position[0] - half_width * sin_angle, self.position[1] + half_width * cos_angle)
        bottom_left = (bottom_right[0] - self.arm_length * cos_angle, bottom_right[1] - self.arm_length * sin_angle)
        top_left = (bottom_left[0] + self.arm_width * sin_angle, bottom_left[1] - self.arm_width * cos_angle)
        top_right = (top_left[0] + self.arm_length * cos_angle, top_left[1] + self.arm_length * sin_angle)
        arm_polygon = [bottom_right,
                   bottom_left,
                   top_left,
                   top_right]
        # Bucket polygon 
        bucket_polygon = []
        bucket_width = self.projectile_radius * 1.5
        bucket_center = (top_left[0], top_left[1] - math.sin(self.arm_angle) *  (self.projectile_radius/2))
        for i in range (13): 
            use_angle = (i * 15) * (math.pi/180)
            sin_angle = math.sin(use_angle)
            cos_angle = math.cos(use_angle)
            new_pos = rotate_point_by_angle((bucket_width * cos_angle , bucket_width * sin_angle), self.arm_angle)
            bucket_polygon.append(new_pos)
        for i in range(len(bucket_polygon)):
            bucket_polygon[i] = (bucket_polygon[i][0] + bucket_center[0], bucket_polygon[i][1] + bucket_center[1])
        # Draw arm 
        pygame.draw.polygon(screen, DARK_BROWN, arm_polygon)

        return top_left, bucket_polygon

    def draw(self, screen):
        # Draw firing arm 
        projectile_location, bucket_polygon = self.draw_firing_arm(screen)
        # Draw base of firing arm 
        pygame.draw.circle(screen, BROWN, (self.position[0], self.position[1]), 10)
        pygame.draw.circle(screen, BLACK, (self.position[0], self.position[1]), 6)
        # Draw projectile prior to release
        if not self.projectile_released:
            pygame.draw.circle(screen, MATERIALS[self.projectile_material]['color'], projectile_location, self.projectile_radius)
        # Draw bucket
        pygame.draw.polygon(screen, DARK_METAL, bucket_polygon)

class Projectile:
    def __init__(self, catapult, space):
        self.catapult = catapult 
        self.color = MATERIALS[catapult.projectile_material]['color']
        self.mass = catapult.projectile_mass
        self.radius = catapult.projectile_radius 
        moment = pymunk.moment_for_circle(self.mass, 0, catapult.projectile_radius) 
        self.body = pymunk.Body(self.mass, moment)
        self.body.position = catapult.position[0] - catapult.arm_length * math.cos(catapult.firing_angle), catapult.position[1] - catapult.arm_length * math.sin(catapult.firing_angle)
        self.shape = pymunk.Circle(self.body, self.catapult.projectile_radius)
        self.shape.elasticity = 0.9
        self.shape.friction = 0.5
        self.material = PROJECTILE_MATERIAL
        self.shape.collision_type = COLLIDER_TYPE_PROJECTILE
        space.add(self.body, self.shape)
        
    def launch(self, speed, angle): 
        self.body.velocity = (speed * math.sin(angle), -speed * math.cos(angle))

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.body.position[0]), int(self.body.position[1])), self.radius)

class LevelObject: 
    def __init__(self, position, dimensions, angle, space, material='wood', is_goal = False):
        self.goal = is_goal
        self.material = material
        self.mass = SCALE_FACTOR**2 * dimensions[0] * dimensions[1] * MATERIALS[self.material]['density'] # assumes all objects are 1m into the screen
        self.angle = angle 
        self.dimensions = dimensions 
        self.color = MATERIALS[self.material]['color']
        self.outline_color = BLACK
        body_poly_points = [(-dimensions[0]/2,-dimensions[1]/2),
                            (-dimensions[0]/2,dimensions[1]/2),
                            (dimensions[0]/2,dimensions[1]/2),
                            (dimensions[0]/2,-dimensions[1]/2)]
        moment = pymunk.moment_for_poly(self.mass, body_poly_points, (0, 0))
        self.body = pymunk.Body(self.mass, moment)
        self.body.position = position
        self.poly = pymunk.Poly(self.body, body_poly_points)
        self.poly.friction = 1 
        if self.goal: 
            self.poly.collision_type = COLLIDER_TYPE_GOAL
        space.add(self.body, self.poly)
        
    def draw(self, screen):
        half_width = self.dimensions[0] / 2 
        half_height = self.dimensions[1] / 2 
        bottom_right = (half_width, half_height)
        bottom_left = (-half_width, half_height)
        top_left = (-half_width, -half_height)
        top_right = (half_width, -half_height)
        object_polygon = [bottom_right,
                   bottom_left,
                   top_left,
                   top_right]
        for i in range(len(object_polygon)):
            object_polygon[i] = rotate_point_by_angle(object_polygon[i], self.body.angle)
            object_polygon[i] = (object_polygon[i][0] + self.body.position[0], object_polygon[i][1] + self.body.position[1])
        pygame.draw.polygon(screen, self.color, object_polygon)
        pygame.draw.polygon(screen, self.outline_color, object_polygon, 2)
        

class Level:
    def __init__(self):
        self.objects = []
        self.target = None
        
    # Returns True if the level requires the goal to hit the ground 
    def setup_new_level(self, space, ground_shape): 
        if random.randint(0, 1) == 1: 
            # Level type where target object must hit the ground 
            self.setup_ground_hit_level(space)
            ground_shape.collision_type = COLLIDER_TYPE_GROUND
            return True 
        else:
            # Level type where projectile must hit target object
            self.setup_hit_target_level(space)
            return False 
        
            
    def setup_ground_hit_level(self, space): 
        support_1 = LevelObject((700, CATAPULT_Y_POS - 40), (20,80), 0, space)
        support_2 = LevelObject((800, CATAPULT_Y_POS - 40), (20,80), 0, space)
        bridge = LevelObject((750, CATAPULT_Y_POS - 80), (160,10), 0, space, 'aluminum')
        goal = LevelObject((750, CATAPULT_Y_POS - 100), (50,40), 0, space, 'wood', True)
        goal.color = GOLD 
        self.objects.append(support_1)
        self.objects.append(support_2)
        self.objects.append(bridge)
        self.objects.append(goal)
    
    def setup_hit_target_level(self, space): 
        support_1 = LevelObject((700, CATAPULT_Y_POS - 40), (40,80), 0, space)
        support_2 = LevelObject((800, CATAPULT_Y_POS - 40), (40,80), 0, space)
        support_3 = LevelObject((700, CATAPULT_Y_POS - 120), (20,40), 0, space)
        support_4 = LevelObject((800, CATAPULT_Y_POS - 120), (20,40), 0, space)
        bridge_1 = LevelObject((750, CATAPULT_Y_POS - 80), (160,10), 0, space, 'aluminum')
        bridge_2 = LevelObject((750, CATAPULT_Y_POS - 170), (140,10), 0, space, 'aluminum')
        goal = LevelObject((750, CATAPULT_Y_POS - 100), (40,30), 0, space, 'wood', True)
        goal.color = GOLD 
        self.objects.append(support_1)
        self.objects.append(support_2)
        self.objects.append(support_3)
        self.objects.append(support_4)
        self.objects.append(bridge_1)
        self.objects.append(bridge_2)
        self.objects.append(goal)
    
def draw_tree(screen, pos, height):
    pygame.draw.rect(screen, BROWN, (pos[0], pos[1], 15, height))  
    pygame.draw.circle(screen, DARK_GREEN, (pos[0]+15, pos[1]+4), height/1.8) 
    pygame.draw.circle(screen, GRASS_GREEN, (pos[0], pos[1]), height/2) 
    
def draw_cloud(screen, x, y):
    pygame.draw.circle(screen, WHITE, (x, y), 40) 
    pygame.draw.circle(screen, WHITE, (x+40, y-10), 30) 
    pygame.draw.circle(screen, WHITE, (x-33, y+4), 26) 
    
def draw_mountains(screen):
    mountains_poly_1 = [(0,HEIGHT),
               (200, 200),
               (400, HEIGHT),
               (600, 300),
               (WIDTH, HEIGHT)]
    mountains_poly_2 = [(0,HEIGHT),
               (400, 400),
               (600, HEIGHT),
               (850, 250),
               (WIDTH, HEIGHT)]
    pygame.draw.polygon(screen, (200,200,200), mountains_poly_2)
    pygame.draw.polygon(screen, (160,160,160), mountains_poly_1)

    
def draw_background(screen):
    screen.fill(SKY_BLUE)
    draw_mountains(screen) 
    pygame.draw.rect(screen, GRASS_GREEN, (0, HEIGHT-150, WIDTH, 150))
    draw_tree(screen, (400,HEIGHT-200), 60)
    draw_tree(screen, (500,HEIGHT-210), 60)
    draw_cloud(screen, math.sin(pygame.time.get_ticks() * 0.00005) * WIDTH*0.6, 40)
    draw_cloud(screen, math.sin(pygame.time.get_ticks() * 0.00004 + 4) * WIDTH*0.62, 60)
    draw_cloud(screen, math.sin(pygame.time.get_ticks() * 0.00003 + 8) * WIDTH*0.64, 70)
    
def draw_complete_game_screen(screen): 
    complete_text = COMPLETE_FONT.render(f'YOUR SCORE {SCORE}', False, (255, 255, 255))
    reset_text = RESTART_FONT.render('Press SPACEBAR to play again', False, (255, 255, 255))
    screen.blit(complete_text, (100, HEIGHT/2 - 40))
    screen.blit(reset_text, (100, HEIGHT/2 + 40))
    
def draw_UI(screen, catapult): 
    # Fire button 
    pygame.draw.rect(screen, (200, 0, 0), (FIRE_POS[0]-10, FIRE_POS[1], 60, 22))
    fire_text = UI_FONT.render('FIRE', False, (255, 255, 255))
    screen.blit(fire_text, (FIRE_POS[0],FIRE_POS[1]))
    
    ######################
    # Catapult arm length 
    ######################
    pygame.draw.rect(screen, (100, 100, 100), (ARM_LENGTH_POS[0]-10, ARM_LENGTH_POS[1], 130, 22))
    arm_text = UI_FONT.render('ARM LENGTH', False, (255, 255, 255))
    screen.blit(arm_text, (ARM_LENGTH_POS[0],ARM_LENGTH_POS[1]))
    # Decrement arm length
    points = [(ARM_LENGTH_POS[0] + 15, ARM_LENGTH_POS[1] - 20),
              (ARM_LENGTH_POS[0] + 15, ARM_LENGTH_POS[1] - 40),
              (ARM_LENGTH_POS[0]-5, ARM_LENGTH_POS[1] - 30)]
    pygame.draw.polygon(screen, (40, 40, 40), points)
    pygame.draw.polygon(screen, BLACK, points, 2)
    # Increment arm length 
    points = [(ARM_LENGTH_POS[0] + 95, ARM_LENGTH_POS[1] - 20),
              (ARM_LENGTH_POS[0] + 95, ARM_LENGTH_POS[1] - 40),
              (ARM_LENGTH_POS[0] + 115, ARM_LENGTH_POS[1] - 30)]
    pygame.draw.polygon(screen, (40, 40, 40), points)
    pygame.draw.polygon(screen, BLACK, points, 2)
    # Current arm length 
    arm_text = UI_FONT.render(f'{catapult.arm_length*SCALE_FACTOR:.1f} (m)', False, (255, 255, 255))
    screen.blit(arm_text, (ARM_LENGTH_POS[0] + 32, ARM_LENGTH_POS[1] - 40))
    
    ######################
    # Projectile radius 
    ######################
    pygame.draw.rect(screen, (100, 100, 100), (PROJECTILE_RADIUS_POS[0]-10, PROJECTILE_RADIUS_POS[1], 190, 22))
    arm_text = UI_FONT.render('PROJECTILE RADIUS', False, (255, 255, 255))
    screen.blit(arm_text, (PROJECTILE_RADIUS_POS[0],PROJECTILE_RADIUS_POS[1]))
    # Decrement projectile radius
    points = [(PROJECTILE_RADIUS_POS[0] + PROJECTILE_X_OFFSET, PROJECTILE_RADIUS_POS[1] - 20),
              (PROJECTILE_RADIUS_POS[0] + PROJECTILE_X_OFFSET, PROJECTILE_RADIUS_POS[1] - 40),
              (PROJECTILE_RADIUS_POS[0] + (PROJECTILE_X_OFFSET - 20), PROJECTILE_RADIUS_POS[1] - 30)]
    pygame.draw.polygon(screen, (40, 40, 40), points)
    pygame.draw.polygon(screen, BLACK, points, 2)
    # Increment projectile radius
    points = [(PROJECTILE_RADIUS_POS[0] + 80 + PROJECTILE_X_OFFSET, PROJECTILE_RADIUS_POS[1] - 20),
              (PROJECTILE_RADIUS_POS[0] + 80 + PROJECTILE_X_OFFSET, PROJECTILE_RADIUS_POS[1] - 40),
              (PROJECTILE_RADIUS_POS[0] + 80 + (PROJECTILE_X_OFFSET + 20), PROJECTILE_RADIUS_POS[1] - 30)]
    pygame.draw.polygon(screen, (40, 40, 40), points)
    pygame.draw.polygon(screen, BLACK, points, 2)
    # Current projectile radius 
    rad_text = UI_FONT.render(f'{catapult.projectile_radius*SCALE_FACTOR:.1f} (m)', False, (255, 255, 255))
    screen.blit(rad_text, (PROJECTILE_RADIUS_POS[0] + PROJECTILE_X_OFFSET + 16, PROJECTILE_RADIUS_POS[1] - 40))
    
    ######################
    # Catapult Strength
    ######################
    pygame.draw.rect(screen, (100, 100, 100), (STRENGTH_POS[0]-10, STRENGTH_POS[1], 190, 22))
    arm_text = UI_FONT.render('CATAPULT STRENGTH', False, (255, 255, 255))
    screen.blit(arm_text, (STRENGTH_POS[0],STRENGTH_POS[1]))
    # Decrement catapult strength
    points = [(STRENGTH_POS[0] + STRENGTH_X_OFFSET, STRENGTH_POS[1] - 20),
              (STRENGTH_POS[0] + STRENGTH_X_OFFSET, STRENGTH_POS[1] - 40),
              (STRENGTH_POS[0] + (STRENGTH_X_OFFSET - 20), STRENGTH_POS[1] - 30)]
    pygame.draw.polygon(screen, (40, 40, 40), points)
    pygame.draw.polygon(screen, BLACK, points, 2)
    # Increment catapult strength 
    points = [(STRENGTH_POS[0] + 80 + STRENGTH_X_OFFSET, STRENGTH_POS[1] - 20),
              (STRENGTH_POS[0] + 80 + STRENGTH_X_OFFSET, STRENGTH_POS[1] - 40),
              (STRENGTH_POS[0] + 80 + (STRENGTH_X_OFFSET + 20), STRENGTH_POS[1] - 30)]
    pygame.draw.polygon(screen, (40, 40, 40), points)
    pygame.draw.polygon(screen, BLACK, points, 2)
    # Current catapult strength 
    str_text = UI_FONT.render(f'{catapult.torque / (MAX_TORQUE/100)} %', False, (255, 255, 255))
    screen.blit(str_text, (STRENGTH_POS[0] + STRENGTH_X_OFFSET + 16, STRENGTH_POS[1] - 40))
    
    ######################
    # Firing Angle 
    ######################
    pygame.draw.rect(screen, (100, 100, 100), (FIRING_ANGLE_POS[0]-10, FIRING_ANGLE_POS[1], 140, 22))
    arm_text = UI_FONT.render('FIRING ANGLE', False, (255, 255, 255))
    screen.blit(arm_text, (FIRING_ANGLE_POS[0],FIRING_ANGLE_POS[1]))
    # Decrement catapult strength
    points = [(FIRING_ANGLE_POS[0] + FIRING_ANGLE_X_OFFSET, FIRING_ANGLE_POS[1] - 20),
              (FIRING_ANGLE_POS[0] + FIRING_ANGLE_X_OFFSET, FIRING_ANGLE_POS[1] - 40),
              (FIRING_ANGLE_POS[0] + (FIRING_ANGLE_X_OFFSET - 20), FIRING_ANGLE_POS[1] - 30)]
    pygame.draw.polygon(screen, (40, 40, 40), points)
    pygame.draw.polygon(screen, BLACK, points, 2)
    # Increment catapult strength 
    points = [(FIRING_ANGLE_POS[0] + 80 + FIRING_ANGLE_X_OFFSET, FIRING_ANGLE_POS[1] - 20),
              (FIRING_ANGLE_POS[0] + 80 + FIRING_ANGLE_X_OFFSET, FIRING_ANGLE_POS[1] - 40),
              (FIRING_ANGLE_POS[0] + 80 + (FIRING_ANGLE_X_OFFSET + 20), FIRING_ANGLE_POS[1] - 30)]
    pygame.draw.polygon(screen, (40, 40, 40), points)
    pygame.draw.polygon(screen, BLACK, points, 2)
    # Current catapult strength 
    str_text = UI_FONT.render(f'{catapult.firing_angle * (180/math.pi):.0f} deg', False, (255, 255, 255))
    screen.blit(str_text, (FIRING_ANGLE_POS[0] + FIRING_ANGLE_X_OFFSET + 16, FIRING_ANGLE_POS[1] - 40))
    
    ######################
    # Projectile Material 
    ######################
    pygame.draw.rect(screen, (100, 100, 100), (MATERIAL_POS[0]-10, MATERIAL_POS[1], 210, 22))
    arm_text = UI_FONT.render('PROJECTILE MATERIAL', False, (255, 255, 255))
    screen.blit(arm_text, (MATERIAL_POS[0],MATERIAL_POS[1]))
    # Decrement catapult strength
    points = [(MATERIAL_POS[0] + MATERIAL_X_OFFSET, MATERIAL_POS[1] - 20),
              (MATERIAL_POS[0] + MATERIAL_X_OFFSET, MATERIAL_POS[1] - 40),
              (MATERIAL_POS[0] + (MATERIAL_X_OFFSET - 20), MATERIAL_POS[1] - 30)]
    pygame.draw.polygon(screen, (40, 40, 40), points)
    pygame.draw.polygon(screen, BLACK, points, 2)
    # Increment catapult strength 
    points = [(MATERIAL_POS[0] + 100 + MATERIAL_X_OFFSET, MATERIAL_POS[1] - 20),
              (MATERIAL_POS[0] + 100 + MATERIAL_X_OFFSET, MATERIAL_POS[1] - 40),
              (MATERIAL_POS[0] + 100 + (MATERIAL_X_OFFSET + 20), MATERIAL_POS[1] - 30)]
    pygame.draw.polygon(screen, (40, 40, 40), points)
    pygame.draw.polygon(screen, BLACK, points, 2)
    # Current catapult strength 
    str_text = UI_FONT.render(f'{catapult.projectile_material}', False, (255, 255, 255))
    screen.blit(str_text, (MATERIAL_POS[0] + MATERIAL_X_OFFSET + 16, MATERIAL_POS[1] - 40))

    
def handle_mouse_click(mouse_pos):
    # Fire button 
    if FIRE_POS[0] - 10 <= mouse_pos[0] <= (FIRE_POS[0] - 10) + 60: 
        if FIRE_POS[1] <= mouse_pos[1] <= FIRE_POS[1] + 22: 
            return 'fire'
        
    # Decrement arm length      
    if ARM_LENGTH_POS[0] - 5 <= mouse_pos[0] <= ARM_LENGTH_POS[0] + 15: 
        if ARM_LENGTH_POS[1] - 40 <= mouse_pos[1] <= ARM_LENGTH_POS[1] - 20: 
            return 'decrement_arm'
    # Increment arm length      
    if ARM_LENGTH_POS[0] + 95 <= mouse_pos[0] <= ARM_LENGTH_POS[0] + 115: 
        if ARM_LENGTH_POS[1] - 40 <= mouse_pos[1] <= ARM_LENGTH_POS[1] - 20: 
            return 'increment_arm'
        
    # Decrement projectile radius 
    if PROJECTILE_RADIUS_POS[0] + (PROJECTILE_X_OFFSET - 20) <= mouse_pos[0] <= PROJECTILE_RADIUS_POS[0] + PROJECTILE_X_OFFSET: 
        if PROJECTILE_RADIUS_POS[1] - 40 <= mouse_pos[1] <= PROJECTILE_RADIUS_POS[1] - 20: 
            return 'decrement_radius'
    # Increment projectile radius      
    if PROJECTILE_RADIUS_POS[0] + 80 + PROJECTILE_X_OFFSET <= mouse_pos[0] <= PROJECTILE_RADIUS_POS[0] + 80 + (PROJECTILE_X_OFFSET + 20): 
        if PROJECTILE_RADIUS_POS[1] - 40 <= mouse_pos[1] <= PROJECTILE_RADIUS_POS[1] - 20: 
            return 'increment_radius'
        
    # Decrement catapult strength
    if STRENGTH_POS[0] + (STRENGTH_X_OFFSET - 20) <= mouse_pos[0] <= STRENGTH_POS[0] + STRENGTH_X_OFFSET: 
        if STRENGTH_POS[1] - 40 <= mouse_pos[1] <= STRENGTH_POS[1] - 20: 
            return 'decrement_strength'
    # Increment catapult strength
    if STRENGTH_POS[0] + 80 + STRENGTH_X_OFFSET <= mouse_pos[0] <= STRENGTH_POS[0] + 80 + (STRENGTH_X_OFFSET + 20): 
        if STRENGTH_POS[1] - 40 <= mouse_pos[1] <= STRENGTH_POS[1] - 20: 
            return 'increment_strength'
        
    # Decrement firing angle
    if FIRING_ANGLE_POS[0] + (FIRING_ANGLE_X_OFFSET - 20) <= mouse_pos[0] <= FIRING_ANGLE_POS[0] + FIRING_ANGLE_X_OFFSET: 
        if FIRING_ANGLE_POS[1] - 40 <= mouse_pos[1] <= FIRING_ANGLE_POS[1] - 20: 
            return 'decrement_firing_angle'
    # Increment firing angle
    if FIRING_ANGLE_POS[0] + 80 + FIRING_ANGLE_X_OFFSET <= mouse_pos[0] <= FIRING_ANGLE_POS[0] + 80 + (FIRING_ANGLE_X_OFFSET + 20): 
        if FIRING_ANGLE_POS[1] - 40 <= mouse_pos[1] <= FIRING_ANGLE_POS[1] - 20: 
            return 'increment_firing_angle'
        
    # Decrement material
    if MATERIAL_POS[0] + (MATERIAL_X_OFFSET - 20) <= mouse_pos[0] <= MATERIAL_POS[0] + MATERIAL_X_OFFSET: 
        if MATERIAL_POS[1] - 40 <= mouse_pos[1] <= MATERIAL_POS[1] - 20: 
            return 'decrement_material'
    # Increment material
    if MATERIAL_POS[0] + 80 + MATERIAL_X_OFFSET <= mouse_pos[0] <= MATERIAL_POS[0] + 100 + (MATERIAL_X_OFFSET + 20): 
        if MATERIAL_POS[1] - 40 <= mouse_pos[1] <= MATERIAL_POS[1] - 20: 
            return 'increment_material'

    return None 
 
def main():
    global CATAPULT_OBJECT
    global CURRENT_LEVEL
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    space = pymunk.Space()
    space.gravity = (0, 900)

    # Create ground 
    ground_shape = pymunk.Segment(space.static_body, (0, CATAPULT_Y_POS), (WIDTH, CATAPULT_Y_POS), 1.0)
    ground_shape.friction = 1.0
    space.add(ground_shape)

    # Create Catapult 
    catapult = Catapult()
    CATAPULT_OBJECT = catapult 

    level = Level()
    CURRENT_LEVEL = level 
    ground_type = level.setup_new_level(space, ground_shape)
    # Create collision response for goal 
    if ground_type: 
        goal_col = space.add_collision_handler(COLLIDER_TYPE_GROUND, COLLIDER_TYPE_GOAL)
        goal_col.begin = handle_goal_collision   
    else: 
        goal_col = space.add_collision_handler(COLLIDER_TYPE_PROJECTILE, COLLIDER_TYPE_GOAL)
        goal_col.begin = handle_goal_collision   

    running = True
    
    while running:
        
        draw_background(screen)
        
        if COMPLETE_LEVEL_ON:
            
            draw_complete_game_screen(screen)
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        reset_game()
        else: 
            
            draw_UI(screen, catapult)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        catapult.trigger_fire()
                elif event.type == pygame.MOUSEBUTTONDOWN: 
                    if not catapult.firing and not catapult.resetting: 
                        mouse_pos = pygame.mouse.get_pos() 
                        click_result = handle_mouse_click(mouse_pos)
                        if click_result == 'fire': 
                            catapult.trigger_fire()
                        elif click_result == 'decrement_arm':
                            catapult.decrement_arm_length()
                        elif click_result == 'increment_arm': 
                            catapult.increment_arm_length()
                        elif click_result == 'decrement_radius':
                            catapult.decrement_projectile_radius()
                        elif click_result == 'increment_radius':
                            catapult.increment_projectile_radius()
                        elif click_result == 'decrement_strength':
                            catapult.decrement_catapult_strength()
                        elif click_result == 'increment_strength':
                            catapult.increment_catapult_strength()
                        elif click_result == 'decrement_firing_angle':
                            catapult.decrement_firing_angle()
                        elif click_result == 'increment_firing_angle':
                            catapult.increment_firing_angle()
                        elif click_result == 'decrement_material':
                            catapult.decrement_material()
                        elif click_result == 'increment_material':
                            catapult.increment_material()
                    
            if catapult.firing: 
                catapult.tick_fire(space)
            for projectile in GAME_PROJECTILES: 
                projectile.draw(screen)
            
                
        if catapult.resetting: 
            catapult.tick_reset(space)

        for obj in level.objects:
            obj.draw(screen)

        catapult.draw(screen)
        
        pygame.display.flip()

        clock.tick(FPS)

        space.step(1 / 60)

    pygame.quit()

if __name__ == "__main__":
    main()