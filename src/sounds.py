import pygame
import os

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUND_DIR = os.path.join(BASE_DIR, "..", "assets", "sound")

class SoundManager:
    def __init__(self):
        self.sounds = {
            "jump": pygame.mixer.Sound(os.path.join(SOUND_DIR, "jumping.mp3")),
            "hit": pygame.mixer.Sound(os.path.join(SOUND_DIR, "trying_to_eat.mp3")),
            "eaten": pygame.mixer.Sound(os.path.join(SOUND_DIR, "successfully_eating.mp3")),
            "walk": pygame.mixer.Sound(os.path.join(SOUND_DIR, "walk.mp3")),
            "gameover": pygame.mixer.Sound(os.path.join(SOUND_DIR, "game_over.mp3")),
            "flashsound": pygame.mixer.Sound(os.path.join(SOUND_DIR, "FAHH.mp3")),
            "ring": pygame.mixer.Sound(os.path.join(SOUND_DIR, "ringtone.mp3")),
        }

    def play(self, name, volume=None):
        if name in self.sounds:
            if volume is not None:
                self.sounds[name].set_volume(volume)
            self.sounds[name].play()

    def play_music(self):
        pygame.mixer.music.load(os.path.join(SOUND_DIR, "background_music.mp3"))
        pygame.mixer.music.play(-1)

    def stop_music(self):
        pygame.mixer.music.stop()

