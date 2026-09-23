"""
Module de synthèse et de reconnaissance vocale pour Nora.
- Détection automatique du vrai microphone actif (évite les périphériques muets comme Voicemod/NVIDIA)
- Synthèse : edge-tts avec voix ultra-réaliste française 'fr-FR-VivienneMultilingualNeural'
- Reconnaissance : SpeechRecognition avec micro actif
"""
import os
import sys
import time
import asyncio
import threading
from pathlib import Path
import pygame
import edge_tts
import speech_recognition as sr
import pyaudio
import numpy as np

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

NORA_VOICE = "fr-FR-VivienneMultilingualNeural"

try:
    pygame.mixer.init()
except Exception as e:
    print(f"Avertissement audio: {e}")

_is_speaking = False
_cached_mic_index = None

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

async def _generate_audio_async(text: str, output_path: Path):
    communicate = edge_tts.Communicate(text, NORA_VOICE)
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

import queue

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

            audio_file = AUDIO_DIR / f"speech_{int(time.time()*1000)}.mp3"
            final_audio = audio_file

            try:
                asyncio.run(_generate_audio_async(text, audio_file))

                try:
                    import voice_cloning
                    final_audio = voice_cloning.convert_to_zero_two(audio_file)
                except Exception:
                    final_audio = audio_file

                # Si le fichier est un MP3, le convertir en WAV via ffmpeg pour une lecture Win32 instantanée et 100% fiable
                wav_file = final_audio.with_suffix(".wav")
                if final_audio.suffix.lower() == ".mp3":
                    ffmpeg_exe = BASE_DIR / "ffmpeg.exe"
                    if not ffmpeg_exe.exists():
                        ffmpeg_exe = Path(sys.executable).parent / "ffmpeg.exe"
                    if not ffmpeg_exe.exists():
                        try:
                            import imageio_ffmpeg
                            ffmpeg_exe = Path(imageio_ffmpeg.get_ffmpeg_exe())
                        except Exception:
                            pass
                    if ffmpeg_exe.exists():
                        import subprocess
                        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
                        subprocess.run(
                            [str(ffmpeg_exe), "-y", "-i", str(final_audio), "-acodec", "pcm_s16le", "-ar", "44100", str(wav_file)],
                            capture_output=True, creationflags=flags
                        )
                        if wav_file.exists() and wav_file.stat().st_size > 1000:
                            final_audio = wav_file

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

                # Nettoyage immédiat du fichier audio lu
                try:
                    if audio_file.exists():
                        os.remove(str(audio_file))
                    if final_audio != audio_file and final_audio.exists():
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
