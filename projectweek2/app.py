import pygame
import sys
import random
import math
import os
from sounds import SoundManager 

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
pygame.display.set_caption("Fly Feast")
clock = pygame.time.Clock()

# ---------------- SOUND SETUP ----------------
sound = SoundManager()
sound.play_music()
pygame.mixer.music.set_volume(0.4)  # 0.0 = silent, 1.0 = max volume

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
NUM_BEES = 6
TIMER_START_SECONDS = 90
SCORE_ANIMATION_DURATION = 200
ANIMATION_SPEED = 150

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

bee_img, _ = load_image("fly.png", convert_alpha=True)
background_img, background_loaded = load_image("view.png")

# Load ground tiles
ground_tiles = {}
ground_tiles_loaded = False
tile_size = None

if os.path.exists("ground_tiles_25_pngs"):
    for row in range(1, 6):
        for col in range(1, 6):
            path = os.path.join("ground_tiles_25_pngs", f"tile_r{row}_c{col}.png")
            if os.path.exists(path):
                try:
                    tile = pygame.image.load(path).convert_alpha()
                    ground_tiles[(row, col)] = tile
                    if tile_size is None:
                        tile_size = tile.get_width()  # Assume square tiles
                except:
                    pass
    if ground_tiles:
        ground_tiles_loaded = True

# Load tree images
tree_images = None
tree_loaded = False
tree_width, tree_height = 150, 250
try:
    tree_left, _ = load_image("projectweek2/tree_img/tree_left_final_clean2.png", convert_alpha=True)
    tree_middle, _ = load_image("projectweek2/tree_img/tree_middle_final_clean2.png", convert_alpha=True)
    tree_right, _ = load_image("projectweek2/tree_img/tree_right_final_clean2.png", convert_alpha=True)
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
TONGUE_DIR = "projectweek2/tongues_split_pngs"

if os.path.exists(TONGUE_DIR):
    for i in range(1, 9):  # tongue_01.png to tongue_08.png
        path = os.path.join(TONGUE_DIR, f"tongue_{i:02d}.png")
        if os.path.exists(path):
            try:
                frame = pygame.image.load(path).convert_alpha()
                tongue_frames.append(frame)
            except:
                pass
    if tongue_frames:
        tongue_loaded = True


# Load frog sprites
frog_frames = {
    "idle_left": [], "idle_right": [],
    "walk_left": [], "walk_right": [],
    "jump_left": [], "jump_right": []
}
sprite_sheet_loaded = False

FROG_DIR = "projectweek2/frogs_split" 

if os.path.exists(FROG_DIR):
    for anim_type in ["standing", "walk", "jump"]:
        frame_count = 4 if anim_type == "standing" else 3
        for i in range(1, frame_count + 1):
            for direction in ["left", "right"]:
                key = f"{anim_type.replace('standing', 'idle')}_{direction}"
                path = os.path.join(FROG_DIR, f"{anim_type}_{direction}_f{i}.png")
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

# --- pixel font (PATH FIXED) ---
PIXEL_FONT_DIR = "projectweek2/pixel_font"

pixel_font_images = {}
pixel_font_loaded = False
default_char_width, default_char_height = 20, 20

if os.path.exists(PIXEL_FONT_DIR):
    for char in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        path = os.path.join(PIXEL_FONT_DIR, f"{char}.png")
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
game_over = False
game_over_start_time = 0  # For screen shake timing
shake_duration = 800      # milliseconds
shake_magnitude = 25      # pixels


