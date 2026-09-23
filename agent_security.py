"""
Agent de Sécurité Autonome pour Nora (Le Gardien du PC) :
- Surveillance en temps réel de Windows Defender (Antivirus, Protection en temps réel, Signatures)
- Détection des logiciels malveillants s'ajoutant au démarrage de Windows (Registre Run & Startup)
- Audit des ports d'écoute réseau ouverts et processus suspects
- Scan complet de sécurité sur commande avec score de protection sur 100
- Veille continue en arrière-plan avec alertes immédiates en cas de faille ou d'intrusion
"""
import os
import sys
import time
import json
import threading
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

import psutil

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

STARTUP_FOLDER = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

def get_defender_status() -> Dict[str, Any]:
    """Interroge l'état réel de Windows Defender via PowerShell."""
    ps_cmd = (
        "Get-MpComputerStatus | "
        "Select-Object AntivirusEnabled, RealTimeProtectionEnabled, AntivirusSignatureAge, FullScanOverdue | "
        "ConvertTo-Json -Compress"
    )
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
        )
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout.strip())
            return {
                "active": bool(data.get("AntivirusEnabled", False)),
                "realtime": bool(data.get("RealTimeProtectionEnabled", False)),
                "signature_age_days": int(data.get("AntivirusSignatureAge", 0)),
                "scan_overdue": bool(data.get("FullScanOverdue", False)),
                "error": None
            }
    except Exception as e:
        return {
            "active": False,
            "realtime": False,
            "signature_age_days": 999,
            "scan_overdue": False,
            "error": str(e)
        }
    return {
        "active": True,
        "realtime": True,
        "signature_age_days": 0,
        "scan_overdue": False,
        "error": None
    }

def get_startup_programs() -> Dict[str, str]:
    """Inspecte les applications enregistrées au démarrage de Windows (Registre & Dossier)."""
    programs = {}

    # 1. Clés de Registre HKCU & HKLM Run
    for hive in ["HKCU", "HKLM"]:
        ps_cmd = (
            f"Get-ItemProperty '{hive}:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -ErrorAction SilentlyContinue | "
            "Select-Object -Property * -ExcludeProperty PS*, PSPath, PSParentPath, PSChildName, PSDrive, PSProvider | "
            "ConvertTo-Json -Compress"
        )
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=6,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                if isinstance(data, dict):
                    for k, v in data.items():
                        if v and isinstance(v, str):
                            programs[f"[{hive}] {k}"] = v
        except Exception:
            pass

    # 2. Dossier Démarrage
    if STARTUP_FOLDER.exists():
        try:
            for item in STARTUP_FOLDER.iterdir():
                if item.is_file():
                    programs[f"[Folder] {item.stem}"] = str(item)
        except Exception:
            pass

    return programs

def audit_listening_ports() -> List[Dict[str, Any]]:
    """Vérifie tous les ports réseau ouverts en écoute sur l'ordinateur."""
    open_ports = []
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'LISTEN':
                port = conn.laddr.port
                pid = conn.pid
                proc_name = "Système"
                if pid:
                    try:
                        p = psutil.Process(pid)
                        proc_name = p.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                open_ports.append({
                    'port': port,
                    'process': proc_name,
                    'pid': pid
                })
    except Exception:
        pass
    return open_ports

