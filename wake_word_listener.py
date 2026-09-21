"""
Module d'écoute continue mains-libres (Wake Word : 'Dis Nora', 'Hey Nora', 'Nora').
Sélectionne automatiquement le vrai microphone actif et tolère les variantes phonétiques de Google Speech.
"""
import time
import re
import threading
import speech_recognition as sr
import sound_effects
import voice_engine

# Variantes phonétiques couramment transcrites par Google Speech pour "Dis Nora" / "Hey Nora"
WAKE_PATTERNS = [
    r"\b(dis nora|dit nora|10 nora|dis-moi nora|hey nora|eh nora|hé nora|hay nora|salut nora|ok nora|nora|norah|noah|dora|laura)\b"
]

class WakeWordDetector:
    def __init__(self, on_wake_callback=None, on_command_callback=None):
        self.on_wake_callback = on_wake_callback
        self.on_command_callback = on_command_callback
        self.is_running = False
        self.thread = None
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 180
        self.recognizer.dynamic_energy_threshold = True

    def start(self):
        """Démarre l'écoute en arrière-plan."""
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print("🎧 Écoute mains-libres 'Dis Nora' active sur le microphone actif !")

    def stop(self):
        """Arrête l'écoute en arrière-plan."""
        self.is_running = False

    def _listen_loop(self):
        mic_idx = voice_engine.get_active_microphone_index()
        try:
            with sr.Microphone(device_index=mic_idx) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
                while self.is_running:
                    # Ne pas écouter pendant que Nora parle pour éliminer les retours micro
                    if voice_engine.is_speaking():
                        time.sleep(0.3)
                        continue

                    try:
                        # Écoute de courts segments de voix
                        audio = self.recognizer.listen(source, timeout=3.0, phrase_time_limit=7.0)
                        if voice_engine.is_speaking():
                            continue

                        text = self.recognizer.recognize_google(audio, language="fr-FR").lower()

                        print(f"👂 [Audio capté] : '{text}'")

                        # Vérifier si l'un des mots de réveil est présent
                        is_wake = any(re.search(pat, text) for pat in WAKE_PATTERNS)
                        if is_wake:
                            print(f"✨ Mot-clé détecté : '{text}'")
                            sound_effects.play_wake_chime()

                            # Extraire la commande après le mot-clé si présente
                            clean_command = re.sub(
                                r"^(dis nora|dit nora|10 nora|dis-moi nora|hey nora|eh nora|hé nora|hay nora|salut nora|ok nora|nora|norah|noah|dora|laura)\s*,?\s*",
                                "",
                                text
                            ).strip()

                            if clean_command:
                                if self.on_command_callback:
                                    self.on_command_callback(clean_command)
                            else:
                                if self.on_wake_callback:
                                    self.on_wake_callback()

                            time.sleep(1.2)

                    except (sr.WaitTimeoutError, sr.UnknownValueError):
                        continue
                    except Exception as e:
                        time.sleep(0.5)

        except Exception as e:
            print(f"Erreur initialisation micro mains-libres : {e}")
            self.is_running = False
