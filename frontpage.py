import os
import sys
import json
import pygame

pygame.init()
pygame.mixer.init()

#-------------- CONFIG / CONSTANTS -----------
W, H = 1000, 650
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Frog Platformer - Menu System")
clock = pygame.time.Clock()

FONT_BIG = pygame.font.Font(None, 72)
FONT = pygame.font.Font(None, 40)
FONT_SMALL = pygame.font.Font(None, 28)

PLAYERS_PATH = "players.json"
SETTINGS_PATH = "settings.json"

DEFAULT_SETTINGS = {
    "keybinds": {  # AZERTY defaults
        "left": "K_q",
        "right": "K_d",
        "jump": "K_SPACE",
        "tongue": "K_LCTRL",
        "pause": "K_ESCAPE"
    },
    "sound": {
        "music": 0.5,
        "sfx": 0.7,
        "muted": False
    }
}

#-------------- ASSETS (IMAGES) -----------
# Put images in ./assets/
ASSETS_DIR = "assets"

def safe_load_image(path, size=None, alpha=True):
    """
    Loads an image if it exists; otherwise returns None.
    - size: (W,H) to scale to.
    - alpha: use convert_alpha() for PNG transparency.
    """
    if not os.path.exists(path):
        return None
    img = pygame.image.load(path)
    img = img.convert_alpha() if alpha else img.convert()
    if size is not None:
        img = pygame.transform.smoothscale(img, size)
    return img

# Backgrounds (full screen)
BG_USERNAME    = safe_load_image(os.path.join(ASSETS_DIR, "bg_username.png"),    (W, H), alpha=False)
BG_HOME        = safe_load_image(os.path.join(ASSETS_DIR, "bg_home.png"),        (W, H), alpha=False)
BG_SETTINGS    = safe_load_image(os.path.join(ASSETS_DIR, "bg_settings.png"),    (W, H), alpha=False)
BG_LEADERBOARD = safe_load_image(os.path.join(ASSETS_DIR, "bg_leaderboard.png"), (W, H), alpha=False)
BG_GAME        = safe_load_image(os.path.join(ASSETS_DIR, "bg_game.png"),        (W, H), alpha=False)

# Optional icons (used on Home buttons)
ICON_PLAY        = safe_load_image(os.path.join(ASSETS_DIR, "icon_play.png"),        (90, 90), alpha=True)
ICON_SETTINGS    = safe_load_image(os.path.join(ASSETS_DIR, "icon_settings.png"),    (90, 90), alpha=True)
ICON_LEADERBOARD = safe_load_image(os.path.join(ASSETS_DIR, "icon_leaderboard.png"), (90, 90), alpha=True)

#-------------- PERSISTENCE / HELPERS -----------
def load_json(path, fallback):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return fallback
    return fallback

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def clamp(v, a, b):
    return max(a, min(b, v))

def keyname_to_keyconst(name: str) -> int:
    return getattr(pygame, name, pygame.K_UNKNOWN)

def keyconst_to_keyname(k: int) -> str:
    for attr in dir(pygame):
        if attr.startswith("K_") and getattr(pygame, attr) == k:
            return attr
    return "K_UNKNOWN"

def human_key(k: int) -> str:
    return pygame.key.name(k).upper()

def draw_text(surf, text, font, x, y, color=(235,235,235)):
    img = font.render(text, True, color)
    surf.blit(img, (x, y))
    return img.get_rect(topleft=(x, y))

def draw_bg_or_color(surf, bg_img, fallback_color):
    """
    If bg_img exists, blit it. Otherwise fill with fallback color.
    """
    if bg_img is not None:
        surf.blit(bg_img, (0, 0))
    else:
        surf.fill(fallback_color)

#-------------- UI WIDGETS -----------
class Button:
    def __init__(self, rect, label):
        self.rect = pygame.Rect(rect)
        self.label = label

    def draw(self, surf):
        mx, my = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mx, my)
        bg = (60, 60, 70) if hover else (40, 40, 48)
        pygame.draw.rect(surf, bg, self.rect, border_radius=16)
        pygame.draw.rect(surf, (130,130,150), self.rect, 2, border_radius=16)
        txt = FONT.render(self.label, True, (240,240,240))
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

