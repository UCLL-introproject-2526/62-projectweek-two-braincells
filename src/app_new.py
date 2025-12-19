import pygame
import sys
import random
import math
import os
import subprocess
import json
from sounds import SoundManager

# Initialize Pygame
pygame.init()
try:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
except:
    # Fallback to a default window size if fullscreen fails
    SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Fly Feast")
clock = pygame.time.Clock()

# Get the directory where this script is located, then go up one level to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SPRITES_DIR = os.path.join(ASSETS_DIR, "sprites")

sound = SoundManager()
sound.play_music()

# Load settings
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
settings = {
    "sound": {
        "music": 0.25,
        "sfx": 0.5,
        "muted": False
    }
}

def load_settings():
    global settings
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                loaded = json.load(f)
                if "sound" in loaded:
                    settings["sound"].update(loaded["sound"])
        except:
            pass
    pygame.mixer.music.set_volume(settings["sound"]["music"])

def save_settings():
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
    except:
        pass

load_settings()

# Constants
GROUND_Y = SCREEN_HEIGHT - 150
GROUND_HEIGHT = 20
SWAMP_START_X = int(SCREEN_WIDTH * 6 / 10)
SWAMP_WIDTH = int(SCREEN_WIDTH * 3 / 10)
SWAMP_HEIGHT = SCREEN_HEIGHT - GROUND_Y
# Left water area (smaller than right side)
LEFT_WATER_START_X = int(SCREEN_WIDTH * 0.05)
LEFT_WATER_WIDTH = int(SCREEN_WIDTH * 0.15)
LEFT_WATER_HEIGHT = int(SWAMP_HEIGHT * 0.4)  # 40% of right water height
PLATFORM_WIDTH = SWAMP_WIDTH // 2
PLATFORM_HEIGHT = 20
PLATFORM_X = SWAMP_START_X + (SWAMP_WIDTH - PLATFORM_WIDTH) // 2
PLATFORM_Y = GROUND_Y - 80

# Platforms list - empty, only plant platforms are used now
platforms = []

NUM_FLIES = 12
TIMER_START_SECONDS = 90
SCORE_ANIMATION_DURATION = 200
ANIMATION_SPEED = 150
BRANCH_SCALE = 2.2

# Branch position constants
LEFT_BRANCH_POSITIONS = [
    {"y": 0.15, "offset": 35},
    {"y": 0.35, "offset": 35},
    {"y": 0.55, "offset": 20},
    {"y": 0.75, "offset": 20}
]

RIGHT_BRANCH_POSITIONS = [
    {"y": 0.12, "offset": -45},
    {"y": 0.34, "offset": -50},
    {"y": 0.54, "offset": -35},
    {"y": 0.72, "offset": -40}
]


# Colors
BG_COLOR = (135, 206, 250)
GROUND_COLOR = (95, 75, 55)
SWAMP_COLOR = (45, 85, 75)
PLATFORM_COLOR = (105, 85, 65)

# Load images
def load_image(path, convert_alpha=False):
    if not os.path.exists(path):
        return None, False
    try:
        img = pygame.image.load(path)
        return img.convert_alpha() if convert_alpha else img.convert(), True
    except Exception:
        return None, False