# Create bees
bees = []
for _ in range(NUM_BEES):
    bees.append({
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
    
    for bee in bees:
        bee["x"] = random.randint(0, SCREEN_WIDTH)
        bee["y"] = random.randint(0, SCREEN_HEIGHT)
        bee["speed"] = random.randint(2, 4)

def draw_tiled_ground(surface, x, y, width, height, use_grass_top=True):
    """Draw tiled ground using the ground tileset
    use_grass_top: If True, uses grass tiles (r1) on top row. If False, uses ground tiles (r3) on top row.
    """
    if not ground_tiles_loaded or tile_size is None:
        # Fallback to solid color
        pygame.draw.rect(surface, GROUND_COLOR, (x, y, width, height))
        return
    
    # Calculate how many tiles fit - ensure we have enough to cover the area
    tiles_x = max(1, int(math.ceil(width / tile_size)))
    tiles_y = max(1, int(math.ceil(height / tile_size)))
    
    # Calculate actual tile size to evenly fill the area
    actual_tile_width = width / tiles_x
    actual_tile_height = height / tiles_y
    
    for tile_y in range(tiles_y):
        for tile_x in range(tiles_x):
            # Calculate exact position - tiles must touch each other exactly
            # Use integer positions to avoid floating point gaps
            tile_pos_x = int(x + tile_x * actual_tile_width)
            tile_pos_y = int(y + tile_y * actual_tile_height)
            
            # Calculate draw size - ensure tiles fill exactly and touch
            if tile_x == tiles_x - 1:
                # Last tile in row - stretch to fill remaining width exactly
                draw_width = int((x + width) - tile_pos_x)
            else:
                # Regular tile - calculate next tile position to ensure no gap
                next_tile_x = int(x + (tile_x + 1) * actual_tile_width)
                draw_width = next_tile_x - tile_pos_x
            
            if tile_y == tiles_y - 1:
                # Last tile in column - stretch to fill remaining height exactly
                draw_height = int((y + height) - tile_pos_y)
            else:
                # Regular tile - calculate next tile position to ensure no gap
                next_tile_y = int(y + (tile_y + 1) * actual_tile_height)
                draw_height = next_tile_y - tile_pos_y
            
            # Ensure minimum size to avoid gaps
            draw_width = max(1, draw_width)
            draw_height = max(1, draw_height)
            
            # Determine which tile to use based on position
            if tile_y == 0:  # Top row
                if use_grass_top:
                    # Use grass tiles (r1) for surface level
                    if tile_x == 0:
                        tile_key = (1, 1)  # Top-left corner (grass)
                    elif tile_x == tiles_x - 1:
                        tile_key = (1, 5)  # Top-right corner (grass)
                    else:
                        tile_key = (1, min(2 + (tile_x % 3), 4))  # Top edge (grass)
                else:
                    # Use ground tiles (r3) for below surface
                    if tile_x == 0:
                        tile_key = (3, 1)  # Top-left corner (ground)
                    elif tile_x == tiles_x - 1:
                        tile_key = (3, 5)  # Top-right corner (ground)
                    else:
                        tile_key = (3, min(2 + (tile_x % 3), 4))  # Top edge (ground)
            elif tile_y == tiles_y - 1:  # Bottom row - use ground tiles
                if tile_x == 0:
                    tile_key = (5, 1)  # Bottom-left corner
                elif tile_x == tiles_x - 1:
                    tile_key = (5, 5)  # Bottom-right corner
                else:
                    # Bottom edge
                    tile_key = (5, min(2 + (tile_x % 3), 4))
            else:  # Middle rows - use ground tiles
                if tile_x == 0:
                    # Left edge - use r3 or r4
                    tile_key = (3, 1)
                elif tile_x == tiles_x - 1:
                    # Right edge - use r3 or r4
                    tile_key = (3, 5)
                else:
                    # Center/inner tiles - use specified tiles: r2_c3, r4_c2, r4_c3, r5_c5
                    inner_tiles = [(2, 3), (4, 2), (4, 3), (5, 5)]
                    tile_index = (tile_y * tiles_x + tile_x) % len(inner_tiles)
                    tile_key = inner_tiles[tile_index]
            
            # Draw the tile if it exists, scaled to fit the area
            if tile_key in ground_tiles:
                tile_img = ground_tiles[tile_key]
                # Scale tile to exact size needed to fill the space
                scaled_tile = pygame.transform.scale(tile_img, (int(draw_width), int(draw_height)))
                surface.blit(scaled_tile, (int(tile_pos_x), int(tile_pos_y)))

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
    if timer_remaining <= 0 and not game_over:
        reset_game()
    
    keys = pygame.key.get_pressed()
    
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        elif game_over and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            # Restart button coordinates
            button_width, button_height = 300, 100
            button_x = (SCREEN_WIDTH - button_width) // 2
            button_y = (SCREEN_HEIGHT - button_height) // 2
            if button_x <= mouse_x <= button_x + button_width and button_y <= mouse_y <= button_y + button_height:
                reset_game()
                game_over = False
        elif not game_over:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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

    # Walking sound - change sound or remove
    keys = pygame.key.get_pressed()
    moving = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_a] or keys[pygame.K_d]

    if moving and not sound.walking:
        sound.play_loop("walk")
        sound.walking = True

    elif not moving and sound.walking:
        sound.stop("walk")
        sound.walking = False

    # Screen shake
    shake_offset_x, shake_offset_y = 0, 0
    if game_over:
        elapsed_shake = current_time - game_over_start_time
        if elapsed_shake < shake_duration:
            shake_offset_x = random.randint(-shake_magnitude, shake_magnitude)
            shake_offset_y = random.randint(-shake_magnitude, shake_magnitude)

    # Draw background
    if background_loaded:
        if background_img.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
            screen.blit(pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT)), (shake_offset_x, shake_offset_y))
        else:
            screen.blit(background_img, (shake_offset_x, shake_offset_y))
    else:
        screen.fill(BG_COLOR)
    
    # Draw ground and swamp with tiles
    draw_tiled_ground(screen, 0 + shake_offset_x, GROUND_Y + shake_offset_y, SCREEN_WIDTH, GROUND_HEIGHT, use_grass_top=True)
    draw_tiled_ground(screen, 0 + shake_offset_x, GROUND_Y + GROUND_HEIGHT + shake_offset_y, SWAMP_START_X, SWAMP_HEIGHT - GROUND_HEIGHT, use_grass_top=False)
    right_ground_width = SCREEN_WIDTH - (SWAMP_START_X + SWAMP_WIDTH)
    draw_tiled_ground(screen, SWAMP_START_X + SWAMP_WIDTH, GROUND_Y + GROUND_HEIGHT, 
                     right_ground_width, SWAMP_HEIGHT - GROUND_HEIGHT, use_grass_top=False)
    
    # Swamp (keep as solid color)
    pygame.draw.rect(screen, SWAMP_COLOR, (SWAMP_START_X, GROUND_Y, SWAMP_WIDTH, SWAMP_HEIGHT))
    
    # Platform over swamp (with grass on top)
    draw_tiled_ground(screen, PLATFORM_X, PLATFORM_Y, PLATFORM_WIDTH, PLATFORM_HEIGHT, use_grass_top=True)
    
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
        game_over_start_time = pygame.time.get_ticks()  # Start screen shake

    
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
        
        # Bee collision
        bees_to_remove = []
        for i, bee in enumerate(bees):
            bee_center_x = bee["x"] + 20
            bee_center_y = bee["y"] + 20
            to_bee_x = bee_center_x - frog_center_x
            to_bee_y = bee_center_y - frog_center_y
            dot_product = to_bee_x * math.cos(character["tongue_angle"]) + to_bee_y * math.sin(character["tongue_angle"])
            
            if 0 <= dot_product <= character["tongue_length"]:
                perp_distance = abs(-to_bee_x * math.sin(character["tongue_angle"]) + to_bee_y * math.cos(character["tongue_angle"]))
                if perp_distance < 30:
                    sound.play("eaten")
                    bees_to_remove.append(i)
        
        for i in reversed(bees_to_remove):
            bees.pop(i)
            score += 1
            if score > high_score:
                high_score = score
            score_animation_time = current_time
            bees.append({
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
    

        # ---------------- GAME OVER SCREEN ----------------
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
            draw_pixel_text(screen, text, text_x, SCREEN_HEIGHT // 2 - 140, scale=scale, color=(255, 50, 50))

        # RESTART text (clickable, no rectangle)
        if pixel_font_loaded:
            text = "RESTART"
            scale = 0.6

            text_width = len(text) * int(default_char_width * scale)
            text_height = int(default_char_height * scale)

    # Position (left + down like you want)
            text_x = (SCREEN_WIDTH - text_width) // 2
            text_y = (SCREEN_HEIGHT // 2) + 10

            mouse_x, mouse_y = pygame.mouse.get_pos()

    # Hover detection using text bounds
            hover = (
                text_x <= mouse_x <= text_x + text_width and
                text_y <= mouse_y <= text_y + text_height
            )

            color = (255, 255, 255) if hover else (200, 200, 200)

            draw_pixel_text(screen, text, text_x, text_y, scale=scale, color=color)

    # Save rect for clicking (IMPORTANT)
            restart_rect = pygame.Rect(text_x, text_y, text_width, text_height)



    pygame.display.flip()

sound.stop_music()
pygame.quit()
sys.exit()