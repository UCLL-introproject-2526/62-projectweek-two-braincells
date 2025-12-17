import pygame
import sys
import random
import math
import os
from sounds import SoundManager

# Initialize Pygame
pygame.init()
# screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN) # todo: revert back to this
screen = pygame.display.set_mode((0, 0))
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
pygame.display.set_caption("Fly Feast")
clock = pygame.time.Clock()

sound = SoundManager()
sound.play_music()
pygame.mixer.music.set_volume(0.3)

# Constants
GROUND_Y = SCREEN_HEIGHT - 150
GROUND_HEIGHT = 20
SWAMP_START_X = int(SCREEN_WIDTH * 6 / 10)
SWAMP_WIDTH = int(SCREEN_WIDTH * 3 / 10)
SWAMP_HEIGHT = SCREEN_HEIGHT - GROUND_Y
PLATFORM_WIDTH = SWAMP_WIDTH // 2
PLATFORM_HEIGHT = 20
PLATFORM_X = SWAMP_START_X + (SWAMP_WIDTH - PLATFORM_WIDTH) // 2
PLATFORM_Y = GROUND_Y - 80
NUM_FLIES = 6
TIMER_START_SECONDS = 90
SCORE_ANIMATION_DURATION = 200
ANIMATION_SPEED = 150
BASE_DIR = os.getcwd()
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SPRITES_DIR = os.path.join(ASSETS_DIR, "sprites")

# Colors
BG_COLOR = (135, 206, 250)
GROUND_COLOR = (95, 75, 55)
SWAMP_COLOR = (45, 85, 75)
PLATFORM_COLOR = (105, 85, 65)

# Load images
def load_image(path, convert_alpha=False):
    try:
        img = pygame.image.load(path)
        return img.convert_alpha() if convert_alpha else img.convert(), True
    except:
        return None, False

fly_img, _ = load_image(f"{SPRITES_DIR}/fly/fly.png", convert_alpha=True)
background_img, background_loaded = load_image(f"{ASSETS_DIR}/background.png")

# Load tree images
tree_images = None
tree_loaded = False
tree_width, tree_height = 150, 250
try:
    tree_left, _ = load_image(f"{SPRITES_DIR}/trees/tree_left_final_clean2.png", convert_alpha=True)
    tree_middle, _ = load_image(f"{SPRITES_DIR}/trees/tree_middle_final_clean2.png", convert_alpha=True)
    tree_right, _ = load_image(f"{SPRITES_DIR}/trees/tree_right_final_clean2.png", convert_alpha=True)
    if tree_left and tree_middle and tree_right:
        tree_left = pygame.transform.scale(tree_left, (tree_width, tree_height))
        tree_middle = pygame.transform.scale(tree_middle, (tree_width, tree_height))
        tree_right = pygame.transform.scale(tree_right, (tree_width, tree_height))
        tree_images = [tree_left, tree_middle, tree_right]
        tree_loaded = True
except:
    pass

# Load tongue sprites
tongue_frames = []
tongue_loaded = False
tongue_paths = [
    "tongues_split_pngs",
    f"{SPRITES_DIR}/frog/tongue" # place tongue pictures in /assets/sprites/frog/tongue
]

for tongue_dir in tongue_paths:
    if os.path.exists(tongue_dir):
        for i in range(1, 9):  # tongue_01.png to tongue_08.png
            path = f"{SPRITES_DIR}/frog/tongue/tongue_{i:02d}.png" # place tongue pictures in /assets/sprites/frog/tongue
            if os.path.exists(path):
                try:
                    frame = pygame.image.load(path).convert_alpha()
                    tongue_frames.append(frame)
                except:
                    pass
        if tongue_frames:
            tongue_loaded = True
            break

# Load frog sprites
frog_frames = {
    "idle_left": [], "idle_right": [],
    "walk_left": [], "walk_right": [],
    "jump_left": [], "jump_right": []
}
sprite_sheet_loaded = False

