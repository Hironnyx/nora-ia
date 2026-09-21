"""
Effets sonores futuristes générés pour Nora (réveil mains-libres, confirmation, fin de mission).
"""
import os
import sys
import wave
from pathlib import Path
import numpy as np
import pygame

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent

SOUNDS_DIR = (BASE_DIR / "sound_assets").resolve()
SOUNDS_DIR.mkdir(exist_ok=True)

WAKE_FILE = SOUNDS_DIR / "wake_chime.wav"
SUCCESS_FILE = SOUNDS_DIR / "success_chime.wav"

def generate_chimes_if_missing():
    """Génère les fichiers audio d'effets s'ils ne sont pas encore présents."""
    sample_rate = 44100

    # 1. Carillon de réveil ascendant (Mi -> La -> Mi aigu)
    if not WAKE_FILE.exists():
        freqs = [659.25, 880.0, 1318.51]
        samples = []
        for f in freqs:
            t = np.linspace(0, 0.10, int(sample_rate * 0.10), False)
            env = np.exp(-12 * t)
            tone = (np.sin(2 * np.pi * f * t) + 0.2 * np.sin(4 * np.pi * f * t)) * env * 0.35
            samples.extend(tone)
        arr = (np.array(samples) * 32767).astype(np.int16)
        with wave.open(str(WAKE_FILE), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(arr.tobytes())

    # 2. Carillon de succès / accomplissement (Do -> Sol)
    if not SUCCESS_FILE.exists():
        freqs = [523.25, 659.25, 783.99, 1046.50]
        samples = []
        for f in freqs:
            t = np.linspace(0, 0.08, int(sample_rate * 0.08), False)
            env = np.exp(-10 * t)
            tone = np.sin(2 * np.pi * f * t) * env * 0.3
            samples.extend(tone)
        arr = (np.array(samples) * 32767).astype(np.int16)
        with wave.open(str(SUCCESS_FILE), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(arr.tobytes())

_cached_wake_sound = None
_cached_success_sound = None

def _get_wake_sound():
    global _cached_wake_sound
    if _cached_wake_sound is None:
        generate_chimes_if_missing()
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        _cached_wake_sound = pygame.mixer.Sound(str(WAKE_FILE))
        _cached_wake_sound.set_volume(0.6)
    return _cached_wake_sound

def _get_success_sound():
    global _cached_success_sound
    if _cached_success_sound is None:
        generate_chimes_if_missing()
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        _cached_success_sound = pygame.mixer.Sound(str(SUCCESS_FILE))
        _cached_success_sound.set_volume(0.6)
    return _cached_success_sound

def play_wake_chime():
    """Joue le carillon de réveil préchargé en RAM (0 ms d'attente)."""
    try:
        snd = _get_wake_sound()
        if snd:
            snd.play()
    except Exception as e:
        print(f"Son réveil : {e}")

def play_success_chime():
    """Joue le carillon de mission accomplie préchargé en RAM."""
    try:
        snd = _get_success_sound()
        if snd:
            snd.play()
    except Exception as e:
        print(f"Son succès : {e}")

if __name__ == "__main__":
    generate_chimes_if_missing()
    print("Sons générés avec succès !")
