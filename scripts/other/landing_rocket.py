"""
Rocket Landing Physics Simulation.

This simulation models the dynamics of a rocket attempting to land vertically
on a designated landing pad. It demonstrates principles of rocket propulsion,
momentum conservation, gravity, and control systems. The simulation incorporates
realistic physics including changing mass as fuel is consumed, thrust vectoring
for attitude control, aerodynamic forces, and the challenge of balancing these
factors to achieve a soft landing. Users can experience the delicate balance 
required in rocket landings similar to those performed by modern reusable rockets.
"""

import pygame
from pygame.locals import *
import numpy as np
import Box2D
from Box2D.b2 import *


class Options(object):
    def __init__(self):
        self.pixels_per_meter = 10
        self.screen_width = 1024
        self.screen_height = 768
        self.target_fps = 90
        self.colors = {staticBody: (255, 255, 255, 255), dynamicBody: (0, 0, 255, 255)}


class World(object):
    def __init__(self, options):
        self.screen_width = options.screen_width
        self.screen_height = options.screen_height
        self.pixels_per_meter = options.pixels_per_meter
        self.colors = options.colors
        #
        self.wind = True
        self.wind_str = np.random.random_integers(-39, 39+1) * 1.0
        #
        self.gravity = -30.0
        #
        self.world = world(gravity=(0, self.gravity), doSleep=False)


class Platform(object):
    def __init__(self, world_obj):
        self.type = "decoration"
        self.color = (255, 255, 255, 255)
        #
        self.screen_width = world_obj.screen_width
        self.pixels_per_meter = world_obj.pixels_per_meter
        #
        self.position_x = (self.screen_width / self.pixels_per_meter) / 2.0
        self.position_y = 3.1
        self.position_angle = 0.0
        #
        self.height = 0.8
        self.width = 12
        #
        self.vel_x = 0.0
        self.vel_y = 0.0

        self.body = world_obj.world.CreateKinematicBody(position=(self.position_x, self.position_y),
                                                        angle=self.position_angle,
                                                        userData="decoration_body")
        self.box = self.body.CreatePolygonFixture(vertices=[(-self.width, 0),
                                                            (-self.width, self.height),
                                                            (self.width, self.height),
                                                            (self.width, 0),
                                                            (self.width - 2.2, -self.height),
                                                            (-self.width + 2.2, -self.height)],
                                                  density=0,
                                                  friction=0.3,
                                                  restitution=0, userData="platform")
        self.live = True
        self.report()

    def __inc_angle__(self):
        self.position_angle += np.pi / 110.0
        if self.position_angle >= np.pi * 2.0 * 57.0:
            self.position_angle = 0.0

    def __angle_flow__(self):
        self.body.angle = np.sin(self.position_angle) / 30.0

    def __position_go__(self):
        self.vel_x = np.sin(self.position_angle) * 1.3
        self.vel_y = np.sin(self.position_angle) * 1.5
        self.body.linearVelocity = (self.vel_x, self.vel_y)

    def act(self):
        self.__inc_angle__()
        self.__angle_flow__()
        self.__position_go__()

    def report(self):
        return {"type": "decoration", "angle": self.body.angle, "px": self.body.position[0],
                "py": self.body.position[1], "vx": self.body.linearVelocity[0], "vy": self.body.linearVelocity[1]}


