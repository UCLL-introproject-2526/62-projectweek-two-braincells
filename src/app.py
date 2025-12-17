import pygame
import sys
import random
import math
import os
import subprocess
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
pygame.mixer.music.set_volume(0.25)

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

# Additional platforms for jumping around - evenly distributed across the map
platforms = [
    # Left side platforms (evenly spaced)
    {"x": int(SCREEN_WIDTH * 0.05), "y": GROUND_Y - 100, "width": 100, "height": PLATFORM_HEIGHT},
    {"x": int(SCREEN_WIDTH * 0.20), "y": GROUND_Y - 160, "width": 100, "height": PLATFORM_HEIGHT},
    {"x": int(SCREEN_WIDTH * 0.35), "y": GROUND_Y - 80, "width": 100, "height": PLATFORM_HEIGHT},
    {"x": int(SCREEN_WIDTH * 0.50), "y": GROUND_Y - 140, "width": 100, "height": PLATFORM_HEIGHT},

    # Platform over swamp
    {"x": PLATFORM_X, "y": PLATFORM_Y, "width": PLATFORM_WIDTH, "height": PLATFORM_HEIGHT},

    # Right side platforms (evenly spaced)
    {"x": SWAMP_START_X + SWAMP_WIDTH + int(SCREEN_WIDTH * 0.02), "y": GROUND_Y - 120, "width": 100, "height": PLATFORM_HEIGHT},
    {"x": int(SCREEN_WIDTH * 0.92), "y": GROUND_Y - 180, "width": 100, "height": PLATFORM_HEIGHT},

    # Upper area platforms (higher up on the screen)
    {"x": int(SCREEN_WIDTH * 0.10), "y": GROUND_Y - 280, "width": 90, "height": PLATFORM_HEIGHT},
    {"x": int(SCREEN_WIDTH * 0.30), "y": GROUND_Y - 320, "width": 90, "height": PLATFORM_HEIGHT},
    {"x": int(SCREEN_WIDTH * 0.55), "y": GROUND_Y - 300, "width": 90, "height": PLATFORM_HEIGHT},
    {"x": SWAMP_START_X + SWAMP_WIDTH + int(SCREEN_WIDTH * 0.05), "y": GROUND_Y - 260, "width": 90, "height": PLATFORM_HEIGHT},
    {"x": int(SCREEN_WIDTH * 0.88), "y": GROUND_Y - 340, "width": 90, "height": PLATFORM_HEIGHT},
]

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

# Fly size used for collision + boundaries
FLY_W = fly_img.get_width() if fly_img else 40
FLY_H = fly_img.get_height() if fly_img else 40

# Load UI images
UI_DIR = os.path.join(ASSETS_DIR, "ui")
wooden_sign_img, wooden_sign_loaded = load_image(f"{UI_DIR}/wooden_sign_transparent_cleared.png", convert_alpha=True)

# Load ground tiles
ground_tiles_dir = os.path.join(ASSETS_DIR, "ground_tiles_25_pngs")
GROUND_TILE_SCALE = 2
ground_tile_upper_raw, ground_tile_upper_loaded = load_image(f"{ground_tiles_dir}/tile_r1_c2.png")
ground_tile_main_raw, ground_tile_main_loaded = load_image(f"{ground_tiles_dir}/tile_r2_c3.png")
ground_tile_corner_raw, ground_tile_corner_loaded = load_image(f"{ground_tiles_dir}/tile_r1_c3.png")
ground_tile_left_corner_raw, ground_tile_left_corner_loaded = load_image(f"{ground_tiles_dir}/tile_r1_c1.png")

# Scale ground tiles
if ground_tile_upper_loaded and ground_tile_upper_raw:
    original_size = ground_tile_upper_raw.get_size()
    ground_tile_upper = pygame.transform.scale(
        ground_tile_upper_raw,
        (int(original_size[0] * GROUND_TILE_SCALE), int(original_size[1] * GROUND_TILE_SCALE))
    )
else:
    ground_tile_upper = None

if ground_tile_main_loaded and ground_tile_main_raw:
    original_size = ground_tile_main_raw.get_size()
    ground_tile_main = pygame.transform.scale(
        ground_tile_main_raw,
        (int(original_size[0] * GROUND_TILE_SCALE), int(original_size[1] * GROUND_TILE_SCALE))
    )
else:
    ground_tile_main = None

if ground_tile_corner_loaded and ground_tile_corner_raw:
    original_size = ground_tile_corner_raw.get_size()
    ground_tile_corner = pygame.transform.scale(
        ground_tile_corner_raw,
        (int(original_size[0] * GROUND_TILE_SCALE), int(original_size[1] * GROUND_TILE_SCALE))
    )
