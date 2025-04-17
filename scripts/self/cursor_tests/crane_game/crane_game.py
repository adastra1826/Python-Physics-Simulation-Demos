import pymunk
import pymunk.pygame_util
import pygame
import math

pygame.init()

FPS = 60 
WIDTH, HEIGHT = 800, 800 

SPACE_GRAVITY = (0, 981)  
SPACE_DAMPING = 0.9  

GROUND_THICKNESS = 10  
GROUND_ELASTICITY = 0.1  
GROUND_FRICTION = 0.5  

CRANE_BASE_WIDTH, CRANE_BASE_HEIGHT = 50, 50  
BOOM_Y_POS = 300  
BOOM_THICKNESS = 10  
BOOM_LENGTH = WIDTH - 300  
COUNTER_BOOM_LENGTH = BOOM_LENGTH / 4  
MAST_HEIGHT = HEIGHT - GROUND_THICKNESS - CRANE_BASE_HEIGHT - BOOM_Y_POS  
MAST_THICKNESS = 10  

COUNTERWEIGHT_WIDTH, COUNTERWEIGHT_HEIGHT = 30, 30  
COUNTERWEIGHT_MASS = 10  

TROLLEY_WIDTH, TROLLEY_HEIGHT = 20, 20  
TROLLEY_MIN_X = TROLLEY_WIDTH * 2  
TROLLEY_MAX_X = BOOM_LENGTH - TROLLEY_WIDTH  

HOOK_WIDTH, HOOK_HEIGHT = 10, 10  
HOOK_MASS = 1  

OBSTACLE_WIDTH, OBSTACLE_HEIGHT = 30, 30  
OBSTACLE_MASS = 10  
OBSTACLE_ELASTICITY = 0.9  
OBSTACLE_FRICTION = 0.5  

CONTAINER_WIDTH, CONTAINER_HEIGHT = OBSTACLE_WIDTH * 4, OBSTACLE_HEIGHT * 5  
CONTAINER_WALL_THICKNESS = BOOM_THICKNESS / 2  
CONTAINER_ELASTICITY = 0.7  
CONTAINER_FRICTION = 0.5  

INITIAL_ROPE_LENGTH = 100  
ROPE_STIFFNESS = 1000  
ROPE_DAMPING = 60  
MIN_ROPE_LENGTH = 20  
MAX_ROPE_LENGTH = 500  

K_MOVE_LEFT = pygame.K_a  
K_MOVE_RIGHT = pygame.K_d  
K_TROLLEY_LEFT = pygame.K_j  
K_TROLLEY_RIGHT = pygame.K_l  
K_HOOK_UP = pygame.K_i  
K_HOOK_DOWN = pygame.K_k  
K_ATTACH = pygame.K_w  
K_DETACH = pygame.K_w

CRANE_MOVE_SPEED = 1  
TROLLEY_MOVE_SPEED = 3  
ROPE_MOVE_SPEED = 3  

BACKGROUND_COLOR = (173, 216, 230, 255)  
CRANE_COLOR = (255, 215, 0, 255)  
TROLLEY_COLOR = (255, 165, 0, 255)  
HOOK_COLOR = (255, 0, 0, 255)  
CONTAINER_COLOR = (0, 0, 255, 255)  
GROUND_COLOR = (139, 69, 19, 255)  
OBSTACLE_COLOR = (105, 105, 105, 255)  
CAN_GRAB_COLOR = (10, 255, 10, 255)  
CANNOT_GRAB_COLOR = (255, 10, 10, 255)  

