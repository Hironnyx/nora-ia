"""
Module de synthèse et de reconnaissance vocale haute fidélité pour Nora (J.A.R.V.I.S. Class).
- Profils vocaux neuronaux calibrés (Nora Exécutive, Nora J.A.R.V.I.S., Nora Studio, Nora Cyber Tech)
- Pipeline de mastering audio studio broadcast (dé-clic, micro-fondu 5ms, normalisation crête -1.5 dBFS)
- Cache audio LRU multi-profils (0 ms de latence sur les répliques fréquentes)
- Détection automatique du vrai microphone actif (évite les périphériques muets)
"""
import os
import sys
import time
import asyncio
import threading
import subprocess
import queue
from pathlib import Path
import pygame
import edge_tts
import speech_recognition as sr
import pyaudio
import numpy as np

import memory_manager
import nora_audio_cache

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent

AUDIO_DIR = (BASE_DIR / "temp_audio").resolve()
AUDIO_DIR.mkdir(exist_ok=True)

try:
    pygame.mixer.init()
except Exception as e:
    print(f"Avertissement audio: {e}")

_is_speaking = False
_cached_mic_index = None

def _find_ffmpeg() -> str:
    """Localise l'exécutable ffmpeg avec fallbacks multiples."""
    candidates = [
        BASE_DIR / "ffmpeg.exe",
        Path(sys.executable).parent / "ffmpeg.exe",
        Path(sys.executable).parent / "Scripts" / "ffmpeg.exe",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    return "ffmpeg"

def _master_audio_pcm(input_path: Path, output_wav: Path) -> Path:
    """
    Pipeline de mastering audio studio broadcast pour Nora :
    1. Décodage vers PCM 16-bit 44.1kHz mono via ffmpeg
    2. Micro-fondu de 5ms en entrée et sortie pour supprimer les clics numériques
    3. Normalisation crête à -1.5 dBFS (niveau broadcast optimal, ni trop fort ni trop faible)
    4. Exportation WAV 16-bit ultra-compatible winsound
    """
    ffmpeg_exe = _find_ffmpeg()
    raw_wav = output_wav.with_name(f"{output_wav.stem}_raw.wav")

    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
    cmd = [
        str(ffmpeg_exe), "-y", "-i", str(input_path),
        "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1",
        str(raw_wav)
    ]
    try:
        subprocess.run(cmd, capture_output=True, creationflags=flags)
    except Exception as e:
        print(f"⚠️ [VoiceMastering] Erreur ffmpeg : {e}")
        return input_path

    if not raw_wav.exists() or raw_wav.stat().st_size < 500:
        return input_path

    try:
        import soundfile as sf
        data, samplerate = sf.read(str(raw_wav))
        if data.ndim > 1:
            data = data.mean(axis=1)

        # 5ms fade-in / fade-out
        fade_len = int(samplerate * 0.005)
        if len(data) > fade_len * 2:
            fade_in = np.linspace(0.0, 1.0, fade_len)
            fade_out = np.linspace(1.0, 0.0, fade_len)
            data[:fade_len] *= fade_in
            data[-fade_len:] *= fade_out

        # Peak normalization à -1.5 dBFS (0.84)
        peak = np.max(np.abs(data))
        if peak > 0:
            data = data * (0.84 / peak)

        sf.write(str(output_wav), data, samplerate, subtype='PCM_16')
        try:
            raw_wav.unlink(missing_ok=True)
        except Exception:
            pass
        return output_wav
    except Exception as e:
        print(f"⚠️ [VoiceMastering] Fallback post-processing : {e}")
        return raw_wav

def get_active_microphone_index() -> int:
    """Scanne et trouve automatiquement le microphone physique actif avec un signal réel."""
    global _cached_mic_index
    if _cached_mic_index is not None:
        return _cached_mic_index

    p = pyaudio.PyAudio()
    best_idx = None
    best_rms = 0.0

    for idx in range(p.get_device_count()):
        try:
            info = p.get_device_info_by_host_api_device_index(0, idx)
            if info['maxInputChannels'] > 0:
                name = info['name'].lower()
                rate = int(info['defaultSampleRate'])
                stream = p.open(format=pyaudio.paInt16, channels=1, rate=rate, input=True, input_device_index=idx, frames_per_buffer=1024)
                data = stream.read(1024, exception_on_overflow=False)
                stream.stop_stream()
                stream.close()
                samples = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(samples.astype(np.float32)**2))

                # Préférer les vrais micros aux sorties virtuelles
                if rms > best_rms and "output" not in name:
                    best_rms = rms
                    best_idx = idx
        except Exception:
            pass

    p.terminate()

    # Si rien de net n'est trouvé, fallback sur l'index 2 (Yamaha AG06/AG03) ou 0
    if best_idx is None or best_rms < 1.0:
        best_idx = 2

    _cached_mic_index = best_idx
    print(f"🎙️ Microphone sélectionné automatiquement : Index {best_idx}")
    return best_idx