else:
    ground_tile_corner = None

if ground_tile_left_corner_loaded and ground_tile_left_corner_raw:
    original_size = ground_tile_left_corner_raw.get_size()
    ground_tile_left_corner = pygame.transform.scale(
        ground_tile_left_corner_raw,
        (int(original_size[0] * GROUND_TILE_SCALE), int(original_size[1] * GROUND_TILE_SCALE))
    )
else:
    ground_tile_left_corner = None

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
    f"{SPRITES_DIR}/frog/tongue"  # place tongue pictures in /assets/sprites/frog/tongue
]

for tongue_dir in tongue_paths:
    if os.path.exists(tongue_dir):
        for i in range(1, 9):  # tongue_01.png to tongue_08.png
            path = f"{SPRITES_DIR}/frog/tongue/tongue_{i:02d}.png"
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
shake_duration = 700
shake_magnitude = 20

# --- PAUSE STATE ---
paused = False
pause_start_time = 0
pause_menu_y = -500
pause_menu_target_y = None
pause_menu_slide_speed = 15
pause_menu_visible = False

# --- GAME END STATE (timer ended) ---
game_end = False
game_end_start_time = 0
game_end_menu_y = -500
game_end_menu_target_y = None
game_end_menu_slide_speed = 15
game_end_menu_visible = False

# Helper: spawn a fly anywhere + random movement pattern
def make_fly():
    ang = random.uniform(0, math.tau)         # random direction
    spd = random.uniform(2.0, 4.0)            # base speed
    # movement pattern: after some frames, pick a new random direction/speed
    change_timer = random.randint(30, 120)
    return {
        "x": random.randint(0, SCREEN_WIDTH - 1),
        "y": random.randint(0, SCREEN_HEIGHT - 1),
        "vx": math.cos(ang) * spd,
        "vy": math.sin(ang) * spd,
        "change_timer": change_timer
    }

# Create flies (random spawn + random direction)
flies = []
for _ in range(NUM_FLIES):
    flies.append(make_fly())

# Character
sprite_padding_offset = 5
character = {
    "x": SCREEN_WIDTH // 2,
    "y": GROUND_Y - 30 + sprite_padding_offset,
    "width": 50,
    "height": 30,
    "speed": 5,
    "jump_speed": -15,
    "velocity_y": 0,
    "gravity": 0.8,
    "on_ground": False,
    "ground_y": GROUND_Y - 30 + sprite_padding_offset,
    "has_double_jump": True,
    "double_jump_cooldown_end": 0,

    "tongue_extended": False,
    "tongue_length": 0,
    "tongue_max_length": 300,
    "tongue_angle": 0,
    "tongue_speed": 50,
    "tongue_end_time": 0,

    # Tongue retraction animation state
    "tongue_retracting": False,
    "tongue_retract_speed": 65,  # tweak retract speed

    "facing_direction": "right"
}

def reset_game():
    global score, score_animation_time, timer_start_time, timer_remaining, flies, game_end
    score = 0
    score_animation_time = 0
    timer_start_time = pygame.time.get_ticks()
    timer_remaining = TIMER_START_SECONDS
    game_end = False
    game_end_menu_y = -500
    game_end_menu_visible = False
    game_end_menu_target_y = None

    character["x"] = SCREEN_WIDTH // 2
    character["y"] = GROUND_Y - 30 + sprite_padding_offset
    character["velocity_y"] = 0
    character["on_ground"] = False
    character["ground_y"] = GROUND_Y - 30 + sprite_padding_offset
    character["has_double_jump"] = True
    character["double_jump_cooldown_end"] = 0

    character["tongue_extended"] = False
    character["tongue_length"] = 0
    character["tongue_angle"] = 0
    character["tongue_end_time"] = 0
    character["tongue_retracting"] = False

    character["facing_direction"] = "right"

    # Respawn all flies on reset (fresh random spawn + pattern)
    flies = []
    for _ in range(NUM_FLIES):
        flies.append(make_fly())

def draw_tiled_ground(surface, tile_img, x, y, width, height):
    """Draw tiled ground texture without gaps"""
    if not tile_img:
        return
    tile_width = tile_img.get_width()
    tile_height = tile_img.get_height()

    num_tiles_x = int(math.ceil(width / tile_width)) + 1
    num_tiles_y = int(math.ceil(height / tile_height)) + 1

    for ty in range(num_tiles_y):
        for tx in range(num_tiles_x):
            tile_x = x + tx * tile_width
            tile_y = y + ty * tile_height
            surface.blit(tile_img, (tile_x, tile_y))

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

