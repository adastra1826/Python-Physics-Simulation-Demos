import pygame
import pymunk
import pymunk.pygame_util
import random

# Window size
WIDTH, HEIGHT = 800, 600

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 150, 0)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (200, 200, 200)

class Slider:
    """
    A simple slider UI component for adjusting numeric values.
    """
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.dragging = False
        # Calculate handle position based on initial value
        self.handle_pos = self.x + (self.value - self.min_val) / (self.max_val - self.min_val) * self.width
        
    def draw(self, screen, font):
        # Draw slider track
        pygame.draw.rect(screen, LIGHT_GRAY, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, DARK_GRAY, (self.x, self.y, self.width, self.height), 2)
        
        # Draw handle
        pygame.draw.rect(screen, DARK_GRAY, (self.handle_pos - 5, self.y - 5, 10, self.height + 10))
        
        # Draw label and value
        label_text = font.render(f"{self.label}: {int(self.value)}", True, DARK_GRAY)
        screen.blit(label_text, (self.x, self.y - 25))
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.x <= event.pos[0] <= self.x + self.width and self.y - 5 <= event.pos[1] <= self.y + self.height + 5:
                self.dragging = True
                # Update handle position
                self.handle_pos = max(self.x, min(event.pos[0], self.x + self.width))
                # Update value based on handle position
                self.value = self.min_val + (self.handle_pos - self.x) / self.width * (self.max_val - self.min_val)
                
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            # Update handle position
            self.handle_pos = max(self.x, min(event.pos[0], self.x + self.width))
            # Update value based on handle position
            self.value = self.min_val + (self.handle_pos - self.x) / self.width * (self.max_val - self.min_val)
            
