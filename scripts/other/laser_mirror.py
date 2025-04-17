import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (160, 160, 160)
RED = (255, 0, 0)
MIRROR_SIZE = 10
MIRROR_THICKNESS = 80
LASER_WIDTH = 40
UI_PADDING = 120
MIN_DISTANCE = 100
ROTATE_RADIUS = 50
MAX_BOUNCES = 10

# Setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Laser & Mirror Simulation")
font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()

# Objects
laser_rect = None
laser_angle = 0
laser_on = False
mirrors = []
dragging_object = None
drag_offset = (0, 0)

# Button
button_rect = pygame.Rect(WIDTH - 100, 10, 90, 50)
button_text = font.render("On/Off", True, BLACK)

def create_mirror_surface():
    visual = pygame.Surface((MIRROR_THICKNESS, MIRROR_SIZE), pygame.SRCALPHA)
    color_map = pygame.Surface((MIRROR_THICKNESS, MIRROR_SIZE))

    # Gray (reflective) on top
    pygame.draw.rect(visual, GRAY, (0, 0, MIRROR_THICKNESS, MIRROR_SIZE // 2))
    pygame.draw.rect(color_map, GRAY, (0, 0, MIRROR_THICKNESS, MIRROR_SIZE // 2))

    # Black (absorptive) on bottom
    pygame.draw.rect(visual, BLACK, (0, MIRROR_SIZE // 2, MIRROR_THICKNESS, MIRROR_SIZE // 2))
    pygame.draw.rect(color_map, BLACK, (0, MIRROR_SIZE // 2, MIRROR_THICKNESS, MIRROR_SIZE // 2))

    return visual, color_map


def check_overlap(new_center):
    new_rect = pygame.Rect(0, 0, MIRROR_THICKNESS, MIRROR_SIZE)
    new_rect.center = new_center

    for m in mirrors:
        if new_rect.colliderect(m["rect"]):
            return True
        dist = math.hypot(m["rect"].centerx - new_center[0], m["rect"].centery - new_center[1])
        if dist < MIN_DISTANCE:
            return True

    if laser_rect:
        dist_laser = math.hypot(laser_rect.centerx - new_center[0], laser_rect.centery - new_center[1])
        if dist_laser < MIN_DISTANCE or new_rect.colliderect(laser_rect):
            return True

    return False

def is_near(center, mouse_pos, radius=ROTATE_RADIUS):
    dx = mouse_pos[0] - center[0]
    dy = mouse_pos[1] - center[1]
    return dx * dx + dy * dy <= radius * radius

def reflect_vector(incident, normal):
    dot = incident[0]*normal[0] + incident[1]*normal[1]
    return (
        incident[0] - 2 * dot * normal[0],
        incident[1] - 2 * dot * normal[1]
    )

def normalize(v):
    length = math.hypot(*v)
    return (v[0]/length, v[1]/length) if length != 0 else (0, 0)

def get_normal_at(mask, point):
    x, y = point
    w, h = mask.get_size()
    x1 = max(x - 1, 0)
    x2 = min(x + 1, w - 1)
    y1 = max(y - 1, 0)
    y2 = min(y + 1, h - 1)
    dx = mask.get_at((x2, y)) - mask.get_at((x1, y))
    dy = mask.get_at((x, y2)) - mask.get_at((x, y1))
    normal = (-dx, -dy)
    return normalize(normal)

def cast_laser(start_pos, direction, mirrors, max_bounces=MAX_BOUNCES):
    path = [start_pos]
    for _ in range(max_bounces):
        closest_dist = float('inf')
        hit_point = None
        new_direction = None

        for mirror in mirrors:
            angle_rad = math.radians(mirror["angle"])
            mirror_surf = mirror["surface"]
            rotated_surf = pygame.transform.rotate(mirror_surf, mirror["angle"])
            mask = pygame.mask.from_surface(rotated_surf)
            rect = rotated_surf.get_rect(center=mirror["rect"].center)

            for i in range(1, 1000):
                test_x = int(start_pos[0] + direction[0] * i)
                test_y = int(start_pos[1] + direction[1] * i)
                if not (0 <= test_x < WIDTH and 0 <= test_y < HEIGHT):
                    break
                rel_x = test_x - rect.left
                rel_y = test_y - rect.top
                if 0 <= rel_x < rect.width and 0 <= rel_y < rect.height:
                    if mask.get_at((rel_x, rel_y)):
                        dist = math.hypot(test_x - start_pos[0], test_y - start_pos[1])
                        if dist < closest_dist:
                            hit_point = (test_x, test_y)
                            # Sample color from rotated color map
                            rotated_map = pygame.transform.rotate(mirror["color_map"], mirror["angle"])
                            color = rotated_map.get_at((rel_x, rel_y))[:3]  # remove alpha

                            if color == GRAY:
                                # Normal vector perpendicular to the mirror surface (based on angle)
                                angle_rad = math.radians(mirror["angle"])
                                normal = (-math.sin(angle_rad), -math.cos(angle_rad))
                                reflected = reflect_vector(direction, normal)
                                new_direction = normalize(reflected)
                            else:
                                new_direction = None

                            closest_dist = dist
                        break

        if hit_point:
            path.append(hit_point)
            if new_direction:
                EPSILON = 1.5  # bigger step to ensure escape
                start_pos = (
                    hit_point[0] + new_direction[0] * EPSILON,
                    hit_point[1] + new_direction[1] * EPSILON
                )

                direction = new_direction
                continue
            else:
                break
        else:
            end_x = start_pos[0] + direction[0] * 1000
            end_y = start_pos[1] + direction[1] * 1000
            path.append((end_x, end_y))
            break

    return path

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos

            if button_rect.collidepoint(event.pos):
                laser_on = not laser_on

            elif event.button == 1:  # Left-click for placing objects
                if laser_rect is None and mouse_x < WIDTH - UI_PADDING:
                    laser_rect = pygame.Rect(mouse_x, mouse_y, LASER_WIDTH, 10)
                elif len(mirrors) < 3 and mouse_x < WIDTH - UI_PADDING:
                    if not check_overlap((mouse_x, mouse_y)):
                        surface, color_map = create_mirror_surface()
                        rect = surface.get_rect(center=(mouse_x, mouse_y))
                        mirrors.append({"surface": surface, "color_map": color_map, "rect": rect, "angle": 0})

            elif event.button == 3:  # Right-click for dragging
                if laser_rect and is_near(laser_rect.center, event.pos):
                    dragging_object = "laser"
                    dx = event.pos[0] - laser_rect.centerx
                    dy = event.pos[1] - laser_rect.centery
                    drag_offset = (dx, dy)
                for mirror in mirrors:
                    if is_near(mirror["rect"].center, event.pos):
                        dragging_object = mirror
                        dx = event.pos[0] - mirror["rect"].centerx
                        dy = event.pos[1] - mirror["rect"].centery
                        drag_offset = (dx, dy)
                        break

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                dragging_object = None

        elif event.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = event.pos
            if event.buttons[0]:
                if laser_rect and is_near(laser_rect.center, event.pos):
                    dx = mouse_x - laser_rect.centerx
                    dy = mouse_y - laser_rect.centery
                    laser_angle = math.degrees(math.atan2(-dy, dx))
                for mirror in mirrors:
                    if is_near(mirror["rect"].center, event.pos):
                        dx = mouse_x - mirror["rect"].centerx
                        dy = mouse_y - mirror["rect"].centery
                        mirror["angle"] = math.degrees(math.atan2(-dy, dx))

            if event.buttons[2]:
                if dragging_object == "laser":
                    laser_rect.centerx = mouse_x - drag_offset[0]
                    laser_rect.centery = mouse_y - drag_offset[1]
                elif isinstance(dragging_object, dict):
                    dragging_object["rect"].centerx = mouse_x - drag_offset[0]
                    dragging_object["rect"].centery = mouse_y - drag_offset[1]

    screen.fill(WHITE)

    if laser_rect:
        rotated_laser = pygame.Surface((LASER_WIDTH, 10), pygame.SRCALPHA)
        rotated_laser.fill(BLACK)
        rotated_laser = pygame.transform.rotate(rotated_laser, laser_angle)
        laser_draw_rect = rotated_laser.get_rect(center=laser_rect.center)
        screen.blit(rotated_laser, laser_draw_rect)

        if laser_on:
            direction = (
                math.cos(math.radians(laser_angle)),
                -math.sin(math.radians(laser_angle))
            )
            laser_path = cast_laser(laser_rect.center, direction, mirrors)
            for i in range(len(laser_path) - 1):
                pygame.draw.line(screen, RED, laser_path[i], laser_path[i + 1], 2)

    for mirror in mirrors:
        rotated = pygame.transform.rotate(mirror["surface"], mirror["angle"])
        draw_rect = rotated.get_rect(center=mirror["rect"].center)
        mirror["rect"] = draw_rect
        screen.blit(rotated, draw_rect)

    pygame.draw.rect(screen, BLACK, button_rect, 2)
    screen.blit(button_text, (button_rect.centerx - button_text.get_width() // 2,
                              button_rect.centery - button_text.get_height() // 2))

    if laser_rect is None:
        prompt = font.render("Click to place laser", True, BLACK)
    elif len(mirrors) < 3:
        prompt = font.render("Click to place mirror (gray reflects, black absorbs)", True, BLACK)
    else:
        prompt = font.render("Left drag = rotate, Right drag = move", True, BLACK)
    screen.blit(prompt, (10, 10))

    pygame.display.flip()
    clock.tick(60)