for anim_type in ["standing", "walk", "jump"]:
    frame_count = 4 if anim_type == "standing" else 3
    for i in range(1, frame_count + 1):
        for direction in ["left", "right"]:
            key = f"{anim_type.replace('standing', 'idle')}_{direction}"
            path = f"{SPRITES_DIR}/frog/{anim_type}_{direction}_f{i}.png"
            if os.path.exists(path):
                try:
                    frame = pygame.image.load(path).convert_alpha()
                    frog_frames[key].append(frame)
                except:
                    pass

sprite_sheet_loaded = any(len(frames) > 0 for frames in frog_frames.values())

# Animation state
animation_frames = {key: 0 for key in frog_frames.keys()} if sprite_sheet_loaded else {}
animation_timers = {key: 0 for key in frog_frames.keys()} if sprite_sheet_loaded else {}
current_animation = "idle_right"

# Load pixel font
pixel_font_images = {}
pixel_font_loaded = False
default_char_width, default_char_height = 20, 20

for char in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    path = f"{ASSETS_DIR}/pixel_font/{char}.png"

    if os.path.exists(path):
        try:
            pixel_font_images[char] = pygame.image.load(path).convert_alpha()
        except:
            pass

if pixel_font_images:
    pixel_font_loaded = True
    default_char_width = pixel_font_images['0'].get_width()
    default_char_height = pixel_font_images['0'].get_height()

# Game state
score = 0
high_score = 0
score_animation_time = 0
timer_start_time = None
timer_remaining = TIMER_START_SECONDS

# --- GAME OVER STATE ---
game_over = False
game_over_start_time = 0
shake_duration = 700      # ms
shake_magnitude = 20


# Create flies
flies = []
for _ in range(NUM_FLIES):
    flies.append({
        "x": random.randint(0, SCREEN_WIDTH),
        "y": random.randint(0, SCREEN_HEIGHT),
        "speed": random.randint(2, 4)
    })

# Character
character = {
    "x": SCREEN_WIDTH // 2,
    "y": GROUND_Y - 30,
    "width": 50,
    "height": 30,
    "speed": 5,
    "jump_speed": -15,
    "velocity_y": 0,
    "gravity": 0.8,
    "on_ground": False,
    "ground_y": GROUND_Y - 30,
    "has_double_jump": True,
    "double_jump_cooldown_end": 0,
    "tongue_extended": False,
    "tongue_length": 0,
    "tongue_max_length": 300,
    "tongue_angle": 0,
    "tongue_speed": 50,
    "tongue_end_time": 0,
    "facing_direction": "right"
}

def reset_game():
    global score, score_animation_time, timer_start_time, timer_remaining
    score = 0
    score_animation_time = 0
    timer_start_time = pygame.time.get_ticks()
    timer_remaining = TIMER_START_SECONDS
    
    character["x"] = SCREEN_WIDTH // 2
    character["y"] = GROUND_Y - 30
    character["velocity_y"] = 0
    character["on_ground"] = False
    character["ground_y"] = GROUND_Y - 30
    character["has_double_jump"] = True
    character["double_jump_cooldown_end"] = 0
    character["tongue_extended"] = False
    character["tongue_length"] = 0
    character["tongue_angle"] = 0
    character["tongue_end_time"] = 0
    character["facing_direction"] = "right"
    
    for fly in flies:
        fly["x"] = random.randint(0, SCREEN_WIDTH)
        fly["y"] = random.randint(0, SCREEN_HEIGHT)
        fly["speed"] = random.randint(2, 4)

def draw_pixel_text(surface, text, x, y, scale=1.0, color=None):
    current_x = x
    for char in text.upper():
        if char in pixel_font_images:
            char_img = pixel_font_images[char]
            scaled_width = int(default_char_width * scale)
            scaled_height = int(default_char_height * scale)
            scaled_char = pygame.transform.scale(char_img, (scaled_width, scaled_height))
            
            if color:
                color_surface = pygame.Surface(scaled_char.get_size(), pygame.SRCALPHA)
                color_surface.fill(color)
                scaled_char = scaled_char.copy()
                scaled_char.blit(color_surface, (0, 0), special_flags=pygame.BLEND_MULT)
            
            surface.blit(scaled_char, (current_x, y))
            current_x += scaled_width + 2
        elif char == ' ':
            current_x += int(default_char_width * scale) // 2

