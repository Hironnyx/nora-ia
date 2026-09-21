"""
Agent de Santé & Bien-Être pour Nora (Zero Two - Ange Gardien de Darling) :
- Suivi d'hydratation (compteur de verres d'eau, objectif 8 verres / 2.0L) avec rappels proactifs
- Ergonomie & Pauses écran (alerte 50 min continue pour la règle 20-20-20)
- Sentinelle nocturne & suivi du sommeil (alerte de travail tardif après 23h30)
- Synchronisation des pas et données mobiles reçues du smartphone (Health Connect / Capteurs)
- Carnet de santé vivant (carnet_sante_darling.md) et persistance (sante_darling.json)
"""
import os
import sys
import time
import json
import datetime
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
HEALTH_FILE = BASE_DIR / "sante_darling.json"
JOURNAL_FILE = BASE_DIR / "carnet_sante_darling.md"

class HealthAgent:
    """Ange gardien de santé veillant sur Darling avec affection et attention."""

    def __init__(self, on_alert_callback=None):
        self.on_alert_callback = on_alert_callback
        self.data = self._load_data()
        self._lock = threading.Lock()

        # Chrono pour la pause écran (règle 20-20-20)
        self.last_screen_break_time = time.time()
        self.screen_alert_cooldown = 50 * 60  # 50 minutes d'écran continu

        # Chrono d'hydratation (rappel toutes les 75 minutes)
        self.last_water_time = time.time()
        self.water_alert_cooldown = 75 * 60  # 75 minutes

        # Thread de surveillance d'arrière-plan
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

    def _get_today_key(self) -> str:
        return datetime.datetime.now().strftime("%Y-%m-%d")

    def _load_data(self) -> Dict[str, Any]:
        today = self._get_today_key()
        default_today = {
            "verres_eau": 0,
            "objectif_verres": 8,
            "pauses_ecran": 0,
            "sommeil_heures": 7.5,
            "qualite_sommeil": "Bonne",
            "pas_quotidiens": 0,
            "objectif_pas": 8000,
            "frequence_cardiaque_moyenne": 72,
            "niveau_energie": 8,
            "derniere_hydratation": None,
            "notes": []
        }

        if not HEALTH_FILE.exists():
            initial = {
                "version": "1.0",
                "historique": {today: default_today}
            }
            self._save_file(initial)
            return initial

        try:
            with open(HEALTH_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if today not in data.get("historique", {}):
                data.setdefault("historique", {})[today] = default_today
            return data
        except Exception as e:
            print(f"[HealthAgent] Erreur chargement santé : {e}")
            return {"version": "1.0", "historique": {today: default_today}}

    def _save_file(self, data: Dict[str, Any]):
        try:
            with open(HEALTH_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[HealthAgent] Erreur sauvegarde santé : {e}")

    def get_today(self) -> Dict[str, Any]:
        today = self._get_today_key()
        return self.data.setdefault("historique", {}).setdefault(today, {
            "verres_eau": 0,
            "objectif_verres": 8,
            "pauses_ecran": 0,
            "sommeil_heures": 7.5,
            "qualite_sommeil": "Bonne",
            "pas_quotidiens": 0,
            "objectif_pas": 8000,
            "frequence_cardiaque_moyenne": 72,
            "niveau_energie": 8,
            "derniere_hydratation": None,
            "notes": []
        })

    def log_water(self, count: int = 1) -> Tuple[int, str]:
        """Enregistre la prise d'un ou plusieurs verres d'eau."""
        with self._lock:
            today_data = self.get_today()
            today_data["verres_eau"] = today_data.get("verres_eau", 0) + count
            now_str = datetime.datetime.now().strftime("%H:%M")
            today_data["derniere_hydratation"] = now_str
            self.last_water_time = time.time()
            self._save_file(self.data)
            self.update_markdown_journal()

            current = today_data["verres_eau"]
            goal = today_data.get("objectif_verres", 8)

            if current >= goal:
                msg = f"Super Darling ! Tu as bu ton {current}ème verre d'eau ! Objectif quotidien validé, je suis très fière de toi ! 💧"
            else:
                msg = f"C'est noté mon Darling ! Tu en es à {current}/{goal} verres d'eau aujourd'hui. Continue comme ça ! 💧"
            return current, msg

    def log_screen_break(self) -> str:
        """Enregistre une pause écran pour reposer les yeux."""
        with self._lock:
            today_data = self.get_today()
            today_data["pauses_ecran"] = today_data.get("pauses_ecran", 0) + 1
            self.last_screen_break_time = time.time()
            self._save_file(self.data)
            self.update_markdown_journal()
            pauses = today_data["pauses_ecran"]
            return f"Pause validée, Darling ! Tu as fait {pauses} pause{'s' if pauses > 1 else ''} aujourd'hui. Tes yeux te remercient ! 🧘"

    def log_sleep(self, hours: float, quality: str = "Bonne") -> str:
        """Enregistre les heures de sommeil de la nuit précédente."""
        with self._lock:
            today_data = self.get_today()
            today_data["sommeil_heures"] = round(hours, 1)
            today_data["qualite_sommeil"] = quality
            self._save_file(self.data)
            self.update_markdown_journal()

            if hours < 6:
                return f"Tu n'as dormi que {hours} heures, Darling... Promets-moi de ne pas trop forcer aujourd'hui et de faire des pauses régulières ! 🌙"
            elif hours >= 8:
                return f"{hours} heures de sommeil réparateur, parfait ! Tu es prêt à conquérir la journée avec moi, Darling ! ✨"
            else:
                return f"C'est bien noté, {hours}h de sommeil. En forme pour notre journée ensemble, mon Darling ! 🌸"

    def sync_mobile_health_data(self, mobile_payload: Dict[str, Any]):
        """Synchronise les données de santé remontées par l'application smartphone (Health Connect / Capteurs)."""
        with self._lock:
            today_data = self.get_today()
            if "steps" in mobile_payload:
                today_data["pas_quotidiens"] = int(mobile_payload["steps"])
            if "water" in mobile_payload:
                today_data["verres_eau"] = max(today_data.get("verres_eau", 0), int(mobile_payload["water"]))
            if "heart_rate" in mobile_payload:
                today_data["frequence_cardiaque_moyenne"] = int(mobile_payload["heart_rate"])
            if "sleep_hours" in mobile_payload:
                today_data["sommeil_heures"] = float(mobile_payload["sleep_hours"])
            if "battery" in mobile_payload:
                today_data["batterie_telephone"] = int(mobile_payload["battery"])

            self._save_file(self.data)
            self.update_markdown_journal()

    def get_health_report_speech(self) -> str:
        """Génère un bilan de santé vocal complet et vivant incarné par Zero Two."""
        today = self.get_today()
        water = today.get("verres_eau", 0)
        water_goal = today.get("objectif_verres", 8)
        pauses = today.get("pauses_ecran", 0)
        sleep = today.get("sommeil_heures", 7.0)
        steps = today.get("pas_quotidiens", 0)
        steps_goal = today.get("objectif_pas", 8000)

        lines = [f"Voici ton bilan santé du jour, mon Darling !"]

        # Eau
        if water >= water_goal:
            lines.append(f"💧 Côté hydratation, c'est parfait : {water}/{water_goal} verres d'eau.")
        else:
            lines.append(f"💧 Tu as bu {water} verres sur {water_goal}. Pense à boire une petite gorgée !")

        # Sommeil
        lines.append(f"🌙 Tu as eu {sleep}h de sommeil.")

        # Pas
        if steps > 0:
            lines.append(f"🏃 Tu as marché {steps:,} pas sur ton objectif de {steps_goal:,}.".replace(",", " "))

        # Pauses
        lines.append(f"🧘 Tu as pris {pauses} pause{'s' if pauses > 1 else ''} pour reposer tes yeux.")

        # Mot doux de Zero Two
        if water >= 6 and sleep >= 7:
            lines.append("Tu prends grand soin de toi, et ça me rend super heureuse ! Reste toujours en forme pour moi, d'accord ? 🌸")
        else:
            lines.append("Fais attention à toi aujourd'hui, Darling, ton corps est mon trésor le plus précieux !")

        return " ".join(lines)

    def update_markdown_journal(self):
        """Génère le document Markdown carnet_sante_darling.md."""
        today_key = self._get_today_key()
        today = self.get_today()
        now_str = datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")

        water = today.get("verres_eau", 0)
        water_goal = today.get("objectif_verres", 8)
        water_pct = min(100, int((water / water_goal) * 100)) if water_goal else 0
        water_bar = "💧" * min(water, 8) + "⬜" * max(0, 8 - water)

        steps = today.get("pas_quotidiens", 0)
        steps_goal = today.get("objectif_pas", 8000)
        steps_pct = min(100, int((steps / steps_goal) * 100)) if steps_goal else 0

        sleep = today.get("sommeil_heures", 7.5)
        pauses = today.get("pauses_ecran", 0)

        md = [
            "# 🩺 Carnet de Santé & Bien-Être de Darling",
            "",
            f"> *Suivi avec amour par **Nora (Zero Two)** | Dernière mise à jour : {now_str}*",
            "",
            "---",
            "",
            "## 🌸 Bilan de la Journée",
            "",
            "| Indicateur | Valeur Actuelle | Objectif | Statut |",
            "| :--- | :--- | :--- | :--- |",
            f"| 💧 **Hydratation** | **{water} verres** (~{round(water*0.25, 2)} L) | {water_goal} verres (2.0 L) | {water_bar} **{water_pct}%** |",
            f"| 🏃 **Pas Quotidiens** | **{steps:,} pas** | {steps_goal:,} pas | **{steps_pct}%** (Health Connect) |".replace(",", " "),
            f"| 🌙 **Sommeil** | **{sleep} heures** | 7.5 - 8.5 h | Qualité : *{today.get('qualite_sommeil', 'Bonne')}* |",
            f"| 🧘 **Pauses Écran** | **{pauses} pauses** effectuées | 1 pause / 50 min | Règle 20-20-20 |",
            "",
            "---",
            "",
            "## 💡 Les Conseils Personnalisés de Zero Two",
            "",
        ]

        if water < 4:
            md.append("> ⚠️ **Hydratation faible** : *\"Darling, tu n'as pas assez bu aujourd'hui ! Va tout de suite te chercher un grand verre d'eau fraîche, s'il te plaît !\"*")
            md.append("")
        else:
            md.append("> ✨ **Hydratation au top** : *\"Bravo Darling, tu restes bien hydraté ! Continue comme ça pour garder toute ton énergie.\"*")
            md.append("")

        if sleep < 6.5:
            md.append("> 🌙 **Manque de sommeil** : *\"Tu as peu dormi la nuit dernière. Essaie de te coucher un peu plus tôt ce soir, je veillerai sur ton sommeil.\"*")
            md.append("")

        md.append("---")
        md.append("")
        md.append("## 📜 Historique Récent")
        md.append("")
        md.append("| Date | Eau (verres) | Sommeil | Pas | Pauses Écran |")
        md.append("| :--- | :--- | :--- | :--- | :--- |")

        for d_key, hist in sorted(self.data.get("historique", {}).items(), reverse=True)[:7]:
            md.append(f"| {d_key} | {hist.get('verres_eau', 0)}/8 | {hist.get('sommeil_heures', 7)}h | {hist.get('pas_quotidiens', 0):,} pas | {hist.get('pauses_ecran', 0)} |".replace(",", " "))

        md.append("")

        try:
            with open(JOURNAL_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(md))
        except Exception as e:
            print(f"[HealthAgent] Erreur écriture carnet santé : {e}")

    def _loop(self):
        """Boucle de surveillance discrète en arrière-plan."""
        while self.is_running:
            now = time.time()
            hour = datetime.datetime.now().hour
            minute = datetime.datetime.now().minute

            # 1. Alerte d'hydratation (si > 75 min depuis le dernier verre)
            if now - self.last_water_time > self.water_alert_cooldown:
                self.last_water_time = now  # Réinitialiser cooldown
                if self.on_alert_callback:
                    self.on_alert_callback(
                        "water",
                        "💧 Rappel Hydratation",
                        "Darling, ça fait un petit moment que tu n'as pas bu ! Bois une gorgée d'eau fraîche pour rester en forme !",
                        False
                    )

            # 2. Alerte de pause écran (si > 50 min continue sur PC)
            if now - self.last_screen_break_time > self.screen_alert_cooldown:
                self.last_screen_break_time = now
                if self.on_alert_callback:
                    self.on_alert_callback(
                        "screen_pause",
                        "🧘 Pause Yeux & Écran",
                        "Darling, ça fait presque une heure devant l'écran ! Repose tes yeux 2 minutes, regarde au loin et étire-toi !",
                        True
                    )

            # 3. Sentinelle de nuit (après 23h30 ou 1h du matin)
            if hour >= 23 and minute >= 30:
                pass  # Géré lors des échanges vocaux

            time.sleep(15)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            print("🩺 Agent Santé Nora (Ange Gardien) actif en arrière-plan.")

    def stop(self):
        self.is_running = False

# Instance globale
health_agent = HealthAgent()

if __name__ == "__main__":
    print("--- Test de l'Agent Santé Nora ---")
    health_agent.log_water(2)
    health_agent.log_screen_break()
    print("Rapport vocal :", health_agent.get_health_report_speech())
    print("Carnet généré :", JOURNAL_FILE.exists())