def draw_pause_menu(surface, menu_y):
    """Draw the pause menu with wooden sign"""
    if not wooden_sign_loaded or not wooden_sign_img:
        return None, None, None, None

    sign_width = wooden_sign_img.get_width()
    sign_height = wooden_sign_img.get_height()

    scale_factor = min(SCREEN_WIDTH * 0.6 / sign_width, SCREEN_HEIGHT * 0.6 / sign_height)
    scaled_width = int(sign_width * scale_factor)
    scaled_height = int(sign_height * scale_factor)
    scaled_sign = pygame.transform.scale(wooden_sign_img, (scaled_width, scaled_height))

    sign_x = (SCREEN_WIDTH - scaled_width) // 2
    sign_y = menu_y

    surface.blit(scaled_sign, (sign_x, sign_y))

    text_start_y = sign_y + int(scaled_height * 0.15)
    text_spacing = int(scaled_height * 0.12)

    if pixel_font_loaded:
        paused_text = "PAUSED"
        paused_scale = 0.45
        paused_width = len(paused_text) * int(default_char_width * paused_scale) + (len(paused_text) - 1) * 2
        paused_x = sign_x + (scaled_width - paused_width) // 2
        draw_pixel_text(surface, paused_text, paused_x, text_start_y, scale=paused_scale, color=(255, 255, 255))

        score_text = f"SCORE: {score}"
        score_scale = 0.3
        score_width = len(score_text) * int(default_char_width * score_scale) + (len(score_text) - 1) * 2
        score_x = sign_x + (scaled_width - score_width) // 2
        draw_pixel_text(surface, score_text, score_x, text_start_y + text_spacing * 1.5, scale=score_scale, color=(255, 255, 255))

        high_score_text = f"HIGH SCORE: {high_score}"
        high_score_scale = 0.28
        high_score_width = len(high_score_text) * int(default_char_width * high_score_scale) + (len(high_score_text) - 1) * 2
        if high_score_width > scaled_width * 0.9:
            high_score_scale = (scaled_width * 0.9) / (len(high_score_text) * default_char_width + (len(high_score_text) - 1) * 2)
            high_score_width = len(high_score_text) * int(default_char_width * high_score_scale) + (len(high_score_text) - 1) * 2

        high_score_x = sign_x + (scaled_width - high_score_width) // 2
        draw_pixel_text(surface, high_score_text, high_score_x, text_start_y + text_spacing * 2.5, scale=high_score_scale, color=(255, 255, 255))

        mouse_x, mouse_y = pygame.mouse.get_pos()

        continue_text = "CONTINUE"
        continue_scale = 0.35
        continue_width = len(continue_text) * int(default_char_width * continue_scale) + (len(continue_text) - 1) * 2
        continue_x = sign_x + (scaled_width - continue_width) // 2
        continue_y = text_start_y + text_spacing * 3.8
        continue_hover = (continue_x <= mouse_x <= continue_x + continue_width and
                          continue_y <= mouse_y <= continue_y + int(default_char_height * continue_scale))
        continue_color = (200, 255, 200) if continue_hover else (255, 255, 255)
        draw_pixel_text(surface, continue_text, continue_x, continue_y, scale=continue_scale, color=continue_color)
        continue_rect = pygame.Rect(continue_x, continue_y, continue_width, int(default_char_height * continue_scale))

        settings_text = "SETTINGS"
        settings_scale = 0.35
        settings_width = len(settings_text) * int(default_char_width * settings_scale) + (len(settings_text) - 1) * 2
        settings_x = sign_x + (scaled_width - settings_width) // 2
        settings_y = text_start_y + text_spacing * 4.8
        settings_hover = (settings_x <= mouse_x <= settings_x + settings_width and
                          settings_y <= mouse_y <= settings_y + int(default_char_height * settings_scale))
        settings_color = (200, 255, 200) if settings_hover else (255, 255, 255)
        draw_pixel_text(surface, settings_text, settings_x, settings_y, scale=settings_scale, color=settings_color)
        settings_rect = pygame.Rect(settings_x, settings_y, settings_width, int(default_char_height * settings_scale))

        exit_text = "EXIT GAME"
        exit_scale = 0.35
        exit_width = len(exit_text) * int(default_char_width * exit_scale) + (len(exit_text) - 1) * 2
        exit_x = sign_x + (scaled_width - exit_width) // 2
        exit_y = text_start_y + text_spacing * 5.8
        exit_hover = (exit_x <= mouse_x <= exit_x + exit_width and
                      exit_y <= mouse_y <= exit_y + int(default_char_height * exit_scale))
        exit_color = (255, 200, 200) if exit_hover else (255, 255, 255)
        draw_pixel_text(surface, exit_text, exit_x, exit_y, scale=exit_scale, color=exit_color)
        exit_rect = pygame.Rect(exit_x, exit_y, exit_width, int(default_char_height * exit_scale))

        return continue_rect, settings_rect, exit_rect, (sign_x, sign_y, scaled_width, scaled_height)

    return None, None, None, None