# Main game loop
running = True
if timer_start_time is None:
    timer_start_time = pygame.time.get_ticks()

while running:
    clock.tick(60)
    current_time = pygame.time.get_ticks()
    
    # Update timer
    elapsed_seconds = (current_time - timer_start_time) // 1000
    timer_remaining = max(0, TIMER_START_SECONDS - elapsed_seconds)
    if timer_remaining <= 0:
        reset_game()
    

    keys = pygame.key.get_pressed()

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

        elif game_over and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            if restart_rect.collidepoint(mouse_x, mouse_y):
                reset_game()
                game_over = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            sound.play("hit") 
            if not character["tongue_extended"]:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                frog_center_x = character["x"] + character["width"] // 2
                frog_center_y = character["y"] + character["height"] // 2
                character["tongue_angle"] = math.atan2(mouse_y - frog_center_y, mouse_x - frog_center_x)
                character["tongue_extended"] = True
                character["tongue_length"] = 0
                character["tongue_end_time"] = current_time + 300
        elif event.type == pygame.KEYDOWN and (event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w):
            sound.play("jump")
            if character["on_ground"]:
                character["velocity_y"] = character["jump_speed"]
                character["on_ground"] = False
            elif not character["on_ground"] and character["has_double_jump"] and current_time >= character["double_jump_cooldown_end"]:
                character["velocity_y"] = character["jump_speed"]
                character["has_double_jump"] = False
                character["double_jump_cooldown_end"] = current_time + 2000
    
    shake_x, shake_y = 0, 0
    if game_over:
        elapsed = pygame.time.get_ticks() - game_over_start_time
        if elapsed < shake_duration:
            shake_x = random.randint(-shake_magnitude, shake_magnitude)
            shake_y = random.randint(-shake_magnitude, shake_magnitude)

    # Draw background
    if background_loaded:
        if background_img.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
            screen.blit(pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT)), (shake_x, shake_y))
        else:
            screen.blit(background_img, (0, 0))
    else:
        screen.fill(BG_COLOR)
    
    # Draw ground and swamp
    pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, SCREEN_WIDTH, GROUND_HEIGHT))
    pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y + GROUND_HEIGHT, SWAMP_START_X, SWAMP_HEIGHT - GROUND_HEIGHT))
    pygame.draw.rect(screen, GROUND_COLOR, (SWAMP_START_X + SWAMP_WIDTH, GROUND_Y + GROUND_HEIGHT, 
                                           SCREEN_WIDTH - (SWAMP_START_X + SWAMP_WIDTH), SWAMP_HEIGHT - GROUND_HEIGHT))
    pygame.draw.rect(screen, SWAMP_COLOR, (SWAMP_START_X, GROUND_Y, SWAMP_WIDTH, SWAMP_HEIGHT))
    pygame.draw.rect(screen, PLATFORM_COLOR, (PLATFORM_X, PLATFORM_Y, PLATFORM_WIDTH, PLATFORM_HEIGHT))
    
    # Draw trees
    if tree_loaded and tree_images:
        # Individual y-positions to align each tree perfectly with ground (no gaps)
        # Account for different transparent padding in each tree image
        tree_y_left = GROUND_Y - tree_height + 23   # Left tree: adjusted to sit on ground
        tree_y_middle = GROUND_Y - tree_height + 26  # Middle tree: less offset (raise it, less padding)
        tree_y_right = GROUND_Y - tree_height + 33   # Right tree: more offset (lower it, more padding)
        tree_positions = [
            (SCREEN_WIDTH // 8, tree_y_left, tree_images[0]),
            (SCREEN_WIDTH // 4, tree_y_middle, tree_images[1]),
            (SCREEN_WIDTH // 2 - 50, tree_y_right, tree_images[2])
        ]
        for tree_x, tree_y_pos, tree_img in tree_positions:
            if tree_x < SWAMP_START_X:
                screen.blit(tree_img, (tree_x, tree_y_pos))
    
    # Character movement
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        character["x"] -= character["speed"]
        character["facing_direction"] = "left"
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        character["x"] += character["speed"]
        character["facing_direction"] = "right"
    
    character["x"] = max(0, min(character["x"], SCREEN_WIDTH - character["width"]))
    
    # Physics
    character["velocity_y"] += character["gravity"]
    character["y"] += character["velocity_y"]
    
    # Ground/platform collision
    character_feet_y = character["y"] + character["height"]
    on_ground = False
    
    if character_feet_y >= GROUND_Y:
        character["y"] = GROUND_Y - character["height"]
        character["velocity_y"] = 0
        on_ground = True
    
    platform_rect = pygame.Rect(PLATFORM_X, PLATFORM_Y, PLATFORM_WIDTH, PLATFORM_HEIGHT)
    char_rect = pygame.Rect(character["x"], character["y"], character["width"], character["height"])
    if char_rect.colliderect(platform_rect) and character["velocity_y"] >= 0:
        if character["y"] + character["height"] <= PLATFORM_Y + PLATFORM_HEIGHT:
            character["y"] = PLATFORM_Y - character["height"]
            character["velocity_y"] = 0
            on_ground = True
    
    character["on_ground"] = on_ground
    if on_ground:
        character["has_double_jump"] = True
    
    # Swamp death check
    character_center_x = character["x"] + character["width"] // 2
    character_bottom = character["y"] + character["height"]
    on_platform = (PLATFORM_X <= character_center_x <= PLATFORM_X + PLATFORM_WIDTH and 
                   PLATFORM_Y <= character_bottom <= PLATFORM_Y + PLATFORM_HEIGHT + 5)
    
    if (SWAMP_START_X <= character_center_x <= SWAMP_START_X + SWAMP_WIDTH and 
        character_bottom >= GROUND_Y and not on_platform and not game_over):

        sound.play("gameover")
        game_over = True
        game_over_start_time = pygame.time.get_ticks()

    
    # Update tongue
    if character["tongue_extended"]:
        if character["tongue_length"] < character["tongue_max_length"]:
            character["tongue_length"] += character["tongue_speed"]
        else:
            character["tongue_length"] = character["tongue_max_length"]
        
        if current_time >= character["tongue_end_time"]:
            character["tongue_extended"] = False
            character["tongue_length"] = 0
        
        frog_center_x = character["x"] + character["width"] // 2
        frog_center_y = character["y"] + character["height"] // 2
        tongue_end_x = frog_center_x + math.cos(character["tongue_angle"]) * character["tongue_length"]
        tongue_end_y = frog_center_y + math.sin(character["tongue_angle"]) * character["tongue_length"]
        
        # Fly collision
        flies_to_remove = []
        for i, fly in enumerate(flies):
            fly_center_x = fly["x"] + 20
            fly_center_y = fly["y"] + 20
            to_fly_x = fly_center_x - frog_center_x
            to_fly_y = fly_center_y - frog_center_y
            dot_product = to_fly_x * math.cos(character["tongue_angle"]) + to_fly_y * math.sin(character["tongue_angle"])
            
            if 0 <= dot_product <= character["tongue_length"]:
                perp_distance = abs(-to_fly_x * math.sin(character["tongue_angle"]) + to_fly_y * math.cos(character["tongue_angle"]))
                if perp_distance < 30:
                    sound.play("eaten")
                    flies_to_remove.append(i)
        
        for i in reversed(flies_to_remove):
            flies.pop(i)
            score += 1
            if score > high_score:
                high_score = score
            score_animation_time = current_time
            flies.append({
                "x": random.randint(0, SCREEN_WIDTH),
                "y": random.randint(0, SCREEN_HEIGHT),
                "speed": random.randint(2, 4)
            })
    
    # Draw character
    if sprite_sheet_loaded and frog_frames:
        direction = character["facing_direction"]
        if not character["on_ground"]:
            animation_key = f"jump_{direction}"
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            animation_key = "walk_right"
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            animation_key = "walk_left"
        else:
            animation_key = f"idle_{direction}"
        
        if animation_key != current_animation:
            animation_frames[animation_key] = 0
            animation_timers[animation_key] = current_time
            current_animation = animation_key
        
        if current_time - animation_timers[animation_key] >= ANIMATION_SPEED:
            animation_timers[animation_key] = current_time
            if animation_key in frog_frames and frog_frames[animation_key]:
                animation_frames[animation_key] = (animation_frames[animation_key] + 1) % len(frog_frames[animation_key])
        
        if animation_key in frog_frames and frog_frames[animation_key]:
            frame_index = animation_frames[animation_key]
            current_sprite = frog_frames[animation_key][frame_index]
            if current_sprite.get_size() != (character["width"], character["height"]):
                current_sprite = pygame.transform.scale(current_sprite, (character["width"], character["height"]))
            screen.blit(current_sprite, (character["x"], character["y"]))
    else:
        pygame.draw.rect(screen, (255, 100, 100), (character["x"], character["y"], character["width"], character["height"]))
    
    # Draw tongue
    if character["tongue_extended"] and tongue_loaded and tongue_frames:
        frog_center_x = character["x"] + character["width"] // 2
        frog_center_y = character["y"] + character["height"] // 2
        
        # Select frame based on tongue extension progress
        progress = character["tongue_length"] / character["tongue_max_length"]
        frame_index = min(int(progress * len(tongue_frames)), len(tongue_frames) - 1)
        tongue_sprite = tongue_frames[frame_index]
        
        # Get original sprite dimensions
        original_width = tongue_sprite.get_width()
        original_height = tongue_sprite.get_height()
        
        # Scale sprite to match actual tongue length
        # The sprite extends horizontally, so scale width to match tongue_length
        scale_factor = character["tongue_length"] / original_width if original_width > 0 else 1.0
        scaled_width = int(original_width * scale_factor)
        scaled_height = int(original_height * scale_factor)
        
        # Scale the sprite
        scaled_tongue = pygame.transform.scale(tongue_sprite, (scaled_width, scaled_height))
        
        # Calculate rotation angle
        angle_degrees = math.degrees(character["tongue_angle"])
        angle_rad = character["tongue_angle"]
        
        # Rotate scaled tongue sprite
        rotated_tongue = pygame.transform.rotate(scaled_tongue, -angle_degrees)
        rotated_rect = rotated_tongue.get_rect()
        
        # Calculate where the start point (left center) of scaled sprite is after rotation
        sprite_center_x = scaled_width // 2
        sprite_center_y = scaled_height // 2
        
        # Vector from sprite center to start point (left edge, center vertically)
        start_vec_x = -sprite_center_x
        start_vec_y = 0
        
        # Rotate this vector
        rotated_start_x = start_vec_x * math.cos(angle_rad) - start_vec_y * math.sin(angle_rad)
        rotated_start_y = start_vec_x * math.sin(angle_rad) + start_vec_y * math.cos(angle_rad)
        
        # Position so the rotated start point aligns with frog's mouth
        # Account for the fact that rotated sprite is larger
        size_diff_x = (rotated_rect.width - scaled_width) // 2
        size_diff_y = (rotated_rect.height - scaled_height) // 2
        
        draw_x = frog_center_x - (sprite_center_x + rotated_start_x) - size_diff_x
        draw_y = frog_center_y - (sprite_center_y + rotated_start_y) - size_diff_y
        
        screen.blit(rotated_tongue, (draw_x, draw_y))
    elif character["tongue_extended"]:
        # Fallback to simple line if tongue sprites not loaded
        frog_center_x = character["x"] + character["width"] // 2
        frog_center_y = character["y"] + character["height"] // 2
        tongue_end_x = frog_center_x + math.cos(character["tongue_angle"]) * character["tongue_length"]
        tongue_end_y = frog_center_y + math.sin(character["tongue_angle"]) * character["tongue_length"]
        pygame.draw.line(screen, (200, 0, 0), (frog_center_x, frog_center_y), (tongue_end_x, tongue_end_y), 8)
        pygame.draw.circle(screen, (150, 0, 0), (int(tongue_end_x), int(tongue_end_y)), 6)
    
    # Draw flies
    for fly in flies:
        fly["x"] += fly["speed"]
        fly["y"] += random.choice([-1, 0, 1])
        if fly["x"] > SCREEN_WIDTH:
            fly["x"] = -40
            fly["y"] = random.randint(0, SCREEN_HEIGHT)
        if fly_img:
            screen.blit(fly_img, (fly["x"], fly["y"]))
        else:
            pygame.draw.rect(screen, (255, 255, 0), (fly["x"], fly["y"], 40, 40))
    
    # Draw UI
    if pixel_font_loaded:
        # High score
        high_score_text = f"HIGHEST SCORE: {high_score}"
        high_score_scale = 0.3
        high_score_y = 20 + (int(default_char_height * 0.7) - int(default_char_height * high_score_scale)) // 2
        draw_pixel_text(screen, high_score_text, 20, high_score_y, scale=high_score_scale)
        
        # Timer
        timer_text = str(int(timer_remaining))
        timer_scale = 0.7
        if timer_remaining <= 15:
            heartbeat = 1.0 + 0.15 * abs(math.sin((current_time % 1000) / 1000.0 * math.pi * 2))
            timer_scale = 0.7 * heartbeat
        char_width = int(default_char_width * timer_scale)
        text_width = len(timer_text) * char_width + (len(timer_text) - 1) * 2
        timer_x = (SCREEN_WIDTH - text_width) // 2
        timer_color = (255, 0, 0) if timer_remaining <= 10 else (255, 255, 255)
        draw_pixel_text(screen, timer_text, timer_x, 20, scale=timer_scale, color=timer_color)
        
        # Score
        score_text = str(score)
        base_scale = 0.7
        scale = base_scale
        if score_animation_time > 0:
            elapsed = current_time - score_animation_time
            if elapsed < SCORE_ANIMATION_DURATION:
                scale = base_scale + (0.3 * (1.0 - elapsed / SCORE_ANIMATION_DURATION))
            else:
                score_animation_time = 0
        char_width = int(default_char_width * scale)
        text_width = len(score_text) * char_width + (len(score_text) - 1) * 2
        score_x = SCREEN_WIDTH - text_width - 20
        draw_pixel_text(screen, score_text, score_x, 20, scale=scale)
    
    if game_over:
    # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

    # GAME OVER text
        if pixel_font_loaded:
            text = "GAME OVER"
            scale = 1.2
            text_width = len(text) * int(default_char_width * scale)
            text_x = (SCREEN_WIDTH - text_width) // 2
            draw_pixel_text(
                screen,
                text,
                text_x,
                SCREEN_HEIGHT // 2 - 140,
                scale=scale,
                color=(255, 50, 50)
            )

            # RESTART text (clickable)
            restart_text = "RESTART"
            restart_scale = 0.6

            text_width = len(restart_text) * int(default_char_width * restart_scale)
            text_height = int(default_char_height * restart_scale)

            text_x = (SCREEN_WIDTH - text_width) // 2
            text_y = (SCREEN_HEIGHT // 2) + 10

            mouse_x, mouse_y = pygame.mouse.get_pos()

            hover = (
                text_x <= mouse_x <= text_x + text_width and
                text_y <= mouse_y <= text_y + text_height
            )

            color = (255, 255, 255) if hover else (200, 200, 200)

            draw_pixel_text(
                screen,
                restart_text,
                text_x,
                text_y,
                scale=restart_scale,
                color=color
            )

            restart_rect = pygame.Rect(text_x, text_y, text_width, text_height)

    pygame.display.flip()

pygame.quit()
sys.exit()