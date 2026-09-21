"""
Moteur d'Auto-amélioration et de Prise d'Initiatives Proactives pour Nora :
- Veille proactive : analyse l'état du PC et détecte les améliorations utiles à proposer
- RÈGLE FONDAMENTALE : Nora DEMANDE TOUJOURS L'ACCORD DE L'UTILISATEUR AVANT D'AGIR
- Enregistre les initiatives acceptées dans la mémoire persistante pour apprendre et évoluer
"""
import os
import sys
import time
import json
import threading
from pathlib import Path
from typing import Optional, Dict, Any

import tools_pc
import memory_manager

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

DOWNLOADS_DIR = Path.home() / "Downloads"
TEMP_DIR = Path(os.environ.get("TEMP", "C:\\Windows\\Temp"))

# État de l'initiative en attente d'approbation
_current_pending_initiative: Optional[Dict[str, Any]] = None
_last_scan_attempt_time: float = 0.0
_is_scanning: bool = False
_scan_lock = threading.Lock()

# Historique des propositions pour respecter un délai (cooldown de 12h par initiative)
_initiative_cooldowns: Dict[str, float] = {}
COOLDOWN_SECONDS = 43200  # 12 heures

def get_pending_initiative() -> Optional[Dict[str, Any]]:
    return _current_pending_initiative

def set_pending_initiative(init_data: Dict[str, Any]):
    global _current_pending_initiative
    _current_pending_initiative = init_data

def clear_pending_initiative():
    global _current_pending_initiative
    _current_pending_initiative = None

def can_propose(init_id: str) -> bool:
    now = time.time()
    last = _initiative_cooldowns.get(init_id, 0)
    return (now - last) > COOLDOWN_SECONDS

def mark_proposed(init_id: str):
    _initiative_cooldowns[init_id] = time.time()

def _run_scan_background():
    global _current_pending_initiative, _is_scanning
    with _scan_lock:
        try:
            # 1. Initiative : Rangement du dossier Téléchargements
            if can_propose("organize_downloads") and DOWNLOADS_DIR.exists():
                unorganized_files = [f for f in DOWNLOADS_DIR.iterdir() if f.is_file() and not f.name.endswith(('.tmp', '.crdownload'))]
                if len(unorganized_files) >= 10:
                    mark_proposed("organize_downloads")
                    _current_pending_initiative = {
                        "id": "organize_downloads",
                        "title": "Rangement des Téléchargements",
                        "speech": (
                            f"Dis Darling, j'ai remarqué que ton dossier Téléchargements a accumulé {len(unorganized_files)} fichiers en vrac. "
                            "Veux-tu que je range tout automatiquement par catégories propres ?"
                        ),
                        "action_name": "Ranger Téléchargements"
                    }
                    return

            # 2. Initiative : Nettoyage des fichiers temporaires Windows
            if can_propose("clean_temp") and TEMP_DIR.exists():
                total_bytes = 0
                for item in TEMP_DIR.iterdir():
                    if item.is_file():
                        try:
                            total_bytes += item.stat().st_size
                        except Exception:
                            pass
                size_mb = int(total_bytes / (1024 * 1024))
                if size_mb >= 300:
                    mark_proposed("clean_temp")
                    _current_pending_initiative = {
                        "id": "clean_temp",
                        "title": "Nettoyage Fichiers Temporaires",
                        "speech": (
                            f"Darling, j'ai repéré environ {size_mb} Mo de fichiers temporaires inutiles qui dorment sur ton disque C:. "
                            "Tu veux que je fasse un brin de ménage pour libérer cet espace ?"
                        ),
                        "action_name": "Nettoyer Fichiers Temp"
                    }
                    return

            # 3. Initiative : Scan de Sécurité de routine
            if can_propose("routine_security_scan"):
                mark_proposed("routine_security_scan")
                _current_pending_initiative = {
                    "id": "routine_security_scan",
                    "title": "Scan de Sécurité Périodique",
                    "speech": "Darling, nous n'avons pas vérifié les défenses et les ports de ton PC depuis un moment. Tu veux qu'on lance un scan rapide de sécurité ?",
                    "action_name": "Lancer Scan Sécurité"
                }
                return
        except Exception:
            pass
        finally:
            _is_scanning = False