async def _generate_audio_async(text: str, output_path: Path, profile_id: str = None):
    profile = memory_manager.get_voice_profile_info(profile_id)
    voice_name = profile.get("voice", "fr-FR-DeniseNeural")
    rate = profile.get("rate", "+2%")
    pitch = profile.get("pitch", "-1Hz")
    communicate = edge_tts.Communicate(text, voice_name, rate=rate, pitch=pitch)
    await communicate.save(str(output_path))

def cleanup_stale_audio():
    """Nettoie les fichiers audio temporaires orphelins de plus de 5 minutes au démarrage."""
    try:
        now = time.time()
        for f in AUDIO_DIR.glob("speech_*.*"):
            try:
                if now - f.stat().st_mtime > 300:
                    f.unlink()
            except Exception:
                pass
    except Exception:
        pass

cleanup_stale_audio()

_speech_queue = queue.Queue()
_speech_worker_thread = None

def _speech_worker_loop():
    global _is_speaking
    while True:
        try:
            item = _speech_queue.get()
            if item is None:
                break
            text, on_start, on_end, done_event = item
            _is_speaking = True

            profile_id = memory_manager.get_voice_profile()

            # 1. Vérification dans le cache audio studio instantané (0 ms de latence)
            try:
                cached_audio = nora_audio_cache.get_cached_audio(text, profile_id)
                if cached_audio and cached_audio.exists():
                    if on_start:
                        try:
                            on_start()
                        except Exception:
                            pass
                    if sys.platform == "win32":
                        try:
                            import winsound
                            winsound.PlaySound(str(cached_audio), winsound.SND_FILENAME)
                        except Exception:
                            pass
                    if on_end:
                        try:
                            on_end()
                        except Exception:
                            pass
                    if done_event:
                        done_event.set()
                    _is_speaking = False
                    continue
            except Exception:
                pass

            audio_file = AUDIO_DIR / f"speech_{int(time.time()*1000)}.mp3"
            final_audio = audio_file

            try:
                asyncio.run(_generate_audio_async(text, audio_file, profile_id))

                if memory_manager.is_voice_cloning_enabled():
                    try:
                        import voice_cloning
                        final_audio = voice_cloning.convert_to_zero_two(audio_file)
                    except Exception:
                        final_audio = audio_file

                # Mastering audio studio broadcast (dé-clic, micro-fondu 5ms, normalisation crête -1.5 dBFS)
                wav_file = audio_file.with_suffix(".wav")
                mastered_wav = _master_audio_pcm(final_audio, wav_file)
                if mastered_wav.exists() and mastered_wav.stat().st_size > 1000:
                    final_audio = mastered_wav

                # Enregistrement automatique dans le cache audio sous ce profil
                if final_audio and final_audio.exists():
                    try:
                        nora_audio_cache.save_cached_audio(text, final_audio, profile_id)
                    except Exception:
                        pass

                if on_start:
                    try:
                        on_start()
                    except Exception:
                        pass

                # Lecture audio ultra-fiable sans blocage
                played_via_winsound = False
                if sys.platform == "win32" and final_audio.suffix.lower() == ".wav" and final_audio.exists():
                    try:
                        import winsound
                        winsound.PlaySound(str(final_audio), winsound.SND_FILENAME)
                        played_via_winsound = True
                    except Exception as we:
                        print(f"Avertissement winsound : {we}")
                        played_via_winsound = False

                if not played_via_winsound:
                    if not pygame.mixer.get_init():
                        try:
                            pygame.mixer.init()
                        except Exception:
                            pass

                    pygame.mixer.music.load(str(final_audio))
                    pygame.mixer.music.play()

                    t_start = time.time()
                    # Timeout de sécurité strict de 15s max pour ne jamais figer la boucle
                    while pygame.mixer.music.get_busy() and (time.time() - t_start < 15.0):
                        time.sleep(0.04)

            except Exception as e:
                print(f"Erreur de lecture vocale : {e}")
            finally:
                _is_speaking = False
                try:
                    pygame.mixer.music.unload()
                except Exception:
                    pass
                if on_end:
                    try:
                        on_end()
                    except Exception:
                        pass
                if done_event:
                    done_event.set()

                # Nettoyage immédiat du fichier audio temporaire non-caché
                try:
                    if audio_file.exists():
                        os.remove(str(audio_file))
                    if final_audio != audio_file and final_audio.exists() and "audio_cache" not in str(final_audio):
                        os.remove(str(final_audio))
                except Exception:
                    pass

                _speech_queue.task_done()

        except Exception as e:
            print(f"Erreur worker vocal : {e}")
            _is_speaking = False
            time.sleep(0.1)

