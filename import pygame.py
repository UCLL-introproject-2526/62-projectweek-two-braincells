import pygame
import sys
import random
from sounds import SoundManager   # ✅ ADDED

# ---------------- INIT ----------------
pygame.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
pygame.display.set_caption("Fly Feast")

clock = pygame.time.Clock()

# ---------------- SOUND SETUP (ADDED) ----------------
sound = SoundManager()
sound.play_music()

# ---------------- LOAD IMAGES ----------------
def load_image(filename):
    """Load image from images folder."""
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
BEE_SIZE = 40

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

    # ---------------- EVENTS ----------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_SPACE:
                sound.play("jump")   # ✅ jump sound

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            sound.play("hit")       # ✅ hit sound
            mouse_x, mouse_y = event.pos

            for bee in bees:
                bee_rect = pygame.Rect(bee["x"], bee["y"], BEE_SIZE, BEE_SIZE)
                if bee_rect.collidepoint(mouse_x, mouse_y):
                    sound.play("eaten")  # ✅ eaten sound

    # ---------------- WALK SOUND (HOLD KEY) ----------------
    keys = pygame.key.get_pressed()
    moving = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]

    if moving and not sound.walking:
        sound.play_loop("walk")
        sound.walking = True

    elif not moving and sound.walking:
        sound.stop("walk")
        sound.walking = False

    # ---------------- DRAW ----------------
    if bg_img:
        screen.blit(bg_img, (0, 0))
    else:
        screen.fill((0, 0, 0))

    for bee in bees:
        bee["x"] += bee["speed"]
        bee["y"] += random.choice([-1, 0, 1])

        if bee["x"] > SCREEN_WIDTH:
            bee["x"] = -BEE_SIZE
            bee["y"] = random.randint(0, SCREEN_HEIGHT)

        if bee_img:
            screen.blit(bee_img, (bee["x"], bee["y"]))
        else:
            pygame.draw.rect(
                screen,
                (255, 255, 0),
                (bee["x"], bee["y"], BEE_SIZE, BEE_SIZE)
            )

    pygame.display.flip()

# ---------------- CLEANUP ----------------
sound.stop_music()
pygame.quit()
sys.exit()
