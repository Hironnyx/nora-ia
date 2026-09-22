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
                msg = f"Parfait Maverick ! Vous avez bu votre {current}ème verre d'eau, votre objectif quotidien est validé ! 💧"
            else:
                msg = f"C'est noté, Maverick. Vous en êtes à {current}/{goal} verres d'eau aujourd'hui. 💧"
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
            return f"Pause enregistrée, Maverick. Vous avez accordé {pauses} pause{'s' if pauses > 1 else ''} à vos yeux aujourd'hui. 🧘"

    def log_sleep(self, hours: float, quality: str = "Bonne") -> str:
        """Enregistre les heures de sommeil de la nuit précédente."""
        with self._lock:
            today_data = self.get_today()
            today_data["sommeil_heures"] = round(hours, 1)
            today_data["qualite_sommeil"] = quality
            self._save_file(self.data)
            self.update_markdown_journal()

            if hours < 6:
                return f"Vous n'avez dormi que {hours} heures, Maverick. Pensez à modérer vos efforts aujourd'hui et à faire des pauses régulières. 🌙"
            elif hours >= 8:
                return f"{hours} heures de sommeil réparateur, parfait, Maverick ! Vous voilà en excellente condition pour la journée. ✨"
            else:
                return f"C'est bien noté, {hours}h de sommeil. Vous êtes prêt pour la journée, Maverick."

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
        """Génère un bilan de santé vocal complet pour Maverick."""
        today = self.get_today()
        water = today.get("verres_eau", 0)
        water_goal = today.get("objectif_verres", 8)
        pauses = today.get("pauses_ecran", 0)
        sleep = today.get("sommeil_heures", 7.0)
        steps = today.get("pas_quotidiens", 0)
        steps_goal = today.get("objectif_pas", 8000)

        lines = [f"Voici votre bilan de santé et de forme du jour, Monsieur Maverick."]

        # Eau
        if water >= water_goal:
            lines.append(f"💧 Côté hydratation, votre objectif est atteint : {water}/{water_goal} verres d'eau.")
        else:
            lines.append(f"💧 Vous avez bu {water} verres sur {water_goal}. Pensez à vous hydrater régulièrement.")

        # Sommeil
        lines.append(f"🌙 Vous avez enregistré {sleep}h de sommeil.")

        # Pas
        if steps > 0:
            lines.append(f"🏃 Vous avez effectué {steps:,} pas sur votre objectif de {steps_goal:,}.".replace(",", " "))

        # Pauses
        lines.append(f"🧘 Vous avez accordé {pauses} pause{'s' if pauses > 1 else ''} à votre regard.")

        if water >= 6 and sleep >= 7:
            lines.append("Vous maintenez un excellent équilibre, continuez ainsi Maverick !")
        else:
            lines.append("Prenez soin de vous et ménagez vos efforts aujourd'hui, Maverick.")

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
            "## 💡 Les Conseils Personnalisés de Nora",
            "",
        ]

        if water < 4:
            md.append("> ⚠️ **Hydratation faible** : *\"Monsieur Maverick, vous n'avez pas assez bu aujourd'hui. Prenez un grand verre d'eau fraîche, s'il vous plaît.\"*")
            md.append("")
        else:
            md.append("> ✨ **Hydratation au top** : *\"Bravo Maverick, vous restez parfaitement hydraté ! Continuez ainsi pour préserver votre énergie.\"*")
            md.append("")

        if sleep < 6.5:
            md.append("> 🌙 **Manque de sommeil** : *\"Vous avez peu dormi la nuit dernière. Tâchez de vous reposer un peu plus tôt ce soir, je veillerai sur votre tranquillité.\"*")
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
                        "Monsieur Maverick, cela fait un moment que vous n'avez pas bu. Pensez à vous hydrater pour rester en forme !",
                        False
                    )

            # 2. Alerte de pause écran (si > 50 min continue sur PC)
            if now - self.last_screen_break_time > self.screen_alert_cooldown:
                self.last_screen_break_time = now
                if self.on_alert_callback:
                    self.on_alert_callback(
                        "screen_pause",
                        "🧘 Pause Yeux & Écran",
                        "Monsieur Maverick, cela fait près d'une heure devant l'écran. Reposez vos yeux deux minutes et étirez-vous.",
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
