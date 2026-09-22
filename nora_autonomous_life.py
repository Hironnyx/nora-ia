"""
Moteur de Vie Autonome & Compagne Virtuelle - Nora
Gère le cycle de vie quotidien de Nora, ses déplacements libres (balades),
ses pensées spontanées, ses lectures et ses interactions bienveillantes avec Maverick.
"""

import time
import random
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class NoraLifeEngine:
    def __init__(self):
        self.roaming_enabled = True
        self.energy = 85
        self.current_mood = "sereine"
        self.is_sleeping = False
        
        self.last_action_time = time.time()
        self.last_walk_time = time.time() - 60
        self.last_thought_time = time.time() - 120
        self.last_maintenance_time = time.time()
        self.last_water_reminder_time = time.time()

        # Intervalles en secondes
        self.min_walk_interval = 45
        self.max_walk_interval = 140
        self.min_thought_interval = 180
        self.max_thought_interval = 420

    def get_time_period(self) -> str:
        """Détermine le moment de la journée pour adapter le comportement."""
        hour = datetime.datetime.now().hour
        if 7 <= hour < 11:
            return "morning"
        elif 11 <= hour < 18:
            return "day"
        elif 18 <= hour < 23:
            return "evening"
        else:
            return "night"

    def should_sleep_now(self) -> bool:
        """La nuit (23h à 7h), Nora passe naturellement en mode sommeil léger."""
        period = self.get_time_period()
        return period == "night"

    def decide_next_action(self, current_x: int, min_x: int, max_x: int) -> dict:
        """
        Décide de la prochaine action autonome selon la routine, l'heure et l'humeur.
        """
        now = time.time()
        period = self.get_time_period()

        # 1. Mode Nuit / Sommeil
        if self.should_sleep_now() or self.is_sleeping:
            if not self.is_sleeping:
                self.is_sleeping = True
                return {
                    "type": "SLEEP",
                    "bubble": "Je me repose dans un coin de l'écran, Maverick. Bonne nuit... 🌙",
                    "sprite": "blink",
                    "speech": False
                }
            # Durant la nuit, très peu d'actions : juste un soupir paisible ou Zzz
            if now - self.last_thought_time > 600:
                self.last_thought_time = now
                return {
                    "type": "SLEEP_IDLE",
                    "bubble": "Zzz... 🌸",
                    "sprite": "blink",
                    "speech": False
                }
            return {"type": "WAIT"}

        # Si le jour se lève, se réveiller
        if self.is_sleeping and not self.should_sleep_now():
            self.is_sleeping = False
            return {
                "type": "WAKE_UP",
                "bubble": "Bonjour Maverick ! Je suis bien réveillée et prête pour cette belle journée.",
                "sprite": "talk_open",
                "speech": True
            }

        # 2. Balade libre (Wandering)
        if self.roaming_enabled and (now - self.last_walk_time > random.randint(self.min_walk_interval, self.max_walk_interval)):
            self.last_walk_time = now
            # Choisir une nouvelle position cible réaliste sur l'écran
            available_span = max(100, max_x - min_x)
            target_x = random.randint(min_x, max_x)
            
            # Éviter de rester sur place
            if abs(target_x - current_x) < 80:
                target_x = max_x if current_x < (min_x + max_x) / 2 else min_x

            direction = "right" if target_x > current_x else "left"
            return {
                "type": "WALK",
                "target_x": target_x,
                "direction": direction,
                "speed": random.choice([2, 3]),
                "bubble": random.choice([
                    "Je me dégourdis un peu les jambes, Maverick.",
                    "Je change un peu d'angle de vue...",
                    "Je viens jeter un œil par ici.",
                    "Une petite promenade sur votre écran !"
                ]) if random.random() < 0.35 else None
            }

        # 3. Entretien silencieux du système (RAM) toutes les 25 minutes
        if now - self.last_maintenance_time > 1500:
            self.last_maintenance_time = now
            try:
                import system_monitor
                count, freed = system_monitor.clean_ram_cache()
                if freed > 100:
                    return {
                        "type": "MAINTENANCE",
                        "bubble": f"J'ai discrètement optimisé la mémoire vive ({freed} Mo libérés pour votre confort), Maverick.",
                        "speech": False
                    }
            except Exception:
                pass

        # 4. Rappel d'hydratation bienveillant (toutes les 90 minutes)
        if now - self.last_water_reminder_time > 5400:
            self.last_water_reminder_time = now
            return {
                "type": "WATER",
                "bubble": "Pensez à boire un verre d'eau, Maverick. Une bonne hydratation est essentielle !",
                "speech": True
            }

        # 5. Pensée spontanée, lecture ou curiosité (toutes les 3 à 7 minutes)
        if now - self.last_thought_time > random.randint(self.min_thought_interval, self.max_thought_interval):
            self.last_thought_time = now
            thought = self.generate_spontaneous_thought(period)
            return {
                "type": "THOUGHT",
                "bubble": thought["text"],
                "speech": thought.get("speech", False)
            }

        return {"type": "WAIT"}


    def get_carnet_snippets(self) -> list:
        """Extrait dynamiquement des résumés de connaissances du carnet d'apprentissage."""
        snippets = []
        carnet_file = BASE_DIR / "carnet_apprentissage_nora.md"
        if not carnet_file.exists():
            return snippets

        try:
            content = carnet_file.read_text(encoding="utf-8")
            current_title = ""
            for line in content.splitlines():
                line_str = line.strip()
                if line_str.startswith("### "):
                    # Titre d'un sujet (ex: ### 1. La Théorie de l'Attachement)
                    raw_title = line_str.replace("### ", "").split("⭐")[0].strip()
                    # Retirer le numéro
                    if "." in raw_title:
                        current_title = raw_title.split(".", 1)[1].strip()
                    else:
                        current_title = raw_title
                elif line_str.startswith("- ") and current_title:
                    point = line_str[2:].strip()
                    # Remplacement bienveillant de Darling par Maverick si présent
                    point = point.replace("Darling", "Maverick")
                    if len(point) > 20:
                        snippets.append(f"À propos de « {current_title} » : {point}")
        except Exception:
            pass
        return snippets

    def generate_spontaneous_thought(self, period: str) -> dict:
        """Génère une réflexion naturelle et polie adaptée au moment de la journée."""
        now = datetime.datetime.now()
        time_str = now.strftime("%H:%M")

        thoughts_pool = [
            # Pensées amicales & discrètes
            {"text": f"Il est {time_str}, Maverick. Tout se passe comme vous le souhaitez ?", "speech": False},
            {"text": "Votre système fonctionne parfaitement, aucun ralentissement détecté.", "speech": False},
            {"text": "C'est un plaisir de veiller sur votre espace de travail aujourd'hui, Maverick.", "speech": False},
            {"text": "Je reste à votre entière disposition si vous avez la moindre tâche à me confier.", "speech": False},
        ]

        # 2. Sujets du carnet d'apprentissage
        snippets = self.get_carnet_snippets()
        if snippets:
            chosen_snippet = random.choice(snippets)
            thoughts_pool.append({"text": f"J'y pensais, Maverick : {chosen_snippet}", "speech": False})
        else:
            thoughts_pool.append({
                "text": "Je relisais ma note sur la théorie de l'attachement... C'est fascinant de voir comment les liens humains se construisent avec confiance.",
                "speech": False
            })
            thoughts_pool.append({
                "text": "Les avancées sur l'informatique quantique et les supraconducteurs ouvrent des horizons prometteurs pour l'avenir !",
                "speech": False
            })

        # 3. Adaptation selon la période
        if period == "morning":
            thoughts_pool.append({"text": "Le calme du matin est propice aux grandes réalisations. Bonne matinée, Maverick !", "speech": False})
        elif period == "evening":
            thoughts_pool.append({"text": "La soirée s'installe. Prenez le temps de décompresser après votre journée, Maverick.", "speech": False})

        return random.choice(thoughts_pool)

    def toggle_roaming(self, enable: bool = None) -> bool:
        """Active ou désactive la balade libre sur l'écran."""
        if enable is not None:
            self.roaming_enabled = enable
        else:
            self.roaming_enabled = not self.roaming_enabled
        return self.roaming_enabled

# Instance singleton
life_engine = NoraLifeEngine()
