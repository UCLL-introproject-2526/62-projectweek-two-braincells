import pygame
import sys
import random
import os

# ---------------- INIT ----------------
pygame.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
pygame.display.set_caption("Fly Feast")

clock = pygame.time.Clock()

# ---------------- IMAGES FOLDER ----------------
IMAGES_FOLDER = "images"  # folder where your images are stored

def load_image(name, alpha=False):
    path = os.path.join(IMAGES_FOLDER, name)
    try:
        if alpha:
            return pygame.image.load(path).convert_alpha()
        else:
            return pygame.image.load(path).convert()
    except Exception as e:
        print(f"Failed to load {name}: {e}")
        return None

# ---------------- LOAD IMAGES ----------------
bg_img = load_image("view.png")              # background image
bee_img = load_image("fly.png", alpha=True)  # bee image

# Scale background to fullscreen
if bg_img:
    bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

# ---------------- BEE SETUP ----------------
bees = []
for _ in range(6):
    bees.append({
        "x": random.randint(0, SCREEN_WIDTH),
        "y": random.randint(0, SCREEN_HEIGHT),
        "speed": random.randint(2, 4)
    })

# ---------------- MAIN LOOP ----------------
running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    # -------- CLEAR SCREEN --------
    screen.fill((0, 0, 0))  # clear everything before drawing
    if bg_img:
        screen.blit(bg_img, (0, 0))  # draw background

    # -------- DRAW BEES --------
    for bee in bees:
        bee["x"] += bee["speed"]
        bee["y"] += random.choice([-1, 0, 1])  # zig-zag
        if bee["x"] > SCREEN_WIDTH:
            bee["x"] = -40
            bee["y"] = random.randint(0, SCREEN_HEIGHT)
        if bee_img:
            screen.blit(bee_img, (bee["x"], bee["y"]))
        else:
            pygame.draw.rect(screen, (255, 255, 0), (bee["x"], bee["y"], 40, 40))

    pygame.display.flip()

pygame.quit()
sys.exit()