class Button:
    """
    A simple button UI component.
    """
    def __init__(self, x, y, width, height, label):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        
    def draw(self, screen, font):
        # Draw button background
        pygame.draw.rect(screen, LIGHT_GRAY, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, DARK_GRAY, (self.x, self.y, self.width, self.height), 2)
        
        # Draw label
        label_text = font.render(self.label, True, DARK_GRAY)
        text_width, text_height = font.size(self.label)
        screen.blit(label_text, (self.x + (self.width - text_width) // 2, self.y + (self.height - text_height) // 2))
        
    def is_clicked(self, pos):
        return self.x <= pos[0] <= self.x + self.width and self.y <= pos[1] <= self.y + self.height

class TemperatureGauge:
    """
    Visual representation of temperature with a thermometer-like gauge.
    """
    def __init__(self, x, y, width, height, max_temp):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_temp = max_temp
        
    def draw(self, screen, font, temperature):
        # Draw gauge background
        pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, DARK_GRAY, (self.x, self.y, self.width, self.height), 2)
        
        # Calculate fill height based on temperature
        fill_height = min(self.height * (temperature / self.max_temp), self.height)
        
        # Draw temperature fill
        if temperature / self.max_temp < 0.33:
            color = (0, 0, 255)  # Blue for cold
        elif temperature / self.max_temp < 0.66:
            color = (255, 165, 0)  # Orange for medium
        else:
            color = (255, 0, 0)  # Red for hot
            
        pygame.draw.rect(screen, color, (self.x, self.y + self.height - fill_height, self.width, fill_height))
        
        # Draw temperature value
        temp_text = font.render(f"{int(temperature)}°", True, DARK_GRAY)
        screen.blit(temp_text, (self.x + self.width + 10, self.y + self.height // 2 - 10))
        
        # Draw label
        label_text = font.render("Temperature", True, DARK_GRAY)
        screen.blit(label_text, (self.x, self.y - 25))

class IceBlock:
    """
    Represents a block of ice in our physics simulation.
    This block will shrink from the bottom up based on temperature,
    and its mass will be reduced accordingly.
    """
    def __init__(self, space, x, y, width, height):
        self.body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)
        self.body.position = x, y
        self.shape = pymunk.Poly.create_box(self.body, size=(width, height))
        self.shape.elasticity = 0.9
        self.shape.friction = 0.5
        self.density = 0.001  # Arbitrary density for mass calculation
        self.shape.density = self.density
        space.add(self.body, self.shape)
        self.width = width
        self.height = height
        self.melting = False
        self.space = space

    def melt(self, temperature):
        """
        Melts the ice block from the bottom up, updating mass and shape.
        The melt rate increases with the simulation's temperature.
        """
        if self.melting and self.height > 0:
            # Calculate melt rate based on temperature
            melt_rate = 0.1 * temperature  # temperature-dependent melting
            old_height = self.height
            self.height = max(0, self.height - melt_rate)
            
            # Remove old shape
            self.space.remove(self.shape)
            
            # Create new shape with updated height
            if self.height > 0:
                # Create new shape with updated size
                self.shape = pymunk.Poly.create_box(self.body, size=(self.width, self.height))
                self.shape.elasticity = 0.9
                self.shape.friction = 0.5
                self.shape.density = self.density
                self.space.add(self.shape)
            else:
                self.melting = False

class WaterParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vel_x = random.uniform(-0.5, 0.5)
        self.vel_y = random.uniform(0.1, 0.5)

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y

def main():
    """
    Main function to set up the window, physics space,
    and run the simulation loop until the user exits.
    """
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ice Block Melting Simulation")
    clock = pygame.time.Clock()
    space = pymunk.Space()
    space.gravity = (0, 1000)

    # --- Add a simple static hot plate at the bottom ---
    hot_plate_body = pymunk.Body(body_type=pymunk.Body.STATIC)
    hot_plate_body.position = (WIDTH / 2, HEIGHT - 10)
    hot_plate_shape = pymunk.Poly.create_box(hot_plate_body, size=(WIDTH, 20))
    hot_plate_shape.friction = 0.5
    hot_plate_shape.elasticity = 0.5
    space.add(hot_plate_body, hot_plate_shape)
    # ----------------------------------------------------

    ice_blocks = [IceBlock(space, 100, 100, 50, 50), IceBlock(space, 200, 200, 50, 50)]
    water_particles = []
    temperature = 1  # Start with a non-zero temperature
    max_temperature = 20  # Maximum temperature for the gauge

    # Create UI elements
    font = pygame.font.Font(None, 24)
    big_font = pygame.font.Font(None, 36)
    
    # Sliders for controlling block properties
    width_slider = Slider(20, 30, 150, 15, 10, 100, 50, "Width")
    height_slider = Slider(20, 80, 150, 15, 10, 100, 50, "Height")
    x_slider = Slider(200, 30, 150, 15, 0, WIDTH, WIDTH//2, "X Position")
    y_slider = Slider(200, 80, 150, 15, 0, HEIGHT//2, HEIGHT//4, "Y Position")
    
    # Temperature gauge
    temp_gauge = TemperatureGauge(WIDTH - 80, 30, 30, 150, max_temperature)
    
    # Reset button
    reset_button = Button(WIDTH - 100, HEIGHT - 50, 80, 30, "Reset")
    
    # Add block button
    add_button = Button(380, 55, 100, 30, "Add Block")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check if reset button is clicked
                if reset_button.is_clicked(event.pos):
                    # Remove old ice blocks from space
                    for block in ice_blocks:
                        space.remove(block.shape, block.body)
                    ice_blocks = [IceBlock(space, 100, 100, 50, 50), IceBlock(space, 200, 200, 50, 50)]
                    water_particles = []
                    temperature = 1
                
                # Check if add block button is clicked
                elif add_button.is_clicked(event.pos):
                    new_block = IceBlock(
                        space, 
                        x_slider.value, 
                        y_slider.value,
                        width_slider.value,
                        height_slider.value
                    )
                    ice_blocks.append(new_block)
                
            # Update sliders
            width_slider.handle_event(event)
            height_slider.handle_event(event)
            x_slider.handle_event(event)
            y_slider.handle_event(event)
            
            # Keep keyboard shortcut for reset
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Remove old ice blocks from space
                    for block in ice_blocks:
                        space.remove(block.shape, block.body)
                    ice_blocks = [IceBlock(space, 100, 100, 50, 50), IceBlock(space, 200, 200, 50, 50)]
                    water_particles = []
                    temperature = 1

        screen.fill(WHITE)

        # Draw UI elements
        width_slider.draw(screen, font)
        height_slider.draw(screen, font)
        x_slider.draw(screen, font)
        y_slider.draw(screen, font)
        temp_gauge.draw(screen, font, temperature)
        reset_button.draw(screen, font)
        add_button.draw(screen, font)

        # Draw hot plate
        pygame.draw.rect(
            screen, (150, 75, 0),
            (0, HEIGHT - 20, WIDTH, 20)
        )

        # Process and draw ice blocks
        for i, ice_block in enumerate(ice_blocks[:]):
            # Call the new melt logic, which depends on temperature
            if ice_block.melting:
                ice_block.melt(temperature)
            
            # Draw the ice block
            if ice_block.height > 0:
                pygame.draw.rect(screen, BLUE, (
                    ice_block.body.position.x - ice_block.width / 2,
                    ice_block.body.position.y - ice_block.height / 2,
                    ice_block.width, ice_block.height
                ))
            else:
                # Remove fully melted blocks
                space.remove(ice_block.body)
                ice_blocks.remove(ice_block)

        # Process and draw water particles
        for water_particle in water_particles[:]:
            water_particle.update()
            pygame.draw.circle(screen, BLUE, (int(water_particle.x), int(water_particle.y)), 2)
            if water_particle.y > HEIGHT:
                water_particles.remove(water_particle)

        # Check if ice is touching the hot plate to start melting
        for ice_block in ice_blocks:
            if not ice_block.melting and ice_block.body.position.y + ice_block.height/2 >= HEIGHT - 20:
                ice_block.melting = True
                # Add multiple water particles when melting starts
                for _ in range(5):
                    water_particles.append(WaterParticle(
                        ice_block.body.position.x + random.uniform(-ice_block.width/2, ice_block.width/2),
                        ice_block.body.position.y + ice_block.height/2
                    ))

        # Add water particles periodically for melting blocks
        for ice_block in ice_blocks:
            if ice_block.melting and random.random() < 0.1 * temperature / max_temperature:
                water_particles.append(WaterParticle(
                    ice_block.body.position.x + random.uniform(-ice_block.width/2, ice_block.width/2),
                    ice_block.body.position.y + ice_block.height/2
                ))

        # Gradually increase temperature
        temperature += 0.01
        
        # Draw hot plate label
        hot_plate_text = font.render("Hot Plate", True, WHITE)
        text_width = hot_plate_text.get_width()
        screen.blit(hot_plate_text, (WIDTH//2 - text_width//2, HEIGHT - 17))

        space.step(1 / 50)
        pygame.display.flip()
        clock.tick(50)

    pygame.quit()

if __name__ == '__main__':
    main()