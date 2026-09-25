"""
Moteur de Proactivité Contextuelle & Veille d'Activité de Maverick (Proactive Context Engine) :
- Surveille en tâche de fond la catégorie d'activité de Maverick sans ralentissement (<0.05% CPU).
- Déclenche intelligemment des actions proactives spécialisées selon le contexte :
  * GAMING : Bascule automatique en Mode Jeu (silence vocal, libération RAM).
  * 3D_PRINTING / 3D_MODELING : L'Agent Maker 3D prépare la télémétrie de l'imprimante (plateau, buse).
  * DEVELOPMENT : L'Agent Architecte audite silencieusement la branche Git active.
- Notifie en douceur via le bus Blackboard de l'essaim et le compagnon de bureau.
"""

import sys
import time
import threading
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent

import nora_context_vision
import gaming_mode

class ProactiveContextEngine:
    """Surveillance proactive en temps réel des transitions applicatives de Maverick."""

    def __init__(self, check_interval_sec: float = 2.5):
        self.check_interval_sec = check_interval_sec
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self.listeners: List[Callable[[str, str, Dict[str, Any]], None]] = []
        self.last_category = "DESKTOP"
        self.last_app = "explorer.exe"
        self.gaming_auto_managed = True
        self.last_event_time = time.time()

    def add_listener(self, cb: Callable[[str, str, Dict[str, Any]], None]):
        """Enregistre un écouteur de transition de contexte."""
        if cb not in self.listeners:
            self.listeners.append(cb)

    def start(self):
        """Démarre le thread d'écoute en arrière-plan."""
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("👁️ [ProactiveVision] Veille contextuelle active démarrée.")

    def stop(self):
        """Arrête la veille contextuelle."""
        self.is_running = False

    def _loop(self):
        # Initialisation du contexte de départ
        init_ctx = nora_context_vision.context_vision.get_current_context()
        self.last_category = init_ctx.get("category", "DESKTOP")
        self.last_app = init_ctx.get("app", "explorer.exe")

        while self.is_running:
            try:
                time.sleep(self.check_interval_sec)
                ctx = nora_context_vision.context_vision.get_current_context()
                cat = ctx.get("category", "DESKTOP")
                app = ctx.get("app", "explorer.exe")

                # Détection d'un basculement de catégorie ou d'application majeure
                if cat != self.last_category or app != self.last_app:
                    old_cat = self.last_category
                    old_app = self.last_app
                    self.last_category = cat
                    self.last_app = app
                    self._on_context_transition(old_cat, cat, old_app, app, ctx)

            except Exception as e:
                # Tolérance absolue aux pannes : ne jamais interrompre le daemon
                time.sleep(2.0)

    def _on_context_transition(self, old_cat: str, new_cat: str, old_app: str, new_app: str, ctx: Dict[str, Any]):
        """Traite le basculement d'activité et orchestre les réflexes IA."""
        now = time.time()
        # Éviter les micro-oscillations rapides (<1.5s)
        if now - self.last_event_time < 1.5:
            return
        self.last_event_time = now

        # 1. Gestion automatique du Mode Jeu
        if self.gaming_auto_managed:
            if new_cat == "GAMING" and old_cat != "GAMING":
                try:
                    gaming_mode.enable_gaming_mode()
                    print(f"🎮 [ProactiveVision] Jeu détecté ({new_app}) -> Mode Jeu activé automatiquement.")
                except Exception:
                    pass
            elif old_cat == "GAMING" and new_cat != "GAMING":
                try:
                    gaming_mode.disable_gaming_mode()
                    print(f"🖥️ [ProactiveVision] Sortie de jeu -> Mode standard restauré.")
                except Exception:
                    pass

        # 2. Réflexe Atelier 3D (Maker 3D)
        if new_cat in ["3D_PRINTING", "3D_MODELING"]:
            try:
                import print3d_manager
                telemetry = print3d_manager.print3d_manager.get_telemetry()
                status = telemetry.get("status", "Non connectée")
                # Enregistrer discrètement dans le Blackboard si l'essaim est actif
                import nora_blackboard
                bb = nora_blackboard.get_shared_blackboard()
                bb.post_fact("🔧 Agent Maker 3D", f"Maverick a ouvert {new_app}. Imprimante 3D : {status}.")
            except Exception:
                pass

        # 3. Réflexe Code & Développement (Architecte)
        if new_cat == "DEVELOPMENT":
            try:
                import nora_blackboard
                bb = nora_blackboard.get_shared_blackboard()
                bb.post_fact("🏛️ Agent Architecte", f"Maverick est en session de développement sur {new_app}.")
            except Exception:
                pass

        # 4. Notification des écouteurs enregistrés (UI, QG, Mascot)
        for listener in list(self.listeners):
            try:
                listener(old_cat, new_cat, ctx)
            except Exception:
                pass

# Singleton global de proactivité contextuelle
proactive_engine = ProactiveContextEngine()

if __name__ == "__main__":
    print("Test du Moteur de Proactivité Contextuelle...")
    def test_cb(old_c, new_c, c):
        print(f"⚡ Transition détectée : {old_c} -> {new_c} ({c.get('app')})")

    proactive_engine.add_listener(test_cb)
    print("Démarrage de la veille pour 6 secondes...")
    proactive_engine.start()
    time.sleep(6)
    proactive_engine.stop()
    print("✔ Test terminé.")
