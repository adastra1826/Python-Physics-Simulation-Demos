# 3 hours

import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
import random
import math
# Constants
WIDTH, HEIGHT = 800, 600
ON_RAMP_X, ON_RAMP_Y = 100, 300
OFF_RAMP_X, OFF_RAMP_Y = 600, 300
TRACK_CENTER_X, TRACK_CENTER_Y = WIDTH // 2, HEIGHT // 2
TRACK_SCALE = WIDTH / 5

TRACK_POINTS = [
    (0, -1),
    (2, -1),
    (2, 1),
    (0, 1),
    (-2, 1),
    (-2, -1)
]

ON_RAMP_POINTS = [
    (-1, -1),
    (0, 0)
]

OFF_RAMP_POINTS = [
    (0, 2),
    (-1, 3)
]

# Track class
class TrackSegment:
    def __init__(self, start_point, end_point, angle):
        start_x = TRACK_CENTER_X + start_point[0] * TRACK_SCALE
        start_y = TRACK_CENTER_Y + start_point[1] * TRACK_SCALE
        end_x = TRACK_CENTER_X + end_point[0] * TRACK_SCALE
        end_y = TRACK_CENTER_Y + end_point[1] * TRACK_SCALE
        self.start_point = (start_x, start_y)
        self.end_point = (end_x, end_y)
        self.angle = angle
        self.length = self.calculate_length()
        self.start_z = 0
        self.points = self.calculate_points()
        
    def calculate_length(self):
        if self.angle == 0:
            dx = self.end_point[0] - self.start_point[0]
            dy = self.end_point[1] - self.start_point[1]
            return (dx * dx + dy * dy) ** 0.5
        else:
            radius = TRACK_SCALE
            return abs(radius * self.angle)
    
    def calculate_points(self):
        points = []
        for i in range(int(self.length)):
            points.append(self.get_position(i))
        return points
            
    def get_position(self, z):
        """Convert z position to (x,y) coordinates within this segment"""
        local_z = z - self.start_z
        if self.angle == 0:
            # Linear segment
            progress = local_z / self.length
            x = self.start_point[0] + (self.end_point[0] - self.start_point[0]) * progress
            y = self.start_point[1] + (self.end_point[1] - self.start_point[1]) * progress
            return (x, y)
        else:
            # Curved segment
            radius = TRACK_SCALE
            angle_start = math.atan2(self.start_point[1] - TRACK_CENTER_Y, self.start_point[0] - TRACK_CENTER_X)
            progress = local_z / self.length
            current_angle = angle_start + progress * self.angle
            
            x = TRACK_CENTER_X + radius * math.cos(current_angle)
            y = TRACK_CENTER_Y + radius * math.sin(current_angle)
            return (x, y)

class Track:
    def __init__(self, segments):
        self.segments = segments
        self.total_length = 0
        self.initialize_segments()
        
    def initialize_segments(self):
        """Calculate total length and set start_z for each segment"""
        current_z = 0
        for segment in self.segments:
            segment.start_z = current_z
            current_z += segment.length
        self.total_length = current_z
        
    def get_position(self, z):
        """Convert z coordinate to (x,y) position on track"""
        # Normalize z to track length (for looping around)
        z = z % self.total_length
        
        # Find which segment contains this z position
        for segment in self.segments:
            if segment.start_z <= z < segment.start_z + segment.length:
                return segment.get_position(z)
        
        # Should never reach here if z is properly normalized
        return self.segments[0].get_position(0)
    
    def get_segment_at(self, z):
        """Get the segment that contains the given z position"""
        z = z % self.total_length
        for segment in self.segments:
            if segment.start_z <= z < segment.start_z + segment.length:
                return segment
        return self.segments[0]
    
    def return_points(self):
        points = []
        for segment in self.segments:
            points.append(segment.start_point)
            points.append(segment.end_point)
        return points

class OnRamp(TrackSegment):
    def __init__(self, start_point, shared_end_point, radius):
        # OnRamp has a shared end_point with another track segment
        super().__init__(start_point, shared_end_point, radius)

class OffRamp(TrackSegment):
    def __init__(self, shared_start_point, end_point, radius):
        # OffRamp has a shared start_point with another track segment
        super().__init__(shared_start_point, end_point, radius)


# Vehicle classes
class Vehicle:
    def __init__(self, x, y, max_speed, turn_speed, acceleration, size):
        self.x = x
        self.y = y
        self.max_speed = max_speed
        self.turn_speed = turn_speed
        self.acceleration = acceleration
        self.size = size
        self.speed = 0

    def move(self):
        self.speed = min(self.speed + self.acceleration, self.max_speed)
        self.x += self.speed

    def turn(self):
        self.speed = self.turn_speed