def simulate():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    space = pymunk.Space()
    space.gravity = SPACE_GRAVITY
    space.damping = SPACE_DAMPING

    objects_in_container = 0

    ground_body = pymunk.Body(body_type=pymunk.Body.STATIC)
    ground_shape = pymunk.Segment(ground_body, (0, HEIGHT - GROUND_THICKNESS), (WIDTH, HEIGHT - GROUND_THICKNESS), 5)
    ground_shape.elasticity = GROUND_ELASTICITY
    ground_shape.friction = GROUND_FRICTION
    ground_shape.color = GROUND_COLOR
    space.add(ground_body, ground_shape)

    crane_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)

    crane_body.position = (100, HEIGHT - GROUND_THICKNESS - CRANE_BASE_HEIGHT / 2)
    crane_base_shape = pymunk.Poly.create_box(crane_body, size=(CRANE_BASE_WIDTH, CRANE_BASE_HEIGHT))
    crane_base_shape.color = CRANE_COLOR
    mast_shape = pymunk.Segment(crane_body, (0, -CRANE_BASE_HEIGHT / 2), (0, -CRANE_BASE_HEIGHT / 2 - MAST_HEIGHT), BOOM_THICKNESS)
    mast_shape.color = CRANE_COLOR
    boom_shape = pymunk.Segment(crane_body, (0, -CRANE_BASE_HEIGHT / 2 - MAST_HEIGHT), (BOOM_LENGTH, - CRANE_BASE_HEIGHT / 2 - MAST_HEIGHT), BOOM_THICKNESS)
    boom_shape.color = CRANE_COLOR
    counter_boom_shape = pymunk.Segment(crane_body, (0, -CRANE_BASE_HEIGHT / 2 - MAST_HEIGHT), (-COUNTER_BOOM_LENGTH, -CRANE_BASE_HEIGHT / 2 - MAST_HEIGHT), BOOM_THICKNESS)
    counter_boom_shape.color = CRANE_COLOR
    counterweight_shape = pymunk.Segment(crane_body, (-COUNTER_BOOM_LENGTH, -CRANE_BASE_HEIGHT / 2 - MAST_HEIGHT + BOOM_THICKNESS), (-COUNTER_BOOM_LENGTH, -CRANE_BASE_HEIGHT / 2 - MAST_HEIGHT + BOOM_THICKNESS - COUNTERWEIGHT_HEIGHT), COUNTERWEIGHT_WIDTH)
    counterweight_shape.color = CRANE_COLOR
    space.add(crane_body, crane_base_shape, mast_shape, boom_shape, counter_boom_shape, counterweight_shape)

    trolley_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
    trolley_body.position = (crane_body.position.x + TROLLEY_WIDTH * 2, crane_body.position.y - CRANE_BASE_HEIGHT / 2 - MAST_HEIGHT + BOOM_THICKNESS + TROLLEY_HEIGHT / 2)
    trolley_shape = pymunk.Poly.create_box(trolley_body, size=(TROLLEY_WIDTH, TROLLEY_HEIGHT))
    trolley_shape.color = TROLLEY_COLOR
    space.add(trolley_body, trolley_shape)

    hook_moment = pymunk.moment_for_box(HOOK_MASS, (HOOK_WIDTH, HOOK_HEIGHT))
    hook_body = pymunk.Body(mass=HOOK_MASS, moment=hook_moment)
    hook_body.position = (trolley_body.position.x, trolley_body.position.y + TROLLEY_HEIGHT / 2 + INITIAL_ROPE_LENGTH)
    hook_shape = pymunk.Poly.create_box(hook_body, size=(HOOK_WIDTH, HOOK_HEIGHT))
    hook_shape.color = HOOK_COLOR
    space.add(hook_body, hook_shape)

    rope_length = INITIAL_ROPE_LENGTH
    rope = pymunk.DampedSpring(trolley_body, hook_body, (0, TROLLEY_HEIGHT / 2), (0, -HOOK_HEIGHT / 2), rope_length, ROPE_STIFFNESS, ROPE_DAMPING)
    space.add(rope)

    objects = []
    for i in range(8):
        object_moment = pymunk.moment_for_box(OBSTACLE_MASS, (OBSTACLE_WIDTH, OBSTACLE_HEIGHT))
        object_body = pymunk.Body(mass=OBSTACLE_MASS, moment=object_moment)
        object_body.position = (crane_body.position.x + 100 + i * (OBSTACLE_WIDTH * 2), HEIGHT - GROUND_THICKNESS - OBSTACLE_HEIGHT / 2)
        object_shape = pymunk.Poly.create_box(object_body, size=(OBSTACLE_WIDTH, OBSTACLE_HEIGHT))
        object_shape.elasticity = OBSTACLE_ELASTICITY
        object_shape.friction = OBSTACLE_FRICTION
        object_shape.color = OBSTACLE_COLOR
        space.add(object_body, object_shape)
        objects.append((object_body, object_shape))

    container_body = pymunk.Body(body_type=pymunk.Body.STATIC)
    container_body.position = (WIDTH - CONTAINER_WIDTH / 2 - OBSTACLE_WIDTH, HEIGHT - GROUND_THICKNESS - CONTAINER_WALL_THICKNESS)
    space.add(container_body)
    edges = [
        ((-CONTAINER_WIDTH / 2, -CONTAINER_HEIGHT), (-CONTAINER_WIDTH / 2, 0)),
        ((-CONTAINER_WIDTH / 2, 0), (CONTAINER_WIDTH / 2, 0)),
        ((CONTAINER_WIDTH / 2, 0), (CONTAINER_WIDTH / 2, -CONTAINER_HEIGHT)),
    ]
    for edge in edges:
        container_shape = pymunk.Segment(container_body, edge[0], edge[1], CONTAINER_WALL_THICKNESS)
        container_shape.elasticity = CONTAINER_ELASTICITY
        container_shape.friction = CONTAINER_FRICTION
        space.add(container_shape)

    draw_options = pymunk.pygame_util.DrawOptions(screen)

    attached_object = None  
    paused = False  
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == K_ATTACH or event.key == K_DETACH:
                    if attached_object is None:
                        for obj in objects:
                            if (
                                hook_body.position.x > obj[0].position.x - OBSTACLE_WIDTH / 2 and 
                                hook_body.position.x < obj[0].position.x + OBSTACLE_WIDTH / 2 and
                                hook_body.position.y > obj[0].position.y - OBSTACLE_HEIGHT / 2 - HOOK_HEIGHT
                            ):
                                joint = pymunk.PivotJoint(hook_body, obj[0], hook_body.position)
                                joint.max_force = math.inf
                                space.add(joint)
                                attached_object = obj
                                break
                    else:
                        for joint in space.constraints:
                            if isinstance(joint, pymunk.PivotJoint) and (joint.a == hook_body or joint.b == hook_body):
                                space.remove(joint)
                        attached_object = None
                elif event.key == pygame.K_SPACE:
                    paused = not paused  
                elif event.key == pygame.K_r:
                    return True  
                elif event.key == pygame.K_q:
                    return False  

        keys = pygame.key.get_pressed()
        if keys[K_MOVE_LEFT]:
            crane_body.position = (crane_body.position.x - CRANE_MOVE_SPEED, crane_body.position.y)
            trolley_body.position = (trolley_body.position.x - CRANE_MOVE_SPEED, trolley_body.position.y)
        if keys[K_MOVE_RIGHT]:
            crane_body.position = (crane_body.position.x + CRANE_MOVE_SPEED, crane_body.position.y)
            trolley_body.position = (trolley_body.position.x + CRANE_MOVE_SPEED, trolley_body.position.y)
        if keys[K_HOOK_UP]:
            rope_length = max(MIN_ROPE_LENGTH, rope_length - ROPE_MOVE_SPEED)
            rope.rest_length = rope_length
        if keys[K_HOOK_DOWN]:
            rope_length = min(MAX_ROPE_LENGTH, rope_length + ROPE_MOVE_SPEED)
            rope.rest_length = rope_length
        if keys[K_TROLLEY_LEFT]:
            trolley_body.position = (max(TROLLEY_MIN_X + crane_body.position.x, trolley_body.position.x - TROLLEY_MOVE_SPEED), trolley_body.position.y)
        if keys[K_TROLLEY_RIGHT]:
            trolley_body.position = (min(TROLLEY_MAX_X + crane_body.position.x, trolley_body.position.x + TROLLEY_MOVE_SPEED), trolley_body.position.y)

        objects_in_container = 0
        for obj in objects:
            if (obj[0].position.x > WIDTH - CONTAINER_WIDTH - OBSTACLE_WIDTH and 
                obj[0].position.x < WIDTH - OBSTACLE_WIDTH and
                obj[0].position.y > HEIGHT - GROUND_THICKNESS - CONTAINER_HEIGHT and
                obj[0].position.y < HEIGHT - GROUND_THICKNESS):
                objects_in_container += 1

        can_grab = False
        for obj in objects:
            if (hook_body.position.x > obj[0].position.x - OBSTACLE_WIDTH / 2 and 
                hook_body.position.x < obj[0].position.x + OBSTACLE_WIDTH / 2 and
                hook_body.position.y > obj[0].position.y - OBSTACLE_HEIGHT / 2 - HOOK_HEIGHT):
                can_grab = True
                break

        font = pygame.font.Font(None, 24)
        controls = [
            "Controls:",
            "A/D - Move crane left/right",
            "J/L - Move trolley left/right",
            "I/K - Raise/lower hook",
            "W - Attach/detach objects",
            "Space - Pause simulation",
            "R - Reset simulation",
            "Q - Quit"
        ]
        
        controls.append(f"Objects in container: {objects_in_container}/{len(objects)}")
        
        grab_text = "Can grab" if can_grab else "Cannot grab"
        controls.append(grab_text)
        
        line_height = 25
        total_height = len(controls) * line_height
        
        screen.fill(BACKGROUND_COLOR)
        
        space.debug_draw(draw_options)
        
        pygame.draw.line(screen, HOOK_COLOR, 
                         (trolley_body.position.x, trolley_body.position.y + TROLLEY_HEIGHT / 2),
                         (hook_body.position.x, hook_body.position.y - HOOK_HEIGHT / 2), 2)
        
        text_surface = pygame.Surface((250, total_height + 10))
        text_surface.set_alpha(128)
        text_surface.fill((255, 255, 255))
        screen.blit(text_surface, (10, 10))
        
        for i, text in enumerate(controls):
            if i == len(controls) - 1:  
                text_color = CAN_GRAB_COLOR if can_grab else CANNOT_GRAB_COLOR
            else:
                text_color = (0, 0, 0)
            
            text_surface = font.render(text, True, text_color)
            screen.blit(text_surface, (15, 15 + i * line_height))
        
        pygame.display.flip()
        
        clock.tick(60)

        if not paused:
            space.step(1 / FPS)

def main():
    reset = True
    while reset:
        reset = simulate()

    pygame.quit()

if __name__ == '__main__':
    main()

