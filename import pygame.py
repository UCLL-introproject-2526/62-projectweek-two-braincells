import pygame
import sys
import random

# ---------------- INIT ----------------
pygame.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
pygame.display.set_caption("Fly Feast")

clock = pygame.time.Clock()

# ---------------- LOAD BACKGROUND ----------------
try:
    bg_img = pygame.image.load("view.png").convert()
    bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
except Exception as e:
    print(f"Warning: background_final.png not found or failed to load: {e}")
    bg_img = None  # if missing, screen will clear to black

# ---------------- BEE SETUP ----------------
try:
    bee_img = pygame.image.load("fly.png").convert_alpha()
except:
    bee_img = None

bees = []
for _ in range(6):
    bees.append({
        "x": random.randint(0, SCREEN_WIDTH),
        "y": random.randint(0, SCREEN_HEIGHT),
        "speed": random.randint(2, 4)
    })

# ---------------- FROG SETUP ----------------
FRAME_W, FRAME_H = 16, 16
frog_sheet = pygame.image.load("frog.png").convert_alpha()

def slice_sprite_sheet(sheet, frame_width, frame_height, frames_per_row):
    animations = {}
    for row_index, frames_count in enumerate(frames_per_row):
        frames = []
        for col in range(frames_count):
            frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0),
                       (col * frame_width, row_index * frame_height, frame_width, frame_height))
            frames.append(frame)
        animations[row_index] = frames
    return animations

frames_per_row = [4, 4, 3, 3]  # idle_right, idle_left, jump_right, jump_left
sheet_animations = slice_sprite_sheet(frog_sheet, FRAME_W, FRAME_H, frames_per_row)

frog_animations = {
    "idle_right": sheet_animations[0],
    "idle_left": sheet_animations[1],
    "jump_right": sheet_animations[2],
    "jump_left": sheet_animations[3],
}

frog_x = SCREEN_WIDTH // 2
frog_y = SCREEN_HEIGHT // 2
frog_speed = 6

state = "idle"
direction = "right"
current_animation = "idle_right"
frame_index = 0
animation_speed = 0.15

jumping = False
jump_cooldown = 0

# ---------------- MAIN LOOP ----------------
running = True
while running:
    clock.tick(60)

    if jump_cooldown > 0:
        jump_cooldown -= 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    keys = pygame.key.get_pressed()

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
        screen.blit(bg_img, (0, 0))  # clear screen with background image
    else:
        screen.fill((0, 0, 0))       # fallback clear to black if no image

    # Draw bees
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

    # Draw frog
    frog_img = frog_animations[current_animation][int(frame_index)]
    screen.blit(frog_img, (frog_x, frog_y))

    # Keep frog on screen
    frog_x = max(0, min(frog_x, SCREEN_WIDTH - FRAME_W))
    frog_y = max(0, min(frog_y, SCREEN_HEIGHT - FRAME_H))

    # Update display
    pygame.display.flip()

pygame.quit()
sys.exit()