class Rocket(object):
    def __init__(self, world_obj):
        self.type = "actor"
        self.world_obj = world_obj
        self.color = (50, 150, 255, 255)
        self.position_x = (world_obj.screen_width / world_obj.pixels_per_meter) / 2 + np.random.random_integers(-21, 21+1)
        self.position_y = (world_obj.screen_height / world_obj.pixels_per_meter) / 4 * 4
        self.position_angle = 0
        #
        self.wind = world_obj.wind
        self.wind_str = world_obj.wind_str
        #
        self.height = 7.1
        self.width = 0.7

        self.body = world_obj.world.CreateDynamicBody(position=(self.position_x, self.position_y),
                                                      angle=self.position_angle,
                                                      userData="actor_body")
        self.box = self.body.CreatePolygonFixture(box=(self.width, self.height),
                                                  density=1,
                                                  friction=0.3,
                                                  userData="frame")
        self.box2 = self.body.CreatePolygonFixture(vertices=[(-2, -self.height),
                                                             (2, -self.height),
                                                             (1.2, -self.height + 0.9),
                                                             (-1.2, -self.height + 0.9)],
                                                   density=1,
                                                   friction=0.3,
                                                   userData="wings")
        self.fuel = 999.9
        self.consumption = 1.0
        self.durability = 9.0
        #
        self.body.linearVelocity[1] = -39.0
        self.body.linearVelocity[0] = np.random.random_integers(-39, 39+1) * 1.0
        #
        self.body.angle += 0.2999 * (self.body.linearVelocity[0] / 39.0)
        #
        self.enj = True
        self.left_enj_power = 500.0
        self.right_enj_power = 500.0
        self.main_enj_power = 1000.0
        #
        self.live = True
        self.contact = False
        self.dist1 = 999.0
        self.dist2 = 999.0
        self.contact_time = 0
        self.frame_c = False
        self.wings_c = False
        #
        self.bvx = self.body.linearVelocity[0]
        self.bvy = self.body.linearVelocity[1]
        #
        self.debug = False
        self.debug_p = (world_obj.screen_width / world_obj.pixels_per_meter / 2,
                        world_obj.screen_height / world_obj.pixels_per_meter / 2)

        self.report()

    def __is_alive__(self):
        self.contact = False
        self.frame_c = False
        self.wings_c = False

        if len(self.body.contacts) > 0:
            for b2e in self.body.contacts:
                tb2e = b2e.contact.touching
                if tb2e:
                    if b2e.contact.fixtureA.userData == "frame":
                        self.frame_c = True
                    if b2e.contact.fixtureA.userData == "wings":
                        self.wings_c = True

        if len(self.body.contacts) > 0 and self.wings_c:
            uadd = 3.9
            if np.fabs(np.fabs(self.body.linearVelocity[1]) - np.fabs(self.bvy)) > (self.durability + uadd) or \
                    np.fabs(np.fabs(self.body.linearVelocity[0]) - np.fabs(self.bvx)) > (self.durability + uadd):
                self.live = False
        if len(self.body.contacts) > 0 and (self.frame_c or self.dist1 < 0.021):
            self.contact = True
            self.contact_time += 0.01
            #print(self.contact_time)
            if np.fabs(np.fabs(self.body.linearVelocity[1]) - np.fabs(self.bvy)) > self.durability or \
                    np.fabs(np.fabs(self.body.linearVelocity[0]) - np.fabs(self.bvx)) > self.durability:
                self.live = False
        else:
            self.contact_time = 0
        self.bvx = self.body.linearVelocity[0]
        self.bvy = self.body.linearVelocity[1]

    def __dist__(self):
        polygonA1 = self.box.shape
        polygonA2 = self.box2.shape
        polygonATransform = self.body.transform
        polygonB = None
        polygonBTransform = None
        for b in self.world_obj.world.bodies:
            if b.userData == "decoration_body":
                polygonB = b.fixtures[0].shape
                polygonBTransform = b.transform
        self.dist1 = Box2D.b2Distance(shapeA=polygonA1, shapeB=polygonB,
                                      transformA=polygonATransform, transformB=polygonBTransform).distance
        self.dist2 = Box2D.b2Distance(shapeA=polygonA2, shapeB=polygonB,
                                      transformA=polygonATransform, transformB=polygonBTransform).distance

    def act(self, keys=[0, 0, 0, 0]):
        if keys[0] != 0:
            self.__up__()
        if keys[1] != 0:
            self.__left__()
        if keys[2] != 0:
            self.__right__()
        if self.wind:
            self.__wind__()
        self.__dist__()
        self.__is_alive__()

    def __up__(self):
        if self.fuel > 0 and self.enj:
            f = self.body.GetWorldVector(localVector=(0.0, self.main_enj_power))
            p = self.body.GetWorldPoint(localPoint=(0.0, 0.0 - self.height))
            if self.debug:
                self.debug_p = p
            self.body.ApplyForce(f, p, True)
            self.fuel -= (self.consumption + 0.25)
        else:
            self.enj = False

    def __left__(self):
        if self.fuel > 0 and self.enj:
            f = self.body.GetWorldVector(localVector=(0.0, self.left_enj_power))
            p = self.body.GetWorldPoint(localPoint=(2.0, 0.0 - self.height))
            self.body.ApplyForce(f, p, True)
            self.fuel -= self.consumption
        else:
            self.enj = False

    def __right__(self):
        if self.fuel > 0 and self.enj:
            f = self.body.GetWorldVector(localVector=(0.0, self.right_enj_power))
            p = self.body.GetWorldPoint(localPoint=(-2.0, 0.0 - self.height))
            self.body.ApplyForce(f, p, True)
            self.fuel -= self.consumption
        else:
            self.enj = False

    def __wind__(self):
        f = self.body.GetWorldVector(localVector=(self.wind_str, 0.0))
        p = self.body.GetWorldPoint(localPoint=(0.0, 0.0))
        self.body.ApplyForce(f, p, True)

    def report(self):
        return {"type": "actor", "angle": self.body.angle, "fuel": self.fuel,
                "vx": self.body.linearVelocity[0], "vy": self.body.linearVelocity[1],
                "px": self.body.position[0], "py": self.body.position[1], "dist": np.amin([self.dist1, self.dist2]),
                "live": self.live, "enj": self.enj, "contact": self.contact, "wind": self.wind_str,
                "contact_time": self.contact_time}


