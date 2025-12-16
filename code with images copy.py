import pygame
import sys
import random
import subprocess

# ---------------- INIT ----------------
pygame.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
pygame.display.set_caption("Fly Feast")

clock = pygame.time.Clock()

# ---------------- LOAD IMAGES ----------------
def load_image(filename):
    """Load image from intro_project/images folder."""
    path = f"images/{filename}"
    try:
        return pygame.image.load(path).convert_alpha()
    except Exception as e:
        print(f"⚠️ Failed to load {path}: {e}")
        return None

bg_img = load_image("view.png")
bee_img = load_image("fly.png")

# ---------------- GAME VARIABLES ----------------
bees = []
for _ in range(6):
    bees.append({
        "x": random.randint(0, SCREEN_WIDTH),
        "y": random.randint(0, SCREEN_HEIGHT),
        "speed": random.randint(2, 4)
    })

# ---------------- GIT PUSH FUNCTION ----------------
def git_push(commit_message="Auto-update from Python"):
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✅ Git push successful!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git push failed: {e}")

# ---------------- MAIN LOOP ----------------
running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    # DRAW
    if bg_img:
        screen.blit(bg_img, (0, 0))
    else:
        screen.fill((0, 0, 0))

    for bee in bees:
        bee["x"] += bee["speed"]
        bee["y"] += random.choice([-1, 0, 1])
        if bee["x"] > SCREEN_WIDTH:
            bee["x"] = -40
            bee["y"] = random.randint(0, SCREEN_HEIGHT)
        if bee_img:
            screen.blit(bee_img, (bee["x"], bee["y"]))
        else:
            pygame.draw.rect(screen, (255, 255, 0), (bee["x"], bee["y"], 40, 40))

    pygame.display.flip()

# ---------------- CLEANUP ----------------
git_push("Auto-commit game assets and updates")
pygame.quit()
sys.exit()
