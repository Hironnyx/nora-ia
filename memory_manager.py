"""
Gestionnaire de mémoire persistante pour Nora et son équipe d'agents.
Conserve l'historique des missions, les préférences, le prénom et les habitudes de l'utilisateur.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent

MEMORY_FILE = (BASE_DIR / "memoire_nora.json").resolve()

DEFAULT_MEMORY = {
    "user": {
        "name": "Maverick",
        "preferences": {
            "theme_visuel": "cyberpunk",
            "mode_vocal": True,
            "dossiers_favoris": ["Downloads", "Desktop", "Documents"]
        },
        "faits_appris": [
            "L'utilisateur travaille sur Windows.",
            "L'utilisateur s'intéresse à la programmation Python et aux agents IA."
        ]
    },
    "missions_historique": [],
    "statistiques": {
        "missions_reussies": 0,
        "fichiers_reorganises": 0,
        "doublons_traites": 0,
        "derniere_interaction": None
    }
}

_cached_memory = None

def load_memory(force_reload: bool = False) -> dict:
    """Charge la mémoire depuis le cache RAM (0 ms), ou depuis le disque si premier accès."""
    global _cached_memory
    if _cached_memory is not None and not force_reload:
        return _cached_memory

    if not MEMORY_FILE.exists():
        save_memory(DEFAULT_MEMORY)
        _cached_memory = DEFAULT_MEMORY.copy()
        return _cached_memory
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Compléter les champs manquants éventuels
            for k, v in DEFAULT_MEMORY.items():
                if k not in data:
                    data[k] = v
            _cached_memory = data
            return _cached_memory
    except Exception as e:
        print(f"Erreur chargement mémoire : {e}")
        _cached_memory = DEFAULT_MEMORY.copy()
        return _cached_memory

def save_memory(data: dict):
    """Enregistre l'état actuel de la mémoire dans le cache RAM et dans le fichier JSON."""
    global _cached_memory
    _cached_memory = data
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erreur sauvegarde mémoire : {e}")

def get_user_name() -> str:
    """Retourne le prénom de l'utilisateur."""
    mem = load_memory()
    return mem.get("user", {}).get("name", "Maverick")

def set_user_name(name: str):
    """Met à jour le prénom de l'utilisateur."""
    mem = load_memory()
    mem["user"]["name"] = name.strip()
    save_memory(mem)

def add_user_fact(fact: str):
    """Enregistre un fait ou une habitude apprise sur l'utilisateur."""
    mem = load_memory()
    faits = mem["user"].setdefault("faits_appris", [])
    if fact not in faits:
        faits.append(fact)
        if len(faits) > 25:  # Limiter pour garder l'essentiel
            faits.pop(0)
        save_memory(mem)

def get_current_outfit() -> str:
    """Retourne la tenue actuellement sélectionnée pour Nora (franxx, school, hoodie)."""
    mem = load_memory()
    return mem.get("user", {}).get("preferences", {}).get("tenue_active", "franxx")

def set_current_outfit(outfit: str):
    """Sauvegarde la tenue active choisie par l'utilisateur."""
    if outfit not in ["franxx", "school", "hoodie"]:
        outfit = "franxx"
    mem = load_memory()
    prefs = mem.setdefault("user", {}).setdefault("preferences", {})
    prefs["tenue_active"] = outfit
    save_memory(mem)

def is_voice_cloning_enabled() -> bool:
    """Indique si le clonage vocal Zero Two RVC sur RTX 4080 est activé."""
    mem = load_memory()
    return mem.get("user", {}).get("preferences", {}).get("voice_cloning_zero_two", True)

def set_voice_cloning_enabled(enabled: bool):
    """Active ou désactive le clonage vocal Zero Two RVC."""
    mem = load_memory()
    prefs = mem.setdefault("user", {}).setdefault("preferences", {})
    prefs["voice_cloning_zero_two"] = bool(enabled)
    save_memory(mem)

def record_completed_mission(goal: str, summary: str):
    """Enregistre une mission réussie dans l'historique de Nora."""
    mem = load_memory()
    now_str = datetime.now().strftime("%d/%m/%Y à %H:%M")

    mem["missions_historique"].append({
        "date": now_str,
        "objectif": goal,
        "resume": summary[:250]
    })
    # Conserver les 10 dernières missions
    if len(mem["missions_historique"]) > 10:
        mem["missions_historique"].pop(0)

    stats = mem.setdefault("statistiques", {})
    stats["missions_reussies"] = stats.get("missions_reussies", 0) + 1
    stats["derniere_interaction"] = now_str
    save_memory(mem)

def format_memory_for_prompt() -> str:
    """Formate la mémoire de Nora sous forme de texte concis pour le contexte de Gemini."""
    mem = load_memory()
    user = mem.get("user", {})
    name = user.get("name", "l'utilisateur")
    faits = user.get("faits_appris", [])
    missions = mem.get("missions_historique", [])
    
    lines = [f"- L'utilisateur s'appelle : {name}"]
    if faits:
        lines.append("- Ce que tu sais sur lui : " + " ; ".join(faits[-4:]))
    if missions:
        last = missions[-1]
        lines.append(f"- Dernière mission réussie ({last['date']}) : '{last['objectif']}'")
    
    return "\n".join(lines)

def get_welcome_message() -> str:
    """Génère un message d'accueil personnalisé basé sur les souvenirs de Nora."""
    mem = load_memory()
    name = get_user_name()
    missions = mem.get("missions_historique", [])
    count = mem.get("statistiques", {}).get("missions_reussies", 0)

    if missions:
        last_mission = missions[-1]
        return f"Ravi de te revoir {name} ! Nos {count} mission(s) passée(s) se sont super bien passées. Que puis-je faire pour toi aujourd'hui ?"
    else:
        return f"Bonjour {name} ! Je suis Nora, ta mascotte et copilote IA. Je me souviens de tout ! De quoi as-tu besoin ?"
