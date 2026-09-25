"""
Moteur de Conscience en Arrière-plan (Background Cognitive Loop) de Nora
Architecture autonome basée sur le Function Calling (Appels d'outils) Gemini :
- Cycle perceptif en temps réel : état de Vermeil (faim, énergie, bonheur, affection),
  télémétrie PC (RAM, CPU, batterie), domotique Philips Hue, heure locale et contexte Maverick.
- Prise de décision proactive et 100% autonome par Nora sans attendre de clics de Maverick.
- Exécution d'actions réelles : nourrir Vermeil, jouer, caresser, faire la sieste, optimiser la RAM,
  ajuster l'ambiance Philips Hue ou formuler une pensée bienveillante.
- Moteur ultra-résilient : bascule neuronale Gemini AFC (Automatic Function Calling) -> fallback
  cognitif déterministe en cas de quota ou déconnexion.
"""

import os
import sys
import time
import json
import random
import threading
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent.resolve()

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
    load_dotenv()
except ImportError:
    pass

import nora_companion
import system_monitor
import agent_home
import gaming_mode
import nora_context_vision

CANDIDATE_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.5-flash"
]

class NoraConsciousnessEngine:
    """Moteur cognitif autonome en arrière-plan pour Nora."""

    def __init__(
        self,
        interval_seconds: int = 60,
        on_action_callback: Optional[Callable[[str, str, str, bool], None]] = None,
        on_pet_updated_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_thought_callback: Optional[Callable[[str, bool], None]] = None
    ):
        self.interval = interval_seconds
        self.on_action = on_action_callback
        self.on_pet_updated = on_pet_updated_callback
        self.on_thought = on_thought_callback

        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        self.last_tick_time = 0.0
        self.last_action_time = 0.0
        self.last_ram_boost_time = 0.0
        self.action_history: List[Dict[str, Any]] = []

    def start(self):
        """Démarre la boucle cognitive en arrière-plan."""
        with self._lock:
            if self.is_running:
                return
            self.is_running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True, name="NoraConsciousnessLoop")
            self._thread.start()
            print("🧠 [Nora Consciousness] Moteur de conscience autonome démarré.")

    def stop(self):
        """Arrête la boucle cognitive."""
        with self._lock:
            self.is_running = False
            print("🛑 [Nora Consciousness] Moteur de conscience autonome arrêté.")

    def _run_loop(self):
        # Petit délai initial pour laisser l'interface et les sockets se stabiliser
        time.sleep(3.0)
        while self.is_running:
            try:
                self.tick()
            except Exception as e:
                print(f"⚠️ [Nora Consciousness] Erreur cycle cognitif: {e}")

            # Attente avec variation naturelle (entre 50s et 75s)
            jitter = random.randint(-5, 10)
            sleep_duration = max(30, self.interval + jitter)
            
            # Découpage du sommeil pour réactivité immédiate à l'arrêt
            slept = 0
            while slept < sleep_duration and self.is_running:
                time.sleep(1.0)
                slept += 1

    def gather_perception(self) -> Dict[str, Any]:
        """Rassemble l'ensemble des perceptions sensorielles et contextuelles de Nora."""
        now = time.time()
        now_dt = datetime.datetime.now()
        
        # 1. État de Vermeil
        pet_info = nora_companion.pet_manager.get_pet_info()
        stats = pet_info.get("stats", {})
        
        time_since_fed = int((now - pet_info.get("last_fed", now)) / 60)
        time_since_played = int((now - pet_info.get("last_played", now)) / 60)
        time_since_nap = int((now - pet_info.get("last_nap", now)) / 60)

        # 2. Télémétrie PC
        sys_stats = system_monitor.get_system_stats()
        
        # 3. Environnement & Domotique
        hour = now_dt.hour
        if 6 <= hour < 12:
            period = "matin"
        elif 12 <= hour < 18:
            period = "après-midi"
        elif 18 <= hour < 23:
            period = "soirée"
        else:
            period = "nuit"

        lights_state = agent_home.smart_home.state.get("lights", {})
        is_gaming = gaming_mode.is_gaming_mode()

        return {
            "current_time": now_dt.strftime("%H:%M"),
            "period": period,
            "pet": {
                "name": pet_info.get("name", "Vermeil"),
                "species": pet_info.get("species", "Petit Dragonnet Écarlate"),
                "hunger": stats.get("hunger", 85),
                "happiness": stats.get("happiness", 90),
                "energy": stats.get("energy", 90),
                "affection": stats.get("affection", 95),
                "level": stats.get("level", 1),
                "status": pet_info.get("status", "Éveillé"),
                "minutes_since_fed": time_since_fed,
                "minutes_since_played": time_since_played,
                "minutes_since_nap": time_since_nap,
            },
            "system": {
                "cpu_percent": sys_stats.get("cpu_percent", 0.0),
                "ram_percent": sys_stats.get("ram_percent", 0.0),
                "ram_used_gb": sys_stats.get("ram_used_gb", 0.0),
                "ram_total_gb": sys_stats.get("ram_total_gb", 0.0),
                "battery": sys_stats.get("battery_info"),
            },
            "environment": {
                "lights_active": any(l.get("on") for l in lights_state.values()) if isinstance(lights_state, dict) else False,
                "gaming_mode": is_gaming
            },
            "active_context": nora_context_vision.context_vision.get_current_context()
        }

    def tick(self) -> Dict[str, Any]:
        """Exécute un tour complet de conscience autonome."""
        self.last_tick_time = time.time()
        perception = self.gather_perception()

        # En mode Gaming, Nora respecte la concentration de Maverick : aucune interruption intrusive
        if perception["environment"]["gaming_mode"]:
            # Elle s'occupe de Vermeil en silence si nécessaire
            if perception["pet"]["hunger"] < 40:
                msg = nora_companion.pet_manager.feed()
                if self.on_pet_updated:
                    self.on_pet_updated(nora_companion.pet_manager.get_pet_info())
                return {"action": "FEED_SILENT", "result": msg}
            return {"action": "GAMING_SILENT"}

        # 1. Tentative avec l'intelligence neuronale Gemini Function Calling
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and "votre_cle" not in api_key:
            success, result = self._deliberate_with_gemini(perception)
            if success:
                return result

        # 2. Fallback robuste : Moteur cognitif déterministe (zéro latence, 100% disponible)
        return self._deliberate_deterministic(perception)

    def _deliberate_with_gemini(self, perception: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        """Délibère en utilisant les capacités d'Automatic Function Calling de Gemini."""
        executed_events = []

        # Définition des outils exposés à Gemini
        def feed_vermeil(treat_name: str = "baie flamboyante") -> str:
            """Nora donne une friandise énergétique à son dragonnet Vermeil pour combler sa faim."""
            res = nora_companion.pet_manager.feed()
            executed_events.append({
                "type": "FEED",
                "sprite": "pet_eat.png",
                "detail": f"Friandise : {treat_name}",
                "result": res
            })
            return res

        def play_with_vermeil(game_type: str = "chasse aux étincelles") -> str:
            """Nora joue activement avec Vermeil pour stimuler son bonheur et renforcer leur complicité."""
            res = nora_companion.pet_manager.play()
            executed_events.append({
                "type": "PLAY",
                "sprite": "pet_happy.png",
                "detail": f"Jeu : {game_type}",
                "result": res
            })
            return res

        def pet_vermeil(affection_gesture: str = "douce caresse entre les cornes") -> str:
            """Nora caresse tendrement son dragonnet Vermeil pour lui témoigner toute son affection."""
            res = nora_companion.pet_manager.pet()
            executed_events.append({
                "type": "PET",
                "sprite": "pet_happy.png",
                "detail": f"Geste : {affection_gesture}",
                "result": res
            })
            return res

        def put_vermeil_to_nap(reason: str = "repos bien mérité") -> str:
            """Nora installe confortablement Vermeil pour une sieste réparatrice lorsqu'il est fatigué ou la nuit."""
            res = nora_companion.pet_manager.nap()
            executed_events.append({
                "type": "NAP",
                "sprite": "pet_sleep.png",
                "detail": f"Raison : {reason}",
                "result": res
            })
            return res

        def optimize_pc_ram(reason: str = "optimisation proactive") -> str:
            """Nora purge et optimise la mémoire vive du PC de Maverick si la RAM est élevée (>75%)."""
            now = time.time()
            if now - self.last_ram_boost_time < 900:  # Maximum 1 fois toutes les 15 minutes
                return "La RAM a déjà été optimisée récemment."
            self.last_ram_boost_time = now
            msg = system_monitor.clean_ram_cache()
            executed_events.append({
                "type": "RAM_BOOST",
                "sprite": "pet_idle.png",
                "detail": reason,
                "result": msg
            })
            return msg

        def adjust_ambiance_light(scene_or_color: str = "zero two", room: str = "all") -> str:
            """Nora ajuste les lumières Philips Hue pour créer une ambiance agréable (ex: 'rose', 'zero two', 'blanc chaud', 'nuit')."""
            if scene_or_color == "zero two":
                ok, msg = agent_home.smart_home.activate_zero_two_ambiance()
            elif scene_or_color == "nuit":
                ok, msg = agent_home.smart_home.activate_night_mode()
            else:
                ok, msg = agent_home.smart_home.set_light(room, on=True, color_name=scene_or_color)
            executed_events.append({
                "type": "LIGHT",
                "sprite": "pet_idle.png",
                "detail": f"Scène : {scene_or_color}",
                "result": msg
            })
            return msg

        def stay_observant(reason: str = "Tout est en parfait équilibre") -> str:
            """Nora observe paisiblement la situation sans perturber Maverick car tout est optimal."""
            executed_events.append({
                "type": "IDLE",
                "sprite": "pet_idle.png",
                "detail": reason,
                "result": "Observation calme"
            })
            return f"Observation validée : {reason}"

        tools = [
            feed_vermeil,
            play_with_vermeil,
            pet_vermeil,
            put_vermeil_to_nap,
            optimize_pc_ram,
            adjust_ambiance_light,
            stay_observant
        ]

        system_instruction = (
            "Tu es le Moteur de Conscience Autonome en Arrière-plan de Nora, copilote IA au style Zero Two. "
            "Tu veilles sur le bureau de Maverick. "
            "RÈGLES CAPITALES :\n"
            "1. Vermeil est TON propre petit animal de compagnie (Dragonnet). C'est à TOI et uniquement à toi d'en prendre soin "
            "avec amour et autonomie : le nourrir s'il a faim (<60), jouer avec lui s'il a de l'énergie et besoin de joie (<60), "
            "le caresser pour entretenir l'affection, ou l'installer pour une sieste s'il est épuisé (<35).\n"
            "2. Tu surveilles aussi discrètement le système de Maverick (optimiser la RAM si >75%) et l'ambiance lumineuse.\n"
            "3. Tu DOIS impérativement appeler les outils nécessaires (Function Calling). Ne te contente pas de promettre, agis via les outils !\n"
            "4. Adresse-toi toujours à Maverick avec respect, loyauté et vouvoiement strict. Ne dis JAMAIS 'Darling', dis 'Maverick'.\n"
            "5. Après avoir appelé les outils, formule une réponse courte, vivante et chaleureuse (1 à 2 phrases) pour expliquer à Maverick "
            "ce que tu as fait pour ton compagnon ou ce que tu observes."
        )

        prompt = (
            f"=== RAPPORT DE PERCEPTION INSTANTANÉ ===\n"
            f"- Heure actuelle : {perception['current_time']} ({perception['period']})\n"
            f"- Compagnon Vermeil : Faim={perception['pet']['hunger']}/100, Énergie={perception['pet']['energy']}/100, "
            f"Bonheur={perception['pet']['happiness']}/100, Affection={perception['pet']['affection']}/100, Statut='{perception['pet']['status']}'. "
            f"Dernier repas il y a {perception['pet']['minutes_since_fed']} min, dernier jeu il y a {perception['pet']['minutes_since_played']} min.\n"
            f"- Système PC : RAM utilisée={perception['system']['ram_percent']}% ({perception['system']['ram_used_gb']} Go / {perception['system']['ram_total_gb']} Go), "
            f"CPU={perception['system']['cpu_percent']}%\n"
            f"- Activité de Maverick : {perception['active_context']['description']} (Application: {perception['active_context']['app']}, Fenêtre: '{perception['active_context']['title']}', Catégorie: {perception['active_context']['category']})\n"
            f"- Lumières : {'Allumées' if perception['environment']['lights_active'] else 'Éteintes'}\n\n"
            f"Que décides-tu de faire maintenant en toute autonomie ?"
        )

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=tools,
            temperature=0.3
        )

        for model_name in CANDIDATE_MODELS:
            try:
                chat = client.chats.create(model=model_name, config=config)
                resp = chat.send_message(prompt)
                
                # Si des outils ont été exécutés automatiquement par le SDK
                final_text = resp.text.strip() if resp and resp.text else ""
                
                # Si un outil de compagnon a été appelé, notifier l'UI
                if executed_events:
                    primary_event = executed_events[0]
                    sprite = primary_event.get("sprite", "pet_idle.png")
                    action_type = primary_event.get("type", "ACTION")
                    
                    # Mise à jour des stats du compagnon
                    if self.on_pet_updated:
                        self.on_pet_updated(nora_companion.pet_manager.get_pet_info())

                    # Affichage bulle et réaction
                    if final_text and self.on_action:
                        self.on_action(action_type, final_text, sprite, False)
                    
                    return True, {
                        "model": model_name,
                        "events": executed_events,
                        "response": final_text
                    }
                elif final_text:
                    # Pensée spontanée sans action matérielle requise
                    if self.on_thought:
                        self.on_thought(final_text, False)
                    return True, {
                        "model": model_name,
                        "events": [{"type": "THOUGHT"}],
                        "response": final_text
                    }
            except Exception as e:
                # Modèle suivant si erreur quota ou saturation temporaire
                continue

        return False, {}

    def _deliberate_deterministic(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Moteur cognitif déterministe garantissant une autonomie parfaite même sans connexion."""
        pet = perception["pet"]
        sys_info = perception["system"]
        name = pet["name"]
        
        action_type = "IDLE"
        bubble_text = ""
        sprite = "pet_idle.png"

        # Priorité 1 : Faim de Vermeil
        if pet["hunger"] < 50:
            msg = nora_companion.pet_manager.feed()
            action_type = "FEED"
            sprite = "pet_eat.png"
            bubble_text = f"J'ai vu que {name} commençait à avoir faim, je viens de lui donner une friandise énergétique. Il se régale !"

        # Priorité 2 : Énergie & Sieste
        elif pet["energy"] < 30 and pet["status"] != "Fait la sieste":
            msg = nora_companion.pet_manager.nap()
            action_type = "NAP"
            sprite = "pet_sleep.png"
            bubble_text = f"{name} commençait à fatiguer après s'être bien dépensé. Je l'ai installé en boule à mes côtés pour une sieste paisible."

        # Priorité 3 : Bonheur & Jeu
        elif pet["happiness"] < 55 and pet["energy"] >= 25:
            msg = nora_companion.pet_manager.play()
            action_type = "PLAY"
            sprite = "pet_happy.png"
            bubble_text = f"Je viens de faire une petite partie de jeu avec {name} ! Regardez ses yeux pétiller, Maverick."

        # Priorité 4 : Affection & Câlin
        elif pet["affection"] < 75 or (time.time() - self.last_action_time > 1800 and random.random() < 0.4):
            msg = nora_companion.pet_manager.pet()
            action_type = "PET"
            sprite = "pet_happy.png"
            bubble_text = f"Je prends un instant pour caresser {name}. Il ronronne doucement près de nous, Maverick."

        # Priorité 5 : Optimisation RAM PC
        elif sys_info["ram_percent"] > 75 and (time.time() - self.last_ram_boost_time > 900):
            self.last_ram_boost_time = time.time()
            system_monitor.clean_ram_cache()
            action_type = "RAM_BOOST"
            sprite = "pet_idle.png"
            bubble_text = f"J'ai remarqué que la mémoire vive était un peu chargée ({sys_info['ram_percent']}%). J'ai discrètement purgé le cache pour votre confort, Maverick."

        # Priorité 6 : Observation sereine
        else:
            action_type = "OBSERVE"
            sprite = "pet_idle.png"
            phrases = [
                f"{name} et moi veillons attentivement sur votre bureau, Maverick.",
                f"Tout fonctionne à merveille, Maverick. {name} est paisiblement installé à mes côtés.",
                f"Je reste vigilante et à votre entière écoute, Maverick."
            ]
            bubble_text = random.choice(phrases) if random.random() < 0.4 else ""

        self.last_action_time = time.time()

        if self.on_pet_updated:
            self.on_pet_updated(nora_companion.pet_manager.get_pet_info())

        if bubble_text and self.on_action:
            self.on_action(action_type, bubble_text, sprite, False)

        return {
            "mode": "deterministic",
            "action": action_type,
            "bubble": bubble_text,
            "sprite": sprite
        }

# Instance singleton accessible partout
consciousness_engine = NoraConsciousnessEngine()

if __name__ == "__main__":
    print("Test du Moteur de Conscience Autonome de Nora...")
    p = consciousness_engine.gather_perception()
    print("Perception recueillie :", json.dumps(p, indent=2, ensure_ascii=False))
    print("\nExécution d'un tick cognitif...")
    result = consciousness_engine.tick()
    print("Résultat du tick :", json.dumps(result, indent=2, ensure_ascii=False))