class Car(Vehicle):

    MAX_SPEED = 5
    TURN_SPEED = 2
    ACCELERATION = 0.5
    SIZE = 10

    def __init__(self, x, y):
        super().__init__(x, y, Car.MAX_SPEED, Car.TURN_SPEED, Car.ACCELERATION, Car.SIZE)

class SemiTruck(Vehicle):

    MAX_SPEED = 3
    TURN_SPEED = 1
    ACCELERATION = 0.2
    SIZE = 20

    def __init__(self, x, y):
        super().__init__(x, y, SemiTruck.MAX_SPEED, SemiTruck.TURN_SPEED, SemiTruck.ACCELERATION, SemiTruck.SIZE)

class Motorcycle(Vehicle):
    
    MAX_SPEED = 10
    TURN_SPEED = 5
    ACCELERATION = 1
    SIZE = 5

    def __init__(self, x, y):
        super().__init__(x, y, Motorcycle.MAX_SPEED, Motorcycle.TURN_SPEED, Motorcycle.ACCELERATION, Motorcycle.SIZE)

# Simulation class
class Simulation:

    SEGMENTS = [
        TrackSegment(TRACK_POINTS[0], TRACK_POINTS[1], 0),
        TrackSegment(TRACK_POINTS[1], TRACK_POINTS[2], math.pi),
        TrackSegment(TRACK_POINTS[2], TRACK_POINTS[3], 0),
        TrackSegment(TRACK_POINTS[3], TRACK_POINTS[4], 0),
        TrackSegment(TRACK_POINTS[4], TRACK_POINTS[5], -math.pi),
        TrackSegment(TRACK_POINTS[5], TRACK_POINTS[0], 0),
    ]

    def __init__(self, master):
        self.master = master
        self.canvas = tk.Canvas(self.master, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.vehicles = []
        self.rate = 10
        self.speed = 1
        self.off_ramp_chance = 0.5
        self.on_ramp_vehicle = None

        self.rate_slider = tk.Scale(self.master, from_=1, to=100, orient=tk.HORIZONTAL, label='Rate of cars entering', command=self.update_rate)
        self.rate_slider.set(self.rate)
        self.rate_slider.pack()

        self.speed_slider = tk.Scale(self.master, from_=0.1, to=10, orient=tk.HORIZONTAL, label='Speed of simulation', command=self.update_speed)
        self.speed_slider.set(self.speed)
        self.speed_slider.pack()

        self.off_ramp_slider = tk.Scale(self.master, from_=0, to=100, orient=tk.HORIZONTAL, label='Percent chance cars leave the ramp', command=self.update_off_ramp_chance)
        self.off_ramp_slider.set(self.off_ramp_chance * 100)
        self.off_ramp_slider.pack()

        self.track = Track(Simulation.SEGMENTS)

        self.draw_track()
        self.draw_on_ramp()
        self.draw_off_ramp()
        self.update()

    def draw_track(self):
        points = self.track.return_points()
        for i in range(len(points) - 1):
            self.canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1])

    def draw_on_ramp(self):
        self.canvas.create_line(ON_RAMP_X, ON_RAMP_Y, ON_RAMP_X + 50, ON_RAMP_Y)

    def draw_off_ramp(self):
        self.canvas.create_line(OFF_RAMP_X, OFF_RAMP_Y, OFF_RAMP_X + 50, OFF_RAMP_Y)

    def update_rate(self, value):
        self.rate = int(value)

    def update_speed(self, value):
        self.speed = float(value)

    def update_off_ramp_chance(self, value):
        self.off_ramp_chance = float(value) / 100

    def update(self):
        if random.random() < self.rate / 100:
            vehicle_type = random.choice([Car, SemiTruck, Motorcycle])
            self.on_ramp_vehicle = vehicle_type(ON_RAMP_X, ON_RAMP_Y)
            self.vehicles.append(self.on_ramp_vehicle)

        for vehicle in self.vehicles:
            vehicle.move()
            if vehicle.x > OFF_RAMP_X and random.random() < self.off_ramp_chance:
                self.vehicles.remove(vehicle)
            elif vehicle.x > TRACK_CENTER_X + TRACK_SCALE:
                vehicle.x = TRACK_CENTER_X - TRACK_SCALE
                vehicle.turn()

        self.canvas.delete('all')
        self.draw_track()
        self.draw_on_ramp()
        self.draw_off_ramp()
        for vehicle in self.vehicles:
            self.canvas.create_rectangle(vehicle.x, vehicle.y, vehicle.x + vehicle.size, vehicle.y + vehicle.size)

        self.master.after(int(1000 / self.speed), self.update)

root = tk.Tk()
sim = Simulation(root)
root.mainloop()