def darken_image(image, factor=0.7):
    """Darken an image by a factor (0.0 = black, 1.0 = original)"""
    if not image:
        return None
    try:
        darkened = image.copy()
        has_alpha = image.get_flags() & pygame.SRCALPHA
        dark_surface = pygame.Surface(darkened.get_size(), pygame.SRCALPHA if has_alpha else 0)
        dark_surface.fill((int(255 * factor), int(255 * factor), int(255 * factor), 255 if has_alpha else 0))
        darkened.blit(dark_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return darkened.convert_alpha() if has_alpha and not (darkened.get_flags() & pygame.SRCALPHA) else darkened
    except Exception:
        return image if image else None

def scale_branch(branch_img, scale):
    """Scale a branch image"""
    if not branch_img:
        return None
    w = int(branch_img.get_width() * scale)
    h = int(branch_img.get_height() * scale)
    return pygame.transform.scale(branch_img, (w, h))

def create_platform_segments_from_branch(branch_img, branch_x, branch_y, scan_step=2):
    """Create platform segments from branch image by scanning for solid pixels"""
    if not branch_img:
        return []
    platform_segments = []
    width = branch_img.get_width()
    height = branch_img.get_height()
    
    for y in range(0, height, scan_step):
        current_segment_start = None
        for x in range(0, width, scan_step):
            try:
                pixel_color = branch_img.get_at((x, y))
                r, g, b, a = pixel_color
                if a > 128:
                    if current_segment_start is None:
                        current_segment_start = x
                else:
                    if current_segment_start is not None:
                        segment_width = (x - current_segment_start) + scan_step
                        if segment_width >= 4:
                            platform_segments.append({
                                "x": branch_x + current_segment_start,
                                "y": branch_y + y,
                                "width": segment_width,
                                "height": PLATFORM_HEIGHT
                            })
                        current_segment_start = None
            except:
                if current_segment_start is not None:
                    segment_width = (x - current_segment_start) + scan_step
                    if segment_width >= 4:
                        platform_segments.append({
                            "x": branch_x + current_segment_start,
                            "y": branch_y + y,
                            "width": segment_width,
                            "height": PLATFORM_HEIGHT
                        })
                    current_segment_start = None
        
        if current_segment_start is not None:
            segment_width = width - current_segment_start
            if segment_width >= 4:
                platform_segments.append({
                    "x": branch_x + current_segment_start,
                    "y": branch_y + y,
                    "width": segment_width,
                    "height": PLATFORM_HEIGHT
                })
    
    return platform_segments

def check_branch_horizontal_collision(character, branch_img, branch_x, branch_y, prev_x, prev_y, sprite_padding_offset, is_left_side=True):
    """Check horizontal collision with a branch and adjust character position"""
    char_left = character["x"]
    char_right = character["x"] + character["width"]
    char_top = character["y"]
    char_bottom = character["y"] + character["height"]
    branch_width = branch_img.get_width()
    branch_height = branch_img.get_height()
    branch_right = branch_x + branch_width
    
    if not (char_right > branch_x and char_left < branch_right and char_bottom > branch_y and char_top < branch_y + branch_height):
        return
    
    platform_target_y = branch_y - character["height"] + sprite_padding_offset
    is_on_top = (character["y"] >= platform_target_y - 15 and character["y"] <= platform_target_y + 15) or \
               (prev_y >= platform_target_y - 15 and prev_y <= platform_target_y + 15)
    
    if is_on_top:
        return
    
    char_rel_x_start = max(0, char_left - branch_x)
    char_rel_x_end = min(branch_width, char_right - branch_x)
    char_rel_y_start = max(0, char_top - branch_y)
    char_rel_y_end = min(branch_height, char_bottom - branch_y)
    
    has_collision = False
    sample_step = 4
    for y in range(int(char_rel_y_start), int(char_rel_y_end), sample_step):
        for x in range(int(char_rel_x_start), int(char_rel_x_end), sample_step):
            try:
                pixel_color = branch_img.get_at((x, y))
                r, g, b, a = pixel_color
                if a > 128:
                    has_collision = True
                    break
            except:
                pass
        if has_collision:
            break
    
    if not has_collision:
        return
    
    char_rel_y = int((char_top + char_bottom) // 2 - branch_y)
    if is_left_side:
        if prev_x + character["width"] <= branch_right and char_left < branch_right and character["x"] > prev_x:
            rightmost_solid = branch_x
            for x in range(branch_width - 1, -1, -sample_step):
                try:
                    pixel_color = branch_img.get_at((x, char_rel_y))
                    r, g, b, a = pixel_color
                    if a > 128:
                        rightmost_solid = branch_x + x + sample_step
                        break
                except:
                    pass
            character["x"] = rightmost_solid
    else:
        if prev_x >= branch_right and char_right > branch_right and character["x"] < prev_x:
            leftmost_solid = branch_x + branch_width
            for x in range(0, branch_width, sample_step):
                try:
                    pixel_color = branch_img.get_at((x, char_rel_y))
                    r, g, b, a = pixel_color
                    if a > 128:
                        leftmost_solid = branch_x + x
                        break
                except:
                    pass
            character["x"] = leftmost_solid - character["width"]

fly_img, _ = load_image(os.path.join(SPRITES_DIR, "fly", "fly.png"), convert_alpha=True)
fly_img_frame2, _ = load_image(os.path.join(SPRITES_DIR, "fly", "fly_second_frame.png"), convert_alpha=True)
background_img, background_loaded = load_image(os.path.join(ASSETS_DIR, "background.png"))

# Fly size used for collision + boundaries
FLY_W = fly_img.get_width() if fly_img else 40
FLY_H = fly_img.get_height() if fly_img else 40

# Fly animation settings
FLY_ANIMATION_SPEED = 8  # Frames per animation cycle (lower = faster chirping)

# Load UI images
UI_DIR = os.path.join(ASSETS_DIR, "ui")
wooden_sign_img, wooden_sign_loaded = load_image(os.path.join(UI_DIR, "wooden_sign_transparent_cleared.png"), convert_alpha=True)

# Load water tiles and crocodile
WATER_TILE_SCALE = 2.3  # Scale adjusted to ensure no gaps
water_tiles_dir = os.path.join(ASSETS_DIR, "sprites", "water_tiles_transparent")
water_tile_1_raw, water_tile_1_loaded = load_image(os.path.join(water_tiles_dir, "tile_1_top_left.png"), convert_alpha=True)
water_tile_2_raw, water_tile_2_loaded = load_image(os.path.join(water_tiles_dir, "tile_2_top_right.png"), convert_alpha=True)
water_tile_3_raw, water_tile_3_loaded = load_image(os.path.join(water_tiles_dir, "tile_3_bottom_left.png"), convert_alpha=True)
water_tile_4_raw, water_tile_4_loaded = load_image(os.path.join(water_tiles_dir, "tile_4_bottom_right.png"), convert_alpha=True)

# Scale water tiles with smooth scaling and darken them
WATER_TILE_DARKEN_FACTOR = 0.75  # Darken water tiles to match theme
if water_tile_1_loaded and water_tile_1_raw:
    original_size = water_tile_1_raw.get_size()
    scaled = pygame.transform.smoothscale(water_tile_1_raw, 
                                         (int(original_size[0] * WATER_TILE_SCALE), 
                                          int(original_size[1] * WATER_TILE_SCALE)))
    water_tile_1 = darken_image(scaled, WATER_TILE_DARKEN_FACTOR)
else:
    water_tile_1 = None

if water_tile_2_loaded and water_tile_2_raw:
    original_size = water_tile_2_raw.get_size()
    scaled = pygame.transform.smoothscale(water_tile_2_raw, 
                                         (int(original_size[0] * WATER_TILE_SCALE), 
                                          int(original_size[1] * WATER_TILE_SCALE)))
    water_tile_2 = darken_image(scaled, WATER_TILE_DARKEN_FACTOR)
else:
    water_tile_2 = None

if water_tile_3_loaded and water_tile_3_raw:
    original_size = water_tile_3_raw.get_size()
    scaled = pygame.transform.smoothscale(water_tile_3_raw, 
                                         (int(original_size[0] * WATER_TILE_SCALE), 
                                          int(original_size[1] * WATER_TILE_SCALE)))
    water_tile_3 = darken_image(scaled, WATER_TILE_DARKEN_FACTOR)
else:
    water_tile_3 = None

if water_tile_4_loaded and water_tile_4_raw:
    original_size = water_tile_4_raw.get_size()
    scaled = pygame.transform.smoothscale(water_tile_4_raw, 
                                         (int(original_size[0] * WATER_TILE_SCALE), 
                                          int(original_size[1] * WATER_TILE_SCALE)))
    water_tile_4 = darken_image(scaled, WATER_TILE_DARKEN_FACTOR)
else:
    water_tile_4 = None

crocodile_frames_dir = os.path.join(ASSETS_DIR, "sprites", "crocodile_frames")
crocodile_frame_1_raw, crocodile_frame_1_loaded = load_image(os.path.join(crocodile_frames_dir, "crocodile_frame_1.png"), convert_alpha=True)
crocodile_frame_2_raw, crocodile_frame_2_loaded = load_image(os.path.join(crocodile_frames_dir, "crocodile_frame_2.png"), convert_alpha=True)

# Scale and darken crocodile frames to match theme (same pattern as water tiles)
CROCODILE_SCALE = WATER_TILE_SCALE  # Same scale as water tiles
CROCODILE_DARKEN_FACTOR = 0.75  # Darken crocodile to match theme
if crocodile_frame_1_loaded and crocodile_frame_1_raw:
    original_size = crocodile_frame_1_raw.get_size()
    scaled = pygame.transform.smoothscale(crocodile_frame_1_raw,
                                         (int(original_size[0] * CROCODILE_SCALE),
                                          int(original_size[1] * CROCODILE_SCALE)))
    crocodile_frame_1 = darken_image(scaled, CROCODILE_DARKEN_FACTOR)
else:
    crocodile_frame_1 = None

if crocodile_frame_2_loaded and crocodile_frame_2_raw:
    original_size = crocodile_frame_2_raw.get_size()
    scaled = pygame.transform.smoothscale(crocodile_frame_2_raw,
                                         (int(original_size[0] * CROCODILE_SCALE),
                                          int(original_size[1] * CROCODILE_SCALE)))
    crocodile_frame_2 = darken_image(scaled, CROCODILE_DARKEN_FACTOR)
else:
    crocodile_frame_2 = None

# Water animation state
water_animation_timer = 0
water_animation_speed = 500  # milliseconds per frame
water_frame = 0  # 0 or 1 for tiles 1/2, 0 or 1 for tiles 3/4

crocodile_animation_timer = 0
crocodile_animation_speed = 500  # milliseconds per frame
crocodile_frame = 0  # 0 or 1

# Load ground tiles
ground_tiles_dir = os.path.join(ASSETS_DIR, "ground_tiles_25_pngs")
GROUND_TILE_SCALE = 2
ground_tile_upper_raw, ground_tile_upper_loaded = load_image(os.path.join(ground_tiles_dir, "tile_r1_c2.png"))
ground_tile_main_raw, ground_tile_main_loaded = load_image(os.path.join(ground_tiles_dir, "tile_r2_c3.png"))
ground_tile_corner_raw, ground_tile_corner_loaded = load_image(os.path.join(ground_tiles_dir, "tile_r1_c3.png"))
ground_tile_left_corner_raw, ground_tile_left_corner_loaded = load_image(os.path.join(ground_tiles_dir, "tile_r1_c1.png"))

# Scale and darken ground tiles
GROUND_TILE_DARKEN_FACTOR = 0.7

def scale_and_darken_tile(raw_img, scale, darken_factor):
    if not raw_img:
        return None
    size = raw_img.get_size()
    scaled = pygame.transform.scale(raw_img, (int(size[0] * scale), int(size[1] * scale)))
    return darken_image(scaled, darken_factor) or scaled

ground_tile_upper = scale_and_darken_tile(ground_tile_upper_raw, GROUND_TILE_SCALE, GROUND_TILE_DARKEN_FACTOR) if ground_tile_upper_loaded else None
ground_tile_main = scale_and_darken_tile(ground_tile_main_raw, GROUND_TILE_SCALE, GROUND_TILE_DARKEN_FACTOR) if ground_tile_main_loaded else None
ground_tile_corner = scale_and_darken_tile(ground_tile_corner_raw, GROUND_TILE_SCALE, GROUND_TILE_DARKEN_FACTOR) if ground_tile_corner_loaded else None
ground_tile_left_corner = scale_and_darken_tile(ground_tile_left_corner_raw, GROUND_TILE_SCALE, GROUND_TILE_DARKEN_FACTOR) if ground_tile_left_corner_loaded else None

# Load tree images
tree_images = None
tree_loaded = False
tree_width, tree_height = 150, 250
tree_left, _ = load_image(os.path.join(SPRITES_DIR, "trees", "tree_left_final_clean2.png"), convert_alpha=True)
tree_middle, _ = load_image(os.path.join(SPRITES_DIR, "trees", "tree_middle_final_clean2.png"), convert_alpha=True)
tree_right, _ = load_image(os.path.join(SPRITES_DIR, "trees", "tree_right_final_clean2.png"), convert_alpha=True)
if tree_left and tree_middle and tree_right:
    tree_images = [
        pygame.transform.scale(tree_left, (tree_width, tree_height)),
        pygame.transform.scale(tree_middle, (tree_width, tree_height)),
        pygame.transform.scale(tree_right, (tree_width, tree_height))
    ]
    tree_loaded = True

# Load plant for water
plant_img, plant_loaded = load_image(os.path.join(SPRITES_DIR, "trees", "plant_for_water_big.png"), convert_alpha=True)
# Load red plant for water (background layer)
plant_red_img, plant_red_loaded = load_image(os.path.join(SPRITES_DIR, "trees", "plant_for_water_big_red.png"), convert_alpha=True)

# Load smaller plant for water (left side, between left water and rock)
small_plant_img, small_plant_loaded = load_image(f"{SPRITES_DIR}/trees/plant_for_water_smaller (1).png", convert_alpha=True)
# Load red version of small plant (background layer, for collision detection)
small_plant_red_img, small_plant_red_loaded = load_image(f"{SPRITES_DIR}/trees/small_plant_red.png", convert_alpha=True)

# Load tree trunk design for left side
thumbnail_wood_img, thumbnail_wood_loaded = load_image(f"{SPRITES_DIR}/trees/thumbnail_wood.png", convert_alpha=True)

# Load tree branches for left trunk
branch_1_img, branch_1_loaded = load_image(f"{SPRITES_DIR}/trees/branches_left_separated/branches_left_part_1.png", convert_alpha=True)
branch_2_img, branch_2_loaded = load_image(f"{SPRITES_DIR}/trees/branches_left_separated/branches_left_part_2.png", convert_alpha=True)
branch_3_img, branch_3_loaded = load_image(f"{SPRITES_DIR}/trees/branches_left_separated/branches_left_part_3.png", convert_alpha=True)
branch_4_img, branch_4_loaded = load_image(f"{SPRITES_DIR}/trees/branches_left_separated/branches_left_part_4.png", convert_alpha=True)

# Load tree branches for right trunk
branch_right_1_img, branch_right_1_loaded = load_image(f"{SPRITES_DIR}/trees/branches_right_separated/branches_right_part_1.png", convert_alpha=True)
branch_right_2_img, branch_right_2_loaded = load_image(f"{SPRITES_DIR}/trees/branches_right_separated/branches_right_part_2.png", convert_alpha=True)
branch_right_3_img, branch_right_3_loaded = load_image(f"{SPRITES_DIR}/trees/branches_right_separated/branches_right_part_3.png", convert_alpha=True)
branch_right_4_img, branch_right_4_loaded = load_image(f"{SPRITES_DIR}/trees/branches_right_separated/branches_right_part_4.png", convert_alpha=True)

# Load tree tiles for top rows
TREE_TILE_SCALE = 0.7  # Scale tiles down
TREE_TILE_DARKEN_FACTOR = 0.7  # Darken tiles to match theme
tree_tile_16_raw, tree_tile_16_loaded = load_image(os.path.join(SPRITES_DIR, "tree tiles", "tile_16_row6_col2.png"), convert_alpha=True)
tree_tile_21_raw, tree_tile_21_loaded = load_image(os.path.join(SPRITES_DIR, "tree tiles", "tile_21_row8_col1.png"), convert_alpha=True)
tree_tile_22_raw, tree_tile_22_loaded = load_image(os.path.join(SPRITES_DIR, "tree tiles", "tile_22_row8_col2.png"), convert_alpha=True)
tree_tile_23_raw, tree_tile_23_loaded = load_image(os.path.join(SPRITES_DIR, "tree tiles", "tile_23_row8_col3.png"), convert_alpha=True)

# Scale and darken the tiles
if tree_tile_16_loaded and tree_tile_16_raw:
    tree_tile_16_scaled = pygame.transform.scale(tree_tile_16_raw, 
        (int(tree_tile_16_raw.get_width() * TREE_TILE_SCALE), 
         int(tree_tile_16_raw.get_height() * TREE_TILE_SCALE)))
    tree_tile_16_img = darken_image(tree_tile_16_scaled, TREE_TILE_DARKEN_FACTOR)
else:
    tree_tile_16_img = None

if tree_tile_21_loaded and tree_tile_21_raw:
    tree_tile_21_scaled = pygame.transform.scale(tree_tile_21_raw, 
        (int(tree_tile_21_raw.get_width() * TREE_TILE_SCALE), 
         int(tree_tile_21_raw.get_height() * TREE_TILE_SCALE)))
    tree_tile_21_img = darken_image(tree_tile_21_scaled, TREE_TILE_DARKEN_FACTOR)
else:
    tree_tile_21_img = None

if tree_tile_22_loaded and tree_tile_22_raw:
    tree_tile_22_scaled = pygame.transform.scale(tree_tile_22_raw, 
        (int(tree_tile_22_raw.get_width() * TREE_TILE_SCALE), 
         int(tree_tile_22_raw.get_height() * TREE_TILE_SCALE)))
    tree_tile_22_img = darken_image(tree_tile_22_scaled, TREE_TILE_DARKEN_FACTOR)
else:
    tree_tile_22_img = None

if tree_tile_23_loaded and tree_tile_23_raw:
    tree_tile_23_scaled = pygame.transform.scale(tree_tile_23_raw, 
        (int(tree_tile_23_raw.get_width() * TREE_TILE_SCALE), 
         int(tree_tile_23_raw.get_height() * TREE_TILE_SCALE)))
    tree_tile_23_img = darken_image(tree_tile_23_scaled, TREE_TILE_DARKEN_FACTOR)
else:
    tree_tile_23_img = None

# Load rocks to place between water areas
rocks_img_raw, rocks_loaded = load_image(os.path.join(SPRITES_DIR, "rocks.png"), convert_alpha=True)
# Darken rocks to match theme
ROCKS_DARKEN_FACTOR = 0.7  # Darken rocks to match theme
ROCKS_SCALE = 1.2  # Make rocks smaller
if rocks_loaded and rocks_img_raw:
    rocks_img_scaled = pygame.transform.scale(rocks_img_raw, 
        (int(rocks_img_raw.get_width() * ROCKS_SCALE), 
         int(rocks_img_raw.get_height() * ROCKS_SCALE)))
    rocks_img = darken_image(rocks_img_scaled, ROCKS_DARKEN_FACTOR)
else:
    rocks_img = None

# Load red rocks for collision detection (invisible, behind regular rocks)
red_rocks_img_raw, red_rocks_loaded = load_image(os.path.join(ASSETS_DIR, "red_rocks_v2.png"), convert_alpha=True)
if red_rocks_loaded and red_rocks_img_raw:
    red_rocks_img = pygame.transform.scale(red_rocks_img_raw,
        (int(red_rocks_img_raw.get_width() * ROCKS_SCALE),
         int(red_rocks_img_raw.get_height() * ROCKS_SCALE)))
else:
    red_rocks_img = None

# Load vines image
vines_img, vines_loaded = load_image(os.path.join(SPRITES_DIR, "vines.png"), convert_alpha=True)

# Load hanging vines for top of screen
vines_top_1_img, vines_top_1_loaded = load_image(os.path.join(SPRITES_DIR, "vines_separated", "vines_part_1.png"), convert_alpha=True)
vines_top_2_img, vines_top_2_loaded = load_image(os.path.join(SPRITES_DIR, "vines_separated", "vines_part_2.png"), convert_alpha=True)
vines_top_3_img, vines_top_3_loaded = load_image(os.path.join(SPRITES_DIR, "vines_separated", "vines_part_3.png"), convert_alpha=True)

# Load tongue sprites
tongue_frames = []
tongue_path = os.path.join(SPRITES_DIR, "frog", "tongue")
for i in range(1, 9):
    path = os.path.join(tongue_path, f"tongue_{i:02d}.png")
    if os.path.exists(path):
        frame, loaded = load_image(path, convert_alpha=True)
        if loaded and frame:
            tongue_frames.append(frame)
tongue_loaded = len(tongue_frames) > 0

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
            path = os.path.join(SPRITES_DIR, "frog", f"{anim_type}_{direction}_f{i}.png")
            frame, loaded = load_image(path, convert_alpha=True)
            if loaded and frame:
                    frog_frames[key].append(frame)

sprite_sheet_loaded = any(len(frames) > 0 for frames in frog_frames.values())

# Load dying frames
dying_frames = []
dying_frames_dir = os.path.join(SPRITES_DIR, "frog", "dead_frog_two_frames")
for i in range(1, 3):
    path = os.path.join(dying_frames_dir, f"dead_frog_frame_{i}.png")
    frame, loaded = load_image(path, convert_alpha=True)
    if loaded and frame:
        dying_frames.append(frame)
dying_frames_loaded = len(dying_frames) > 0

# Animation state
animation_frames = {key: 0 for key in frog_frames.keys()} if sprite_sheet_loaded else {}
animation_timers = {key: 0 for key in frog_frames.keys()} if sprite_sheet_loaded else {}
dying_frame_index = 0
dying_animation_timer = 0
DYING_ANIMATION_SPEED = 200  # milliseconds per frame
current_animation = "idle_right"

# Load pixel font
pixel_font_images = {}
pixel_font_loaded = False
default_char_width, default_char_height = 20, 20

for char in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    path = os.path.join(ASSETS_DIR, "pixel_font", f"{char}.png")
    img, loaded = load_image(path, convert_alpha=True)
    if loaded and img:
        pixel_font_images[char] = img

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
total_paused_time = 0  # Track total time spent paused (in milliseconds)
pause_menu_y = -500
pause_menu_target_y = None
pause_menu_slide_speed = 15
pause_menu_visible = False

# Settings menu state
settings_open = False
settings_menu_y = -500
settings_menu_target_y = None
settings_menu_slide_speed = 15
settings_menu_visible = False
# Slider dragging state
music_slider_dragging = False
sfx_slider_dragging = False

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
    # Animation state: random offset so flies don't all chirp at the same time
    animation_timer = random.randint(0, FLY_ANIMATION_SPEED - 1)
    return {
        "x": random.randint(50, SCREEN_WIDTH - FLY_W - 50),
        "y": random.randint(50, GROUND_Y - FLY_H - 50),
        "vx": math.cos(ang) * spd,
        "vy": math.sin(ang) * spd,
        "change_timer": change_timer,
        "animation_timer": animation_timer,
        "frame": 0  # 0 = first frame, 1 = second frame
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
    global score, score_animation_time, timer_start_time, timer_remaining, flies, game_end, total_paused_time, dying_frame_index, dying_animation_timer
    score = 0
    score_animation_time = 0
    timer_start_time = pygame.time.get_ticks()
    timer_remaining = TIMER_START_SECONDS
    total_paused_time = 0
    game_end = False
    game_end_menu_y = -500
    game_end_menu_visible = False
    game_end_menu_target_y = None
    
    # Reset dying animation
    dying_frame_index = 0
    dying_animation_timer = 0
    
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

# Cache for all platforms (generated once, reused every frame)
cached_all_platforms = None

def generate_all_platforms():
    """Generate all platform segments once at initialization. This is expensive, so we cache the result."""
    global cached_all_platforms
    all_platforms = list(platforms)  # Copy the platforms list
    
    # Add left tree branches as platforms
    if thumbnail_wood_loaded and thumbnail_wood_img and (branch_1_loaded and branch_2_loaded and branch_3_loaded and branch_4_loaded):
        trunk_width = thumbnail_wood_img.get_width()
        branch_imgs = [branch_1_img, branch_2_img, branch_3_img, branch_4_img]
        for pos, branch_img in zip(LEFT_BRANCH_POSITIONS, branch_imgs):
            scaled = scale_branch(branch_img, BRANCH_SCALE)
            if scaled:
                branch_x = trunk_width - scaled.get_width() // 2 + pos["offset"]
                branch_y = int(SCREEN_HEIGHT * pos["y"])
                all_platforms.extend(create_platform_segments_from_branch(scaled, branch_x, branch_y))
    
    # Add right tree branches as platforms
    if thumbnail_wood_loaded and thumbnail_wood_img and (branch_right_1_loaded and branch_right_2_loaded and branch_right_3_loaded and branch_right_4_loaded):
        trunk_width = thumbnail_wood_img.get_width()
        right_trunk_x = SCREEN_WIDTH - trunk_width
        branch_imgs = [branch_right_1_img, branch_right_2_img, branch_right_3_img, branch_right_4_img]
        for pos, branch_img in zip(RIGHT_BRANCH_POSITIONS, branch_imgs):
            scaled = scale_branch(branch_img, BRANCH_SCALE)
            if scaled:
                branch_x = right_trunk_x + trunk_width - scaled.get_width() // 2 + pos["offset"]
                branch_y = int(SCREEN_HEIGHT * pos["y"])
                all_platforms.extend(create_platform_segments_from_branch(scaled, branch_x, branch_y))
    
    # Add hanging vine leaves as platforms
    if vines_top_1_loaded and vines_top_2_loaded and vines_top_3_loaded:
        VINE_SCALE = 3.0  # Same scale as drawing
        vine_positions = [
            {"x": int(SCREEN_WIDTH * 0.15), "img": vines_top_1_img},
            {"x": int(SCREEN_WIDTH * 0.5), "img": vines_top_2_img},
            {"x": int(SCREEN_WIDTH * 0.85), "img": vines_top_3_img}
        ]
        for vine_data in vine_positions:
            vine_img = vine_data["img"]
            # Scale the vine image for platform collision
            scaled_width = int(vine_img.get_width() * VINE_SCALE)
            scaled_height = int(vine_img.get_height() * VINE_SCALE)
            vine_scaled = pygame.transform.scale(vine_img, (scaled_width, scaled_height))
            vine_x = vine_data["x"] - vine_scaled.get_width() // 2
            vine_y = 0
            all_platforms.extend(create_platform_segments_from_branch(vine_scaled, vine_x, vine_y))
    
    # Add small plant platforms based on red parts of small plant red image
    if small_plant_loaded and small_plant_img and small_plant_red_loaded and small_plant_red_img:
        small_plant_width = small_plant_img.get_width()
        small_plant_height = small_plant_img.get_height()
        
        # Calculate position (same as where it's drawn)
        left_water_end = LEFT_WATER_START_X + LEFT_WATER_WIDTH
        space_between = SWAMP_START_X - left_water_end
        
        # Calculate rock position first to position plant relative to it
        if rocks_loaded and rocks_img:
            rocks_width = rocks_img.get_width()
            rocks_x = left_water_end + int(space_between * 0.5) - rocks_width // 2
        else:
            rocks_x = left_water_end + int(space_between * 0.5)
        
        # Position red plant at same location as regular plant (invisible, behind regular plant)
        small_plant_x = left_water_end + int((rocks_x - left_water_end) * 0.3) - small_plant_width // 2
        small_plant_y = GROUND_Y - small_plant_height
        
        # Scan red plant image for red pixels and create platforms
        scan_step = 4  # Scan every 4 pixels for performance
        platform_segments = []
        
        for y in range(0, small_plant_height, scan_step):
            current_segment_start = None
            for x in range(0, small_plant_width, scan_step):
                try:
                    # Get pixel color at this position
                    pixel_color = small_plant_red_img.get_at((x, y))
                    r, g, b, a = pixel_color
                    
                    # Check if pixel is red (R > G and R > B) and visible
                    if (a > 128 and r > g and r > b and r > 100):
                        if current_segment_start is None:
                            current_segment_start = x
                    else:
                        # End of red segment
                        if current_segment_start is not None:
                            segment_width = (x - current_segment_start) + scan_step
                            if segment_width >= 12:  # Only add segments wide enough
                                platform_segments.append({
                                    "x": small_plant_x + current_segment_start,
                                    "y": small_plant_y + y,
                                    "width": segment_width,
                                    "height": PLATFORM_HEIGHT
                                })
                            current_segment_start = None
                except:
                    # Skip if pixel is out of bounds
                    if current_segment_start is not None:
                        segment_width = (x - current_segment_start) + scan_step
                        if segment_width >= 12:
                            platform_segments.append({
                                "x": small_plant_x + current_segment_start,
                                "y": small_plant_y + y,
                                "width": segment_width,
                                "height": PLATFORM_HEIGHT
                            })
                        current_segment_start = None
            
            # Handle segment that extends to end of row
            if current_segment_start is not None:
                segment_width = small_plant_width - current_segment_start
                if segment_width >= 12:
                    platform_segments.append({
                        "x": small_plant_x + current_segment_start,
                        "y": small_plant_y + y,
                        "width": segment_width,
                        "height": PLATFORM_HEIGHT
                    })
        
        # Add platform segments to all_platforms
        all_platforms.extend(platform_segments)
    
    # Add red rocks platforms and walls based on red parts of red rocks image
    # Horizontal red lines = platforms (can stand on them)
    if rocks_loaded and rocks_img and red_rocks_loaded and red_rocks_img:
        rocks_width = rocks_img.get_width()
        rocks_height = rocks_img.get_height()
        
        # Calculate the space between water areas
        left_water_end = LEFT_WATER_START_X + LEFT_WATER_WIDTH
        space_between = SWAMP_START_X - left_water_end
        
        # Position red rocks at same location as regular rocks (invisible, behind regular rocks)
        red_rocks_x = left_water_end + int(space_between * 0.5) - rocks_width // 2
        red_rocks_y = GROUND_Y - rocks_height
        
        scan_step = 4  # Scan every 4 pixels for performance
        
        # Scan horizontally for platforms (horizontal red lines)
        for y in range(0, rocks_height, scan_step):
            current_segment_start = None
            for x in range(0, rocks_width, scan_step):
                try:
                    pixel_color = red_rocks_img.get_at((x, y))
                    r, g, b, a = pixel_color
                    
                    if (a > 128 and r > g and r > b and r > 100):
                        if current_segment_start is None:
                            current_segment_start = x
                    else:
                        # End of horizontal segment - create platform
                        if current_segment_start is not None:
                            segment_width = (x - current_segment_start) + scan_step
                            if segment_width >= 12:  # Only add segments wide enough for platforms
                                platform = {
                                    "x": red_rocks_x + current_segment_start,
                                    "y": red_rocks_y + y,
                                    "width": segment_width,
                                    "height": PLATFORM_HEIGHT
                                }
                                all_platforms.append(platform)
                            current_segment_start = None
                except:
                    if current_segment_start is not None:
                        segment_width = (x - current_segment_start) + scan_step
                        if segment_width >= 12:
                            platform = {
                                "x": red_rocks_x + current_segment_start,
                                "y": red_rocks_y + y,
                                "width": segment_width,
                                "height": PLATFORM_HEIGHT
                            }
                            all_platforms.append(platform)
                        current_segment_start = None
        
        # Handle segment that extends to end of row
        if current_segment_start is not None:
            segment_width = rocks_width - current_segment_start
            if segment_width >= 12:
                platform = {
                    "x": red_rocks_x + current_segment_start,
                    "y": red_rocks_y + y,
                    "width": segment_width,
                    "height": PLATFORM_HEIGHT
                }
                all_platforms.append(platform)
    
    if plant_loaded and plant_img and plant_red_loaded and plant_red_img:
        plant_width = plant_img.get_width()
        plant_height = plant_img.get_height()
        plant_x = SWAMP_START_X + (SWAMP_WIDTH - plant_width) // 2
        plant_y = GROUND_Y + SWAMP_HEIGHT - plant_height
        
        # Red plant is positioned behind regular plant (same position, not visible)
        red_plant_x = plant_x
        red_plant_y = plant_y
        
        # Scan red plant image for red pixels and create platforms
        # Use get_at() to detect red regions (red parts act as platforms)
        scan_step = 4  # Scan every 4 pixels for performance
        platform_segments = []
        
        for y in range(0, plant_height, scan_step):
            current_segment_start = None
            for x in range(0, plant_width, scan_step):
                try:
                    # Get pixel color at this position
                    pixel_color = plant_red_img.get_at((x, y))
                    r, g, b, a = pixel_color
                    
                    # Check if pixel is red (R > G and R > B) and visible
                    if (a > 128 and r > g and r > b and r > 100):
                        if current_segment_start is None:
                            current_segment_start = x
                    else:
                        # End of red segment
                        if current_segment_start is not None:
                            segment_width = (x - current_segment_start) + scan_step
                            if segment_width >= 12:  # Only add segments wide enough
                                platform_segments.append({
                                    "x": red_plant_x + current_segment_start,
                                    "y": red_plant_y + y,
                                    "width": segment_width,
                                    "height": PLATFORM_HEIGHT
                                })
                            current_segment_start = None
                except:
                    # Skip if pixel is out of bounds
                    if current_segment_start is not None:
                        segment_width = (x - current_segment_start) + scan_step
                        if segment_width >= 12:
                            platform_segments.append({
                                "x": red_plant_x + current_segment_start,
                                "y": red_plant_y + y,
                                "width": segment_width,
                                "height": PLATFORM_HEIGHT
                            })
                        current_segment_start = None
            
            # Handle segment that extends to end of row
            if current_segment_start is not None:
                segment_width = plant_width - current_segment_start
                if segment_width >= 12:
                    platform_segments.append({
                        "x": red_plant_x + current_segment_start,
                        "y": red_plant_y + y,
                        "width": segment_width,
                        "height": PLATFORM_HEIGHT
                    })
        
        # Add platform segments to all_platforms
        all_platforms.extend(platform_segments)
    
    cached_all_platforms = all_platforms
    return all_platforms

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
        return None, None, None, None, None

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

        main_menu_text = "MAIN MENU"
        main_menu_scale = 0.35
        main_menu_width = len(main_menu_text) * int(default_char_width * main_menu_scale) + (len(main_menu_text) - 1) * 2
        main_menu_x = sign_x + (scaled_width - main_menu_width) // 2
        main_menu_y = text_start_y + text_spacing * 5.8
        main_menu_hover = (main_menu_x <= mouse_x <= main_menu_x + main_menu_width and
                          main_menu_y <= mouse_y <= main_menu_y + int(default_char_height * main_menu_scale))
        main_menu_color = (200, 255, 200) if main_menu_hover else (255, 255, 255)
        draw_pixel_text(surface, main_menu_text, main_menu_x, main_menu_y, scale=main_menu_scale, color=main_menu_color)
        main_menu_rect = pygame.Rect(main_menu_x, main_menu_y, main_menu_width, int(default_char_height * main_menu_scale))

        exit_text = "EXIT GAME"
        exit_scale = 0.35
        exit_width = len(exit_text) * int(default_char_width * exit_scale) + (len(exit_text) - 1) * 2
        exit_x = sign_x + (scaled_width - exit_width) // 2
        exit_y = text_start_y + text_spacing * 6.8
        exit_hover = (exit_x <= mouse_x <= exit_x + exit_width and
                      exit_y <= mouse_y <= exit_y + int(default_char_height * exit_scale))
        exit_color = (255, 200, 200) if exit_hover else (255, 255, 255)
        draw_pixel_text(surface, exit_text, exit_x, exit_y, scale=exit_scale, color=exit_color)
        exit_rect = pygame.Rect(exit_x, exit_y, exit_width, int(default_char_height * exit_scale))

        return continue_rect, settings_rect, main_menu_rect, exit_rect, (sign_x, sign_y, scaled_width, scaled_height)

    return None, None, None, None

def draw_settings_menu(surface, menu_y):
    """Draw the settings menu with wooden sign"""
    if not wooden_sign_loaded or not wooden_sign_img:
        return None, None, None, None, None, None, None

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
    text_spacing = int(scaled_height * 0.1)

    if pixel_font_loaded:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # Title
        title_text = "SETTINGS"
        title_scale = 0.45
        title_width = len(title_text) * int(default_char_width * title_scale) + (len(title_text) - 1) * 2
        title_x = sign_x + (scaled_width - title_width) // 2
        draw_pixel_text(surface, title_text, title_x, text_start_y, scale=title_scale, color=(255, 255, 255))

        # Music Volume
        music_text = f"MUSIC: {int(settings['sound']['music'] * 100)}%"
        music_scale = 0.3
        music_width = len(music_text) * int(default_char_width * music_scale) + (len(music_text) - 1) * 2
        music_x = sign_x + (scaled_width - music_width) // 2
        music_y = text_start_y + text_spacing * 2
        draw_pixel_text(surface, music_text, music_x, music_y, scale=music_scale, color=(255, 255, 255))
        
        # Music volume slider
        vol_bar_width = int(scaled_width * 0.6)
        vol_bar_height = 20
        vol_bar_x = sign_x + (scaled_width - vol_bar_width) // 2
        vol_bar_y = music_y + int(default_char_height * music_scale) + 10
        
        # Volume bar background
        pygame.draw.rect(surface, (100, 100, 100), (vol_bar_x, vol_bar_y, vol_bar_width, vol_bar_height))
        # Volume bar fill
        fill_width = int(vol_bar_width * settings["sound"]["music"])
        pygame.draw.rect(surface, (100, 200, 100), (vol_bar_x, vol_bar_y, fill_width, vol_bar_height))
        
        # Slider handle
        handle_width = 15
        handle_height = vol_bar_height + 8
        handle_x = vol_bar_x + fill_width - handle_width // 2
        handle_y = vol_bar_y - 4
        handle_rect = pygame.Rect(handle_x, handle_y, handle_width, handle_height)
        handle_hover = handle_rect.collidepoint(mouse_x, mouse_y) or music_slider_dragging
        handle_color = (150, 255, 150) if handle_hover else (200, 200, 200)
        pygame.draw.rect(surface, handle_color, handle_rect)
        pygame.draw.rect(surface, (255, 255, 255), handle_rect, 2)
        
        # Make entire bar clickable
        music_slider_rect = pygame.Rect(vol_bar_x, vol_bar_y - 10, vol_bar_width, vol_bar_height + 20)

        # SFX Volume
        sfx_text = f"SFX: {int(settings['sound']['sfx'] * 100)}%"
        sfx_scale = 0.3
        sfx_width = len(sfx_text) * int(default_char_width * sfx_scale) + (len(sfx_text) - 1) * 2
        sfx_x = sign_x + (scaled_width - sfx_width) // 2
        sfx_y = vol_bar_y + vol_bar_height + text_spacing * 1.5
        draw_pixel_text(surface, sfx_text, sfx_x, sfx_y, scale=sfx_scale, color=(255, 255, 255))
        
        # SFX volume slider
        sfx_vol_bar_x = vol_bar_x
        sfx_vol_bar_y = sfx_y + int(default_char_height * sfx_scale) + 10
        
        # SFX Volume bar background
        pygame.draw.rect(surface, (100, 100, 100), (sfx_vol_bar_x, sfx_vol_bar_y, vol_bar_width, vol_bar_height))
        # SFX Volume bar fill
        sfx_fill_width = int(vol_bar_width * settings["sound"]["sfx"])
        pygame.draw.rect(surface, (100, 200, 100), (sfx_vol_bar_x, sfx_vol_bar_y, sfx_fill_width, vol_bar_height))
        
        # SFX Slider handle
        sfx_handle_x = sfx_vol_bar_x + sfx_fill_width - handle_width // 2
        sfx_handle_y = sfx_vol_bar_y - 4
        sfx_handle_rect = pygame.Rect(sfx_handle_x, sfx_handle_y, handle_width, handle_height)
        sfx_handle_hover = sfx_handle_rect.collidepoint(mouse_x, mouse_y) or sfx_slider_dragging
        sfx_handle_color = (150, 255, 150) if sfx_handle_hover else (200, 200, 200)
        pygame.draw.rect(surface, sfx_handle_color, sfx_handle_rect)
        pygame.draw.rect(surface, (255, 255, 255), sfx_handle_rect, 2)
        
        # Make entire bar clickable
        sfx_slider_rect = pygame.Rect(sfx_vol_bar_x, sfx_vol_bar_y - 10, vol_bar_width, vol_bar_height + 20)

        # Mute toggle
        mute_text = "MUTE: " + ("ON" if settings["sound"]["muted"] else "OFF")
        mute_scale = 0.3
        mute_width = len(mute_text) * int(default_char_width * mute_scale) + (len(mute_text) - 1) * 2
        mute_x = sign_x + (scaled_width - mute_width) // 2
        mute_y = sfx_vol_bar_y + vol_bar_height + text_spacing * 1.5
        mute_hover = (mute_x <= mouse_x <= mute_x + mute_width and mute_y <= mouse_y <= mute_y + int(default_char_height * mute_scale))
        mute_color = (200, 255, 200) if mute_hover else (255, 255, 255)
        draw_pixel_text(surface, mute_text, mute_x, mute_y, scale=mute_scale, color=mute_color)
        mute_rect = pygame.Rect(mute_x, mute_y, mute_width, int(default_char_height * mute_scale))

        # Back button
        back_text = "BACK"
        back_scale = 0.35
        back_width = len(back_text) * int(default_char_width * back_scale) + (len(back_text) - 1) * 2
        back_x = sign_x + (scaled_width - back_width) // 2
        back_y = mute_y + text_spacing * 2.5
        back_hover = (back_x <= mouse_x <= back_x + back_width and back_y <= mouse_y <= back_y + int(default_char_height * back_scale))
        back_color = (200, 255, 200) if back_hover else (255, 255, 255)
        draw_pixel_text(surface, back_text, back_x, back_y, scale=back_scale, color=back_color)
        back_rect = pygame.Rect(back_x, back_y, back_width, int(default_char_height * back_scale))

        return music_slider_rect, sfx_slider_rect, mute_rect, back_rect, vol_bar_x, vol_bar_width, sfx_vol_bar_x

    return None, None, None, None, None, None, None

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

# Generate all platforms once at initialization (expensive operation)
generate_all_platforms()

# Main game loop
running = True
if timer_start_time is None:
    timer_start_time = pygame.time.get_ticks()

while running:
        clock.tick(60)
        current_time = pygame.time.get_ticks()
    
        # Handle pause menu animation
        if paused and not settings_open:
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

        # Handle settings menu animation
        if settings_open:
            if settings_menu_target_y is None and wooden_sign_loaded and wooden_sign_img:
                settings_menu_target_y = 0

        if settings_menu_target_y is not None:
            if settings_menu_y < settings_menu_target_y:
                settings_menu_y += settings_menu_slide_speed
                if settings_menu_y >= settings_menu_target_y:
                    settings_menu_y = settings_menu_target_y
                    settings_menu_visible = True
            else:
                settings_menu_visible = True
        else:
            if settings_menu_y > -500:
                settings_menu_y -= settings_menu_slide_speed
            if settings_menu_y <= -500:
                settings_menu_y = -500
                settings_menu_visible = False
                settings_menu_target_y = None

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

        # Update water and crocodile animations
        if current_time - water_animation_timer >= water_animation_speed:
            water_animation_timer = current_time
            water_frame = 1 - water_frame  # Toggle between 0 and 1
    
        if current_time - crocodile_animation_timer >= crocodile_animation_speed:
            crocodile_animation_timer = current_time
            crocodile_frame = 1 - crocodile_frame  # Toggle between 0 and 1

        # Skip game updates when paused, game ended, or game over
        if not paused and not game_end and not game_over:
            # Update timer (subtract total paused time to account for pauses)
            elapsed_seconds = (current_time - timer_start_time - total_paused_time) // 1000
            timer_remaining = max(0, TIMER_START_SECONDS - elapsed_seconds)
        if timer_remaining <= 0 and not game_end:
            game_end = True
            game_end_start_time = current_time
            game_end_menu_y = -500
            game_end_menu_visible = False
        elif paused:
            # When paused, also account for current pause session in timer calculation
            current_pause_duration = current_time - pause_start_time if pause_start_time > 0 else 0
            elapsed_seconds = (current_time - timer_start_time - total_paused_time - current_pause_duration) // 1000
            timer_remaining = max(0, TIMER_START_SECONDS - elapsed_seconds)
        elif game_over:
            # When game over, timer stops - don't update it
            # Timer remains at the value it had when game_over was set
            pass

        keys = pygame.key.get_pressed()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if settings_open:
                    # Close settings menu and return to pause menu
                    settings_open = False
                    settings_menu_y = -500
                    settings_menu_visible = False
                    settings_menu_target_y = None
                elif not game_over:
                    paused = not paused
                    if paused:
                        pause_start_time = current_time
                        pause_menu_y = -500
                        pause_menu_visible = False
                    else:
                        # When unpausing, add the paused duration to total_paused_time
                        if pause_start_time > 0:
                            total_paused_time += current_time - pause_start_time
                            pause_start_time = 0
                        pause_menu_y = -500
                        pause_menu_visible = False
                        pause_menu_target_y = None

            elif event.type == pygame.KEYDOWN and (event.key == pygame.K_UP or event.key == pygame.K_w):
                if not paused and not game_end and not game_over:
                    sfx_vol = 0.0 if settings["sound"]["muted"] else settings["sound"]["sfx"]
                    sound.play("jump", sfx_vol)
                if character["on_ground"]:
                    character["velocity_y"] = character["jump_speed"]
                    character["on_ground"] = False
                elif not character["on_ground"] and character["has_double_jump"] and current_time >= character["double_jump_cooldown_end"]:
                    character["velocity_y"] = character["jump_speed"]
                    character["has_double_jump"] = False
                    character["double_jump_cooldown_end"] = current_time + 500

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if not paused and not game_end and not game_over:
                    if not character["tongue_extended"]:
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        frog_center_x = character["x"] + character["width"] // 2
                        frog_center_y = character["y"] + character["height"] // 2
                        character["tongue_angle"] = math.atan2(mouse_y - frog_center_y, mouse_x - frog_center_x)
                        character["tongue_extended"] = True
                        character["tongue_retracting"] = False
                        character["tongue_length"] = 0
                        character["tongue_end_time"] = current_time + 300

            elif paused and pause_menu_visible and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                continue_rect, settings_rect, main_menu_rect, exit_rect, _ = draw_pause_menu(screen, pause_menu_y)

                if continue_rect and continue_rect.collidepoint(mouse_x, mouse_y):
                    # When unpausing, add the paused duration to total_paused_time
                    if pause_start_time > 0:
                        total_paused_time += current_time - pause_start_time
                        pause_start_time = 0
                    paused = False
                    pause_menu_y = -500
                    pause_menu_visible = False
                elif settings_rect and settings_rect.collidepoint(mouse_x, mouse_y):
                    settings_open = True
                    settings_menu_y = -500
                    settings_menu_target_y = None
                    settings_menu_visible = False
                elif main_menu_rect and main_menu_rect.collidepoint(mouse_x, mouse_y):
                    # Launch frontpage and exit game
                    FRONTPAGE_DIR = os.path.dirname(os.path.abspath(__file__))
                    FRONTPAGE_PATH = os.path.join(FRONTPAGE_DIR, "frontpage.py")
                    PROJECT_ROOT = os.path.dirname(FRONTPAGE_DIR)
                    if os.path.exists(FRONTPAGE_PATH):
                        subprocess.Popen([sys.executable, os.path.abspath(FRONTPAGE_PATH)], cwd=PROJECT_ROOT)
                    running = False
                elif exit_rect and exit_rect.collidepoint(mouse_x, mouse_y):
                    running = False

            elif settings_open and settings_menu_visible:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                result = draw_settings_menu(screen, settings_menu_y)
                if result:
                    music_slider_rect, sfx_slider_rect, mute_rect, back_rect, vol_bar_x, vol_bar_width, sfx_vol_bar_x = result
                else:
                    music_slider_rect = sfx_slider_rect = mute_rect = back_rect = vol_bar_x = vol_bar_width = sfx_vol_bar_x = None
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if music_slider_rect and music_slider_rect.collidepoint(mouse_x, mouse_y):
                        music_slider_dragging = True
                        # Calculate volume based on click position
                        relative_x = max(0, min(mouse_x - vol_bar_x, vol_bar_width))
                        settings["sound"]["music"] = relative_x / vol_bar_width
                        pygame.mixer.music.set_volume(0.0 if settings["sound"]["muted"] else settings["sound"]["music"])
                        save_settings()
                    elif sfx_slider_rect and sfx_slider_rect.collidepoint(mouse_x, mouse_y):
                        sfx_slider_dragging = True
                        # Calculate volume based on click position
                        relative_x = max(0, min(mouse_x - sfx_vol_bar_x, vol_bar_width))
                        settings["sound"]["sfx"] = relative_x / vol_bar_width
                        save_settings()
                    elif mute_rect and mute_rect.collidepoint(mouse_x, mouse_y):
                        settings["sound"]["muted"] = not settings["sound"]["muted"]
                        pygame.mixer.music.set_volume(0.0 if settings["sound"]["muted"] else settings["sound"]["music"])
                        save_settings()
                    elif back_rect and back_rect.collidepoint(mouse_x, mouse_y):
                        settings_open = False
                        settings_menu_y = -500
                        settings_menu_visible = False
                        settings_menu_target_y = None
                        music_slider_dragging = False
                        sfx_slider_dragging = False
                
                elif event.type == pygame.MOUSEMOTION:
                    if music_slider_dragging and music_slider_rect:
                        relative_x = max(0, min(mouse_x - vol_bar_x, vol_bar_width))
                        settings["sound"]["music"] = relative_x / vol_bar_width
                        pygame.mixer.music.set_volume(0.0 if settings["sound"]["muted"] else settings["sound"]["music"])
                        save_settings()
                    elif sfx_slider_dragging and sfx_slider_rect:
                        relative_x = max(0, min(mouse_x - sfx_vol_bar_x, vol_bar_width))
                        settings["sound"]["sfx"] = relative_x / vol_bar_width
                        save_settings()
                
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    music_slider_dragging = False
                    sfx_slider_dragging = False

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
                    FRONTPAGE_DIR = os.path.dirname(os.path.abspath(__file__))
                    FRONTPAGE_PATH = os.path.join(FRONTPAGE_DIR, "frontpage.py")
                    PROJECT_ROOT = os.path.dirname(FRONTPAGE_DIR)
                    if os.path.exists(FRONTPAGE_PATH):
                        subprocess.Popen([sys.executable, os.path.abspath(FRONTPAGE_PATH)], cwd=PROJECT_ROOT)
                    running = False

            elif game_over and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if restart_rect.collidepoint(mouse_x, mouse_y):
                    reset_game()
                    game_over = False

            elif not paused and not game_end and not game_over and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                sfx_vol = 0.0 if settings["sound"]["muted"] else settings["sound"]["sfx"]
                sound.play("hit", sfx_vol)
                if not character["tongue_extended"]:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    frog_center_x = character["x"] + character["width"] // 2
                    frog_center_y = character["y"] + character["height"] // 2
                    character["tongue_angle"] = math.atan2(mouse_y - frog_center_y, mouse_x - frog_center_x)
                    character["tongue_extended"] = True
                    character["tongue_retracting"] = False
                    character["tongue_length"] = 0
                    character["tongue_end_time"] = current_time + 300

    
        shake_x, shake_y = 0, 0
        if game_over:
            elapsed = pygame.time.get_ticks() - game_over_start_time
            if elapsed < shake_duration:
                shake_x = random.randint(-shake_magnitude, shake_magnitude)
            shake_y = random.randint(-shake_magnitude, shake_magnitude)

        # Draw background
        if background_loaded and background_img:
            if background_img.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
                screen.blit(pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT)), (shake_x, shake_y))
            else:
                screen.blit(background_img, (0, 0))
        else:
            screen.fill(BG_COLOR)
    
        # Draw hanging vines from top of screen
        if vines_top_1_loaded and vines_top_2_loaded and vines_top_3_loaded:
            VINE_SCALE = 3.0  # Scale vines to be much bigger
            vines_top_imgs = [vines_top_1_img, vines_top_2_img, vines_top_3_img]
            # Position vines across the screen, hanging from top
            vine_positions = [
                {"x": int(SCREEN_WIDTH * 0.15), "img": vines_top_1_img},
                {"x": int(SCREEN_WIDTH * 0.5), "img": vines_top_2_img},
                {"x": int(SCREEN_WIDTH * 0.85), "img": vines_top_3_img}
            ]
            for vine_data in vine_positions:
                vine_img = vine_data["img"]
                # Scale the vine image
                scaled_width = int(vine_img.get_width() * VINE_SCALE)
                scaled_height = int(vine_img.get_height() * VINE_SCALE)
                vine_scaled = pygame.transform.scale(vine_img, (scaled_width, scaled_height))
                vine_x = vine_data["x"] - vine_scaled.get_width() // 2
                vine_y = 0  # Hang from top of screen
                screen.blit(vine_scaled, (vine_x, vine_y))
    
        # Draw left tree branches
        if thumbnail_wood_loaded and thumbnail_wood_img and (branch_1_loaded and branch_2_loaded and branch_3_loaded and branch_4_loaded):
            trunk_width = thumbnail_wood_img.get_width()
            branch_imgs = [branch_1_img, branch_2_img, branch_3_img, branch_4_img]
            for i, (pos, branch_img) in enumerate(zip(LEFT_BRANCH_POSITIONS, branch_imgs)):
                scaled = scale_branch(branch_img, BRANCH_SCALE)
                if scaled:
                    branch_x = trunk_width - scaled.get_width() // 2 + pos["offset"]
                    branch_y = int(SCREEN_HEIGHT * pos["y"])
                    screen.blit(scaled, (branch_x, branch_y))
    
        # Draw right tree branches
        if thumbnail_wood_loaded and thumbnail_wood_img and (branch_right_1_loaded and branch_right_2_loaded and branch_right_3_loaded and branch_right_4_loaded):
            trunk_width = thumbnail_wood_img.get_width()
            right_trunk_x = SCREEN_WIDTH - trunk_width
            branch_imgs = [branch_right_1_img, branch_right_2_img, branch_right_3_img, branch_right_4_img]
            for pos, branch_img in zip(RIGHT_BRANCH_POSITIONS, branch_imgs):
                scaled = scale_branch(branch_img, BRANCH_SCALE)
                if scaled:
                    branch_x = right_trunk_x + trunk_width - scaled.get_width() // 2 + pos["offset"]
                    branch_y = int(SCREEN_HEIGHT * pos["y"])
                    screen.blit(scaled, (branch_x, branch_y))
    
        # Draw tree trunk design on both left and right sides - fill the edges vertically with no gaps
        if thumbnail_wood_loaded and thumbnail_wood_img:
            tile_width = thumbnail_wood_img.get_width()
            tile_height = thumbnail_wood_img.get_height()
            
            # Shadow settings
            shadow_offset_x = 8
        shadow_offset_y = 8
        shadow_alpha = 120  # Shadow opacity (0-255)
        
        # Create shadow surface from thumbnail_wood's alpha channel
        shadow_surface = pygame.Surface(thumbnail_wood_img.get_size(), pygame.SRCALPHA)
        shadow_surface.fill((0, 0, 0, shadow_alpha))
        shadow_surface.blit(thumbnail_wood_img, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Calculate how many tiles needed to fill the screen height (add extra to ensure no gaps)
        num_tiles_y = int(math.ceil(SCREEN_HEIGHT / tile_height)) + 2
        
        # Draw tiles vertically on the left edge
        for ty in range(num_tiles_y):
            tree_tile_y = ty * tile_height
            # Skip tiles that extend beyond screen bounds
            if tree_tile_y >= SCREEN_HEIGHT:
                continue
            # Draw shadow first
            screen.blit(shadow_surface, (shadow_offset_x, tree_tile_y + shadow_offset_y))
            # Draw thumbnail_wood tile on the left
            screen.blit(thumbnail_wood_img, (0, tree_tile_y))
        
        # Draw tiles vertically on the right edge (symmetrically)
        right_edge_x = SCREEN_WIDTH - tile_width
        for ty in range(num_tiles_y):
            tree_tile_y = ty * tile_height
            # Skip tiles that extend beyond screen bounds
            if tree_tile_y >= SCREEN_HEIGHT:
                continue
            # Draw shadow first (offset to the left for right side)
            screen.blit(shadow_surface, (right_edge_x - shadow_offset_x, tree_tile_y + shadow_offset_y))
            # Draw thumbnail_wood tile on the right
            screen.blit(thumbnail_wood_img, (right_edge_x, tree_tile_y))
    
        # Draw tree tile 16 along the top row with random orientations (overlapping to fill gaps)
        if tree_tile_16_loaded and tree_tile_16_img:
            tile_16_width = tree_tile_16_img.get_width()
        tile_16_height = tree_tile_16_img.get_height()
        
        # Shadow settings
        shadow_offset_x = 8
        shadow_offset_y = 8
        shadow_alpha = 120  # Shadow opacity (0-255)
        
        # Calculate spacing to ensure tiles overlap and fill the screen
        # Use a smaller spacing than tile width to create overlap
        overlap_amount = tile_16_width * 0.4  # 40% overlap for better coverage
        tile_spacing = tile_16_width - overlap_amount
        
        # Calculate how many tiles needed to cover the screen width (more tiles for better coverage)
        num_tiles_x = int(math.ceil(SCREEN_WIDTH / tile_spacing)) + 3
        
        # Draw tiles along the top row with overlap
        for tx in range(num_tiles_x):
            tile_x = tx * tile_spacing
            if tile_x >= SCREEN_WIDTH + tile_16_width:
                continue
            
            # Use tile position as seed for consistent rotation per tile
            # Save random state to avoid affecting other random operations
            random_state = random.getstate()
            random.seed(tx)
            rotation = random.choice([0, 90, 180, 270])
            random.setstate(random_state)  # Restore random state
            rotated_tile = pygame.transform.rotate(tree_tile_16_img, rotation)
            
            # Create shadow surface for rotated tile
            shadow_surface = pygame.Surface(rotated_tile.get_size(), pygame.SRCALPHA)
            shadow_surface.fill((0, 0, 0, shadow_alpha))
            shadow_surface.blit(rotated_tile, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            # Adjust position if rotated (to keep tiles aligned)
            if rotation == 90 or rotation == 270:
                # For 90/270 degree rotations, swap width and height
                offset_x = (tile_16_height - tile_16_width) // 2
                offset_y = (tile_16_width - tile_16_height) // 2
            else:
                offset_x = 0
                offset_y = 0
            
            # Draw shadow first
            screen.blit(shadow_surface, (tile_x + offset_x + shadow_offset_x, offset_y + shadow_offset_y))
            # Draw tile on top
            screen.blit(rotated_tile, (tile_x + offset_x, offset_y))
    
        # Draw animated tree tiles 21, 22, 23 just below the top row (overlapping to fill gaps)
        if tree_tile_21_loaded and tree_tile_22_loaded and tree_tile_23_loaded:
            if tree_tile_21_img and tree_tile_22_img and tree_tile_23_img:
                tile_21_width = tree_tile_21_img.get_width()
                tile_21_height = tree_tile_21_img.get_height()
                
                # Shadow settings
            shadow_offset_x = 8
            shadow_offset_y = 8
            shadow_alpha = 120  # Shadow opacity (0-255)
            
            # Get current time for animation
            current_time = pygame.time.get_ticks()
            # Change tile every 200ms for animation effect
            animation_frame = (current_time // 200) % 3
            
            # Select which tile to show based on animation frame
            if animation_frame == 0:
                current_animated_tile = tree_tile_21_img
            elif animation_frame == 1:
                current_animated_tile = tree_tile_22_img
            else:
                current_animated_tile = tree_tile_23_img
            
            # Create shadow surface for animated tile
            shadow_surface = pygame.Surface(current_animated_tile.get_size(), pygame.SRCALPHA)
            shadow_surface.fill((0, 0, 0, shadow_alpha))
            shadow_surface.blit(current_animated_tile, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            # Calculate spacing to ensure tiles overlap and fill the screen
            # Use a smaller spacing than tile width to create overlap
            overlap_amount = tile_21_width * 0.4  # 40% overlap for better coverage
            tile_spacing = tile_21_width - overlap_amount
            
            # Calculate how many tiles needed to cover the screen width (more tiles for better coverage)
            num_tiles_x = int(math.ceil(SCREEN_WIDTH / tile_spacing)) + 3
            
            # Get the height of tile 16 to position animated tiles overlapping with it
            tile_16_height = tree_tile_16_img.get_height() if tree_tile_16_loaded and tree_tile_16_img else tile_21_height
            
            # Calculate overlap amount between rows (overlap by 15% of tile height for less overlap)
            row_overlap = tile_16_height * 0.15
            
            # Draw tiles in the row just below the top row with overlap
            for tx in range(num_tiles_x):
                tile_x = tx * tile_spacing
                if tile_x >= SCREEN_WIDTH + tile_21_width:
                    continue
                
                # Position overlapping with the top row but lower (move up by smaller overlap amount)
                tile_y = tile_16_height - row_overlap
                
                # Draw shadow first
                screen.blit(shadow_surface, (tile_x + shadow_offset_x, tile_y + shadow_offset_y))
                # Draw tile on top
                screen.blit(current_animated_tile, (tile_x, tile_y))
    
        # Draw ground and swamp
        if ground_tile_upper_loaded and ground_tile_upper:
            upper_tile_width = ground_tile_upper.get_width()
            upper_tile_height = ground_tile_upper.get_height()

            top_right_corner_x = ((SWAMP_START_X - 1) // upper_tile_width) * upper_tile_width
            top_right_corner_y = GROUND_Y

            top_left_right_ground_x = ((SWAMP_START_X + SWAMP_WIDTH) // upper_tile_width) * upper_tile_width
            top_left_right_ground_y = GROUND_Y
            
            # Calculate left water corner positions
            left_water_left_corner_x = ((LEFT_WATER_START_X - 1) // upper_tile_width) * upper_tile_width
            left_water_right_corner_x = ((LEFT_WATER_START_X + LEFT_WATER_WIDTH) // upper_tile_width) * upper_tile_width

            num_tiles_upper_x = int(math.ceil(SCREEN_WIDTH / upper_tile_width)) + 1
            num_tiles_upper_y = int(math.ceil(GROUND_HEIGHT / upper_tile_height)) + 1
            
            for ty in range(num_tiles_upper_y):
                for tx in range(num_tiles_upper_x):
                    tile_x = tx * upper_tile_width
                    tile_y = GROUND_Y + ty * upper_tile_height
                    tile_right = tile_x + upper_tile_width
                    
                    # Skip tiles that overlap with the left water area
                    if tile_right > LEFT_WATER_START_X and tile_x < LEFT_WATER_START_X + LEFT_WATER_WIDTH:
                        continue
                    # Skip tiles that overlap with the swamp area
                    if tile_right > SWAMP_START_X and tile_x < SWAMP_START_X + SWAMP_WIDTH:
                        continue
                    
                    # Skip corner tiles that are in the left water area (only for first row)
                    if ty == 0 and (tile_x == left_water_left_corner_x or tile_x == left_water_right_corner_x):
                        continue
                    
                    # Skip corner positions (only for first row)
                    if ty == 0:
                        if (tile_x == top_right_corner_x and tile_y == top_right_corner_y) or \
                           (tile_x == top_left_right_ground_x and tile_y == top_left_right_ground_y):
                            continue
                    
                    screen.blit(ground_tile_upper, (tile_x, tile_y))

            # Only draw corner tiles if they're not in the left water area
            if ground_tile_corner_loaded and ground_tile_corner:
                if not (top_right_corner_x >= LEFT_WATER_START_X and top_right_corner_x < LEFT_WATER_START_X + LEFT_WATER_WIDTH):
                    screen.blit(ground_tile_corner, (top_right_corner_x, top_right_corner_y))

            if ground_tile_left_corner_loaded and ground_tile_left_corner:
                if not (top_left_right_ground_x >= LEFT_WATER_START_X and top_left_right_ground_x < LEFT_WATER_START_X + LEFT_WATER_WIDTH):
                    screen.blit(ground_tile_left_corner, (top_left_right_ground_x, top_left_right_ground_y))
        else:
            # Draw ground rectangles, but skip left water and right swamp areas
            pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, LEFT_WATER_START_X, GROUND_HEIGHT))
            pygame.draw.rect(screen, GROUND_COLOR, (LEFT_WATER_START_X + LEFT_WATER_WIDTH, GROUND_Y, 
                                                   SWAMP_START_X - (LEFT_WATER_START_X + LEFT_WATER_WIDTH), GROUND_HEIGHT))
            pygame.draw.rect(screen, GROUND_COLOR, (SWAMP_START_X + SWAMP_WIDTH, GROUND_Y, 
                                                   SCREEN_WIDTH - (SWAMP_START_X + SWAMP_WIDTH), GROUND_HEIGHT))

        # Draw main ground tiles below the top row (always draw if loaded, regardless of upper tiles)
        if ground_tile_main_loaded and ground_tile_main:
            tile_width = ground_tile_main.get_width()
            tile_height = ground_tile_main.get_height()
            
            # Draw left ground (before left water area)
            left_ground_before_water_width = LEFT_WATER_START_X
            left_ground_height = SWAMP_HEIGHT - GROUND_HEIGHT
            left_ground_x = 0
            left_ground_y = GROUND_Y + GROUND_HEIGHT
            
            # Calculate left water area boundaries
            left_water_top = GROUND_Y + SWAMP_HEIGHT - LEFT_WATER_HEIGHT
            left_water_bottom = GROUND_Y + SWAMP_HEIGHT

            num_tiles_x = int(math.ceil(left_ground_before_water_width / tile_width)) + 1
            num_tiles_y = int(math.ceil(left_ground_height / tile_height)) + 1

            for ty in range(num_tiles_y):
                for tx in range(num_tiles_x):
                    tile_x = left_ground_x + tx * tile_width
                    tile_y = left_ground_y + ty * tile_height
                    tile_right = tile_x + tile_width
                    tile_bottom = tile_y + tile_height
                    
                    # Skip all tiles that are horizontally within the left water area bounds
                    # (both above and within the water area)
                    if tile_right > LEFT_WATER_START_X and tile_x < LEFT_WATER_START_X + LEFT_WATER_WIDTH:
                        # Skip if tile is not completely below the water (i.e., above or overlapping)
                        if tile_y < left_water_bottom:
                            continue
                    
                    screen.blit(ground_tile_main, (tile_x, tile_y))

            # Draw ground between left water and right swamp
            middle_ground_start_x = LEFT_WATER_START_X + LEFT_WATER_WIDTH
            middle_ground_width = SWAMP_START_X - middle_ground_start_x
            middle_ground_height = SWAMP_HEIGHT - GROUND_HEIGHT
            middle_ground_y = GROUND_Y + GROUND_HEIGHT
            
            num_tiles_middle_x = int(math.ceil(middle_ground_width / tile_width)) + 1
            num_tiles_middle_y = int(math.ceil(middle_ground_height / tile_height)) + 1
            
            for ty in range(num_tiles_middle_y):
                for tx in range(num_tiles_middle_x):
                    tile_x = middle_ground_start_x + tx * tile_width
                    tile_y = middle_ground_y + ty * tile_height
                    tile_right = tile_x + tile_width
                    tile_bottom = tile_y + tile_height
                    
                    # Skip tiles that overlap with left water area (horizontally and vertically)
                    if tile_right > LEFT_WATER_START_X and tile_x < LEFT_WATER_START_X + LEFT_WATER_WIDTH:
                        # Skip if tile is not completely below the water (i.e., above or overlapping)
                        if tile_y < left_water_bottom:
                            continue
                    
                    screen.blit(ground_tile_main, (tile_x, tile_y))

            # Draw ground after right swamp
            # The top part (GROUND_HEIGHT) is already handled by ground_tile_upper above
            # Only draw the bottom part (SWAMP_HEIGHT - GROUND_HEIGHT) using main tiles
            right_ground_start_x = SWAMP_START_X + SWAMP_WIDTH
            right_ground_width = SCREEN_WIDTH - right_ground_start_x
            right_ground_height = SWAMP_HEIGHT - GROUND_HEIGHT
            right_ground_y = GROUND_Y + GROUND_HEIGHT
            
            num_tiles_right_x = int(math.ceil(right_ground_width / tile_width)) + 1
            num_tiles_right_y = int(math.ceil(right_ground_height / tile_height)) + 1
            
            for ty in range(num_tiles_right_y):
                for tx in range(num_tiles_right_x):
                    tile_x = right_ground_start_x + tx * tile_width
                    tile_y = right_ground_y + ty * tile_height
                    screen.blit(ground_tile_main, (tile_x, tile_y))
        else:
            # Draw ground rectangles, but skip left water and right swamp areas
            pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y + GROUND_HEIGHT, LEFT_WATER_START_X, SWAMP_HEIGHT - GROUND_HEIGHT))
            pygame.draw.rect(screen, GROUND_COLOR, (LEFT_WATER_START_X + LEFT_WATER_WIDTH, GROUND_Y + GROUND_HEIGHT, 
                                                   SWAMP_START_X - (LEFT_WATER_START_X + LEFT_WATER_WIDTH), SWAMP_HEIGHT - GROUND_HEIGHT))
            pygame.draw.rect(screen, GROUND_COLOR, (SWAMP_START_X + SWAMP_WIDTH, GROUND_Y + GROUND_HEIGHT, 
                                                   SCREEN_WIDTH - (SWAMP_START_X + SWAMP_WIDTH), SWAMP_HEIGHT - GROUND_HEIGHT))

        # Draw water tiles and crocodile in swamp area
        if water_tile_1_loaded and water_tile_2_loaded and water_tile_3_loaded and water_tile_4_loaded:
            # Get tile dimensions (already scaled)
            tile_width = water_tile_1.get_width()
        tile_height = water_tile_1.get_height()
        
        # Calculate crocodile position (will be set when crocodile is loaded)
        crocodile_x = SWAMP_START_X + (SWAMP_WIDTH // 2)
        crocodile_y = GROUND_Y
        crocodile_width = 0
        crocodile_height = 0
        
        if crocodile_frame_1_loaded and crocodile_frame_2_loaded and crocodile_frame_1 and crocodile_frame_2:
            # Use pre-scaled and darkened crocodile frames
            current_crocodile = crocodile_frame_1 if crocodile_frame == 0 else crocodile_frame_2
            crocodile_width = current_crocodile.get_width()
            crocodile_height = current_crocodile.get_height()
            # Center crocodile horizontally
            crocodile_x = SWAMP_START_X + (SWAMP_WIDTH - crocodile_width) // 2
            # Position crocodile a little higher than water tiles
            crocodile_y = GROUND_Y - 10  # Move up by 10 pixels
        
        # Draw plant in water first (so water tiles and crocodile can overlap it)
        if plant_loaded and plant_img:
            plant_width = plant_img.get_width()
            plant_height = plant_img.get_height()
            # Center plant horizontally in the swamp
            plant_x = SWAMP_START_X + (SWAMP_WIDTH - plant_width) // 2
            # Position plant at the bottom of the water (ground level)
            plant_y = GROUND_Y + SWAMP_HEIGHT - plant_height
            
            # Red plant is not drawn - it's only used for platform collision detection
            
            # Draw shadow first (offset down and to the right)
            shadow_offset_x = 8
            shadow_offset_y = 8
            shadow_alpha = 120  # Shadow opacity (0-255)
            
            # Create shadow surface from plant's alpha channel
            shadow_surface = pygame.Surface(plant_img.get_size(), pygame.SRCALPHA)
            # Create a dark shadow by extracting alpha from plant and applying dark color
            # Fill with black at the shadow alpha level
            shadow_surface.fill((0, 0, 0, shadow_alpha))
            # Use the plant's alpha channel to shape the shadow
            shadow_surface.blit(plant_img, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            # Draw shadow with offset
            screen.blit(shadow_surface, (plant_x + shadow_offset_x, plant_y + shadow_offset_y))
            
            # Draw plant on top of shadow and red plant
            screen.blit(plant_img, (plant_x, plant_y))
        
        # Calculate how many tiles fit in the swamp (add extra to ensure no gaps)
        num_tiles_x = int(math.ceil(SWAMP_WIDTH / tile_width)) + 2
        num_tiles_y = int(math.ceil(SWAMP_HEIGHT / tile_height)) + 2
        
        # Draw water tiles (on top of plant)
        for ty in range(num_tiles_y):
            for tx in range(num_tiles_x):
                tile_x = SWAMP_START_X + tx * tile_width
                tile_y = GROUND_Y + ty * tile_height
                tile_right = tile_x + tile_width
                tile_bottom = tile_y + tile_height
                
                # Skip tiles that extend outside the swamp boundaries
                if tile_x >= SWAMP_START_X + SWAMP_WIDTH or tile_right <= SWAMP_START_X:
                    continue
                if tile_y >= GROUND_Y + SWAMP_HEIGHT or tile_bottom <= GROUND_Y:
                    continue
                
                # Determine which tile to use based on position
                if ty == 0:  # Top row
                    # Check if this position overlaps with crocodile
                    if crocodile_frame_1_loaded and crocodile_frame_2_loaded and crocodile_width > 0:
                        crocodile_left = crocodile_x
                        crocodile_right = crocodile_x + crocodile_width
                        tile_right = tile_x + tile_width
                        tile_center = tile_x + tile_width // 2
                        crocodile_center = crocodile_x + crocodile_width // 2
                        
                        # If tile center is to the left of crocodile center, use tile 1 (left side)
                        if tile_center < crocodile_center:
                            # Animate between tile 1 and tile 2
                            current_tile = water_tile_1 if water_frame == 0 else water_tile_2
                        # If tile center is to the right of crocodile center, use tile 2 (right side)
                        else:
                            # Animate between tile 2 and tile 1
                            current_tile = water_tile_2 if water_frame == 0 else water_tile_1
                    else:
                        # No crocodile, alternate between tile 1 and 2
                        current_tile = water_tile_1 if (tx + water_frame) % 2 == 0 else water_tile_2
                else:  # Bottom rows
                    # Use tiles 3 and 4, animate between tile 3 and 4
                    current_tile = water_tile_3 if water_frame == 0 else water_tile_4
                
                # Draw tile even if it overlaps with crocodile (crocodile will be drawn on top)
                screen.blit(current_tile, (tile_x, tile_y))
        
        # Draw crocodile on top (at top middle, overlapping plant and water)
        if crocodile_frame_1_loaded and crocodile_frame_2_loaded and crocodile_frame_1 and crocodile_frame_2 and crocodile_width > 0:
            screen.blit(current_crocodile, (crocodile_x, crocodile_y))
    
        # Draw left water section (smaller than right side)
        if water_tile_1_loaded and water_tile_2_loaded and water_tile_3_loaded and water_tile_4_loaded:
            tile_width = water_tile_1.get_width()
        tile_height = water_tile_1.get_height()
        
        # Calculate crocodile position for left water area
        left_crocodile_x = LEFT_WATER_START_X + (LEFT_WATER_WIDTH // 2)
        left_crocodile_y = GROUND_Y + SWAMP_HEIGHT - LEFT_WATER_HEIGHT
        left_crocodile_width = 0
        left_crocodile_height = 0
        
        if crocodile_frame_1_loaded and crocodile_frame_2_loaded and crocodile_frame_1 and crocodile_frame_2:
            # Use pre-scaled and darkened crocodile frames
            current_left_crocodile = crocodile_frame_1 if crocodile_frame == 0 else crocodile_frame_2
            left_crocodile_width = current_left_crocodile.get_width()
            left_crocodile_height = current_left_crocodile.get_height()
            # Center crocodile horizontally in left water area
            left_crocodile_x = LEFT_WATER_START_X + (LEFT_WATER_WIDTH - left_crocodile_width) // 2
            # Position crocodile at the top of the left water area
            left_crocodile_y = GROUND_Y + SWAMP_HEIGHT - LEFT_WATER_HEIGHT - 10  # Move up by 10 pixels
        
        # Calculate how many tiles fit in the left water area (add extra to ensure no gaps)
        num_tiles_x = int(math.ceil(LEFT_WATER_WIDTH / tile_width)) + 2
        num_tiles_y = int(math.ceil(LEFT_WATER_HEIGHT / tile_height)) + 2
        
        # Offset to slide water texture to the left
        water_texture_offset_x = -15
        
        # Draw water tiles for left water section
        for ty in range(num_tiles_y):
            for tx in range(num_tiles_x):
                tile_x = LEFT_WATER_START_X + tx * tile_width + water_texture_offset_x
                tile_y = GROUND_Y + SWAMP_HEIGHT - LEFT_WATER_HEIGHT + ty * tile_height
                tile_right = tile_x + tile_width
                tile_bottom = tile_y + tile_height
                
                # Skip tiles that extend outside the left water boundaries
                if tile_x >= LEFT_WATER_START_X + LEFT_WATER_WIDTH or tile_right <= LEFT_WATER_START_X:
                    continue
                if tile_y >= GROUND_Y + SWAMP_HEIGHT or tile_bottom <= GROUND_Y + SWAMP_HEIGHT - LEFT_WATER_HEIGHT:
                    continue
                
                # Determine which tile to use based on position
                if ty == 0:  # Top row
                    # Check if this position overlaps with crocodile
                    if crocodile_frame_1_loaded and crocodile_frame_2_loaded and left_crocodile_width > 0:
                        left_crocodile_left = left_crocodile_x
                        left_crocodile_right = left_crocodile_x + left_crocodile_width
                        tile_center = tile_x + tile_width // 2
                        left_crocodile_center = left_crocodile_x + left_crocodile_width // 2
                        
                        # If tile center is to the left of crocodile center, use tile 1 (left side)
                        if tile_center < left_crocodile_center:
                            # Animate between tile 1 and tile 2
                            current_tile = water_tile_1 if water_frame == 0 else water_tile_2
                        # If tile center is to the right of crocodile center, use tile 2 (right side)
                        else:
                            # Animate between tile 2 and tile 1
                            current_tile = water_tile_2 if water_frame == 0 else water_tile_1
                    else:
                        # No crocodile, alternate between tile 1 and 2
                        current_tile = water_tile_1 if (tx + water_frame) % 2 == 0 else water_tile_2
                else:  # Bottom rows
                    # Use tiles 3 and 4, animate between tile 3 and 4
                    current_tile = water_tile_3 if water_frame == 0 else water_tile_4
                
                # Draw tile even if it overlaps with crocodile (crocodile will be drawn on top)
                screen.blit(current_tile, (tile_x, tile_y))
        
        # Draw crocodile on top of left water section
        if crocodile_frame_1_loaded and crocodile_frame_2_loaded and crocodile_frame_1 and crocodile_frame_2 and left_crocodile_width > 0:
            screen.blit(current_left_crocodile, (left_crocodile_x, left_crocodile_y))
        else:
            # Fallback to solid color if tiles not loaded
            pygame.draw.rect(screen, SWAMP_COLOR, (SWAMP_START_X, GROUND_Y, SWAMP_WIDTH, SWAMP_HEIGHT))

        # Draw smaller plant to the left of the rock and right of the left water
        if small_plant_loaded and small_plant_img:
            small_plant_width = small_plant_img.get_width()
        small_plant_height = small_plant_img.get_height()
        
        # Calculate position: to the left of rock, right of left water
        left_water_end = LEFT_WATER_START_X + LEFT_WATER_WIDTH
        space_between = SWAMP_START_X - left_water_end
        
        # Calculate rock position first to position plant relative to it
        if rocks_loaded and rocks_img:
            rocks_width = rocks_img.get_width()
            rocks_x = left_water_end + int(space_between * 0.5) - rocks_width // 2
        else:
            rocks_x = left_water_end + int(space_between * 0.5)
        
        # Position plant between left water and rock (about 30% from left water)
        small_plant_x = left_water_end + int((rocks_x - left_water_end) * 0.3) - small_plant_width // 2
        small_plant_y = GROUND_Y - small_plant_height
        
        # Draw red plant behind (invisible, for collision detection)
        if small_plant_red_loaded and small_plant_red_img:
            screen.blit(small_plant_red_img, (small_plant_x, small_plant_y))
        
        # Draw shadow first
        shadow_offset_x = 8
        shadow_offset_y = 8
        shadow_alpha = 120
        shadow_surface = pygame.Surface(small_plant_img.get_size(), pygame.SRCALPHA)
        shadow_surface.fill((0, 0, 0, shadow_alpha))
        shadow_surface.blit(small_plant_img, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(shadow_surface, (small_plant_x + shadow_offset_x, small_plant_y + shadow_offset_y))
        
        # Draw small plant
        screen.blit(small_plant_img, (small_plant_x, small_plant_y))
    
        # Draw smaller plant to the left of the rock and right of the left water
        if small_plant_loaded and small_plant_img:
            small_plant_width = small_plant_img.get_width()
        small_plant_height = small_plant_img.get_height()
        
        # Calculate position: to the left of rock, right of left water
        left_water_end = LEFT_WATER_START_X + LEFT_WATER_WIDTH
        space_between = SWAMP_START_X - left_water_end
        
        # Calculate rock position first to position plant relative to it
        if rocks_loaded and rocks_img:
            rocks_width = rocks_img.get_width()
            rocks_x = left_water_end + int(space_between * 0.5) - rocks_width // 2
        else:
            rocks_x = left_water_end + int(space_between * 0.5)
        
        # Position plant between left water and rock (about 30% from left water)
        small_plant_x = left_water_end + int((rocks_x - left_water_end) * 0.3) - small_plant_width // 2
        small_plant_y = GROUND_Y - small_plant_height
        
        # Draw red plant behind (invisible, for collision detection)
        if small_plant_red_loaded and small_plant_red_img:
            screen.blit(small_plant_red_img, (small_plant_x, small_plant_y))
        
        # Draw shadow first
        shadow_offset_x = 8
        shadow_offset_y = 8
        shadow_alpha = 120
        shadow_surface = pygame.Surface(small_plant_img.get_size(), pygame.SRCALPHA)
        shadow_surface.fill((0, 0, 0, shadow_alpha))
        shadow_surface.blit(small_plant_img, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(shadow_surface, (small_plant_x + shadow_offset_x, small_plant_y + shadow_offset_y))
        
        # Draw small plant
        screen.blit(small_plant_img, (small_plant_x, small_plant_y))
    
        # Draw rocks between the two water areas (natural positioning, not perfectly centered)
        if rocks_loaded and rocks_img:
            rocks_width = rocks_img.get_width()
        rocks_height = rocks_img.get_height()
        
        # Calculate the space between water areas
        left_water_end = LEFT_WATER_START_X + LEFT_WATER_WIDTH
        space_between = SWAMP_START_X - left_water_end
        
        # Position rocks naturally - slightly offset from center (moved more to the right)
        rocks_x = left_water_end + int(space_between * 0.5) - rocks_width // 2
        # Position at ground level (bottom of rocks sits on ground)
        rocks_y = GROUND_Y - rocks_height
        
        # Draw shadow first
        shadow_offset_x = 8
        shadow_offset_y = 8
        shadow_alpha = 120
        shadow_surface = pygame.Surface(rocks_img.get_size(), pygame.SRCALPHA)
        shadow_surface.fill((0, 0, 0, shadow_alpha))
        shadow_surface.blit(rocks_img, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(shadow_surface, (rocks_x + shadow_offset_x, rocks_y + shadow_offset_y))
        
        # Draw rocks
        screen.blit(rocks_img, (rocks_x, rocks_y))
        
        # Draw vines on the left and right sides of the rock
        if vines_loaded and vines_img:
            # Scale vines to be much smaller (about 30% of rock height) for right side
            right_vines_height = int(rocks_height * 0.3)
            right_vines_width = vines_img.get_width() * (right_vines_height / vines_img.get_height())
            right_vines_scaled = pygame.transform.scale(vines_img, (int(right_vines_width), int(right_vines_height)))
            
            # Scale left vine to be bigger (about 40% of rock height)
            left_vines_height = int(rocks_height * 0.4)
            left_vines_width = vines_img.get_width() * (left_vines_height / vines_img.get_height())
            left_vines_scaled = pygame.transform.scale(vines_img, (int(left_vines_width), int(left_vines_height)))
            
            # Apply color tint to match theme (dark green/brown swamp color)
            vine_tint_color = SWAMP_COLOR  # (45, 85, 75) - dark green
            
            # Create tinted versions of the vines
            def apply_vine_tint(vine_surface, tint_color):
                tinted = vine_surface.copy()
                tint_overlay = pygame.Surface(vine_surface.get_size(), pygame.SRCALPHA)
                tint_overlay.fill(tint_color)
                tinted.blit(tint_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                return tinted
            
            right_vines_tinted = apply_vine_tint(right_vines_scaled, vine_tint_color)
            left_vines_tinted = apply_vine_tint(left_vines_scaled, vine_tint_color)
            
            # Position vines at ground level
            right_vines_y = GROUND_Y - right_vines_height
            left_vines_y = GROUND_Y - left_vines_height
            
            # Position vines much closer to the rock (overlap slightly)
            right_overlap_offset = int(right_vines_width * 0.7)  # Overlap 70% of vine width for right side
            left_overlap_offset = int(left_vines_width * 0.2)  # Less overlap for left side (move it more to the right)
            
            # Draw vines on the left side of the rock
            left_vines_x = rocks_x - left_overlap_offset
            screen.blit(left_vines_tinted, (left_vines_x, left_vines_y))
            
            # Draw vines on the right side of the rock (flip horizontally)
            right_vines_flipped = pygame.transform.flip(right_vines_tinted, True, False)
            right_vines_x = rocks_x + rocks_width - right_overlap_offset
            screen.blit(right_vines_flipped, (right_vines_x, right_vines_y))

        # Draw all platforms (removed - platforms are now invisible/untextured)
        # for platform in platforms:
        #     pygame.draw.rect(screen, PLATFORM_COLOR, (platform["x"], platform["y"], platform["width"], platform["height"]))

        # Trees removed - no longer drawing trees

        # Character death animation - slowly ascend when dead
        if game_over:
            # Make character slowly ascend (move upward)
            character["y"] -= 2  # Move up slowly
    
        # Character movement (only when not paused, not game ended, and not game over)
        if not paused and not game_end and not game_over:
            
            # Store previous position for collision detection
            prev_x = character["x"]
        prev_y = character["y"]
        prev_on_ground = character.get("on_ground", False)
        prev_on_platform = character.get("on_platform", False)
        was_on_surface = prev_on_ground or prev_on_platform
        
        # Horizontal movement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            character["x"] -= character["speed"]
            character["facing_direction"] = "left"
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            character["x"] += character["speed"]
            character["facing_direction"] = "right"

        # Collision with thumbnail_wood (solid entity on both left and right sides)
        # Use pixel-perfect collision to match the actual trunk design
        if thumbnail_wood_loaded and thumbnail_wood_img:
            wood_width = thumbnail_wood_img.get_width()
        wood_height = thumbnail_wood_img.get_height()
        
        char_left = character["x"]
        char_right = character["x"] + character["width"]
        char_top = character["y"]
        char_bottom = character["y"] + character["height"]
        
        # Check collision with left trunk using pixel-perfect detection
        if char_right > 0 and char_left < wood_width:
            # Sample trunk pixels at character's position to find collision
            has_collision = False
            sample_step = 4
            
            # Check multiple trunk tiles vertically (trunk repeats)
            for trunk_y_offset in range(0, SCREEN_HEIGHT + wood_height, wood_height):
                char_rel_y_start = max(0, char_top - trunk_y_offset)
                char_rel_y_end = min(wood_height, char_bottom - trunk_y_offset)
                
                if char_rel_y_end > char_rel_y_start:
                    for y in range(int(char_rel_y_start), int(char_rel_y_end), sample_step):
                        for x in range(max(0, char_left), min(wood_width, char_right), sample_step):
                            try:
                                pixel_color = thumbnail_wood_img.get_at((x, y))
                                r, g, b, a = pixel_color
                                if a > 128:  # Solid pixel
                                    has_collision = True
                                    break
                            except:
                                pass
                        if has_collision:
                            break
                if has_collision:
                    break
            
            # If collision detected, push character to the right of trunk
            if has_collision:
                # Find rightmost solid column - check at character's vertical position
                char_mid_y = (char_top + char_bottom) // 2
                trunk_tile_y = char_mid_y % wood_height
                rightmost_solid = 0
                
                for x in range(wood_width - 1, -1, -sample_step):
                    try:
                        pixel_color = thumbnail_wood_img.get_at((x, trunk_tile_y))
                        r, g, b, a = pixel_color
                        if a > 128:
                            rightmost_solid = x + sample_step
                            break
                    except:
                        pass
                
                if rightmost_solid > 0:
                    character["x"] = rightmost_solid
                else:
                    # Fallback: use full width
                    character["x"] = wood_width
        
        # Check collision with right trunk
        right_wood_x = SCREEN_WIDTH - wood_width
        if char_right > right_wood_x and char_left < SCREEN_WIDTH:
            # Sample trunk pixels at character's position to find collision
            has_collision = False
            sample_step = 4
            
            # Check multiple trunk tiles vertically (trunk repeats)
            for trunk_y_offset in range(0, SCREEN_HEIGHT + wood_height, wood_height):
                char_rel_y_start = max(0, char_top - trunk_y_offset)
                char_rel_y_end = min(wood_height, char_bottom - trunk_y_offset)
                
                if char_rel_y_end > char_rel_y_start:
                    char_rel_x_start = max(0, char_left - right_wood_x)
                    char_rel_x_end = min(wood_width, char_right - right_wood_x)
                    
                    for y in range(int(char_rel_y_start), int(char_rel_y_end), sample_step):
                        for x in range(int(char_rel_x_start), int(char_rel_x_end), sample_step):
                            try:
                                pixel_color = thumbnail_wood_img.get_at((x, y))
                                r, g, b, a = pixel_color
                                if a > 128:  # Solid pixel
                                    has_collision = True
                                    break
                            except:
                                pass
                        if has_collision:
                            break
                if has_collision:
                    break
            
            # If collision detected, push character to the left of trunk
            if has_collision:
                # Find leftmost solid column - check at character's vertical position
                char_mid_y = (char_top + char_bottom) // 2
                trunk_tile_y = char_mid_y % wood_height
                leftmost_solid = wood_width
                
                for x in range(0, wood_width, sample_step):
                    try:
                        pixel_color = thumbnail_wood_img.get_at((x, trunk_tile_y))
                        r, g, b, a = pixel_color
                        if a > 128:
                            leftmost_solid = x
                            break
                    except:
                        pass
                
                if leftmost_solid < wood_width:
                    character["x"] = right_wood_x + leftmost_solid - character["width"]
                else:
                    # Fallback: use full width
                    character["x"] = right_wood_x - character["width"]
        
        # Horizontal collision with left branches
        if thumbnail_wood_loaded and thumbnail_wood_img and (branch_1_loaded and branch_2_loaded and branch_3_loaded and branch_4_loaded):
            trunk_width = thumbnail_wood_img.get_width()
            branch_imgs = [branch_1_img, branch_2_img, branch_3_img, branch_4_img]
            for pos, branch_img in zip(LEFT_BRANCH_POSITIONS, branch_imgs):
                scaled = scale_branch(branch_img, BRANCH_SCALE)
                if scaled:
                    branch_x = trunk_width - scaled.get_width() // 2 + pos["offset"]
                    branch_y = int(SCREEN_HEIGHT * pos["y"])
                    check_branch_horizontal_collision(character, scaled, branch_x, branch_y, prev_x, prev_y, sprite_padding_offset, is_left_side=True)
    
        # Horizontal collision with right branches
        if thumbnail_wood_loaded and thumbnail_wood_img and (branch_right_1_loaded and branch_right_2_loaded and branch_right_3_loaded and branch_right_4_loaded):
            trunk_width = thumbnail_wood_img.get_width()
            right_trunk_x = SCREEN_WIDTH - trunk_width
            branch_imgs = [branch_right_1_img, branch_right_2_img, branch_right_3_img, branch_right_4_img]
            for pos, branch_img in zip(RIGHT_BRANCH_POSITIONS, branch_imgs):
                scaled = scale_branch(branch_img, BRANCH_SCALE)
                if scaled:
                    branch_x = right_trunk_x + trunk_width - scaled.get_width() // 2 + pos["offset"]
                    branch_y = int(SCREEN_HEIGHT * pos["y"])
                    check_branch_horizontal_collision(character, scaled, branch_x, branch_y, prev_x, prev_y, sprite_padding_offset, is_left_side=False)
    
        character["x"] = max(0, min(character["x"], SCREEN_WIDTH - character["width"]))
    
        # Y movement constraint: Character can only move in Y direction if:
        # 1. Character jumps using jump key (velocity_y was set to jump_speed)
        # 2. Character doesn't have any surface to stand on (falls down)
    
        # Check if character just jumped (velocity_y is jump_speed, which is negative)
        is_jumping = character["velocity_y"] <= character["jump_speed"] + 1 and character["velocity_y"] < 0
    
        # Initialize collision state
        on_ground = False
        on_platform = False
    
        # First, check platform collision BEFORE deciding if we should lock Y position
        # This prevents the character from floating when walking off platforms
        # Use cached platforms (generated once at initialization)
        if cached_all_platforms is None:
            all_platforms = generate_all_platforms()
        else:
            all_platforms = cached_all_platforms
    
        # Apply physics FIRST, then check collisions
        # Physics
        if game_over:
            # When dead, character flies upward (reduce gravity effect or apply upward force)
            character["velocity_y"] += character["gravity"] * 0.3  # Reduced gravity when dead
            # Add upward force to keep flying up
            if character["velocity_y"] > -5.0:
                character["velocity_y"] -= 0.2  # Continue upward movement
        else:
            character["velocity_y"] += character["gravity"]
    
        character["y"] += character["velocity_y"]
    
        # Calculate character position for collision checks
        character_center_x = character["x"] + character["width"] // 2
        character_bottom = character["y"] + character["height"]
        character_feet_y = character["y"] + character["height"]
        visual_feet_y = character_feet_y - sprite_padding_offset
        target_y = GROUND_Y - character["height"] + sprite_padding_offset
    
        # Check if character is over left water area or swamp area
        is_over_left_water = (LEFT_WATER_START_X <= character_center_x <= LEFT_WATER_START_X + LEFT_WATER_WIDTH)
        is_over_swamp = (SWAMP_START_X <= character_center_x <= SWAMP_START_X + SWAMP_WIDTH)

        # Skip collision checks when dead (let character fly freely)
        if not game_over:
            # Check platform collision FIRST
            for platform in all_platforms:
                platform_rect = pygame.Rect(platform["x"], platform["y"], platform["width"], platform["height"])
                platform_target_y = platform["y"] - character["height"] + sprite_padding_offset
                
                # Check if character is horizontally within platform bounds
                char_left = character["x"]
                char_right = character["x"] + character["width"]
                platform_left = platform["x"]
                platform_right = platform["x"] + platform["width"]
                
                # Character is on platform if there's any horizontal overlap
                is_horizontally_on_platform = (char_right > platform_left and char_left < platform_right)
                
                if is_horizontally_on_platform:
                    # Check if character is on or near the platform
                    if character_feet_y >= platform["y"] - 10 and character_feet_y <= platform["y"] + platform["height"] + 10:
                        # Only apply if character is above or at platform level (not below it)
                        if character["y"] <= platform_target_y + 10:
                            # If falling onto platform or already on platform
                            if character["velocity_y"] >= 0 or abs(character["velocity_y"]) < 0.5:
                                character["y"] = platform_target_y
                                character["velocity_y"] = 0
                                on_ground = True
                                on_platform = True
                                break
        
        # Check ground collision (only if not on platform and not over water/swamp)
        if not on_platform and (visual_feet_y >= GROUND_Y or character_feet_y >= GROUND_Y + sprite_padding_offset) and not is_over_left_water and not is_over_swamp:
            character["y"] = target_y
            character["velocity_y"] = 0
            on_ground = True
    
        character["on_ground"] = on_ground
        character["on_platform"] = on_platform
        if on_ground or on_platform:
            character["has_double_jump"] = True
    
        # Swamp death check (only if character is falling into swamp, not standing on ground)
        if (SWAMP_START_X <= character_center_x <= SWAMP_START_X + SWAMP_WIDTH and 
        character_bottom >= GROUND_Y and not on_platform and not on_ground and not game_over):
            sound.play("gameover", settings["sound"]["sfx"] if not settings["sound"]["muted"] else 0.0)
            game_over = True
            game_over_start_time = pygame.time.get_ticks()
            # Set upward velocity to make character fly up when dying
            character["velocity_y"] = -8.0  # Negative value makes it go up
            # Reset dying animation when character dies
            if dying_frames_loaded:
                dying_frame_index = 0
                dying_animation_timer = current_time
    
        # Left water death check (only if character is falling into water, not standing on ground)
        left_water_top = GROUND_Y + SWAMP_HEIGHT - LEFT_WATER_HEIGHT
        if (LEFT_WATER_START_X <= character_center_x <= LEFT_WATER_START_X + LEFT_WATER_WIDTH and
        character_bottom >= left_water_top and not on_platform and not on_ground and not game_over):
            sound.play("gameover", settings["sound"]["sfx"] if not settings["sound"]["muted"] else 0.0)
            game_over = True
            game_over_start_time = pygame.time.get_ticks()
            # Set upward velocity to make character fly up when dying
            character["velocity_y"] = -8.0  # Negative value makes it go up
            # Reset dying animation when character dies
            if dying_frames_loaded:
                dying_frame_index = 0
                dying_animation_timer = current_time

        # Update tongue (with retract animation)
        if character["tongue_extended"]:
            if character["tongue_retracting"]:
                # Retract the tongue
                character["tongue_length"] -= character["tongue_retract_speed"]
                if character["tongue_length"] <= 0:
                    character["tongue_length"] = 0
                    character["tongue_extended"] = False
                    character["tongue_retracting"] = False
            else:
                # Extend the tongue
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
                sound.play("eaten", settings["sound"]["sfx"] if not settings["sound"]["muted"] else 0.0)

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
        if game_over and dying_frames_loaded and dying_frames:
            if current_time - dying_animation_timer >= DYING_ANIMATION_SPEED:
                dying_animation_timer = current_time
                dying_frame_index = (dying_frame_index + 1) % len(dying_frames)
            
            DYING_SCALE = 1.3
            dying_width = int(character["width"] * DYING_SCALE)
            dying_height = int(character["height"] * DYING_SCALE)
            current_sprite = pygame.transform.scale(dying_frames[dying_frame_index], (dying_width, dying_height))
            
            white_sprite = current_sprite.copy()
            white_overlay = pygame.Surface(white_sprite.get_size(), pygame.SRCALPHA)
            white_overlay.fill((255, 255, 255, 255))
            white_sprite.blit(white_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            offset_x = (character["width"] - dying_width) // 2
            offset_y = (character["height"] - dying_height) // 2
            screen.blit(white_sprite, (character["x"] + offset_x, character["y"] + offset_y))
        elif sprite_sheet_loaded and frog_frames:
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
                # Initialize animation state if missing
                if "animation_timer" not in fly:
                    fly["animation_timer"] = random.randint(0, FLY_ANIMATION_SPEED - 1)
                if "frame" not in fly:
                    fly["frame"] = 0

                # Randomize movement pattern over time
                fly["change_timer"] -= 1
                if fly["change_timer"] <= 0:
                    ang = random.uniform(0, math.tau)
                    spd = random.uniform(2.0, 4.0)
                    fly["vx"] = math.cos(ang) * spd
                    fly["vy"] = math.sin(ang) * spd
                    fly["change_timer"] = random.randint(30, 120)

                # Update animation for chirping effect
                fly["animation_timer"] -= 1
                if fly["animation_timer"] <= 0:
                    fly["frame"] = 1 - fly["frame"]  # Switch between 0 and 1
                    fly["animation_timer"] = FLY_ANIMATION_SPEED

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
                elif fly["y"] > GROUND_Y - FLY_H:
                    fly["y"] = GROUND_Y - FLY_H
                    fly["vy"] *= -1

            # Draw fly with animation frame and direction
            if fly_img:
                current_frame = fly.get("frame", 0)
                vx = fly.get("vx", 0)
                facing_left = vx < 0  # Flip sprite if moving left
                
                # Select the correct frame
                if current_frame == 0:
                    sprite_to_draw = fly_img
                else:
                    sprite_to_draw = fly_img_frame2 if fly_img_frame2 else fly_img
                
                # Flip horizontally if moving left
                if facing_left:
                    sprite_to_draw = pygame.transform.flip(sprite_to_draw, True, False)
                
                screen.blit(sprite_to_draw, (fly["x"], fly["y"]))
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
        if paused and not settings_open:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            draw_pause_menu(screen, pause_menu_y)

        # Draw settings menu
        if settings_open:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            draw_settings_menu(screen, settings_menu_y)

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