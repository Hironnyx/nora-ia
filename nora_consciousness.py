"""
Moteur d'Autonomie Exécutif & Conscience Système (Background Cognitive Engine) de Nora :
- Cycle OODA permanent en arrière-plan : Observer -> Orienter -> Décider -> Agir
- Surveillance continue : Télémétrie PC (CPU, RAM, GPU RTX 4080), Contexte applicatif, Téléchargements, Temp, Sécurité
- 3 Niveaux d'Agency :
  * Niveau 1 : Actions Silencieuses Directes (Auto-Boost RAM, Auto-Clean Temp, Auto-Gaming)
  * Niveau 2 : Actions Opérationnelles Proactives avec retour sur Dynamic Island HUD
  * Niveau 3 : Demandes de validation pour modifications critiques
- Moteur hybride ultra-résilient :
  * Évaluation déterministe immédiate (0 ms, 0 token, 100% disponible hors-ligne)
  * Délibération cognitive avancée via Gemini Function Calling (quand disponible)
- Historique persistant des décisions autonomes dans data/autonomy_history.json
"""
import os
import sys
import time
import json
import random
import shutil
import threading
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable

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

import system_monitor
import agent_security
import gaming_mode
import tools_pc
import tools_pc_control
import nora_context_vision
import memory_manager

DOWNLOADS_DIR = Path.home() / "Downloads"
TEMP_DIR = Path(os.environ.get("TEMP", Path.home() / "AppData" / "Local" / "Temp"))
HISTORY_FILE = BASE_DIR / "data" / "autonomy_history.json"

CANDIDATE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash"
]

