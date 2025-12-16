import pygame
import sys
import random
from sounds import SoundManager  # ✅ ADDED

# ---------------- INIT ----------------
pygame.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
pygame.display.set_caption("Fly Feast")

clock = pygame.time.Clock()

# ---------------- SOUND SETUP ----------------
sound = SoundManager()
sound.play_music()

# ---------------- LOAD BACKGROUND ----------------
try:
    bg_img = pygame.image.load("view.png").convert()
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

        # -------- SOUND EVENTS (ADDED) --------
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            sound.play("jump")

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            sound.play("hit")
            mouse_x, mouse_y = event.pos
            for bee in bees:
                bee_rect = pygame.Rect(bee["x"], bee["y"], 40, 40)
                if bee_rect.collidepoint(mouse_x, mouse_y):
                    sound.play("eaten")

    keys = pygame.key.get_pressed()

    # -------- WALK SOUND (OPTIMIZED, ADDED) --------
    moving = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]
    if moving and not sound.walking:
        sound.play_loop("walk")
        sound.walking = True
    elif not moving and sound.walking:
        sound.stop("walk")
        sound.walking = False

    # -------- FROG MOVEMENT & INPUT --------
    if not jumping and jump_cooldown == 0 and keys[pygame.K_SPACE]:
        state = "jump"
        jumping = True
        jump_cooldown = 15

    if not jumping:
        if keys[pygame.K_LEFT]:
            frog_x -= frog_speed
            direction = "left"
            state = "idle"
        elif keys[pygame.K_RIGHT]:
            frog_x += frog_speed
            direction = "right"
            state = "idle"

    # -------- ANIMATION SELECT --------
    new_animation = f"{state}_{direction}"
    if new_animation != current_animation:
        current_animation = new_animation
        frame_index = 0

    # -------- ANIMATION UPDATE --------
    frame_index += animation_speed
    if frame_index >= len(frog_animations[current_animation]):
        frame_index = 0
        if state == "jump":
            state = "idle"
            jumping = False

    # -------- DRAWING (CLEAR SCREEN FIRST) --------
    if bg_img:
        screen.blit(bg_img, (0, 0))
    else:
        screen.fill((0, 0, 0))

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

    # Draw frog
    frog_img = frog_animations[current_animation][int(frame_index)]
    screen.blit(frog_img, (frog_x, frog_y))

    # Keep frog on screen
    frog_x = max(0, min(frog_x, SCREEN_WIDTH - FRAME_W))
    frog_y = max(0, min(frog_y, SCREEN_HEIGHT - FRAME_H))

    pygame.display.flip()

# ---------------- CLEANUP ----------------
sound.stop_music()
pygame.quit()
sys.exit()
