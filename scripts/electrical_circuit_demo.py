import pygame

# Window size
WIDTH, HEIGHT = 800, 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (100, 100, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
DARK_BLUE = (0, 0, 100)

# Circuit layout positions (rectangular loop)
TOP_LEFT = (150, 100)
TOP_RIGHT = (650, 100)
BOTTOM_LEFT = (150, 500)
BOTTOM_RIGHT = (650, 500)

# Positions for batteries and resistors along the segments
BATTERY_1_POS = ((TOP_LEFT[0] + TOP_RIGHT[0]) // 2, TOP_LEFT[1])
BATTERY_2_POS = ((BOTTOM_LEFT[0] + BOTTOM_RIGHT[0]) // 2, BOTTOM_LEFT[1])
RESISTOR_1_POS = (TOP_LEFT[0], (TOP_LEFT[1] + BOTTOM_LEFT[1]) // 2)
RESISTOR_2_POS = ((TOP_LEFT[0] + TOP_RIGHT[0]) // 2 + 100, TOP_RIGHT[1])
RESISTOR_3_POS = (TOP_RIGHT[0], (TOP_RIGHT[1] + BOTTOM_RIGHT[1]) // 2)
RESISTOR_4_POS = ((BOTTOM_LEFT[0] + BOTTOM_RIGHT[0]) // 2 - 100, BOTTOM_LEFT[1])

# Circuit parameters
R = 10.0  # Resistance per resistor in ohms
TOTAL_R = R * 4  # Total resistance (4 resistors in series)
K = 140.0  # Proportionality constant, pixels per second per ampere
FPS = 60  # Frames per second
GRID_SIZE = 50  # Grid spacing in pixels


class Charge:
    """Represents a moving charge in the circuit."""

    def __init__(self):
        """Initialize the charge at the positive terminal of Battery 1 (right side after flip)."""
        self.x = BATTERY_1_POS[0] + 20  # Positive terminal now on right
        self.y = BATTERY_1_POS[1]
        self.speed = 0
        self.segment = 0  # 0: top, 1: right, 2: bottom, 3: left
        self.direction = 1  # Start clockwise

    def move(self):
        """Move the charge along the rectangular loop based on its speed and direction."""
        if self.speed == 0:
            return

        if self.segment == 0:  # Top segment
            self.x += self.speed * self.direction
            if self.direction == 1 and self.x >= TOP_RIGHT[0]:
                self.x = TOP_RIGHT[0]
                self.segment = 1
            elif self.direction == -1 and self.x <= TOP_LEFT[0]:
                self.x = TOP_LEFT[0]
                self.segment = 3
        elif self.segment == 1:  # Right segment
            self.y += self.speed * self.direction
            if self.direction == 1 and self.y >= BOTTOM_RIGHT[1]:
                self.y = BOTTOM_RIGHT[1]
                self.segment = 2
            elif self.direction == -1 and self.y <= TOP_RIGHT[1]:
                self.y = TOP_RIGHT[1]
                self.segment = 0
        elif self.segment == 2:  # Bottom segment
            self.x -= self.speed * self.direction
            if self.direction == 1 and self.x <= BOTTOM_LEFT[0]:
                self.x = BOTTOM_LEFT[0]
                self.segment = 3
            elif self.direction == -1 and self.x >= BOTTOM_RIGHT[0]:
                self.x = BOTTOM_RIGHT[0]
                self.segment = 1
        elif self.segment == 3:  # Left segment
            self.y -= self.speed * self.direction
            if self.direction == 1 and self.y <= TOP_LEFT[1]:
                self.y = TOP_LEFT[1]
                self.segment = 0
            elif self.direction == -1 and self.y >= BOTTOM_LEFT[1]:
                self.y = BOTTOM_LEFT[1]
                self.segment = 2

    def draw(self, screen):
        """Draw the charge with a blue glow effect."""
        pygame.draw.circle(screen, DARK_BLUE, (int(self.x), int(self.y)), 7)
        pygame.draw.circle(screen, GREEN, (int(self.x), int(self.y)), 5)


def draw_battery(
    screen, pos, voltage, label, orientation="vertical", flip_polarity=False
):
    """Draw a battery with + as longer side and - as shorter side, flipped horizontally."""
    font = pygame.font.Font(None, 24)
    if orientation == "vertical":
        pygame.draw.line(screen, RED, (pos[0], pos[1] - 20), (pos[0], pos[1] + 20), 4)
        plus_y = pos[1] + 20 if not flip_polarity else pos[1] - 20  # + at bottom
        minus_y = pos[1] - 20 if not flip_polarity else pos[1] + 20  # - at top
        pygame.draw.line(
            screen, RED, (pos[0] - 15, plus_y), (pos[0] + 15, plus_y), 4
        )  # Longer line for +
        pygame.draw.line(
            screen, RED, (pos[0] - 10, minus_y), (pos[0] + 10, minus_y), 2
        )  # Shorter line for -
        plus_text = font.render("+", True, WHITE)
        minus_text = font.render("-", True, WHITE)
        screen.blit(
            plus_text, (pos[0] + 15, plus_y + 10 if not flip_polarity else plus_y - 10)
        )
        screen.blit(
            minus_text,
            (pos[0] + 15, minus_y - 10 if not flip_polarity else minus_y + 10),
        )
    else:
        pygame.draw.line(screen, RED, (pos[0] - 20, pos[1]), (pos[0] + 20, pos[1]), 4)
        plus_x = (
            pos[0] + 20 if not flip_polarity else pos[0] - 20
        )  # + on right for Battery 1, left for Battery 2
        minus_x = (
            pos[0] - 20 if not flip_polarity else pos[0] + 20
        )  # - on left for Battery 1, right for Battery 2
        pygame.draw.line(
            screen, RED, (plus_x, pos[1] - 15), (plus_x, pos[1] + 15), 4
        )  # Longer line for +
        pygame.draw.line(
            screen, RED, (minus_x, pos[1] - 10), (minus_x, pos[1] + 10), 2
        )  # Shorter line for -
        plus_text = font.render("+", True, WHITE)
        minus_text = font.render("-", True, WHITE)
        screen.blit(
            plus_text, (plus_x + 5 if not flip_polarity else plus_x - 15, pos[1] - 20)
        )
        screen.blit(
            minus_text,
            (minus_x - 15 if not flip_polarity else minus_x + 5, pos[1] - 20),
        )

    text = font.render(f"{voltage:.1f}V", True, WHITE)
    label_text = font.render(label, True, WHITE)
    if orientation == "vertical":
        screen.blit(text, (pos[0] + 30, pos[1] - 10))
        screen.blit(label_text, (pos[0] - 40, pos[1] + 30))
    else:
        screen.blit(text, (pos[0] - 10, pos[1] + 30))
        screen.blit(label_text, (pos[0] - 30, pos[1] + 50))


def draw_resistor(screen, pos, label, orientation="vertical"):
    """Draw a resistor with a dark gray glow effect."""
    if orientation == "vertical":
        pygame.draw.rect(
            screen, DARK_GRAY, (pos[0] - 15, pos[1] - 20, 30, 40), border_radius=5
        )
        pygame.draw.rect(screen, WHITE, (pos[0] - 10, pos[1] - 15, 20, 30))
    else:
        pygame.draw.rect(
            screen, DARK_GRAY, (pos[0] - 20, pos[1] - 15, 40, 30), border_radius=5
        )
        pygame.draw.rect(screen, WHITE, (pos[0] - 15, pos[1] - 10, 30, 20))

    font = pygame.font.Font(None, 24)
    text = font.render("R", True, BLACK)
    screen.blit(text, (pos[0] - 5, pos[1] - 5))
    resistance_text = font.render(f"{R}Ω", True, WHITE)
    label_text = font.render(label, True, WHITE)
    if orientation == "vertical":
        screen.blit(resistance_text, (pos[0] + 15, pos[1] - 10))
        screen.blit(label_text, (pos[0] - 30, pos[1] + 20))
    else:
        screen.blit(resistance_text, (pos[0] - 10, pos[1] + 30))
        screen.blit(label_text, (pos[0] - 30, pos[1] + 50))


def draw_grid(screen):
    """Draw a grid on the background."""
    for x in range(0, WIDTH, GRID_SIZE):
        pygame.draw.line(screen, LIGHT_GRAY, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, LIGHT_GRAY, (0, y), (WIDTH, y), 1)


def draw_circuit_loop(screen):
    """Draw the circuit loop with wires connecting through batteries and resistors."""
    pygame.draw.line(
        screen, WHITE, TOP_LEFT, (BATTERY_1_POS[0] - 20, BATTERY_1_POS[1]), 2
    )
    pygame.draw.line(
        screen,
        WHITE,
        (BATTERY_1_POS[0] + 20, BATTERY_1_POS[1]),
        (RESISTOR_2_POS[0] - 15, RESISTOR_2_POS[1]),
        2,
    )
    pygame.draw.line(
        screen, WHITE, (RESISTOR_2_POS[0] + 15, RESISTOR_2_POS[1]), TOP_RIGHT, 2
    )
    pygame.draw.line(
        screen, WHITE, TOP_RIGHT, (RESISTOR_3_POS[0], RESISTOR_3_POS[1] - 15), 2
    )
    pygame.draw.line(
        screen, WHITE, (RESISTOR_3_POS[0], RESISTOR_3_POS[1] + 15), BOTTOM_RIGHT, 2
    )
    pygame.draw.line(
        screen, WHITE, BOTTOM_RIGHT, (RESISTOR_4_POS[0] + 15, RESISTOR_4_POS[1]), 2
    )
    pygame.draw.line(
        screen,
        WHITE,
        (RESISTOR_4_POS[0] - 15, RESISTOR_4_POS[1]),
        (BATTERY_2_POS[0] + 20, BATTERY_2_POS[1]),
        2,
    )
    pygame.draw.line(
        screen, WHITE, (BATTERY_2_POS[0] - 20, BATTERY_2_POS[1]), BOTTOM_LEFT, 2
    )
    pygame.draw.line(
        screen, WHITE, BOTTOM_LEFT, (RESISTOR_1_POS[0], RESISTOR_1_POS[1] - 15), 2
    )
    pygame.draw.line(
        screen, WHITE, (RESISTOR_1_POS[0], RESISTOR_1_POS[1] + 15), TOP_LEFT, 2
    )


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    voltage_1 = 10.0
    voltage_2 = 5.0
    charges = [Charge() for _ in range(100)]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    voltage_1 += 1
                elif event.key == pygame.K_DOWN:
                    voltage_1 = max(0, voltage_1 - 1)
                elif event.key == pygame.K_RIGHT:
                    voltage_2 += 1
                elif event.key == pygame.K_LEFT:
                    voltage_2 = max(0, voltage_2 - 1)

        # Total voltage: Both batteries drive in the same direction (clockwise)
        total_voltage = voltage_1 + voltage_2
        current = total_voltage / TOTAL_R if total_voltage != 0 else 0
        speed = (K / FPS) * abs(
            current
        )  # Use absolute value for speed, direction handles sign
        direction = (
            1 if total_voltage > 0 else -1 if total_voltage < 0 else 0
        )  # Allow counterclockwise for negative voltage

        # Draw background and grid
        screen.fill(DARK_GRAY)
        draw_grid(screen)

        # Draw circuit and charges
        draw_circuit_loop(screen)
        for charge in charges:
            charge.speed = speed
            charge.direction = direction
            charge.move()
            charge.draw(screen)

        # Draw batteries and resistors
        draw_battery(
            screen,
            BATTERY_1_POS,
            voltage_1,
            "Battery 1",
            orientation="horizontal",
            flip_polarity=False,
        )
        draw_battery(
            screen,
            BATTERY_2_POS,
            voltage_2,
            "Battery 2",
            orientation="horizontal",
            flip_polarity=True,
        )
        draw_resistor(screen, RESISTOR_1_POS, "Resistor 1", orientation="vertical")
        draw_resistor(screen, RESISTOR_2_POS, "Resistor 2", orientation="horizontal")
        draw_resistor(screen, RESISTOR_3_POS, "Resistor 3", orientation="vertical")
        draw_resistor(screen, RESISTOR_4_POS, "Resistor 4", orientation="horizontal")

        # Display overall circuit stats in top-left
        font = pygame.font.Font(None, 24)
        direction_text = font.render(
            f"Direction: {'Clockwise' if direction == 1 else 'Counterclockwise' if direction == -1 else 'None'}",
            True,
            WHITE,
        )
        screen.blit(direction_text, (10, 10))

        # Display total voltage, current, and resistance in top-right with yellow labels and white data
        volt_label = font.render("Total Voltage: ", True, YELLOW)
        volt_value = font.render(f"{total_voltage:.1f} V", True, WHITE)
        curr_label = font.render("Current: ", True, YELLOW)
        curr_value = font.render(f"{current:.2f} A", True, WHITE)
        res_label = font.render("Total Resistance: ", True, YELLOW)
        res_value = font.render(f"{TOTAL_R:.1f} Ω", True, WHITE)
        screen.blit(volt_label, (WIDTH - 200, 10))
        screen.blit(volt_value, (WIDTH - 200 + volt_label.get_width(), 10))
        screen.blit(curr_label, (WIDTH - 200, 30))
        screen.blit(curr_value, (WIDTH - 200 + curr_label.get_width(), 30))
        screen.blit(res_label, (WIDTH - 200, 50))
        screen.blit(res_value, (WIDTH - 200 + res_label.get_width(), 50))

        # Add instructions at the bottom
        instructions = font.render(
            "Up/Down arrows: Battery 1 voltage | Right/Left arrows: Battery 2 voltage",
            True,
            YELLOW,
        )
        screen.blit(
            instructions, (WIDTH // 2 - instructions.get_width() // 2, HEIGHT - 30)
        )

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
