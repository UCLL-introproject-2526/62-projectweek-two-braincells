import pygame
import os

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class SoundManager:
    def __init__(self):
        self.sounds = {
            "jump": pygame.mixer.Sound(os.path.join(BASE_DIR, "jumping.mp3")),
            "hit": pygame.mixer.Sound(os.path.join(BASE_DIR, "trying_to_eat.mp3")),
            "eaten": pygame.mixer.Sound(os.path.join(BASE_DIR, "successfully_eating.mp3")),
            "walk": pygame.mixer.Sound(os.path.join(BASE_DIR, "walk.mp3")),
            "gameover": pygame.mixer.Sound(os.path.join(BASE_DIR, "game_over.mp3")),
        }

        self.walking = False

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def play_loop(self, name):
        if name in self.sounds:
            self.sounds[name].play(-1)

    def stop(self, name):
        if name in self.sounds:
            self.sounds[name].stop()

    def play_music(self):
        pygame.mixer.music.load(os.path.join(BASE_DIR, "main_menu.mp3"))
        pygame.mixer.music.play(-1)

    def stop_music(self):
        pygame.mixer.music.stop()
