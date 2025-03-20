import pygame
import pymunk
import pymunk.pygame_util
from pygame.locals import *

# Constants for simulation dimensions and properties

WIDTH, HEIGHT = 800, 600

# Wrecking ball properties
BALL_RADIUS = 20
ROPE_LENGTH = 200
BALL_COLLISION_TYPE = 1
BALL_ELASTICITY = 0.5
BALL_FRICTION = 0.9
BALL_MASS = 1

# Floor properties
FLOOR_THICKNESS = 20
FLOOR_ELASTICITY = 0.1
FLOOR_FRICTION = 0.9
FLOOR_COLLISION_TYPE = 3

# Structure (target to break) properties
STRUCT_WIDTH = 100
STRUCT_HEIGHT = HEIGHT * 0.7
STRUCT_COLLISION_TYPE = 2
STRUCT_ELASTICITY = 0.1
STRUCT_FRICTION = 0.5
STRUCT_MASS = 100

# Color definitions (RGBA)
BG_COLOR = (120, 200, 250, 255)
FLOOR_COLOR = (25, 100, 20, 255)
STRUCT_COLOR = (100, 100, 100, 255)
BALL_COLOR = (200, 50, 50, 255)
FONT_COLOR = (0, 0, 0, 255)

# Space and gravity settings
GRAVITY = (0, 981)

# Simulation settings
FPS = 60
BREAK_STRUCTURE_MS_THROTTLE = 100
KINETIC_ENERGY_MS_THROTLE = 200
BREAK_STRUCTURE_MIN_BALL_FORCE = BALL_MASS * 100
BREAK_STRUCTURE_MIN_STRUCT_FORCE = STRUCT_MASS * 5