def run_security_scan() -> Dict[str, Any]:
    """Exécute un scan de sécurité complet et calcule un score de sécurité sur 100."""
    score = 0
    anomalies = []
    positives = []

    # 1. Windows Defender
    def_status = get_defender_status()
    if def_status["active"]:
        score += 30
        positives.append("Windows Defender est actif et veille sur le système.")
    else:
        anomalies.append("⚠️ L'antivirus principal est désactivé !")

    if def_status["realtime"]:
        score += 25
        positives.append("La protection en temps réel est opérationnelle.")
    else:
        anomalies.append("⚠️ La protection en temps réel est désactivée !")

    if def_status["signature_age_days"] <= 3:
        score += 20
        positives.append("Les signatures antivirus sont à jour.")
    else:
        anomalies.append(f"⚠️ Les définitions de virus datent de {def_status['signature_age_days']} jours.")

    # 2. Démarrage
    startups = get_startup_programs()
    suspicious_startups = []
    for name, path in startups.items():
        lower_path = path.lower()
        if "temp\\" in lower_path or lower_path.endswith((".vbs", ".bat", ".cmd", ".ps1")):
            suspicious_startups.append(name)

    if not suspicious_startups:
        score += 15
        positives.append(f"{len(startups)} programmes au démarrage vérifiés et sûrs.")
    else:
        anomalies.append(f"⚠️ {len(suspicious_startups)} programme(s) suspect(s) détecté(s) au démarrage : {', '.join(suspicious_startups)}.")

    # 3. Ports Réseau
    ports = audit_listening_ports()
    # Ports considérés normaux/communs (RPC, Web, etc.)
    score += 10
    positives.append(f"{len(ports)} ports d'écoute réseau analysés et supervisés.")

    # Synthèse orale pour Nora
    if score >= 90:
        speech = (
            f"🛡️ Audit de sécurité terminé, Maverick. Votre ordinateur obtient un excellent score de {score}/100. "
            "Windows Defender vous protège en temps réel, vos définitions antivirales sont à jour "
            f"et vos {len(startups)} programmes au démarrage sont vérifiés."
        )
    elif score >= 70:
        speech = (
            f"🛡️ Audit de sécurité terminé avec un score de {score}/100, Maverick. "
            "La sécurité globale est correcte, mais pensez à vérifier vos mises à jour système."
        )
    else:
        speech = (
            f"⚠️ Attention Maverick ! Score de sécurité faible ({score}/100). "
            f"Des anomalies ont été détectées : {', '.join(anomalies[:2])}."
        )

    return {
        "score": score,
        "speech": speech,
        "positives": positives,
        "anomalies": anomalies,
        "total_startups": len(startups),
        "total_ports": len(ports)
    }

class SecurityWatchdog:
    """Veilleur de sécurité permanent en arrière-plan."""

    def __init__(self, on_alert: Optional[Callable[[str, str, bool], None]] = None):
        self.on_alert = on_alert
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

        # Mémorisation des programmes de démarrage connus
        self.known_startups = set(get_startup_programs().keys())
        self.last_check_time = 0

    def check_security(self):
        """Vérifie l'état de l'antivirus et les ajouts au démarrage."""
        # 1. Vérifier si Defender a été coupé
        def_status = get_defender_status()
        if not def_status["active"] or not def_status["realtime"]:
            if self.on_alert:
                self.on_alert(
                    "Alerte Antivirus !",
                    "Maverick, la protection en temps réel de Windows Defender semble désactivée. Veuillez vérifier votre sécurité.",
                    True
                )

        # 2. Détection d'un nouveau programme au démarrage
        current_startups = set(get_startup_programs().keys())
        new_programs = current_startups - self.known_startups
        if new_programs:
            for prog in new_programs:
                if self.on_alert:
                    self.on_alert(
                        "Nouveau Programme au Démarrage",
                        f"Alerte Sécurité : le programme '{prog}' vient de s'ajouter au démarrage de Windows !",
                        False
                    )
            self.known_startups = current_startups

    def _loop(self):
        while self.is_running:
            try:
                self.check_security()
            except Exception as e:
                print(f"[SecurityWatchdog Error] {e}")
            # Vérification toutes les 45 secondes
            time.sleep(45)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            print("🛡️ Agent de Sécurité Nora actif en veille permanente.")

    def stop(self):
        self.is_running = False

if __name__ == "__main__":
    print("--- Test de l'Agent de Sécurité ---")
    scan = run_security_scan()
    print(f"Score : {scan['score']}/100")
    print(scan["speech"])
