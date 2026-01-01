"""Simple sound manager for Mines Arena.

Provides background music playback and short sound effects. Uses pygame.mixer when
available; falls back to winsound on Windows or no-op with logs otherwise.

Usage:
    from sound import SoundManager
    sm = SoundManager()
    sm.play_music('assets/music/background.wav')
    sm.play_effect('click')

Install (recommended):
    pip install pygame

If pygame is not installed and you're on Windows, the module will use winsound.
"""

import os
import threading
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

try:
    import pygame
    _HAS_PYGAME = True
except Exception:
    _HAS_PYGAME = False

try:
    import winsound
    _HAS_WINSOUND = True
except Exception:
    _HAS_WINSOUND = False

# Prefer winsound on Windows when available; otherwise use pygame if present.
if _HAS_WINSOUND:
    _BACKEND = 'winsound'
elif _HAS_PYGAME:
    _BACKEND = 'pygame'
else:
    _BACKEND = None

class SoundManager:
    def __init__(self, music_file=None, effects_dir=None, volume=0.6):
        self.music_file = music_file
        self.effects_dir = effects_dir
        self.volume = volume
        self.effects = {}  # name -> pygame.mixer.Sound or filepath
        self._music_playing = False

        # Initialize backend
        if _BACKEND == 'pygame':
            try:
                pygame.mixer.init()
                pygame.mixer.set_num_channels(16)
            except Exception as e:
                logger.warning('pygame.mixer init failed: %s', e)
                self._init_failed = True
            else:
                self._init_failed = False
        else:
            # winsound requires no init; or no backend available
            self._init_failed = False

    def play_music(self, music_file=None, loop=True):
        """Play background music. Loop if loop=True."""
        path = music_file or self.music_file
        if not path:
            logger.info('No music file provided')
            return
        if _BACKEND == 'pygame' and not self._init_failed:
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play(-1 if loop else 0)
                self._music_playing = True
                logger.info('Playing music (pygame): %s', path)
            except Exception as e:
                logger.exception('Failed to play music with pygame: %s', e)
        elif _BACKEND == 'winsound':
            try:
                flags = winsound.SND_FILENAME | winsound.SND_ASYNC
                if loop:
                    flags |= winsound.SND_LOOP
                winsound.PlaySound(path, flags)
                self._music_playing = True
                logger.info('Playing music (winsound): %s', path)
            except Exception as e:
                logger.exception('Failed to play music with winsound: %s', e)
        else:
            logger.info('Sound not available; would play: %s', path)

    def stop_music(self):
        if _BACKEND == 'pygame' and not self._init_failed:
            try:
                pygame.mixer.music.stop()
                self._music_playing = False
            except Exception:
                pass
        elif _BACKEND == 'winsound':
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
                self._music_playing = False
            except Exception:
                pass
        else:
            logger.info('stop_music() called')

    def set_volume(self, vol: float):
        self.volume = max(0.0, min(1.0, float(vol)))
        if _BACKEND == 'pygame' and not self._init_failed:
            pygame.mixer.music.set_volume(self.volume)

    def preload_effect(self, name, filepath):
        """Register an effect by name and optionally preload it."""
        if not os.path.isfile(filepath):
            logger.warning('Effect file not found: %s', filepath)
            self.effects[name] = filepath
            return
        if _BACKEND == 'pygame' and not self._init_failed:
            try:
                snd = pygame.mixer.Sound(filepath)
                self.effects[name] = snd
            except Exception as e:
                logger.exception('Failed to load effect: %s', e)
                self.effects[name] = filepath
        else:
            self.effects[name] = filepath

    def play_effect(self, name, fallback_file=None):
        """Play a short effect previously preloaded with `preload_effect`.
        If the name is not found, optionally play `fallback_file` path.
        """
        item = self.effects.get(name)
        if item is None and fallback_file:
            item = fallback_file
        if item is None:
            logger.info('play_effect: no effect for %s', name)
            return

        if _BACKEND == 'pygame' and not self._init_failed and isinstance(item, pygame.mixer.Sound):
            try:
                item.play()
            except Exception:
                logger.exception('Failed to play effect via pygame')
        elif _BACKEND == 'winsound' and isinstance(item, str) and os.path.isfile(item):
            try:
                winsound.PlaySound(item, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                logger.exception('Failed to play effect via winsound')
        elif isinstance(item, str) and os.path.isfile(item):
            # No sound backend; log intended play
            logger.info('Would play effect file: %s', item)
        else:
            logger.info('Effect item not playable: %s', item)


if __name__ == '__main__':
    # Quick demo (doesn't ship WAV files with repo)
    sm = SoundManager()
    print('pygame available:', _HAS_PYGAME)
    print('winsound available:', _HAS_WINSOUND)
    # Example usage - update paths to actual WAV/OGG files in your project
    demo_music = os.path.join('assets', 'music', 'background.wav')
    demo_click = os.path.join('assets', 'fx', 'click.wav')
    if os.path.isfile(demo_music):
        sm.play_music(demo_music)
    else:
        print('Demo music not found:', demo_music)
    if os.path.isfile(demo_click):
        sm.preload_effect('click', demo_click)
        sm.play_effect('click')
    else:
        print('Demo effect not found:', demo_click)
    # Keep running for a few seconds if music started
    try:
        import time
        time.sleep(3)
    except KeyboardInterrupt:
        pass
    sm.stop_music()