def scan_for_initiatives() -> Optional[Dict[str, Any]]:
    """
    Scanne l'environnement de manière 100% asynchrone (aucun blocage de l'interface graphique).
    """
    global _last_scan_attempt_time, _is_scanning, _current_pending_initiative
    if _current_pending_initiative is not None:
        return _current_pending_initiative

    now = time.time()
    # Limiter le déclenchement de scan à une fois toutes les 2 minutes pour préserver le disque
    if (now - _last_scan_attempt_time > 120.0) and not _is_scanning:
        _last_scan_attempt_time = now
        _is_scanning = True
        t = threading.Thread(target=_run_scan_background, daemon=True)
        t.start()

    return _current_pending_initiative

def execute_accepted_initiative(init_id: str) -> str:
    """
    Exécute l'initiative APRÈS que l'utilisateur a donné son accord explicite.
    """
    global _current_pending_initiative
    clear_pending_initiative()

    result_message = "C'est fait Darling !"

    if init_id == "organize_downloads":
        try:
            report = tools_pc.organize_folder(DOWNLOADS_DIR)
            result_message = "Super Darling ! J'ai rangé tous tes téléchargements par catégories bien nettes."
            _record_learned_skill("Rangement autonome des téléchargements sur demande du Darling")
        except Exception as e:
            result_message = f"Une erreur est survenue pendant le rangement : {e}"

    elif init_id == "clean_temp":
        cleaned_mb = 0
        deleted_count = 0
        try:
            for item in TEMP_DIR.iterdir():
                if item.is_file():
                    try:
                        # Supprimer les fichiers de plus de 12 heures
                        if time.time() - item.stat().st_mtime > 43200:
                            sz = item.stat().st_size
                            item.unlink()
                            cleaned_mb += sz
                            deleted_count += 1
                    except Exception:
                        pass
            cleaned_mb = int(cleaned_mb / (1024 * 1024))
            result_message = f"Ménage terminé Darling ! J'ai libéré {cleaned_mb} Mo de fichiers temporaires inutiles."
            _record_learned_skill(f"Nettoyage de {cleaned_mb} Mo temporaires validé par le Darling")
        except Exception as e:
            result_message = f"Ménage partiel effectué : {e}"

    elif init_id == "routine_security_scan":
        import agent_security
        scan = agent_security.run_security_scan()
        result_message = f"Scan terminé avec succès Darling ! Score : {scan['score']}/100. Tout est sous contrôle !"
        _record_learned_skill(f"Audit de sécurité validé avec un score de {scan['score']}/100")

    return result_message

def refuse_initiative(init_id: str) -> str:
    """Enregistre le refus de l'utilisateur sans rien faire."""
    clear_pending_initiative()
    return "C'est compris Darling, je ne touche à rien !"

def _record_learned_skill(description: str):
    """Enregistre l'action réussie dans la mémoire persistante de Nora."""
    try:
        data = memory_manager.load_memory()
        if "initiatives_reussies" not in data.get("statistiques", {}):
            data.setdefault("statistiques", {})["initiatives_reussies"] = 0
        data["statistiques"]["initiatives_reussies"] += 1

        history = data.setdefault("initiatives_historique", [])
        history.append({
            "date": time.strftime("%d/%m/%Y à %H:%M"),
            "action": description
        })
        if len(history) > 20:
            data["initiatives_historique"] = history[-20:]

        memory_manager.save_memory(data)
    except Exception as e:
        print(f"[Memory Init Error] {e}")

if __name__ == "__main__":
    print("--- Test du Moteur d'Initiatives ---")
    init = scan_for_initiatives()
    if init:
        print(f"Initiative proposée : [{init['title']}]")
        print(f"Speech : {init['speech']}")
    else:
        print("Aucune initiative requise pour le moment.")