def _ensure_speech_worker():
    global _speech_worker_thread
    if _speech_worker_thread is None or not _speech_worker_thread.is_alive():
        _speech_worker_thread = threading.Thread(target=_speech_worker_loop, daemon=True)
        _speech_worker_thread.start()

def speak(text: str, on_start=None, on_end=None, blocking: bool = False):
    """Fait parler Nora à voix haute avec sérialisation sans collision sonore."""
    if not text or not text.strip():
        return
    clean_text = text.replace("```", "").replace("#", "").replace("*", "").replace("`", "")
    if len(clean_text) > 400:
        clean_text = clean_text[:400] + "... et voilà !"

    _ensure_speech_worker()

    done_event = threading.Event() if blocking else None
    _speech_queue.put((clean_text, on_start, on_end, done_event))

    if blocking:
        done_event.wait()

def listen_microphone(timeout: int = 5, phrase_time_limit: int = 10) -> str:
    """Écoute le microphone actif et retranscrit les paroles de l'utilisateur."""
    mic_idx = get_active_microphone_index()
    r = sr.Recognizer()
    r.energy_threshold = 200
    r.dynamic_energy_threshold = True

    try:
        with sr.Microphone(device_index=mic_idx) as source:
            r.adjust_for_ambient_noise(source, duration=0.6)
            print("🎙️ Nora vous écoute sur le bon micro...")
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        print("🧠 Transcription en cours...")
        text = r.recognize_google(audio, language="fr-FR")
        return text.strip()
    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        return ""
    except Exception as e:
        print(f"Erreur micro : {e}")
        return ""

def is_speaking():
    return _is_speaking or not _speech_queue.empty()

def get_voice_profile() -> str:
    """Retourne l'identifiant du profil vocal actif."""
    return memory_manager.get_voice_profile()

def set_voice_profile(profile_id: str):
    """Bascule immédiatement vers un nouveau profil vocal."""
    memory_manager.set_voice_profile(profile_id)
    info = memory_manager.get_voice_profile_info(profile_id)
    print(f"🎙️ [VoiceEngine] Profil vocal actif : {info['name']} ({info['voice']})")

def get_available_profiles() -> dict:
    """Retourne la liste des profils vocaux disponibles."""
    return memory_manager.VOICE_PROFILES

def test_voice(profile_id: str = None, text: str = None):
    """Effectue un test vocal immédiat à haute voix."""
    if profile_id:
        set_voice_profile(profile_id)
    info = memory_manager.get_voice_profile_info()
    test_phrase = text or f"Bonjour Maverick. Tous les sous-systèmes de Nora sont opérationnels. Profil vocal : {info['name']}."
    speak(test_phrase, blocking=True)

