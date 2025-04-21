import pygame
import random
import math

# Window dimensions
WIDTH, HEIGHT = 800, 600

# Color palette
SKY_BLUE = (173, 216, 230)
UMBRELLA_COLOR = (6, 64, 43)
RAIN_COLOR = (0, 0, 255)

# Umbrella properties
UMBRELLA_ARC = 150

# Rain properties
RAIN_DROP_SIZE = 1.5

class RainDrop:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(-HEIGHT, 0)
        self.velocity_x = 0  # pixels/frame
        self.velocity_y = 0  # pixels/frame
        self.size = RAIN_DROP_SIZE
        self.mass = random.uniform(0.1, 1.0)  # Random mass between 0.1 and 1.0 (grams or arbitrary unit)
        self.coefficient_of_restitution = 0.55  # Elasticity (COR) - Amount of bounce

    def update(self, umbrella_x, umbrella_y):
        gravity = 0.2  # pixels/frame²
        self.velocity_y += gravity
        self.x += self.velocity_x
        self.y += self.velocity_y

        # Check if the drop is inside the umbrella radius before applying any movement
        dx = self.x - umbrella_x
        dy = self.y - umbrella_y
        distance = math.sqrt(dx**2 + dy**2)

        if distance < UMBRELLA_ARC:  # If the drop is inside the umbrella arc
            norm_dx = dx / distance
            norm_dy = dy / distance
            # Correct the position to be exactly on the circle boundary
            self.x = umbrella_x + norm_dx * UMBRELLA_ARC
            self.y = umbrella_y + norm_dy * UMBRELLA_ARC

        # Now check if the drop is above the umbrella and within the arc radius
        if distance < UMBRELLA_ARC and self.y < umbrella_y:
            # Reflect the velocity based on the umbrella surface
            norm_dx = dx / distance
            norm_dy = dy / distance
            dot = self.velocity_x * norm_dx + self.velocity_y * norm_dy

            # Update velocities using the COR (coefficient of restitution)
            self.velocity_x -= 2 * dot * norm_dx * self.coefficient_of_restitution
            self.velocity_y -= 2 * dot * norm_dy * self.coefficient_of_restitution
        

    def draw(self, screen):
        pygame.draw.circle(screen, RAIN_COLOR, (int(self.x), int(self.y)), self.size)

def draw_umbrella(screen, umbrella_x, umbrella_y):
    # Set the start and end angles for the top semi-circle (180 to 360 degrees)
    start_angle = math.radians(0)
    end_angle = math.radians(180)
    
    # Draw the arc (outline)
    pygame.draw.arc(screen, UMBRELLA_COLOR, 
                    (umbrella_x - UMBRELLA_ARC, umbrella_y - UMBRELLA_ARC, 
                     UMBRELLA_ARC * 2, UMBRELLA_ARC * 2), 
                    start_angle, end_angle, 1)  # 1 is the line width

    # Fill the top half of the circle (concave downward)
    points = []
    for angle in range(0, 181):  # 0 to 180 degrees
        rad = math.radians(angle)
        x = umbrella_x + UMBRELLA_ARC * math.cos(rad)
        y = umbrella_y - UMBRELLA_ARC * math.sin(rad)  # Subtract to move upwards
        points.append((x, y))
    points.append((umbrella_x + UMBRELLA_ARC, umbrella_y))  # Right side point
    points.append((umbrella_x - UMBRELLA_ARC, umbrella_y))  # Left side point
    pygame.draw.polygon(screen, UMBRELLA_COLOR, points)

    # Draw the handle with a visible tip above the umbrella arc
    handle_width = 3
    handle_tip = 160  # how much the handle peeks above the arc
    handle_length = 270 # total length including the tip

    handle_start_y = umbrella_y - handle_tip  # start a little higher
    handle_end_y = handle_start_y + handle_length  # same total length

    pygame.draw.line(screen, UMBRELLA_COLOR, (umbrella_x, handle_start_y), 
                 (umbrella_x, handle_end_y), handle_width)



    # Draw the curved hook
    hook_radius = 6  # use a fixed small radius instead of handle_width*2
    hook_thickness = handle_width  # same as line

    # Align the left edge of the arc with the handle
    hook_center_x = umbrella_x + hook_radius
    hook_center_y = handle_end_y - hook_thickness // 2

    hook_rect = pygame.Rect(
        hook_center_x - hook_radius,
        hook_center_y - hook_radius,
        hook_radius * 2,
        hook_radius * 2
    )

    # Draw a smooth arc (downward-facing hook)
    pygame.draw.arc(screen, UMBRELLA_COLOR, hook_rect, math.radians(180), math.radians(360), hook_thickness)


    # Draw arc from 180° to 360° (flat on top, curve on bottom)
    pygame.draw.arc(screen, UMBRELLA_COLOR, hook_rect, math.radians(180), math.radians(360), handle_width)




def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    umbrella_x, umbrella_y = WIDTH // 2, HEIGHT // 2
    rain_drops = []
    for _ in range(100):
        drop = RainDrop()
        drop.y = random.randint(-HEIGHT * 3, 0)  # Some far above the screen
        rain_drops.append(drop)

    spawn_timer = 0
    SPAWN_INTERVAL = 0  # lower = more drops per second
    DROPS_PER_SPAWN = 7

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        mouse_x, mouse_y = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0]:  # Left mouse button
            umbrella_x, umbrella_y = mouse_x, mouse_y

        screen.fill(SKY_BLUE)

        spawn_timer += 1
        if spawn_timer >= SPAWN_INTERVAL:
            for _ in range(DROPS_PER_SPAWN):
                rain_drops.append(RainDrop())
            spawn_timer = 0

        for rain_drop in rain_drops:
            rain_drop.update(umbrella_x, umbrella_y)
            rain_drop.draw(screen)

            
            # Check if rain drop has hit the ground
            if rain_drop.y > HEIGHT - 10:
                # Simulate splatter
                pygame.draw.circle(screen, RAIN_COLOR, (rain_drop.x, rain_drop.y), rain_drop.size * 1.5)
                rain_drops.remove(rain_drop)

        # Draw umbrella
        draw_umbrella(screen, umbrella_x, umbrella_y)




        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