def draw_game_end_menu(surface, menu_y):
    """Draw the game end menu with wooden sign"""
    if not wooden_sign_loaded or not wooden_sign_img:
        return None, None, None

    sign_width = wooden_sign_img.get_width()
    sign_height = wooden_sign_img.get_height()

    scale_factor = min(SCREEN_WIDTH * 0.6 / sign_width, SCREEN_HEIGHT * 0.6 / sign_height)
    scaled_width = int(sign_width * scale_factor)
    scaled_height = int(sign_height * scale_factor)
    scaled_sign = pygame.transform.scale(wooden_sign_img, (scaled_width, scaled_height))

    sign_x = (SCREEN_WIDTH - scaled_width) // 2
    sign_y = menu_y

    surface.blit(scaled_sign, (sign_x, sign_y))

    text_start_y = sign_y + int(scaled_height * 0.15)
    text_spacing = int(scaled_height * 0.12)

    if pixel_font_loaded:
        # Draw "GAME END" title
        game_end_text = "GAME END"
        game_end_scale = 0.45
        game_end_width = len(game_end_text) * int(default_char_width * game_end_scale) + (len(game_end_text) - 1) * 2
        game_end_x = sign_x + (scaled_width - game_end_width) // 2
        draw_pixel_text(surface, game_end_text, game_end_x, text_start_y, scale=game_end_scale, color=(255, 255, 255))

        # Draw score
        score_text = f"SCORE: {score}"
        score_scale = 0.3
        score_width = len(score_text) * int(default_char_width * score_scale) + (len(score_text) - 1) * 2
        score_x = sign_x + (scaled_width - score_width) // 2
        draw_pixel_text(surface, score_text, score_x, text_start_y + text_spacing * 1.5, scale=score_scale, color=(255, 255, 255))

        # Draw high score
        high_score_text = f"HIGH SCORE: {high_score}"
        high_score_scale = 0.28
        high_score_width = len(high_score_text) * int(default_char_width * high_score_scale) + (len(high_score_text) - 1) * 2
        if high_score_width > scaled_width * 0.9:
            high_score_scale = (scaled_width * 0.9) / (len(high_score_text) * default_char_width + (len(high_score_text) - 1) * 2)
            high_score_width = len(high_score_text) * int(default_char_width * high_score_scale) + (len(high_score_text) - 1) * 2

        high_score_x = sign_x + (scaled_width - high_score_width) // 2
        draw_pixel_text(surface, high_score_text, high_score_x, text_start_y + text_spacing * 2.5, scale=high_score_scale, color=(255, 255, 255))

        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Draw "RESTART" option
        restart_text = "RESTART"
        restart_scale = 0.35
        restart_width = len(restart_text) * int(default_char_width * restart_scale) + (len(restart_text) - 1) * 2
        restart_x = sign_x + (scaled_width - restart_width) // 2
        restart_y = text_start_y + text_spacing * 3.8

        restart_hover = (restart_x <= mouse_x <= restart_x + restart_width and
                        restart_y <= mouse_y <= restart_y + int(default_char_height * restart_scale))
        restart_color = (200, 255, 200) if restart_hover else (255, 255, 255)
        draw_pixel_text(surface, restart_text, restart_x, restart_y, scale=restart_scale, color=restart_color)
        restart_rect = pygame.Rect(restart_x, restart_y, restart_width, int(default_char_height * restart_scale))

        # Draw "MAIN MENU" option
        main_menu_text = "MAIN MENU"
        main_menu_scale = 0.35
        main_menu_width = len(main_menu_text) * int(default_char_width * main_menu_scale) + (len(main_menu_text) - 1) * 2
        main_menu_x = sign_x + (scaled_width - main_menu_width) // 2
        main_menu_y = text_start_y + text_spacing * 4.8

        main_menu_hover = (main_menu_x <= mouse_x <= main_menu_x + main_menu_width and
                          main_menu_y <= mouse_y <= main_menu_y + int(default_char_height * main_menu_scale))
        main_menu_color = (200, 255, 200) if main_menu_hover else (255, 255, 255)
        draw_pixel_text(surface, main_menu_text, main_menu_x, main_menu_y, scale=main_menu_scale, color=main_menu_color)
        main_menu_rect = pygame.Rect(main_menu_x, main_menu_y, main_menu_width, int(default_char_height * main_menu_scale))

        return restart_rect, main_menu_rect, (sign_x, sign_y, scaled_width, scaled_height)

    return None, None, None