class Simulation(object):
    def __init__(self):
        self.screen_width = 1024
        self.screen_height = 768
        self.target_fps = 90
        self.pixels_per_meter = 10
        self.colors = {staticBody: (255, 255, 255, 255), dynamicBody: (0, 0, 255, 255)}

        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), 0, 32)
        pygame.display.set_caption("_F9_Lander_")
        self.clock = pygame.time.Clock()
        self.myfont = pygame.font.SysFont(None, 29)

        self.running = True
        self.label = None
        self.step_number = 0
        self.message = ""
        self.win = "none"
        self.terminal_state = False
        self.score = 0
        self.score_flag = False

    def __restart__(self, world_obj, simulation_array):
        self.win = "none"
        self.terminal_state = False
        self.score_flag = False
        for entity in simulation_array:
            if entity.type == "actor":
                world_obj.world.DestroyBody(entity.body)
                simulation_array.remove(entity)
                world_obj.wind_str = np.random.random_integers(-39, 39+1) * 1.0
                simulation_array.append(Rocket(world_obj))
        return simulation_array

    def __is_terminal_state__(self, entity):
        if self.win == "destroyed" or self.win == "landed" or entity.body.position[1] <= 0.0:
            self.terminal_state = True

    def __get_score__(self, entity):
        if self.win == "landed" and not self.score_flag:
            self.score += (100.0 + entity.fuel)
            self.score_flag = True
        elif self.terminal_state and not self.score_flag:
            self.score += -100.0
            self.score_flag = True
        elif not self.terminal_state and entity.dist1 >= 0.021 and entity.dist2 >= 0.021:
            self.score += 1.0 / (1.0 + entity.dist1)

    def step(self, world_obj, simulation_array=[]):
        keys = [0, 0, 0, 0]
        key = pygame.key.get_pressed()
        keys = [key[pygame.K_s], key[pygame.K_a], key[pygame.K_d], key[pygame.K_n]]

        if keys[3] != 0:
            simulation_array = self.__restart__(world_obj, simulation_array)

        self.screen.fill((0, 0, 0, 0))

        for entity in simulation_array:
            if entity.type == "actor":
                entity.act(keys=keys)
                self.message += "| Dist: " + str(np.round(np.amin([entity.dist1, entity.dist2]), 1))
                self.message += " | Fuel: " + str(np.round((entity.fuel * entity.enj), 1)) \
                                + " | VX: " + str(np.round(entity.body.linearVelocity[0], 1)) \
                                + " | VY: " + str(np.round(entity.body.linearVelocity[1], 1)) \
                                + " | A: " + str(np.round(entity.body.angle, 1)) + " | Wind: " + str(entity.wind_str)
            elif entity.type == "decoration":
                entity.act()
            for fixture in entity.body.fixtures:
                shape = fixture.shape
                vertices = [(entity.body.transform * v) * self.pixels_per_meter for v in shape.vertices]
                vertices = [(v[0], self.screen_height - v[1]) for v in vertices]

                pygame.draw.polygon(self.screen, entity.color, vertices)

                if keys[0] != 0 and entity.type == "actor" and entity.enj and fixture.userData != "wings":
                    pygame.draw.polygon(self.screen, (255, np.random.random_integers(100, 200+1), 0, 150),
                                        (vertices[1], vertices[0],
                                         ((vertices[0][0] + vertices[1][0]) / 2,
                                          vertices[0][1] + np.random.random_integers(21, 27+1))))
                if keys[1] != 0 and entity.type == "actor" and entity.enj and fixture.userData != "wings":
                    pygame.draw.polygon(self.screen, (255, np.random.random_integers(100, 200+1), 0, 150),
                                        (vertices[1], vertices[0],
                                         (vertices[0][0] - np.random.random_integers(3, 7+1),
                                          vertices[0][1] + np.random.random_integers(11, 17+1))))
                if keys[2] != 0 and entity.type == "actor" and entity.enj and fixture.userData != "wings":
                    pygame.draw.polygon(self.screen, (255, np.random.random_integers(100, 200+1), 0, 150),
                                        (vertices[1], vertices[0],
                                         (vertices[1][0] + np.random.random_integers(3, 7+1),
                                          vertices[1][1] + np.random.random_integers(11, 17+1))))

        for entity in simulation_array:
            if entity.type == "actor":
                if entity.live and entity.contact and entity.contact_time >= 2.75 and -0.29 < entity.body.angle < 0.29:
                    entity.color = (0, 255, 0, 255)
                    self.win = "landed"
                if not entity.live:
                    entity.color = (255, 0, 0, 255)
                    self.win = "destroyed"
                self.__is_terminal_state__(entity)
                self.__get_score__(entity)

        world_obj.world.Step(1.0 / self.target_fps, 10, 10)
        world_obj.world.ClearForces()

        self.label = self.myfont.render(self.message, True, (255, 255, 255), (0, 0, 0))
        self.screen.blit(self.label, (10, 10))
        pygame.display.flip()
        self.clock.tick(self.target_fps)

        self.step_number += 1
        self.message = ""

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                self.running = False
                pygame.quit()
                print("All engines stopped")
            if event.type == KEYDOWN and event.key == K_SPACE:
                simulation_array = self.__restart__(world_obj, simulation_array)

        return ()


def main():
    options = Options()
    world = World(options)
    simulation = Simulation()
    entities = [Rocket(world), Platform(world)]
    print(entities)

    while simulation.running:
        report = simulation.step(world, entities)

    print(entities)


if __name__ == "__main__":
    main()