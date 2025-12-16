import pygame, sys

pygame.init()
screen = pygame.display.set_mode((900, 600))
clock = pygame.time.Clock()

# Frog
frog = pygame.Rect(200, 200, 50, 50)
vx = 0
vy = 0

SPEED = 6
JUMP = 16
GRAVITY = 0.8

# Ground (a platform)
ground = pygame.Rect(0, 520, 900, 80)

on_ground = False
running = True
while running:
    dt = clock.tick(60) / 1000  # not required, but useful later

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Jump on key press (one time), only if on ground
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and on_ground:
                vy = -JUMP
                on_ground = False

    # Continuous left/right (AZERTY: Q/D)
    keys = pygame.key.get_pressed()
    vx = 0
    if keys[pygame.K_q]:
        vx = -SPEED
    if keys[pygame.K_d]:
        vx = SPEED

    # Apply gravity
    vy += GRAVITY

    # --- Move X then resolve collisions (simple) ---
    frog.x += vx
    if frog.colliderect(ground):
        # push out
        if vx > 0:
            frog.right = ground.left
        elif vx < 0:
            frog.left = ground.right

    # --- Move Y then resolve collisions ---
    frog.y += int(vy)
    if frog.colliderect(ground):
        if vy > 0:  # falling onto ground
            frog.bottom = ground.top
            vy = 0
            on_ground = True
        elif vy < 0:  # hitting underside (if you add platforms above)
            frog.top = ground.bottom
            vy = 0

    # Draw
    screen.fill((25, 25, 25))
    pygame.draw.rect(screen, (0, 180, 0), frog)     # frog
    pygame.draw.rect(screen, (120, 90, 40), ground) # ground
    pygame.display.flip()

pygame.quit()
sys.exit()


# -------------------platform------------------ 

platforms = [
    pygame.Rect(0, 520, 900, 80),
    pygame.Rect(300, 420, 200, 25),
]

# move X
frog.x += vx
for p in platforms:
    if frog.colliderect(p):
        if vx > 0: frog.right = p.left
        if vx < 0: frog.left  = p.right

# move Y
frog.y += int(vy)
on_ground = False
for p in platforms:
    if frog.colliderect(p):
        if vy > 0:
            frog.bottom = p.top
            vy = 0
            on_ground = True
        elif vy < 0:
            frog.top = p.bottom
            vy = 0

# ------------------cursor dir and interactions--------------

mx, my = pygame.mouse.getpos()
facing_right = (mx >= frog_rect.centerx)

img = current_frame
if not facing_right:
    img = pygame.transform.flip(img, True, False)
screen.blit(img, frog_rect.topleft)

# -------------tongue w/ lim range---------------

import math

TONGUE_range = 140
TONGUE_time = 0.12

tongue_active = False
tongue_timer = 0.0
tongue_end (0,0)