def refresh_keybinds(self):
    self._cached_keybinds = self.get_keybinds()

# Main game loop
running = True
if timer_start_time is None:
    timer_start_time = pygame.time.get_ticks()

while running:
    clock.tick(60)
    current_time = pygame.time.get_ticks()

    # Handle pause menu animation
    if paused:
        if pause_menu_target_y is None and wooden_sign_loaded and wooden_sign_img:
            pause_menu_target_y = 0

        if pause_menu_target_y is not None:
            if pause_menu_y < pause_menu_target_y:
                pause_menu_y += pause_menu_slide_speed
                if pause_menu_y >= pause_menu_target_y:
                    pause_menu_y = pause_menu_target_y
                    pause_menu_visible = True
            else:
                pause_menu_visible = True
    else:
        if pause_menu_y > -500:
            pause_menu_y -= pause_menu_slide_speed
            if pause_menu_y <= -500:
                pause_menu_y = -500
                pause_menu_visible = False
                pause_menu_target_y = None

    # Handle game end menu animation
    if game_end:
        if game_end_menu_target_y is None and wooden_sign_loaded and wooden_sign_img:
            game_end_menu_target_y = 0

        if game_end_menu_target_y is not None:
            if game_end_menu_y < game_end_menu_target_y:
                game_end_menu_y += game_end_menu_slide_speed
                if game_end_menu_y >= game_end_menu_target_y:
                    game_end_menu_y = game_end_menu_target_y
                    game_end_menu_visible = True
            else:
                game_end_menu_visible = True

    # Skip game updates when paused or game ended
    if not paused and not game_end:
        # Update timer
        elapsed_seconds = (current_time - timer_start_time) // 1000
        timer_remaining = max(0, TIMER_START_SECONDS - elapsed_seconds)
        if timer_remaining <= 0 and not game_end:
            game_end = True
            game_end_start_time = current_time
            game_end_menu_y = -500
            game_end_menu_visible = False

    keys = pygame.key.get_pressed()

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if not game_over:
                paused = not paused
                if paused:
                    pause_start_time = current_time
                    pause_menu_y = -500
                    pause_menu_visible = False
                else:
                    pause_menu_y = -500
                    pause_menu_visible = False

        elif paused and pause_menu_visible and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            continue_rect, settings_rect, exit_rect, _ = draw_pause_menu(screen, pause_menu_y)

            if continue_rect and continue_rect.collidepoint(mouse_x, mouse_y):
                paused = False
                pause_menu_y = -500
                pause_menu_visible = False
            elif settings_rect and settings_rect.collidepoint(mouse_x, mouse_y):
                # TODO: Implement settings menu
                pass
            elif exit_rect and exit_rect.collidepoint(mouse_x, mouse_y):
                running = False

        elif game_end and game_end_menu_visible and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            restart_rect, main_menu_rect, _ = draw_game_end_menu(screen, game_end_menu_y)

            if restart_rect and restart_rect.collidepoint(mouse_x, mouse_y):
                reset_game()
                game_end = False
                game_end_menu_y = -500
                game_end_menu_visible = False
                game_end_menu_target_y = None
            elif main_menu_rect and main_menu_rect.collidepoint(mouse_x, mouse_y):
                # Launch frontpage and exit game
                BASE_DIR = os.path.dirname(os.path.abspath(__file__))
                FRONTPAGE_PATH = os.path.join(BASE_DIR, "frontpage.py")
                subprocess.Popen([sys.executable, FRONTPAGE_PATH])
                running = False

        elif game_over and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if restart_rect.collidepoint(mouse_x, mouse_y):
                reset_game()
                game_over = False

        elif not paused and not game_end and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            sound.play("hit")
            if not character["tongue_extended"]:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                frog_center_x = character["x"] + character["width"] // 2
                frog_center_y = character["y"] + character["height"] // 2
                character["tongue_angle"] = math.atan2(mouse_y - frog_center_y, mouse_x - frog_center_x)
                character["tongue_extended"] = True
                character["tongue_retracting"] = False
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
                character["double_jump_cooldown_end"] = current_time + 500

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
    if ground_tile_upper_loaded and ground_tile_upper:
        upper_tile_width = ground_tile_upper.get_width()
        upper_tile_height = ground_tile_upper.get_height()

        top_right_corner_x = ((SWAMP_START_X - 1) // upper_tile_width) * upper_tile_width
        top_right_corner_y = GROUND_Y

        top_left_right_ground_x = ((SWAMP_START_X + SWAMP_WIDTH) // upper_tile_width) * upper_tile_width
        top_left_right_ground_y = GROUND_Y

        num_tiles_upper_x = int(math.ceil(SCREEN_WIDTH / upper_tile_width)) + 1
        for tx in range(num_tiles_upper_x):
            tile_x = tx * upper_tile_width
            tile_y = GROUND_Y
            if not (tile_x == top_right_corner_x and tile_y == top_right_corner_y) and \
               not (tile_x == top_left_right_ground_x and tile_y == top_left_right_ground_y):
                screen.blit(ground_tile_upper, (tile_x, tile_y))

        if ground_tile_corner_loaded and ground_tile_corner:
            screen.blit(ground_tile_corner, (top_right_corner_x, top_right_corner_y))

        if ground_tile_left_corner_loaded and ground_tile_left_corner:
            screen.blit(ground_tile_left_corner, (top_left_right_ground_x, top_left_right_ground_y))
    else:
        pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, SCREEN_WIDTH, GROUND_HEIGHT))

    if ground_tile_main_loaded and ground_tile_main:
        tile_width = ground_tile_main.get_width()
        tile_height = ground_tile_main.get_height()
        left_ground_width = SWAMP_START_X
        left_ground_height = SWAMP_HEIGHT - GROUND_HEIGHT
        left_ground_x = 0
        left_ground_y = GROUND_Y + GROUND_HEIGHT

        top_right_tile_x = ((SWAMP_START_X - 1) // tile_width) * tile_width
        top_right_tile_y = left_ground_y

        num_tiles_x = int(math.ceil(left_ground_width / tile_width)) + 1
        num_tiles_y = int(math.ceil(left_ground_height / tile_height)) + 1

        for ty in range(num_tiles_y):
            for tx in range(num_tiles_x):
                tile_x = left_ground_x + tx * tile_width
                tile_y = left_ground_y + ty * tile_height
                if not (tile_x == top_right_tile_x and tile_y == top_right_tile_y):
                    screen.blit(ground_tile_main, (tile_x, tile_y))

        screen.blit(ground_tile_main, (top_right_tile_x, top_right_tile_y))

        draw_tiled_ground(
            screen, ground_tile_main,
            SWAMP_START_X + SWAMP_WIDTH, GROUND_Y + GROUND_HEIGHT,
            SCREEN_WIDTH - (SWAMP_START_X + SWAMP_WIDTH), SWAMP_HEIGHT - GROUND_HEIGHT
        )
    else:
        pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y + GROUND_HEIGHT, SWAMP_START_X, SWAMP_HEIGHT - GROUND_HEIGHT))
        pygame.draw.rect(screen, GROUND_COLOR, (SWAMP_START_X + SWAMP_WIDTH, GROUND_Y + GROUND_HEIGHT,
                                               SCREEN_WIDTH - (SWAMP_START_X + SWAMP_WIDTH), SWAMP_HEIGHT - GROUND_HEIGHT))

    pygame.draw.rect(screen, SWAMP_COLOR, (SWAMP_START_X, GROUND_Y, SWAMP_WIDTH, SWAMP_HEIGHT))

    # Draw all platforms
    for platform in platforms:
        pygame.draw.rect(screen, PLATFORM_COLOR, (platform["x"], platform["y"], platform["width"], platform["height"]))

    # Draw trees
    if tree_loaded and tree_images:
        tree_y_left = GROUND_Y - tree_height + 23
        tree_y_middle = GROUND_Y - tree_height + 26
        tree_y_right = GROUND_Y - tree_height + 33
        tree_positions = [
            (SCREEN_WIDTH // 8, tree_y_left, tree_images[0]),
            (SCREEN_WIDTH // 4, tree_y_middle, tree_images[1]),
            (SCREEN_WIDTH // 2 - 50, tree_y_right, tree_images[2])
        ]
        for tree_x, tree_y_pos, tree_img in tree_positions:
            if tree_x < SWAMP_START_X:
                screen.blit(tree_img, (tree_x, tree_y_pos))

    # Character movement (only when not paused and not game ended)
    if not paused and not game_end:
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

        visual_feet_y = character_feet_y - sprite_padding_offset
        target_y = GROUND_Y - character["height"] + sprite_padding_offset

        if visual_feet_y >= GROUND_Y or character_feet_y >= GROUND_Y + sprite_padding_offset:
            character["y"] = target_y
            character["velocity_y"] = 0
            on_ground = True

        char_rect = pygame.Rect(character["x"], character["y"], character["width"], character["height"])
        for platform in platforms:
            platform_rect = pygame.Rect(platform["x"], platform["y"], platform["width"], platform["height"])
            if char_rect.colliderect(platform_rect) and character["velocity_y"] >= 0:
                platform_character_feet_y = character["y"] + character["height"]
                platform_visual_feet_y = platform_character_feet_y - sprite_padding_offset
                platform_target_y = platform["y"] - character["height"] + sprite_padding_offset

                if platform_visual_feet_y >= platform["y"] or platform_character_feet_y >= platform["y"] + sprite_padding_offset:
                    if character["y"] + character["height"] <= platform["y"] + platform["height"]:
                        character["y"] = platform_target_y
                        character["velocity_y"] = 0
                        on_ground = True
                        break

        character["on_ground"] = on_ground
        if on_ground:
            character["has_double_jump"] = True

        # Swamp death check
        character_center_x = character["x"] + character["width"] // 2
        character_bottom = character["y"] + character["height"]

        on_platform = False
        for platform in platforms:
            if (platform["x"] <= character_center_x <= platform["x"] + platform["width"] and
                platform["y"] <= character_bottom <= platform["y"] + platform["height"] + 5):
                on_platform = True
                break

        if (SWAMP_START_X <= character_center_x <= SWAMP_START_X + SWAMP_WIDTH and
            character_bottom >= GROUND_Y and not on_platform and not game_over):

            sound.play("gameover")
            game_over = True
            game_over_start_time = pygame.time.get_ticks()

        # Update tongue (with retract animation)
        if character["tongue_extended"]:
            if character["tongue_retracting"]:
                character["tongue_length"] -= character["tongue_retract_speed"]
                if character["tongue_length"] <= 0:
                    character["tongue_length"] = 0
                    character["tongue_extended"] = False
                    character["tongue_retracting"] = False
            else:
                if character["tongue_length"] < character["tongue_max_length"]:
                    character["tongue_length"] += character["tongue_speed"]
                else:
                    character["tongue_length"] = character["tongue_max_length"]

                # when time is up, start retracting (not instant disappear)
                if current_time >= character["tongue_end_time"]:
                    character["tongue_retracting"] = True

            frog_center_x = character["x"] + character["width"] // 2
            frog_center_y = character["y"] + character["height"] // 2

            # Fly collision: ONLY one fly per tongue, and triggers retraction animation
            if not character["tongue_retracting"]:
                hit_idx = None
                hit_dot = None

                for i, fly in enumerate(flies):
                    fly_center_x = fly["x"] + (FLY_W // 2)
                    fly_center_y = fly["y"] + (FLY_H // 2)
                    to_fly_x = fly_center_x - frog_center_x
                    to_fly_y = fly_center_y - frog_center_y

                    dot_product = to_fly_x * math.cos(character["tongue_angle"]) + to_fly_y * math.sin(character["tongue_angle"])
                    if 0 <= dot_product <= character["tongue_length"]:
                        perp_distance = abs(-to_fly_x * math.sin(character["tongue_angle"]) + to_fly_y * math.cos(character["tongue_angle"]))
                        if perp_distance < 30:
                            if hit_dot is None or dot_product < hit_dot:
                                hit_idx = i
                                hit_dot = dot_product

                if hit_idx is not None:
                    sound.play("eaten")

                    flies.pop(hit_idx)
                    score += 1
                    if score > high_score:
                        high_score = score
                    score_animation_time = current_time

                    # Respawn ONLY once all flies have been eaten
                    if len(flies) == 0:
                        for _ in range(NUM_FLIES):
                            flies.append(make_fly())

                    # Start retract animation (does NOT disappear instantly)
                    character["tongue_retracting"] = True

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

        progress = character["tongue_length"] / character["tongue_max_length"]
        frame_index = min(int(progress * len(tongue_frames)), len(tongue_frames) - 1)
        tongue_sprite = tongue_frames[frame_index]

        original_width = tongue_sprite.get_width()
        original_height = tongue_sprite.get_height()

        scale_factor = character["tongue_length"] / original_width if original_width > 0 else 1.0
        scaled_width = int(original_width * scale_factor)
        scaled_height = int(original_height * scale_factor)

        scaled_tongue = pygame.transform.scale(tongue_sprite, (scaled_width, scaled_height))

        angle_degrees = math.degrees(character["tongue_angle"])
        angle_rad = character["tongue_angle"]

        rotated_tongue = pygame.transform.rotate(scaled_tongue, -angle_degrees)
        rotated_rect = rotated_tongue.get_rect()

        sprite_center_x = scaled_width // 2
        sprite_center_y = scaled_height // 2

        start_vec_x = -sprite_center_x
        start_vec_y = 0

        rotated_start_x = start_vec_x * math.cos(angle_rad) - start_vec_y * math.sin(angle_rad)
        rotated_start_y = start_vec_x * math.sin(angle_rad) + start_vec_y * math.cos(angle_rad)

        size_diff_x = (rotated_rect.width - scaled_width) // 2
        size_diff_y = (rotated_rect.height - scaled_height) // 2

        draw_x = frog_center_x - (sprite_center_x + rotated_start_x) - size_diff_x
        draw_y = frog_center_y - (sprite_center_y + rotated_start_y) - size_diff_y

        screen.blit(rotated_tongue, (draw_x, draw_y))
    elif character["tongue_extended"]:
        frog_center_x = character["x"] + character["width"] // 2
        frog_center_y = character["y"] + character["height"] // 2
        tongue_end_x = frog_center_x + math.cos(character["tongue_angle"]) * character["tongue_length"]
        tongue_end_y = frog_center_y + math.sin(character["tongue_angle"]) * character["tongue_length"]
        pygame.draw.line(screen, (200, 0, 0), (frog_center_x, frog_center_y), (tongue_end_x, tongue_end_y), 8)
        pygame.draw.circle(screen, (150, 0, 0), (int(tongue_end_x), int(tongue_end_y)), 6)

    # Update and draw flies (random movement pattern)
    for fly in flies:
        if not paused and not game_end:
            # Ensure old flies still work (if any exist without vx/vy)
            if "vx" not in fly or "vy" not in fly:
                ang = random.uniform(0, math.tau)
                spd = random.uniform(2.0, 4.0)
                fly["vx"] = math.cos(ang) * spd
                fly["vy"] = math.sin(ang) * spd
            if "change_timer" not in fly:
                fly["change_timer"] = random.randint(30, 120)

            # Randomize movement pattern over time
            fly["change_timer"] -= 1
            if fly["change_timer"] <= 0:
                ang = random.uniform(0, math.tau)
                spd = random.uniform(2.0, 4.0)
                fly["vx"] = math.cos(ang) * spd
                fly["vy"] = math.sin(ang) * spd
                fly["change_timer"] = random.randint(30, 120)

            # Move
            fly["x"] += fly["vx"]
            fly["y"] += fly["vy"]

            # Bounce off edges (keeps them on-screen)
            if fly["x"] < 0:
                fly["x"] = 0
                fly["vx"] *= -1
            elif fly["x"] > SCREEN_WIDTH - FLY_W:
                fly["x"] = SCREEN_WIDTH - FLY_W
                fly["vx"] *= -1

            if fly["y"] < 0:
                fly["y"] = 0
                fly["vy"] *= -1
            elif fly["y"] > SCREEN_HEIGHT - FLY_H:
                fly["y"] = SCREEN_HEIGHT - FLY_H
                fly["vy"] *= -1

        if fly_img:
            screen.blit(fly_img, (fly["x"], fly["y"]))
        else:
            pygame.draw.rect(screen, (255, 255, 0), (fly["x"], fly["y"], FLY_W, FLY_H))

    # Draw UI
    if pixel_font_loaded:
        high_score_text = f"HIGHEST SCORE: {high_score}"
        high_score_scale = 0.3
        high_score_y = 20 + (int(default_char_height * 0.7) - int(default_char_height * high_score_scale)) // 2
        draw_pixel_text(screen, high_score_text, 20, high_score_y, scale=high_score_scale)

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

    # Draw pause menu
    if paused:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        draw_pause_menu(screen, pause_menu_y)

    # Draw game end menu (timer ended)
    if game_end:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        draw_game_end_menu(screen, game_end_menu_y)

    if game_over:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        if pixel_font_loaded:
            text = "GAME OVER"
            scale = 1.2
            text_width = len(text) * int(default_char_width * scale)
            text_x = (SCREEN_WIDTH - text_width) // 2
            draw_pixel_text(screen, text, text_x, SCREEN_HEIGHT // 2 - 140, scale=scale, color=(255, 50, 50))

            restart_text = "RESTART"
            restart_scale = 0.6
            text_width = len(restart_text) * int(default_char_width * restart_scale)
            text_height = int(default_char_height * restart_scale)
            text_x = (SCREEN_WIDTH - text_width) // 2
            text_y = (SCREEN_HEIGHT // 2) + 10

            mouse_x, mouse_y = pygame.mouse.get_pos()
            hover = (text_x <= mouse_x <= text_x + text_width and text_y <= mouse_y <= text_y + text_height)
            color = (255, 255, 255) if hover else (200, 200, 200)

            draw_pixel_text(screen, restart_text, text_x, text_y, scale=restart_scale, color=color)
            restart_rect = pygame.Rect(text_x, text_y, text_width, text_height)

    pygame.display.flip()

pygame.quit()
sys.exit()