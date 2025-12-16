import pygame
import sys
import random


# Initialize Pygame
pygame.init()

# Fullscreen setup
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()  # get actual screen size
pygame.display.set_caption("Fly Feast")

# Clock
clock = pygame.time.Clock()

# Bee image
try:
    bee_img = pygame.image.load("fly.png").convert_alpha()
except:
    print("Warning: fly.png not found. Using rectangles instead.")
    bee_img = None

# Create bees
bees = []
NUM_BEES = 6
for _ in range(NUM_BEES):
    bees.append({
        "x": random.randint(0, SCREEN_WIDTH),
        "y": random.randint(0, SCREEN_HEIGHT),
        "speed": random.randint(2, 4)
    })

# Background color
BG_COLOR = (135, 206, 250)  # light sky blue


# Main Game Loop

running = True
while running:
    clock.tick(60)  # 60 FPS

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Optional: Exit on ESC key
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    # Draw Background Color
    screen.fill(BG_COLOR)  # fill the screen with color every frame

    # Move & Draw Bees
    for bee in bees:
        bee["x"] += bee["speed"]
        bee["y"] += random.choice([-1, 0, 1])  # zig-zag movement

        # Reset bee when off screen
        if bee["x"] > SCREEN_WIDTH:
            bee["x"] = -40  # reset just off the left side
            bee["y"] = random.randint(0, SCREEN_HEIGHT)

        # Draw bee
        if bee_img:
            screen.blit(bee_img, (bee["x"], bee["y"]))
        else:
            pygame.draw.rect(screen, (255, 255, 0), (bee["x"], bee["y"], 40, 40))

    # Update Display
    pygame.display.flip()

# Quit Game
pygame.quit()
sys.exit()