class Simulation:
    """
    Simulation class to run a physics simulation of a wrecking ball breaking a structure.

    This class initializes the pygame window, sets up the pymunk space with gravity,
    and creates the simulation objects including a wrecking ball, floor, and a breakable structure.
    It also handles collision events to break the structure when impacted with sufficient force.
    """

    def __init__(self):
        """
        Initialize the simulation.

        Sets up the pygame display, clock, and font for text output.
        Initializes the pymunk space with gravity and creates the simulation objects:
          - A wrecking ball with a static rope anchor.
          - A static floor to prevent objects from falling off-screen.
          - A breakable structure.
        Also configures collision handling.
        """
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.paused = False

        # Initialize font for displaying simulation information
        self.font = pygame.font.Font(None, 24)
        self.kinetic_energy = 0
        self.last_text_update = self.clock.get_time()

        # Set up the pymunk physics space with gravity
        self.space = pymunk.Space()
        self.space.gravity = GRAVITY
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)

        # Set up default collision handler with post-solve callback to handle impact events
        self.handler = self.space.add_default_collision_handler()
        self.handler.post_solve = self.post_solve
        self.last_break_time = 0
        self.total_ball_breaks = 0
        self.total_struct_breaks = 0
        self.last_impact_force = 0

        # Create the wrecking ball with its rope anchor
        self.ball_anchor_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.ball_anchor_body.position = (
            WIDTH // 3,
            (HEIGHT // 2) - (ROPE_LENGTH // 2),
        )
        moment = pymunk.moment_for_circle(BALL_MASS, 0, BALL_RADIUS)
        self.ball_body = pymunk.Body(BALL_MASS, moment)
        self.ball_body.position = (WIDTH // 3, (HEIGHT // 2) + (ROPE_LENGTH // 2))
        self.ball_shape = pymunk.Circle(self.ball_body, BALL_RADIUS)
        self.ball_shape.collision_type = BALL_COLLISION_TYPE
        self.ball_shape.elasticity = BALL_ELASTICITY
        self.ball_shape.friction = BALL_FRICTION
        self.ball_shape.color = BALL_COLOR
        pin_joint = pymunk.PinJoint(
            self.ball_anchor_body, self.ball_body, (0, 0), (0, 0)
        )
        self.space.add(
            self.ball_anchor_body, self.ball_body, self.ball_shape, pin_joint
        )

        # Create a static floor segment to keep objects from falling off-screen
        floor_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        floor_body.position = (0, HEIGHT - FLOOR_THICKNESS)
        floor_shape = pymunk.Segment(floor_body, (0, 0), (WIDTH, 0), FLOOR_THICKNESS)
        floor_shape.collision_type = FLOOR_COLLISION_TYPE
        floor_shape.elasticity = FLOOR_ELASTICITY
        floor_shape.friction = FLOOR_FRICTION
        floor_shape.color = FLOOR_COLOR
        self.space.add(floor_body, floor_shape)

        # Create the structure that will be broken by the wrecking ball impact
        moment = pymunk.moment_for_box(STRUCT_MASS, (STRUCT_WIDTH, STRUCT_HEIGHT))
        structure_body = pymunk.Body(STRUCT_MASS, moment)
        structure_body.position = (
            (WIDTH // 2),
            HEIGHT - (STRUCT_HEIGHT // 2) - FLOOR_THICKNESS,
        )
        structure_shape = pymunk.Poly.create_box(
            structure_body, (STRUCT_WIDTH, STRUCT_HEIGHT), 1
        )
        structure_shape.elasticity = STRUCT_ELASTICITY
        structure_shape.friction = STRUCT_FRICTION
        structure_shape.color = STRUCT_COLOR
        structure_shape.collision_type = STRUCT_COLLISION_TYPE
        self.space.add(structure_body, structure_shape)

    def post_solve(self, arbiter, space, data):
        """
        Collision post-solve callback to handle impact events.

        Determines whether the collision between the wrecking ball or structure
        and another object produces enough force to break the structure.
        It applies a time-based throttle to prevent rapid consecutive breaks.
        """
        ball_shape = None
        struct_shape = None
        force = None
        break_struct = False
        ball_induced = False

        # Identify collision shapes and ignore collisions with the floor
        for shape in arbiter.shapes:
            if shape.collision_type == FLOOR_COLLISION_TYPE:
                return
            elif shape.collision_type == BALL_COLLISION_TYPE:
                ball_shape = shape
            elif shape.collision_type == STRUCT_COLLISION_TYPE:
                struct_shape = shape

        # Calculate impact force if the ball is involved in the collision
        if ball_shape:
            force = ball_shape.body.velocity.length * ball_shape.body.mass
            self.last_impact_force = force
            if force > BREAK_STRUCTURE_MIN_BALL_FORCE:
                ball_induced = True
                break_struct = True
        else:
            # If the collision does not involve the ball, use structure's force
            force = struct_shape.body.velocity.length * struct_shape.body.mass
            if force > BREAK_STRUCTURE_MIN_STRUCT_FORCE:
                break_struct = True

        # If impact force is sufficient, proceed to break the structure
        if break_struct:
            # Throttle the break events to avoid too frequent splits
            current_time = pygame.time.get_ticks()
            if current_time - self.last_break_time < BREAK_STRUCTURE_MS_THROTTLE:
                return
            self.last_break_time = current_time

            # Update break counters based on the source of impact
            if ball_induced:
                self.total_ball_breaks += 1
            else:
                self.total_struct_breaks += 1

            # Call the method to split the structure into two fragments
            self.break_structure(struct_shape, arbiter)

    def break_structure(self, shape, arbiter):
        """
        Break the structure by splitting its polygon into two fragments.

        Uses collision data to determine the splitting line and divides the structure's
        polygon into two new polygons. New physics bodies are then created for each fragment.
        """
        # Check for at least one contact point in the collision
        if len(arbiter.contact_point_set.points) == 0:
            return

        # Compute the average collision point from all contact points
        collision_points = [p.point_a for p in arbiter.contact_point_set.points]
        collision_point = sum(collision_points, pymunk.Vec2d(0, 0)) / len(
            collision_points
        )

        # Calculate the collision impulse and derive the force direction
        impulse = arbiter.total_impulse
        if impulse.length == 0:
            return
        force_direction = impulse.normalized()

        # Define a splitting line perpendicular to the force direction
        split_dir = force_direction.perpendicular().normalized()
        line_normal = split_dir

        # Obtain the structure's polygon vertices in world coordinates
        orig_body = shape.body
        local_vertices = shape.get_vertices()
        world_vertices = [orig_body.local_to_world(v) for v in local_vertices]

        # Helper function to split a polygon along a line defined by a point and a normal vector
        def split_polygon(vertices, line_point, line_normal):
            poly1 = []
            poly2 = []
            n = len(vertices)
            # Process each edge of the polygon
            for i in range(n):
                cur = vertices[i]
                nxt = vertices[(i + 1) % n]
                # Compute signed distances from the splitting line
                cur_dist = (cur - line_point).dot(line_normal)
                nxt_dist = (nxt - line_point).dot(line_normal)
                # Classify the current vertex to a fragment based on its signed distance
                if cur_dist >= 0:
                    poly1.append(cur)
                else:
                    poly2.append(cur)
                # Check if the edge crosses the splitting line and compute intersection if so
                if cur_dist * nxt_dist < 0:
                    edge = nxt - cur
                    t = -(cur - line_point).dot(line_normal) / (edge.dot(line_normal))
                    intersection = cur + edge * t
                    poly1.append(intersection)
                    poly2.append(intersection)
            return poly1, poly2

        # Split the polygon into two fragments using the collision point and line normal
        poly1, poly2 = split_polygon(world_vertices, collision_point, line_normal)

        # Ensure both fragments have enough vertices to form valid polygons
        if len(poly1) < 3 or len(poly2) < 3:
            return

        # Helper function to compute the centroid of a polygon using the shoelace formula
        def compute_centroid(vertices):
            area = 0
            C = pymunk.Vec2d(0, 0)
            n = len(vertices)
            # Loop through vertices to compute area and weighted vertex sum
            for i in range(n):
                cur = vertices[i]
                nxt = vertices[(i + 1) % n]
                cross = cur.x * nxt.y - nxt.x * cur.y
                area += cross
                C += (cur + nxt) * cross
            if area == 0:
                return vertices[0]  # Fallback for degenerate polygon
            area *= 0.5
            return C / (6 * area)

        # Compute centroids for the two new polygon fragments
        centroid1 = compute_centroid(poly1)
        centroid2 = compute_centroid(poly2)

        # Convert the world vertices to local coordinates relative to each fragment's centroid
        local_poly1 = [v - centroid1 for v in poly1]
        local_poly2 = [v - centroid2 for v in poly2]

        # Remove the original structure from the physics space
        self.space.remove(shape, orig_body)

        # Assume equal mass distribution for the fragments
        mass_fragment = orig_body.mass / 2
        moment1 = pymunk.moment_for_poly(mass_fragment, local_poly1)
        moment2 = pymunk.moment_for_poly(mass_fragment, local_poly2)

        # Create new physics body and shape for the first fragment
        body1 = pymunk.Body(mass_fragment, moment1)
        body1.position = centroid1
        new_shape1 = pymunk.Poly(body1, local_poly1, radius=1)
        new_shape1.elasticity = STRUCT_ELASTICITY
        new_shape1.friction = STRUCT_FRICTION
        new_shape1.color = STRUCT_COLOR
        new_shape1.collision_type = STRUCT_COLLISION_TYPE

        # Create new physics body and shape for the second fragment
        body2 = pymunk.Body(mass_fragment, moment2)
        body2.position = centroid2
        new_shape2 = pymunk.Poly(body2, local_poly2, radius=1)
        new_shape2.elasticity = STRUCT_ELASTICITY
        new_shape2.friction = STRUCT_FRICTION
        new_shape2.color = STRUCT_COLOR
        new_shape2.collision_type = STRUCT_COLLISION_TYPE

        # Add both new fragments to the physics space
        self.space.add(body1, new_shape1, body2, new_shape2)

    def run(self):
        """
        Run the main simulation loop.

        Handles event processing, updates the physics simulation, renders the scene,
        and displays simulation data such as kinetic energy, impact force, and break counts.
        """
        running = True
        while running:
            # Process pygame events
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN:
                    # Pause the simulation with space bar or 'p'
                    if event.key == K_SPACE or event.key == K_p:
                        self.paused = not self.paused
                    # Reset the simulation with 'r'
                    elif event.key == K_r:
                        running = False
                        return True
                    # Quit the simulation with escape or 'q'
                    elif event.key == K_ESCAPE or event.key == K_q:
                        running = False
                        return False

            # Update the wrecking ball's anchor position to follow the mouse
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.ball_anchor_body.position = (mouse_x, mouse_y)

            # Step the physics simulation forward by one frame
            if not self.paused:
                self.space.step(1 / FPS)

            # Clear the screen with the background color
            self.screen.fill(BG_COLOR)
            # Draw all physics objects using pymunk's debug draw
            self.space.debug_draw(self.draw_options)

            # Update kinetic energy display at throttled intervals
            current_time = pygame.time.get_ticks()
            if current_time - self.last_text_update > KINETIC_ENERGY_MS_THROTLE:
                self.kinetic_energy = self.ball_body.kinetic_energy
                self.last_text_update = current_time

            # Render text for current kinetic energy of the wrecking ball
            text = self.font.render(
                f"Current Wrecking Ball Kinetic Energy: {self.kinetic_energy:.2f} J",
                True,
                FONT_COLOR,
            )
            self.screen.blit(text, (10, 10))

            # Render text for the last impact force measured
            text = self.font.render(
                f"Last Impact Force: {self.last_impact_force:.2f} N", True, FONT_COLOR
            )
            self.screen.blit(text, (10, 34))

            # Render text for the total number of breaks caused by the wrecking ball
            text = self.font.render(
                f"Total Wrecking Ball Breaks: {self.total_ball_breaks}",
                True,
                FONT_COLOR,
            )
            self.screen.blit(text, (10, 58))

            # Render text for the total number of breaks from structural self-collisions
            text = self.font.render(
                f"Total Structural Self Breaks: {self.total_struct_breaks}",
                True,
                FONT_COLOR,
            )
            self.screen.blit(text, (10, 82))

            # Update the display and control the frame rate
            pygame.display.flip()
            self.clock.tick(FPS)


def main():
    """
    Main function to initialize and run the simulation.

    Initializes pygame, creates an instance of the Simulation class,
    and starts the simulation loop. Allows for simulation resets or exit based on user input.
    """
    pygame.init()

    # Loop to allow resetting the simulation
    reset = True
    while reset:
        sim = Simulation()
        reset = sim.run()
    pygame.quit()


if __name__ == "__main__":
    main()