import tkinter as tk
import pymunk
from pymunk.vec2d import Vec2d
import time
import random
import math

class PhysicsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("2D Physics Simulation")

        # Canvas & controls
        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        ctrl = tk.Frame(root)
        ctrl.pack(fill=tk.X)
        self.pause_btn = tk.Button(ctrl, text="Pause", command=self.toggle_pause)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        tk.Button(ctrl, text="Speed +", command=lambda: self.change_speed(1.2)).pack(side=tk.LEFT, padx=5)
        tk.Button(ctrl, text="Speed -", command=lambda: self.change_speed(0.8)).pack(side=tk.LEFT, padx=5)
        tk.Button(ctrl, text="Reset",   command=self.reset).pack(side=tk.LEFT, padx=5)

        # current speed display
        self.speed = 1.0
        self.speed_label = tk.Label(ctrl, text=f"Speed: {self.speed:.2f}x")
        self.speed_label.pack(side=tk.LEFT, padx=15)

        # ground metrics
        self.soil_height  = 80
        self.grass_height = 20

        # Pymunk space
        self.space = pymunk.Space()
        self.space.gravity    = (0, 900)
        self.space.iterations = 30    # more solver passes for accuracy

        # High‑FPS & sub‑step settings
        self.target_fps  = 120
        self.frame_delay = int(1000 / self.target_fps)  # ≈8ms
        self.dt          = 1 / self.target_fps
        self.substeps    = 4

        # Make walls & clouds before simulation starts
        self._make_walls()
        self.clouds = []
        self._make_clouds()

        # Collision handler → particles
        handler = self.space.add_default_collision_handler()
        handler.post_solve = self._on_collision

        # Slingshot drag state
        self.drag_start   = None
        self.drag_current = None

        # Particle list
        self.particles = []  # each: {x,y,vx,vy,life,color,r}

        # Simulation state
        self.paused = False

        # Bind input
        self.canvas.bind("<Button-1>",             self.add_block)
        self.canvas.bind("<ButtonPress-3>",        self.start_ball_aim)
        self.canvas.bind("<B3-Motion>",            self.update_aim_line)
        self.canvas.bind("<ButtonRelease-3>",      self.fire_ball)
        self.canvas.bind("<Configure>",            lambda e: self._on_resize())

        # Kick off the loop
        self._last_time = time.time()
        self._loop()

    def _make_walls(self):
        for s in getattr(self, '_walls', []):
            self.space.remove(s)
        w = self.canvas.winfo_width()  or 800
        h = self.canvas.winfo_height() or 600
        floor_y = h - self.soil_height
        body = self.space.static_body
        self._walls = [
            pymunk.Segment(body, (0, floor_y), (w, floor_y), 5),
            pymunk.Segment(body, (0, 0),        (0, h),       5),
            pymunk.Segment(body, (w, 0),        (w, h),       5),
        ]
        for seg in self._walls:
            seg.friction   = 1
            seg.elasticity = 0.5
            self.space.add(seg)

    def _make_clouds(self):
        w = self.canvas.winfo_width() or 800
        self.clouds.clear()
        for _ in range(5):
            x    = random.uniform(0, w)
            y    = random.uniform(20, 100)
            size = random.uniform(60, 120)
            self.clouds.append({'x': x, 'y': y, 'size': size})

    def _on_resize(self):
        self._make_walls()
        self._make_clouds()

    def add_block(self, evt):
        body = pymunk.Body(1, pymunk.moment_for_box(1, (50,50)))
        body.position = evt.x, evt.y
        shape = pymunk.Poly.create_box(body, (50,50))
        shape.friction       = 1
        shape.elasticity     = 0.3
        shape.collision_type = 2   # block
        self.space.add(body, shape)

    def start_ball_aim(self, evt):
        self.drag_start   = Vec2d(evt.x, evt.y)
        self.drag_current = Vec2d(evt.x, evt.y)

    def update_aim_line(self, evt):
        if self.drag_start:
            self.drag_current = Vec2d(evt.x, evt.y)

    def fire_ball(self, evt):
        if not self.drag_start:
            return
        end     = Vec2d(evt.x, evt.y)
        impulse = (self.drag_start - end) * 5
        body    = pymunk.Body(1, pymunk.moment_for_circle(1, 0, 15))
        body.position = self.drag_start
        circle = pymunk.Circle(body, 15)
        circle.friction       = 0.5
        circle.elasticity     = 0.8
        circle.collision_type = 1   # ball
        self.space.add(body, circle)
        body.apply_impulse_at_local_point(impulse)
        self.drag_start   = None
        self.drag_current = None

    def _on_collision(self, arbiter, space, data):
        if not arbiter.is_first_contact:
            return True
        if arbiter.total_impulse.length < 100:
            return True
        color = "orange" if any(s.collision_type==1 for s in arbiter.shapes) else "lightblue"
        for cp in arbiter.contact_point_set.points:
            x, y = cp.point_a
            for _ in range(6):
                angle = random.uniform(0, 2*math.pi)
                speed = random.uniform(50, 200)
                vx    = math.cos(angle)*speed
                vy    = math.sin(angle)*speed
                self.particles.append({
                    'x': x, 'y': y,
                    'vx': vx, 'vy': vy,
                    'life': 0.5,
                    'color': color,
                    'r': random.uniform(2,4)
                })
        return True

    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_btn.config(text="Play" if self.paused else "Pause")

    def change_speed(self, factor):
        self.speed *= factor
        self.speed_label.config(text=f"Speed: {self.speed:.2f}x")

    def reset(self):
        for b in list(self.space.bodies):
            if b.body_type == pymunk.Body.DYNAMIC:
                for s in b.shapes:
                    self.space.remove(s)
                self.space.remove(b)
        self._make_walls()

    def _loop(self):
        now     = time.time()
        real_dt = now - self._last_time
        self._last_time = now

        if not self.paused:
            # sub‑stepped physics
            step_dt = self.dt * self.speed / self.substeps
            for _ in range(self.substeps):
                self.space.step(step_dt)

            # animate clouds
            for c in self.clouds:
                c['x'] -= 20 * real_dt
                if c['x'] + c['size'] < 0:
                    c['x'] = self.canvas.winfo_width() + c['size']

            # update particles
            new = []
            for p in self.particles:
                p['life'] -= real_dt
                if p['life'] > 0:
                    p['vy'] += 900 * real_dt
                    p['x']  += p['vx'] * real_dt
                    p['y']  += p['vy'] * real_dt
                    new.append(p)
            self.particles = new

        self._draw()
        self.root.after(self.frame_delay, self._loop)

    def _draw(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        floor_y = h - self.soil_height

        # Sky
        self.canvas.create_rectangle(0, 0, w, h, fill="#87CEEB", width=0)
        # Clouds
        for c in self.clouds:
            x,y,s = c['x'], c['y'], c['size']
            self.canvas.create_oval(x, y, x+0.6*s, y+0.4*s, fill="white", outline="")
            self.canvas.create_oval(x+0.3*s, y-0.2*s, x+0.9*s, y+0.3*s, fill="white", outline="")
            self.canvas.create_oval(x+0.6*s, y, x+1.1*s, y+0.5*s, fill="white", outline="")
        # Ground
        self.canvas.create_rectangle(0, floor_y, w, h, fill="#8B4513", width=0)
        self.canvas.create_rectangle(0, floor_y, w, floor_y + self.grass_height,
                                     fill="#228B22", width=0)
        # Bodies
        for shape in self.space.shapes:
            if isinstance(shape, pymunk.Poly):
                pts = [shape.body.local_to_world(v) for v in shape.get_vertices()]
                coords = [coord for p in pts for coord in (p.x, p.y)]
                self.canvas.create_polygon(coords, fill="lightblue", outline="black")
            elif isinstance(shape, pymunk.Circle):
                p = shape.body.position
                r = shape.radius
                self.canvas.create_oval(p.x-r, p.y-r, p.x+r, p.y+r,
                                        fill="orange", outline="black")
        # Particles
        for p in self.particles:
            x,y,r = p['x'], p['y'], p['r']
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=p['color'], outline="")
        # Slingshot arrow + power
        if self.drag_start and self.drag_current:
            x0,y0 = self.drag_start
            x1,y1 = self.drag_current
            self.canvas.create_line(
                x1, y1, x0, y0,
                fill="red", width=2,
                arrow=tk.LAST, arrowshape=(10,12,5)
            )
            power = int((self.drag_start - self.drag_current).length)
            self.canvas.create_text(
                x0, y0 - 15,
                text=str(power),
                fill="black", font=("Arial", 12, "bold")
            )

if __name__ == "__main__":
    root = tk.Tk()
    app = PhysicsApp(root)
    root.mainloop()
