"""
Gestionnaire de mémoire persistante pour Nora et son équipe d'agents.
Conserve l'historique des missions, les préférences, le prénom et les habitudes de l'utilisateur.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
import math

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

def search_memory_semantic(query: str, top_k: int = 3) -> list:
    """Recherche vectorielle sémantique par similarité cosinus TF-IDF locale (0 ms, sans dépendance lourde)."""
    import re
    from collections import Counter
    mem = load_memory()
    faits = mem.get("user", {}).get("faits_appris", [])
    missions = [m.get("objectif", "") + " " + m.get("resume", "") for m in mem.get("missions_historique", [])]
    documents = faits + missions

    if not documents or not query:
        return documents[:top_k]

    def tokenize(text):
        return re.findall(r'\b\w+\b', text.lower())

    q_tokens = tokenize(query)
    q_vec = Counter(q_tokens)
    q_len = math.sqrt(sum(v ** 2 for v in q_vec.values())) if q_vec else 1.0

    scores = []
    for doc in documents:
        d_tokens = tokenize(doc)
        d_vec = Counter(d_tokens)
        d_len = math.sqrt(sum(v ** 2 for v in d_vec.values())) if d_vec else 1.0
        
        # Produit scalaire
        dot = sum(q_vec[k] * d_vec.get(k, 0) for k in q_vec)
        sim = dot / (q_len * d_len) if (q_len * d_len) > 0 else 0.0
        scores.append((sim, doc))

    scores.sort(key=lambda x: x[0], reverse=True)
    return [doc for sim, doc in scores[:top_k] if sim > 0.05] or documents[:top_k]

def add_learned_fact(fact: str):
    """Enregistre un nouveau fait sémantique dans la mémoire persistante."""
    mem = load_memory()
    faits = mem.setdefault("user", {}).setdefault("faits_appris", [])
    if fact not in faits:
        faits.append(fact)
        save_memory(mem)

def get_welcome_message() -> str:
    """Génère un message d'accueil personnalisé et respectueux pour Maverick."""
    name = get_user_name()
    mem = load_memory()
    count = mem.get("statistiques", {}).get("missions_reussies", 0)

    if count > 0:
        return f"Ravi de vous retrouver, {name} ! Toutes les sondes et agents sont opérationnels. Comment puis-je vous assister aujourd'hui ?"
    else:
        return f"Bonjour {name} ! Je suis Nora, votre copilote et esprit d'équipe IA. De quoi avez-vous besoin aujourd'hui ?"
