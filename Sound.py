import pygame
import os
from utilities import load_sound
class SoundManager:
    def __init__(self):
        # Initialize the pygame mixer if it hasn't been already
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        # Dictionary to store loaded Sound objects (for SFX)
        self.sfx_dict = {}
        
        # Dictionary to store music file paths (music is streamed, not pre-loaded into memory)
        self.music_dict = {}

    # --- Sound Effects (SFX) Methods ---
    
    def load_sfx(self, name, filename):
        """Loads a sound effect into memory using the load_sound helper."""
        try:
            # We just pass the filename (e.g., "jump.wav") to the helper
            self.sfx_dict[name] = load_sound(filename)
        except FileNotFoundError as e:
            # If load_sound fails, it passes the error message up to here
            print(f"Warning: {e}")

    def play_sfx(self, name, volume=1.0):
        """Plays a loaded sound effect."""
        if name in self.sfx_dict:
            sound = self.sfx_dict[name]
            sound.set_volume(volume)
            sound.play()
        else:
            print(f"Warning: SFX '{name}' not loaded.")

    # --- Background Music (BGM) Methods ---

    def load_music(self, name, filepath):
        """Registers a background music track."""
        if os.path.exists(filepath):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            BASE_DIR = os.path.abspath(
                os.path.join(script_dir, "Assets", "Sounds", "Music")
            )
            final_path = os.path.join(BASE_DIR, filepath)
            self.music_dict[name] = final_path
        else:
            print(f"Warning: Music file not found at {final_path}")

    def play_music(self, name, loops=-1, volume=1.0, fade_ms=0):
        """Plays a registered music track. loops=-1 plays indefinitely."""
        if name in self.music_dict:
            pygame.mixer.music.load(self.music_dict[name])
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)
        else:
            print(f"Warning: Music '{name}' not loaded.")

    def stop_music(self, fade_ms=0):
        """Stops the currently playing music."""
        if fade_ms > 0:
            pygame.mixer.music.fadeout(fade_ms)
        else:
            pygame.mixer.music.stop()

    def pause_music(self):
        """Pauses the background music."""
        pygame.mixer.music.pause()

    def unpause_music(self):
        """Resumes paused background music."""
        pygame.mixer.music.unpause()

    def set_music_volume(self, volume):
        """Dynamically adjusts the music volume (0.0 to 1.0)."""
        pygame.mixer.music.set_volume(volume)