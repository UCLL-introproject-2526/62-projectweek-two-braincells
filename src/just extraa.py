import os
import sys
import json
import random
import pygame 
import subprocess
import math

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GAME_PATH = os.path.join(BASE_DIR, "app.py")

pygame.init()
pygame.mixer.init()
pygame.mixer.music.load("assets/sound/main_menu.mp3") 
pygame.mixer.music.set_volume(1.0)
pygame.mixer.music.play(-1)  # loop forever

#-------------- CONFIG / CONSTANTS -----------

W, H = 1000, 650
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Fly Feast")
clock = pygame.time.Clock()

FONT_BIG = pygame.font.Font(None, 64)
FONT = pygame.font.Font(None, 40)
FONT_SMALL = pygame.font.Font(None, 28)

FONT_UI = pygame.font.Font(None, 32)       # Labels & buttons
FONT_UI_SMALL = pygame.font.Font(None, 22) # Helper text

PLAYERS_PATH = "players.json"
SETTINGS_PATH = "settings.json"

DEFAULT_SETTINGS = {
    "keybinds": {  
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
ASSETS_DIR = os.path.join(BASE_DIR, "..", "assets")

def safe_load_image(path, size=None, alpha=True, stretch=False):
    """
    Load an image safely.

    - max_size: tuple (width, height) to limit the size
    - stretch: if True, scale exactly to max_size (for backgrounds)
               if False, preserve aspect ratio (for icons/buttons)
    """
    if not os.path.exists(path):
        return None

    img = pygame.image.load(path)
    img = img.convert_alpha() if alpha else img.convert()
    
    if size is not None:
        if stretch:
            img = pygame.transform.smoothscale(img, size)
        else:
            w, h = img.get_size()
            max_w, max_h = size
            scale = min(max_w / w, max_h / h)
            new_size = (int(w * scale), int(h * scale))
            img = pygame.transform.smoothscale(img, new_size)

    return img


BG_VIEW = safe_load_image(os.path.join(ASSETS_DIR, "background.png"), (W,H), alpha=False)
ICON_PLAY = safe_load_image(os.path.join(ASSETS_DIR, "ui", "play.png"), (90,90))
ICON_SETTINGS = safe_load_image(os.path.join(ASSETS_DIR, "ui", "settings.png"), (90,90))
FLY_IMG = safe_load_image(os.path.join(ASSETS_DIR, "sprites", "fly", "fly.png"), (40,40))
FRONTPAGE_BG = safe_load_image(os.path.join(ASSETS_DIR, "sprites", "frontpagebackground.png"), (W, H), alpha=False)
USERNAME_BG_IMG = safe_load_image(os.path.join(ASSETS_DIR, "ui", "username_placeholder.png"), size=(440,46),stretch=True)
PLAYERNAME_BG_IMG = safe_load_image(
    os.path.join(ASSETS_DIR, "ui", "your_name.png"),
    size=(300, 50),  # pick a size that fits nicely over the name
    stretch=True      # make sure it fits exactly
)
#-------------- HELPERS -----------
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
    if bg_img is not None:
        surf.blit(bg_img, (0, 0))
    else:
        surf.fill(fallback_color)

# 🔴 ADDED START: leaderboard helper
def get_leaderboard_rows(players: dict, limit=8):
    rows = []
    for name, stats in players.items():
        plays = int(stats.get("plays", 0))
        best = int(stats.get("best_score", 0))
        last = int(stats.get("last_score", 0))
        rows.append((name, plays, best, last))
    rows.sort(key=lambda r: (r[2], r[1]), reverse=True)  # best desc, then plays desc
    return rows[:limit]
# 🔴 ADDED END

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
        txt = FONT_UI.render(self.label, True, (240,240,240))
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

class ImageButton:
    def __init__(self, image, center, float_amp=6, float_speed=1.2):
        self.base_image = image
        self.image = image
        self.base_center = pygame.Vector2(center)
        self.rect = image.get_rect(center=center)

        self.hover_scale = 1.08
        self.float_amp = float_amp
        self.float_speed = float_speed
        self.time = random.uniform(0, 10)  # desync buttons slightly

    def update(self, dt):
        self.time += dt * self.float_speed
        offset_y = math.sin(self.time) * self.float_amp
        self.rect.center = (
            self.base_center.x,
            self.base_center.y + offset_y
        )

    def draw(self, surf):
        mx, my = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mx, my)

        if hover:
            w, h = self.base_image.get_size()
            scaled = pygame.transform.smoothscale(
                self.base_image,
                (int(w * self.hover_scale), int(h * self.hover_scale))
            )
            self.image = scaled
            self.rect = self.image.get_rect(center=self.rect.center)
        else:
            self.image = self.base_image

        surf.blit(self.image, self.rect.topleft)

    def clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


class Slider:
    def __init__(self, rect, min_val=0.0, max_val=1.0, value=0.5):
        self.rect = pygame.Rect(rect)
        self.min = min_val
        self.max = max_val
        self.value = value
        self.dragging = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        if self.dragging and event.type == pygame.MOUSEMOTION:
            rel_x = clamp(event.pos[0]-self.rect.left,0,self.rect.width)
            self.value = self.min + (rel_x/self.rect.width)*(self.max-self.min)

    def draw(self, surf):
        pygame.draw.rect(surf,(80,80,90),self.rect,border_radius=8)
        handle_x = int(self.rect.left + (self.value-self.min)/(self.max-self.min)*self.rect.width)
        pygame.draw.circle(surf,(200,200,200),(handle_x,self.rect.centery),12)

#-------------- APP / DATA MODEL -----------
class App:
    def __init__(self):
        self.settings = self.load_json(SETTINGS_PATH, DEFAULT_SETTINGS)
        self.players = self.load_json(PLAYERS_PATH, {}) 
        self.username = None
        self.apply_audio_settings()
        self.scene = UsernameScene(self)

    def load_json(self, path, fallback):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return fallback
        return fallback

    def save_json(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def apply_audio_settings(self):
        s = self.settings["sound"]
        if s.get("muted"):
            pygame.mixer.music.set_volume(0.0)
        else:
            pygame.mixer.music.set_volume(float(s.get("music",0.5)))

    def get_keybinds(self):
        kb = self.settings["keybinds"]
        return {action: keyname_to_keyconst(name) for action, name in kb.items()}

    def ensure_player(self, name: str):
        if name not in self.players:
            self.players[name] = {"plays":0,"best_score":0,"last_score":0}
            self.save_json(PLAYERS_PATH, self.players)

    def record_play(self, score:int):
        if not self.username: return
        self.ensure_player(self.username)
        p = self.players[self.username]
        p["plays"] +=1
        p["last_score"] = int(score)
        p["best_score"] = max(int(p.get("best_score",0)), int(score))
        self.save_json(PLAYERS_PATH, self.players)

    def save_settings(self):
        self.save_json(SETTINGS_PATH, self.settings)
        self.apply_audio_settings()

    def run(self):
        running = True
        while running:
            dt = clock.tick(60)/1000.0
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

#-------------- SCENES -----------
class UsernameScene:
    def __init__(self, app):
        self.app = app
        self.name_entry = TextInput((W//2-220, 300, 440,46),"Enter username")

    def handle_event(self,event):
        enter = self.name_entry.handle_event(event)
        if enter == "enter":
            name = self.name_entry.text.strip()
            if name:
                self.app.username = name
                self.app.ensure_player(name)
                self.app.scene = HomeScene(self.app)

    def update(self,dt): pass
    def draw(self,surf):
        draw_bg_or_color(surf, FRONTPAGE_BG, (16,16,20))
        draw_text(surf,"Fly Feast",FONT_BIG,W//2-150,100)
        self.name_entry.draw(surf)

class HomeScene:
    def __init__(self, app):
        self.app = app
        self.btn_play = ImageButton(
        ICON_PLAY,
        center=(W // 2 - 120, 260)
        )
        self.btn_settings = ImageButton(
        ICON_SETTINGS,
        center=(W // 2 + 120, 260)
        )
        self.username_time = 0.0  # initialize the rainbow/floating time
        self.username_color = (255, 255, 255) 
    def handle_event(self,event):
        if self.btn_play.clicked(event):
            pygame.mixer.music.fadeout(500)
            subprocess.Popen([sys.executable, GAME_PATH])
            pygame.quit()
            sys.exit()
                    
        if self.btn_settings.clicked(event):
            self.app.scene = SettingsScene(self.app)


    def update(self,dt): pass

    def update(self, dt):
        self.btn_play.update(dt)
        self.btn_settings.update(dt)
        r = int((math.sin(self.username_time) + 1) * 127)
        g = int((math.sin(self.username_time + 2) + 1) * 127)
        b = int((math.sin(self.username_time + 4) + 1) * 127)
        self.username_color = (r, g, b)
        self.username_time += dt
        r = int((math.sin(self.username_time) + 1) * 127)
        g = int((math.sin(self.username_time + 2) + 1) * 127)
        b = int((math.sin(self.username_time + 4) + 1) * 127)
        self.username_color = (r, g, b)


    def draw(self, surf):
        draw_bg_or_color(surf, FRONTPAGE_BG, (16, 16, 20))
        
        # Draw title
        title = "Fly Feast"
        shadow = FONT_BIG.render(title, True, (0, 0, 0))
        text = FONT_BIG.render(title, True, (255, 255, 255))
        surf.blit(shadow, (W//2 - text.get_width()//2 + 3, 73))
        surf.blit(text, (W//2 - text.get_width()//2, 70))

        # Draw username background image (brown block)
        if PLAYERNAME_BG_IMG:
            bg_rect = PLAYERNAME_BG_IMG.get_rect(center=(W//2, 165))
            surf.blit(PLAYERNAME_BG_IMG, bg_rect.topleft)
        else:
            bg_rect = pygame.Rect(0, 0, 300, 50)
            bg_rect.center = (W//2, 165)
            pygame.draw.rect(surf, (139,69,19), bg_rect, border_radius=12)  # fallback brown color

        # Render username text
        username_text = f"   Hi: {self.app.username}"
        badge = FONT_SMALL.render(username_text, True, (0, 255, 0))  # bright green text

        # Create padding for the text inside the brown block
        padding_x = 20  # horizontal padding so text not too close to edges
        padding_y = 6   # vertical padding

        # Calculate the max width and height for the text inside the background minus padding
        max_width = bg_rect.width - 2 * padding_x
        max_height = bg_rect.height - 2 * padding_y

        # If text is too wide, scale it down proportionally
        if badge.get_width() > max_width:
            scale_factor = max_width / badge.get_width()
            new_width = int(badge.get_width() * scale_factor)
            new_height = int(badge.get_height() * scale_factor)
            badge = pygame.transform.smoothscale(badge, (new_width, new_height))

        # Position text inside the bg_rect with padding
        text_pos = (bg_rect.left + padding_x, bg_rect.top + (bg_rect.height - badge.get_height()) // 2)

        # Blit text inside the brown block
        surf.blit(badge, text_pos)

        # Draw buttons last so they stay on top
        self.btn_play.draw(surf)
        self.btn_settings.draw(surf)

    # ... your other draw logic ...


        # ...rest of your draw code (leaderboard etc.)

        # Rest of your leaderboard drawing here (unchanged) ...



# 🔴 ADDED START: Leaderboard panel on the Home/frontpage (no overlap)
        # Placed BELOW the buttons row: buttons occupy y ~ 220..320, so panel starts at y=360.
        panel = pygame.Rect(60, 360, W - 120, 250)

        panel_bg = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
        panel_bg.fill((0, 0, 0, 140))  # translucent overlay
        surf.blit(panel_bg, panel.topleft)
        pygame.draw.rect(surf, (160, 160, 180), panel, 2, border_radius=14)

        draw_text(surf, "Leaderboard", FONT, panel.left + 15, panel.top + 12)

        header_y = panel.top + 55
        draw_text(surf, "NAME", FONT_SMALL, panel.left + 15, header_y, (200, 200, 210))
        draw_text(surf, "PLAYS", FONT_SMALL, panel.left + 340, header_y, (200, 200, 210))
        draw_text(surf, "BEST",  FONT_SMALL, panel.left + 460, header_y, (200, 200, 210))
        draw_text(surf, "LAST",  FONT_SMALL, panel.left + 580, header_y, (200, 200, 210))

        rows = get_leaderboard_rows(self.app.players, limit=7)
        y = header_y + 28
        line_h = 26

        if not rows:
            draw_text(surf, "No players yet.", FONT_SMALL, panel.left + 15, y, (220, 220, 230))
        else:
            for i, (name, plays, best, last) in enumerate(rows, start=1):
                is_me = (name == self.app.username)
                col = (255, 220, 120) if is_me else (235, 235, 235)

                draw_text(surf, f"{i:>2}. {name}", FONT_SMALL, panel.left + 15, y, col)
                draw_text(surf, str(plays), FONT_SMALL, panel.left + 350, y, (235, 235, 235))
                draw_text(surf, str(best),  FONT_SMALL, panel.left + 470, y, (235, 235, 235))
                draw_text(surf, str(last),  FONT_SMALL, panel.left + 590, y, (235, 235, 235))

                y += line_h
                if y > panel.bottom - 20:
                    break
        # 🔴 ADDED END

class GameScene:
    def __init__(self, app):
        self.app = app
        self.btn_home = Button((30,30,180,45),"Main Menu")
        self.score = 0
        self.t = 0.0
        self.flies = []
        self.spawn_flies(10)

    def spawn_flies(self,n):
        self.flies = []
        for _ in range(n):
            x = random.randint(50,W-50)
            y = random.randint(100,H-50)
            dx = random.choice([-1,1])*random.uniform(50,150)
            dy = random.choice([-1,1])*random.uniform(50,150)
            self.flies.append({"pos":[x,y],"vel":[dx,dy]})

    def handle_event(self,event):
        kb = self.app.get_keybinds()
        if self.btn_home.clicked(event):
            self.app.scene = HomeScene(self.app)
            return
        if event.type == pygame.KEYDOWN:
            if event.key == kb.get("pause",pygame.K_ESCAPE):
                self.app.scene = HomeScene(self.app)
            if event.key == pygame.K_RETURN:
                self.app.record_play(self.score)
                self.app.scene = HomeScene(self.app)

    def update(self,dt):
        self.t += dt
        self.score = int(self.t*100)
        for f in self.flies:
            f["pos"][0] += f["vel"][0]*dt
            f["pos"][1] += f["vel"][1]*dt
            if f["pos"][0]<0 or f["pos"][0]>W-FLY_IMG.get_width(): f["vel"][0]*=-1
            if f["pos"][1]<100 or f["pos"][1]>H-FLY_IMG.get_height(): f["vel"][1]*=-1

    def draw(self,surf):
        draw_bg_or_color(surf,BG_VIEW,(16,16,20))
        for f in self.flies: surf.blit(FLY_IMG,f["pos"])
        self.btn_home.draw(surf)
        draw_text(surf,f"User: {self.app.username}",FONT,60,550)
        draw_text(surf,f"Score: {self.score}",FONT,300,550)
        draw_text(surf,"Press ESC to return",FONT_SMALL,60,590)

class SettingsScene:
    def __init__(self, app):
        self.app = app
        self.back = Button((30,20,110,36),"Back")
        self.sliders = {
            "music": Slider((300,200,400,20),0.0,1.0,app.settings["sound"].get("music",0.5)),
            "sfx": Slider((300,250,400,20),0.0,1.0,app.settings["sound"].get("sfx",0.7))
        }
        self.key_buttons = {}
        x_start = 300
        y_start = 320
        for i,(action,key_name) in enumerate(app.settings["keybinds"].items()):
            self.key_buttons[action] = Button((x_start,y_start+i*60,200,40),human_key(keyname_to_keyconst(key_name)))
        self.awaiting_key = None
        self.mute_btn = Button((300,500,120,40),"Mute" if not app.settings["sound"].get("muted") else "Unmute")

    def handle_event(self,event):
        if self.back.clicked(event):
            self.app.save_settings()
            self.app.scene = HomeScene(self.app)
        for name, s in self.sliders.items():
            s.handle_event(event)
            self.app.settings["sound"][name] = s.value
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for action,btn in self.key_buttons.items():
                if btn.rect.collidepoint(event.pos):
                    self.awaiting_key = action
            if self.mute_btn.clicked(event):
                self.app.settings["sound"]["muted"] = not self.app.settings["sound"].get("muted",False)
                self.mute_btn.label = "Mute" if not self.app.settings["sound"]["muted"] else "Unmute"
        if self.awaiting_key and event.type == pygame.KEYDOWN:
            self.app.settings["keybinds"][self.awaiting_key] = keyconst_to_keyname(event.key)
            self.key_buttons[self.awaiting_key].label = human_key(event.key)
            self.awaiting_key = None

    def update(self,dt): pass

    def draw(self,surf):
        draw_bg_or_color(surf,BG_VIEW,(16,16,20))
        self.back.draw(surf)
        draw_text(surf,"Settings",FONT_BIG,60,70)
        draw_text(surf,"Music Volume",FONT_UI,100,190)
        self.sliders["music"].draw(surf)
        draw_text(surf,"SFX Volume",FONT_UI,100,240)
        self.sliders["sfx"].draw(surf)
        draw_text(surf,"Keybinds",FONT_UI,100,300)
        for btn in self.key_buttons.values():
            btn.draw(surf)
        self.mute_btn.draw(surf)
        draw_text(surf,"Click button to change key",FONT_UI_SMALL,520,320)

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
                if len(event.unicode)==1 and len(self.text)<18:
                    if event.unicode.isalnum() or event.unicode in ("_","-","."):
                        self.text+=event.unicode
        return None

    def draw(self, surf):
    # Draw PNG background if loaded
        if USERNAME_BG_IMG:
            surf.blit(USERNAME_BG_IMG, self.rect.topleft)
        else:
            # fallback gradient
            grad_height = self.rect.height
            for i in range(grad_height):
                c1 = pygame.Color(60, 60, 70)
                c2 = pygame.Color(40, 40, 48)
                r = c1.r + (c2.r - c1.r) * i / grad_height
                g = c1.g + (c2.g - c1.g) * i / grad_height
                b = c1.b + (c2.b - c1.b) * i / grad_height
                pygame.draw.line(surf, (int(r), int(g), int(b)), (self.rect.left, self.rect.top + i), (self.rect.right, self.rect.top + i))

        # Border with glow effect on focus
        base_border_color = pygame.Color(140, 140, 160)
        glow_color = pygame.Color(100, 200, 255) if self.active else base_border_color

        if self.active:
            glow_surf = pygame.Surface((self.rect.width + 12, self.rect.height + 12), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, glow_color, glow_surf.get_rect(), border_radius=16)
            glow_surf.set_alpha(100)
            surf.blit(glow_surf, (self.rect.left - 6, self.rect.top - 6))

        pygame.draw.rect(surf, glow_color, self.rect, 3, border_radius=12)

        # Draw the text
        shown = self.text if self.text else self.placeholder
        col = (230, 230, 255) if self.text else (140, 160, 180)
        txt = FONT_SMALL.render(shown, True, col)
        surf.blit(txt, txt.get_rect(midleft=(self.rect.left + 14, self.rect.centery)))


#-------------- MAIN -----------
if __name__=="__main__":
    App().run()