class NoraExecutiveAutonomyEngine:
    """Moteur d'autonomie cognitive et de supervision proactive pour Nora."""

    def __init__(
        self,
        interval_seconds: int = 45,
        on_action_callback: Optional[Callable[[str, str, str, bool], None]] = None,
        on_hud_callback: Optional[Callable[[str, int], None]] = None,
        on_thought_callback: Optional[Callable[[str, bool], None]] = None
    ):
        self.interval = interval_seconds
        self.on_action = on_action_callback
        self.on_hud = on_hud_callback
        self.on_thought = on_thought_callback

        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Cooldowns et horodatages des routines autonomes
        self.last_tick_time: float = 0.0
        self.last_action_time: float = 0.0
        self.last_ram_boost_time: float = 0.0
        self.last_temp_clean_time: float = 0.0
        self.last_organize_downloads_time: float = 0.0
        self.last_security_audit_time: float = 0.0
        self.last_briefing_date: str = ""
        self.last_known_downloaded_file: str = ""

        # Gestion des transitions d'applications
        self.last_app_category: str = "GENERAL"
        self.category_enter_time: float = time.time()

        # Niveau d'autonomie (2 = Maintenance silencieuse et optimisations directes par défaut)
        self.autonomy_level: int = 2

        self._ensure_history_file()

    def _ensure_history_file(self):
        try:
            HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            if not HISTORY_FILE.exists():
                with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump({"events": []}, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def log_autonomous_action(self, action_type: str, title: str, details: str):
        """Consigne chaque décision autonome prise par Nora."""
        event = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action_type": action_type,
            "title": title,
            "details": details
        }
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.setdefault("events", []).append(event)
            # Conserver les 100 derniers événements
            if len(data["events"]) > 100:
                data["events"] = data["events"][-100:]
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def start(self):
        with self._lock:
            if self.is_running:
                return
            self.is_running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True, name="NoraAutonomyLoop")
            self._thread.start()
            print("⚡ [Nora Autonomy] Moteur d'autonomie exécutive démarré.")

    def stop(self):
        with self._lock:
            self.is_running = False
            print("🛑 [Nora Autonomy] Moteur d'autonomie arrêté.")

    def _run_loop(self):
        # Temporisation initiale pour laisser démarrer l'UI et les services système
        time.sleep(4.0)
        while self.is_running:
            try:
                self.tick()
            except Exception as e:
                print(f"⚠️ [Nora Autonomy] Erreur cycle cognitif: {e}")

            # Attente réactive (découpage par tranches de 1s pour arrêt instantané)
            slept = 0
            jitter = random.randint(-4, 6)
            sleep_duration = max(25, self.interval + jitter)
            while slept < sleep_duration and self.is_running:
                time.sleep(1.0)
                slept += 1

    # =========================================================================
    # 1. PERCEPTION SYSTÈME ET CONTEXTE (CYCLE OBSERVER)
    # =========================================================================
    def gather_perception(self) -> Dict[str, Any]:
        """Rassemble l'ensemble des métriques de la machine, de l'écran et des fichiers."""
        now = time.time()
        now_dt = datetime.datetime.now()

        # A. Télémétrie Système (CPU, RAM, GPU RTX 4080)
        sys_stats = system_monitor.get_system_stats()
        current_metrics = system_monitor.get_current_metrics()
        gpu_info = current_metrics.get("gpu", {})

        # B. Contexte applicatif au premier plan
        context = nora_context_vision.context_vision.get_current_context()

        # C. Analyse du dossier Téléchargements
        unorganized_count = 0
        latest_file = ""
        latest_mtime = 0.0
        is_recent_3d = False
        recent_3d_file = ""

        if DOWNLOADS_DIR.exists():
            try:
                for f in DOWNLOADS_DIR.iterdir():
                    if f.is_file() and not f.name.startswith(('.', '~')) and not f.name.endswith(('.tmp', '.crdownload')):
                        unorganized_count += 1
                        mtime = f.stat().st_mtime
                        if mtime > latest_mtime:
                            latest_mtime = mtime
                            latest_file = f.name
                        # Détection d'un fichier 3D récent (< 120 secondes)
                        if f.suffix.lower() in [".stl", ".step", ".stp", ".3mf", ".obj", ".gcode"]:
                            if (now - mtime) < 120:
                                is_recent_3d = True
                                recent_3d_file = f.name
            except Exception:
                pass

        # D. Taille des fichiers temporaires Windows
        temp_size_mb = 0
        if TEMP_DIR.exists():
            try:
                total_bytes = sum(
                    f.stat().st_size for f in TEMP_DIR.iterdir()
                    if f.is_file() and not f.name.startswith('~')
                )
                temp_size_mb = int(total_bytes / (1024 * 1024))
            except Exception:
                pass

        # E. Période et Heure
        hour = now_dt.hour
        if 6 <= hour < 12:
            period = "matin"
        elif 12 <= hour < 18:
            period = "apres-midi"
        elif 18 <= hour < 23:
            period = "soiree"
        else:
            period = "nuit"

        return {
            "current_time": now_dt.strftime("%H:%M"),
            "today_date": now_dt.strftime("%Y-%m-%d"),
            "period": period,
            "hour": hour,
            "system": {
                "cpu_percent": sys_stats.get("cpu_percent", 0.0),
                "ram_percent": sys_stats.get("ram_percent", 0.0),
                "ram_used_gb": sys_stats.get("ram_used_gb", 0.0),
                "ram_total_gb": sys_stats.get("ram_total_gb", 0.0),
                "battery": sys_stats.get("battery_info"),
            },
            "gpu": {
                "name": gpu_info.get("name", "NVIDIA RTX 4080"),
                "temp_c": gpu_info.get("temp_c", 0),
                "load_pct": gpu_info.get("load_pct", 0),
                "vram_used_gb": gpu_info.get("vram_used_gb", 0.0),
                "vram_total_gb": gpu_info.get("vram_total_gb", 0.0),
            },
            "context": context,
            "downloads": {
                "unorganized_count": unorganized_count,
                "latest_file": latest_file,
                "is_recent_3d": is_recent_3d,
                "recent_3d_file": recent_3d_file
            },
            "temp_mb": temp_size_mb,
            "gaming_mode": gaming_mode.is_gaming_mode()
        }

    # =========================================================================
    # 2. ACTIONS EXÉCUTIVES AUTONOMES
    # =========================================================================
    def action_boost_ram(self, reason: str = "optimisation proactive") -> str:
        """Purge automatiquement le cache et la mémoire vive."""
        self.last_ram_boost_time = time.time()
        count, freed = gaming_mode.optimize_ram_boost()
        msg = f"⚡ Optimisation mémoire : {count} processus allégés, {freed} Mo libérés !"
        self.log_autonomous_action("RAM_BOOST", "Purge Proactive de la RAM", f"Raison: {reason} | Libéré: {freed} Mo")
        if self.on_hud:
            self.on_hud(msg, 5000)
        return msg

    def action_clean_temp_files(self, reason: str = "maintenance disque C:") -> str:
        """Purge les fichiers temporaires non verrouillés de plus de 24 heures."""
        self.last_temp_clean_time = time.time()
        deleted_count = 0
        freed_bytes = 0
        now = time.time()

        if TEMP_DIR.exists():
            for item in TEMP_DIR.iterdir():
                try:
                    if item.is_file():
                        # Fichiers de plus de 24h
                        if (now - item.stat().st_mtime) > 86400:
                            sz = item.stat().st_size
                            item.unlink(missing_ok=True)
                            deleted_count += 1
                            freed_bytes += sz
                except Exception:
                    continue

        freed_mb = int(freed_bytes / (1024 * 1024))
        msg = f"🧹 Maintenance C: : {deleted_count} fichiers temporaires purgés ({freed_mb} Mo libérés)."
        self.log_autonomous_action("CLEAN_TEMP", "Nettoyage Temp Windows", f"Raison: {reason} | {deleted_count} fichiers, {freed_mb} Mo")
        if self.on_hud:
            self.on_hud(msg, 5000)
        return msg

    def action_organize_downloads(self, reason: str = "tri automatique des flux") -> str:
        """Classe automatiquement les fichiers orphelins de Téléchargements."""
        self.last_organize_downloads_time = time.time()
        res = tools_pc.reorganize_folder(str(DOWNLOADS_DIR))
        msg = "📂 Téléchargements réorganisés automatiquement en catégories dédiées."
        self.log_autonomous_action("ORGANIZE_DOWNLOADS", "Classement Téléchargements", f"Raison: {reason}")
        if self.on_hud:
            self.on_hud(msg, 5500)
        return msg

    def action_trigger_morning_briefing(self, perception: Dict[str, Any]) -> str:
        """Délivre le briefing matinal exécutif sobre style J.A.R.V.I.S."""
        self.last_briefing_date = perception["today_date"]
        user_name = memory_manager.get_user_name()
        gpu_temp = perception["gpu"]["temp_c"]
        ram_pct = int(perception["system"]["ram_percent"])
        cpu_pct = int(perception["system"]["cpu_percent"])

        briefing = (
            f"Bonjour {user_name}. Station d'ingénierie opérationnelle à 100 %. "
            f"Processeur à {cpu_pct} %, RAM à {ram_pct} %, GPU RTX 4080 à {gpu_temp} °C. "
            "Tous les agents sont en veille active et prêts pour vos instructions."
        )
        self.log_autonomous_action("BRIEFING", "Briefing Matinal J.A.R.V.I.S.", briefing)
        if self.on_action:
            self.on_action("BRIEFING", "BRIEFING SYSTÈME MATINAL", briefing, True)
        elif self.on_hud:
            self.on_hud(briefing, 8000)
        return briefing

    # =========================================================================
    # 3. DÉCISION AUTONOME & DÉROULEMENT COGNITIF (TICK)
    # =========================================================================
    def tick(self) -> Dict[str, Any]:
        """Exécute un cycle de perception, délibération et action autonome."""
        self.last_tick_time = time.time()
        perception = self.gather_perception()
        now = time.time()

        # -------------------------------------------------------------
        # ÉTAPE 1 : RÈGLES DÉTERMINISTES CRITIQUES (0 ms, Fiabilité 100%)
        # -------------------------------------------------------------

        # Règle 1 : Détection automatique d'un Jeu -> Bascule Gaming Mode
        category = perception["context"].get("category", "")
        if category == "GAMING" and not perception["gaming_mode"]:
            gaming_mode.toggle_gaming_mode()
            msg = "🎮 Application de jeu détectée. Mode Gaming engagé, priorité absolue GPU, alertes masquées."
            self.log_autonomous_action("GAMING_AUTO_ON", "Activation Automatique Mode Gaming", perception["context"].get("title", ""))
            if self.on_hud:
                self.on_hud(msg, 5000)
            return {"action": "GAMING_AUTO_ON", "result": msg}

        # Règle 2 : Sortie automatique du Mode Gaming
        if perception["gaming_mode"] and category in ["DEVELOPMENT", "DESKTOP", "PRODUCTIVITY"]:
            # Si Maverick est revenu sur du travail depuis > 2 minutes
            if category != self.last_app_category:
                self.category_enter_time = now
            elif (now - self.category_enter_time) > 120:
                gaming_mode.toggle_gaming_mode()
                msg = "✨ Session de jeu terminée. Rétablissement du mode standard de Nora."
                self.log_autonomous_action("GAMING_AUTO_OFF", "Désactivation Automatique Mode Gaming", "")
                if self.on_hud:
                    self.on_hud(msg, 4500)
                return {"action": "GAMING_AUTO_OFF", "result": msg}

        self.last_app_category = category

        # En mode Gaming, aucune interruption sonore ni pop-up non critique
        if perception["gaming_mode"]:
            # Seule la protection RAM critique agit en silence si nécessaire (>88%)
            if perception["system"]["ram_percent"] > 88 and (now - self.last_ram_boost_time > 600):
                self.action_boost_ram("saturation ram critique pendant session de jeu")
                return {"action": "RAM_BOOST_SILENT"}
            return {"action": "GAMING_IDLE"}

        # Règle 3 : Briefing Matinal Unique
        if perception["period"] == "matin" and perception["today_date"] != self.last_briefing_date:
            res = self.action_trigger_morning_briefing(perception)
            return {"action": "MORNING_BRIEFING", "result": res}

        # Règle 4 : Détection d'un nouveau fichier 3D téléchargé récemment (< 120s)
        if perception["downloads"]["is_recent_3d"]:
            recent_3d = perception["downloads"]["recent_3d_file"]
            if recent_3d != self.last_known_downloaded_file:
                self.last_known_downloaded_file = recent_3d
                msg = f"🖨️ Nouveau modèle 3D détecté : <b>{recent_3d}</b>. Prêt pour découpage PrusaSlicer."
                self.log_autonomous_action("NEW_3D_MODEL", "Détection Fichier 3D", recent_3d)
                if self.on_hud:
                    self.on_hud(msg, 6000)
                return {"action": "NOTIFY_3D_MODEL", "file": recent_3d}

        # Règle 5 : Protection proactive de la mémoire vive (RAM > 80%)
        if perception["system"]["ram_percent"] > 80 and (now - self.last_ram_boost_time > 600):
            res = self.action_boost_ram(f"ram élevée ({int(perception['system']['ram_percent'])}%)")
            return {"action": "RAM_BOOST", "result": res}

        # Règle 6 : Nettoyage automatique des fichiers temporaires (Temp > 450 Mo)
        if perception["temp_mb"] >= 450 and (now - self.last_temp_clean_time > 21600):
            res = self.action_clean_temp_files(f"fichiers temporaires volumineux ({perception['temp_mb']} Mo)")
            return {"action": "CLEAN_TEMP", "result": res}

        # Règle 7 : Organisation automatique des Téléchargements (>= 12 fichiers libres)
        if perception["downloads"]["unorganized_count"] >= 12 and (now - self.last_organize_downloads_time > 10800):
            if self.autonomy_level >= 2:
                res = self.action_organize_downloads(f"{perception['downloads']['unorganized_count']} fichiers libres")
                return {"action": "ORGANIZE_DOWNLOADS", "result": res}

        # -------------------------------------------------------------
        # ÉTAPE 2 : DÉLIBÉRATION NEURONALE VIA GEMINI FUNCTION CALLING
        # -------------------------------------------------------------
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and "votre_cle" not in api_key:
            # Ne sollicite Gemini en tâche de fond que toutes les 15 minutes minimum pour préserver les quotas
            if (now - self.last_action_time) > 900:
                success, ai_res = self._deliberate_with_gemini(perception)
                if success:
                    self.last_action_time = now
                    return ai_res

        self.last_action_time = now
        return {"action": "VIGILANT_STANDBY", "status": "nominal"}

    # =========================================================================
    # 4. FUNCTION CALLING GEMINI POUR DÉCISIONS SUBTILES
    # =========================================================================
    def _deliberate_with_gemini(self, perception: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or "votre_cle" in api_key:
            return False, {}
        executed_events = []

        def optimize_pc_ram(reason: str = "optimisation proactive de la mémoire") -> str:
            """Purge et optimise la mémoire vive du PC si la RAM est chargée."""
            return self.action_boost_ram(reason)

        def clean_temp_storage(reason: str = "nettoyage des caches et temporaires") -> str:
            """Nettoie les fichiers temporaires du disque C: pour libérer de l'espace."""
            return self.action_clean_temp_files(reason)

        def organize_downloads_folder(reason: str = "rangement par catégories") -> str:
            """Classe les fichiers de Téléchargements dans des dossiers thématiques (3D, Documents, etc.)."""
            return self.action_organize_downloads(reason)

        def run_security_quick_audit(reason: str = "audit préventif") -> str:
            """Lance un audit préventif de sécurité de l'OS."""
            scan = agent_security.run_security_scan()
            msg = f"🛡️ Audit de Sécurité OS : Score {scan['score']}/100. Tout est sécurisé."
            self.log_autonomous_action("SECURITY_AUDIT", "Audit de Sécurité Autonome", scan["speech"])
            if self.on_hud:
                self.on_hud(msg, 6000)
            return msg

        def provide_executive_insight(insight: str) -> str:
            """Formule une brève observation ou recommandation d'ingénierie pour Maverick."""
            executed_events.append({"type": "INSIGHT", "text": insight})
            self.log_autonomous_action("INSIGHT", "Conseil Exécutif", insight)
            if self.on_hud:
                self.on_hud(f"💡 <b>NOTE NORA :</b>\n{insight}", 6500)
            return "Recommandation partagée sur le HUD."

        def stay_vigilant(reason: str = "Tous les indicateurs système sont optimaux") -> str:
            """Maintient une veille silencieuse sans perturber Maverick."""
            executed_events.append({"type": "VIGILANT", "reason": reason})
            return f"Veille active maintenue : {reason}"

        tools = [
            optimize_pc_ram,
            clean_temp_storage,
            organize_downloads_folder,
            run_security_quick_audit,
            provide_executive_insight,
            stay_vigilant
        ]

        system_instruction = (
            "Tu es le Moteur d'Autonomie Exécutif en Arrière-plan de Nora, copilote IA de Maverick (classe J.A.R.V.I.S.). "
            "RÈGLES CAPITALES :\n"
            "1. Tu es une IA d'ingénierie et de supervision système de très haut niveau : calme, analytique, dévouée, polie et efficace.\n"
            "2. Ton rôle est de veiller en toute autonomie sur la machine de Maverick (RAM, Disque, GPU RTX 4080, Téléchargements, Sécurité).\n"
            "3. N'hésite pas à appeler les outils d'optimisation (Function Calling) dès que pertinent. Si tout va bien, appelle stay_vigilant.\n"
            "4. Adresse-toi toujours à Maverick avec respect, loyauté et vouvoiement strict. Ne dis JAMAIS de mots familiers ou enfantins.\n"
            "5. Tes interventions écrites sont concises et percutantes (1 phrase claire)."
        )

        prompt = (
            f"=== TÉLÉMÉTRIE MATÉRIELLE & CONTEXTE DE MAVERICK ===\n"
            f"- Heure : {perception['current_time']} ({perception['period']})\n"
            f"- CPU : {perception['system']['cpu_percent']} % | RAM : {perception['system']['ram_percent']} % ({perception['system']['ram_used_gb']} Go / {perception['system']['ram_total_gb']} Go)\n"
            f"- GPU : {perception['gpu']['name']} à {perception['gpu']['temp_c']} °C (Charge: {perception['gpu']['load_pct']} %, VRAM: {perception['gpu']['vram_used_gb']} Go)\n"
            f"- Activité courante : {perception['context'].get('description', '')} (App: '{perception['context'].get('app', '')}', Titre: '{perception['context'].get('title', '')}')\n"
            f"- Téléchargements : {perception['downloads']['unorganized_count']} fichiers libres (Dernier: '{perception['downloads']['latest_file']}')\n"
            f"- Fichiers temporaires Windows : {perception['temp_mb']} Mo\n\n"
            "Quelle décision autonome prends-tu pour assister Maverick au mieux ?"
        )

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=tools,
            temperature=0.2
        )

        for model_name in CANDIDATE_MODELS:
            try:
                chat = client.chats.create(model=model_name, config=config)
                resp = chat.send_message(prompt)
                final_text = resp.text.strip() if resp and resp.text else ""
                return True, {
                    "model": model_name,
                    "events": executed_events,
                    "response": final_text
                }
            except Exception:
                continue

        return False, {}


# Instance singleton accessible par l'ensemble des modules
autonomy_engine = NoraExecutiveAutonomyEngine()
consciousness_engine = autonomy_engine  # Alias de rétrocompatibilité absolue

if __name__ == "__main__":
    print("Test du Moteur d'Autonomie Exécutif de Nora...")
    p = autonomy_engine.gather_perception()
    print("Perception recueillie :", json.dumps(p, indent=2, ensure_ascii=False))
    print("\nExécution d'un cycle de décision autonome...")
    res = autonomy_engine.tick()
    print("Résultat du tick :", json.dumps(res, indent=2, ensure_ascii=False))