class TextInput:
    def __init__(self, rect, placeholder=""):
        self.rect = pygame.Rect(rect)
        self.placeholder = placeholder
        self.text = ""
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)

        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                return "enter"
            else:
                if len(event.unicode) == 1 and len(self.text) < 18:
                    if event.unicode.isalnum() or event.unicode in ("_", "-", "."):
                        self.text += event.unicode
        return None

    def draw(self, surf):
        bg = (55,55,65) if self.active else (38,38,45)
        pygame.draw.rect(surf, bg, self.rect, border_radius=12)
        pygame.draw.rect(surf, (140,140,160), self.rect, 2, border_radius=12)

        shown = self.text if self.text else self.placeholder
        col = (240,240,240) if self.text else (160,160,175)
        img = FONT_SMALL.render(shown, True, col)
        surf.blit(img, img.get_rect(midleft=(self.rect.left+12, self.rect.centery)))

class Slider:
    def __init__(self, x, y, w, value=0.5):
        self.rect = pygame.Rect(x, y, w, 10)
        self.value = float(value)
        self.dragging = False

    def handle_event(self, event):
        hit = self.rect.inflate(0, 24)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and hit.collidepoint(event.pos):
            self.dragging = True
            self._set(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set(event.pos[0])

    def _set(self, mx):
        t = (mx - self.rect.left) / self.rect.width
        self.value = clamp(t, 0.0, 1.0)

    def draw(self, surf):
        pygame.draw.rect(surf, (120,120,140), self.rect, border_radius=6)
        knob_x = self.rect.left + int(self.value * self.rect.width)
        pygame.draw.circle(surf, (240,240,240), (knob_x, self.rect.centery), 10)

class ListBox:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.items = []
        self.scroll = 0
        self.row_h = 30

    def set_items(self, items):
        self.items = items
        self.scroll = clamp(self.scroll, 0, max(0, len(self.items)*self.row_h - self.rect.height))

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            if self.rect.collidepoint(mx, my):
                self.scroll = clamp(self.scroll - event.y*30, 0, max(0, len(self.items)*self.row_h - self.rect.height))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                rel_y = event.pos[1] - self.rect.top + self.scroll
                idx = rel_y // self.row_h
                if 0 <= idx < len(self.items):
                    return idx
        return None

    def draw(self, surf, render_item_fn):
        pygame.draw.rect(surf, (30,30,36), self.rect, border_radius=12)
        pygame.draw.rect(surf, (120,120,140), self.rect, 2, border_radius=12)

        clip = surf.get_clip()
        surf.set_clip(self.rect)

        y0 = self.rect.top - self.scroll
        for i, item in enumerate(self.items):
            row_rect = pygame.Rect(self.rect.left, y0 + i*self.row_h, self.rect.width, self.row_h)
            if row_rect.bottom < self.rect.top or row_rect.top > self.rect.bottom:
                continue
            render_item_fn(surf, row_rect, i, item)

        surf.set_clip(clip)

#-------------- APP / DATA MODEL -----------
class App:
    def __init__(self):
        self.settings = load_json(SETTINGS_PATH, DEFAULT_SETTINGS)
        self.players = load_json(PLAYERS_PATH, {})  # {"name": {"plays":int,"best_score":int,"last_score":int}}
        self.username = None
        self.apply_audio_settings()
        self.scene = UsernameScene(self)

    def apply_audio_settings(self):
        s = self.settings["sound"]
        if s.get("muted"):
            pygame.mixer.music.set_volume(0.0)
        else:
            pygame.mixer.music.set_volume(float(s.get("music", 0.5)))

    def get_keybinds(self):
        kb = self.settings["keybinds"]
        return {action: keyname_to_keyconst(name) for action, name in kb.items()}

    def ensure_player(self, name: str):
        if name not in self.players:
            self.players[name] = {"plays": 0, "best_score": 0, "last_score": 0}
            save_json(PLAYERS_PATH, self.players)

    def record_play(self, score: int):
        if not self.username:
            return
        self.ensure_player(self.username)
        p = self.players[self.username]
        p["plays"] += 1
        p["last_score"] = int(score)
        p["best_score"] = max(int(p.get("best_score", 0)), int(score))
        save_json(PLAYERS_PATH, self.players)

    def save_settings(self):
        save_json(SETTINGS_PATH, self.settings)
        self.apply_audio_settings()

    def run(self):
        running = True
        while running:
            dt = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.scene.handle_event(event)

            self.scene.update(dt)
            self.scene.draw(screen)
            pygame.display.flip()

        pygame.quit()
        sys.exit()

#-------------- SCENE: USERNAME SELECT / CREATE -----------
class UsernameScene:
    def __init__(self, app):
        self.app = app
        self.search = TextInput((W//2 - 220, 210, 440, 46), "Search existing usernames...")
        self.name_entry = TextInput((W//2 - 220, 290, 440, 46), "Or type a new username and press Enter")
        self.listbox = ListBox((W//2 - 220, 360, 440, 210))

    def handle_event(self, event):
        self.search.handle_event(event)
        enter = self.name_entry.handle_event(event)

        idx = self.listbox.handle_event(event)
        if idx is not None:
            chosen = self.listbox.items[idx]
            self.app.username = chosen
            self.app.ensure_player(chosen)
            self.app.scene = HomeScene(self.app)

        if enter == "enter":
            name = self.name_entry.text.strip()
            if name:
                self.app.username = name
                self.app.ensure_player(name)
                self.app.scene = HomeScene(self.app)

    def update(self, dt):
        query = self.search.text.strip().lower()
        names = sorted(self.app.players.keys(), key=lambda s: s.lower())
        if query:
            names = [n for n in names if query in n.lower()]
        self.listbox.set_items(names)

    def draw(self, surf):
        #-------------- IMAGE SLOT: START / USERNAME BG -----------
        # Replace bg_username.png in ./assets/ to change this background.
        # If you want no image, delete bg_username.png and it will fall back to a fill color.
        draw_bg_or_color(surf, BG_USERNAME, (16, 16, 20))

        draw_text(surf, "Frog Platformer", FONT_BIG, W//2 - 220, 90)
        draw_text(surf, "Choose a username to continue", FONT, W//2 - 240, 155, (200,200,210))

        self.search.draw(surf)
        self.name_entry.draw(surf)

        draw_text(surf, "Existing players:", FONT_SMALL, W//2 - 220, 335, (200,200,210))

        def render_name(s, r, i, item):
            mx, my = pygame.mouse.get_pos()
            hover = r.collidepoint(mx, my)
            if hover:
                pygame.draw.rect(s, (50,50,60), r)
            txt = FONT_SMALL.render(item, True, (235,235,235))
            s.blit(txt, (r.left+10, r.top+6))

        self.listbox.draw(surf, render_name)

#-------------- SCENE: MAIN HOME PAGE (PLAY / SETTINGS / LEADERBOARD) -----------
class HomeScene:
    def __init__(self, app):
        self.app = app
        self.btn_play = Button((80, 220, 260, 300), "Play")
        self.btn_settings = Button((370, 220, 260, 300), "Settings")
        self.btn_leaderboard = Button((660, 220, 260, 300), "Leaderboard")
        self.btn_switch = Button((W-210, 30, 180, 45), "Switch user")

    def handle_event(self, event):
        if self.btn_switch.clicked(event):
            self.app.scene = UsernameScene(self.app)

        if self.btn_play.clicked(event):
            self.app.scene = GameScene(self.app)

        if self.btn_settings.clicked(event):
            self.app.scene = SettingsScene(self.app)

        if self.btn_leaderboard.clicked(event):
            self.app.scene = LeaderboardScene(self.app)

    def update(self, dt): pass

    def draw(self, surf):
        #-------------- IMAGE SLOT: HOME BG -----------
        # Replace bg_home.png in ./assets/ to change this background.
        draw_bg_or_color(surf, BG_HOME, (16, 16, 20))

        draw_text(surf, "Home", FONT_BIG, 60, 60)
        draw_text(surf, f"Logged in as: {self.app.username}", FONT_SMALL, 62, 130, (190,190,205))

        self.btn_switch.draw(surf)
        self.btn_play.draw(surf)
        self.btn_settings.draw(surf)
        self.btn_leaderboard.draw(surf)

        #-------------- IMAGE SLOT: HOME ICONS -----------
        # Put these in ./assets/ if you want them:
        # icon_play.png, icon_settings.png, icon_leaderboard.png
        # Delete them if you don't want icons.
        if ICON_PLAY:
            surf.blit(ICON_PLAY, (80 + 85, 220 + 60))
        if ICON_SETTINGS:
            surf.blit(ICON_SETTINGS, (370 + 85, 220 + 60))
        if ICON_LEADERBOARD:
            surf.blit(ICON_LEADERBOARD, (660 + 85, 220 + 60))

        draw_text(surf, "Start the game", FONT_SMALL, 130, 535, (170,170,190))
        draw_text(surf, "Edit keybinds + sound", FONT_SMALL, 395, 535, (170,170,190))
        draw_text(surf, "View all players", FONT_SMALL, 705, 535, (170,170,190))

#-------------- SCENE: SETTINGS (KEYBINDS + SOUND) -----------
class SettingsScene:
    def __init__(self, app):
        self.app = app
        self.back = Button((30, 30, 120, 45), "Back")

        self.waiting_for = None
        self.actions = ["left", "right", "jump", "tongue", "pause"]
        self.key_rects = {a: pygame.Rect(260, 180 + i*55, 240, 42) for i, a in enumerate(self.actions)}

        s = self.app.settings["sound"]
        self.music_slider = Slider(260, 520, 320, s.get("music", 0.5))
        self.sfx_slider = Slider(260, 575, 320, s.get("sfx", 0.7))
        self.mute_btn = Button((620, 505, 170, 50), "Mute")
        self.unmute_btn = Button((620, 560, 170, 50), "Unmute")

    def handle_event(self, event):
        if self.back.clicked(event):
            self.app.save_settings()
            self.app.scene = HomeScene(self.app)
            return

        self.music_slider.handle_event(event)
        self.sfx_slider.handle_event(event)

        self.app.settings["sound"]["music"] = self.music_slider.value
        self.app.settings["sound"]["sfx"] = self.sfx_slider.value

        if self.mute_btn.clicked(event):
            self.app.settings["sound"]["muted"] = True
            self.app.apply_audio_settings()

        if self.unmute_btn.clicked(event):
            self.app.settings["sound"]["muted"] = False
            self.app.apply_audio_settings()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for action, r in self.key_rects.items():
                if r.collidepoint(event.pos):
                    self.waiting_for = action

        if self.waiting_for and event.type == pygame.KEYDOWN:
            new_name = keyconst_to_keyname(event.key)

            kb = self.app.settings["keybinds"]
            other = None
            for a, kname in kb.items():
                if a != self.waiting_for and kname == new_name:
                    other = a
                    break
            if other:
                kb[other], kb[self.waiting_for] = kb[self.waiting_for], kb[other]
            else:
                kb[self.waiting_for] = new_name

            self.waiting_for = None

    def update(self, dt):
        if not self.app.settings["sound"].get("muted", False):
            self.app.apply_audio_settings()

    def draw(self, surf):
        #-------------- IMAGE SLOT: SETTINGS BG -----------
        # Replace bg_settings.png in ./assets/ to change this background.
        draw_bg_or_color(surf, BG_SETTINGS, (16, 16, 20))

        self.back.draw(surf)

        draw_text(surf, "Settings", FONT_BIG, 60, 70)
        draw_text(surf, "Keybinds (click one, then press a key)", FONT_SMALL, 60, 150, (200,200,210))

        kb_consts = self.app.get_keybinds()
        for i, action in enumerate(self.actions):
            y = 180 + i*55
            draw_text(surf, action.upper(), FONT_SMALL, 60, y+8, (230,230,240))

            r = self.key_rects[action]
            pygame.draw.rect(surf, (38,38,45), r, border_radius=10)
            pygame.draw.rect(surf, (120,120,140), r, 2, border_radius=10)

            if self.waiting_for == action:
                txt = "Press a key..."
                col = (255, 220, 120)
            else:
                txt = human_key(kb_consts[action])
                col = (235,235,235)

            img = FONT_SMALL.render(txt, True, col)
            surf.blit(img, img.get_rect(center=r.center))

        draw_text(surf, "Sound", FONT, 60, 480)
        draw_text(surf, "Music", FONT_SMALL, 60, 505, (200,200,210))
        self.music_slider.draw(surf)

        draw_text(surf, "SFX", FONT_SMALL, 60, 560, (200,200,210))
        self.sfx_slider.draw(surf)

        muted = self.app.settings["sound"].get("muted", False)
        draw_text(surf, f"Muted: {muted}", FONT_SMALL, 620, 470, (200,200,210))
        self.mute_btn.draw(surf)
        self.unmute_btn.draw(surf)

#-------------- SCENE: LEADERBOARD (EVERYONE WHO PLAYED) -----------
class LeaderboardScene:
    def __init__(self, app):
        self.app = app
        self.back = Button((30, 30, 120, 45), "Back")
        self.search = TextInput((W-360, 40, 320, 40), "Search players...")
        self.listbox = ListBox((60, 180, W-120, 420))

    def handle_event(self, event):
        if self.back.clicked(event):
            self.app.scene = HomeScene(self.app)
            return

        self.search.handle_event(event)
        self.listbox.handle_event(event)

    def update(self, dt):
        q = self.search.text.strip().lower()
        rows = []
        for name, stats in self.app.players.items():
            plays = int(stats.get("plays", 0))
            best = int(stats.get("best_score", 0))
            last = int(stats.get("last_score", 0))
            rows.append((name, plays, best, last))

        if q:
            rows = [r for r in rows if q in r[0].lower()]

        rows.sort(key=lambda r: (r[2], r[1]), reverse=True)
        self.listbox.set_items(rows)

    def draw(self, surf):
        #-------------- IMAGE SLOT: LEADERBOARD BG -----------
        # Replace bg_leaderboard.png in ./assets/ to change this background.
        draw_bg_or_color(surf, BG_LEADERBOARD, (16, 16, 20))

        self.back.draw(surf)

        draw_text(surf, "Leaderboard", FONT_BIG, 60, 70)
        draw_text(surf, "All players who have used the game", FONT_SMALL, 60, 135, (200,200,210))
        self.search.draw(surf)

        header = pygame.Rect(60, 150, W-120, 28)
        pygame.draw.rect(surf, (35,35,42), header, border_radius=10)
        draw_text(surf, "NAME", FONT_SMALL, 75, 154, (200,200,210))
        draw_text(surf, "PLAYS", FONT_SMALL, 450, 154, (200,200,210))
        draw_text(surf, "BEST", FONT_SMALL, 600, 154, (200,200,210))
        draw_text(surf, "LAST", FONT_SMALL, 740, 154, (200,200,210))

        def render_row(s, r, i, item):
            name, plays, best, last = item
            mx, my = pygame.mouse.get_pos()
            hover = r.collidepoint(mx, my)
            if hover:
                pygame.draw.rect(s, (45,45,55), r)

            col = (255,220,120) if name == self.app.username else (235,235,235)
            s.blit(FONT_SMALL.render(name, True, col), (r.left+15, r.top+6))
            s.blit(FONT_SMALL.render(str(plays), True, (235,235,235)), (r.left+390, r.top+6))
            s.blit(FONT_SMALL.render(str(best), True, (235,235,235)), (r.left+540, r.top+6))
            s.blit(FONT_SMALL.render(str(last), True, (235,235,235)), (r.left+680, r.top+6))

        self.listbox.draw(surf, render_row)

#-------------- SCENE: GAME (PLACEHOLDER) -----------
class GameScene:
    def __init__(self, app):
        self.app = app
        self.home = Button((30, 30, 160, 45), "Exit to Home")
        self.score = 0
        self.t = 0.0

    def handle_event(self, event):
        kb = self.app.get_keybinds()
        if self.home.clicked(event):
            self.app.scene = HomeScene(self.app)
            return

        if event.type == pygame.KEYDOWN:
            if event.key == kb.get("pause", pygame.K_ESCAPE):
                self.app.scene = HomeScene(self.app)
                return

            if event.key == pygame.K_RETURN:
                self.app.record_play(self.score)
                self.app.scene = HomeScene(self.app)

    def update(self, dt):
        self.t += dt
        self.score = int(self.t * 100)

    def draw(self, surf):
        #-------------- IMAGE SLOT: GAME BG -----------
        # Replace bg_game.png in ./assets/ to change this placeholder background.
        draw_bg_or_color(surf, BG_GAME, (10, 12, 16))

        self.home.draw(surf)
        draw_text(surf, "GAME PLACEHOLDER", FONT_BIG, 60, 120)
        draw_text(surf, f"User: {self.app.username}", FONT, 60, 210, (200,200,210))
        draw_text(surf, f"Score: {self.score}", FONT, 60, 260, (200,200,210))
        draw_text(surf, "Press ENTER to finish run (updates leaderboard)", FONT_SMALL, 60, 330, (200,200,210))
        draw_text(surf, "Press your Pause key (default ESC) to return", FONT_SMALL, 60, 360, (200,200,210))

#-------------- MAIN -----------
if __name__ == "__main__":
    App().run()