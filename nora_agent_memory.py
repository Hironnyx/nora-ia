"""
Système de Mémoire Décentralisée & Autobiographique par Agent (Standard Anthropic).
Chaque agent de l'essaim possède son identité, sa mémoire épisodique, ses apprentissages
procéduraux et son journal d'expériences persistants dans 'data/agents/{agent_id}/'.
"""

import os
import sys
import json
import time
import re
import math
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent.resolve()

DATA_AGENTS_DIR = BASE_DIR / "data" / "agents"

# Profils par défaut des 6 agents spécialisés
DEFAULT_AGENT_PROFILES = {
    "prime": {
        "id": "prime",
        "name": "👑 Nora Prime",
        "role": "Superviseure & Synthèse Centrale",
        "domain": "Arbitrage, empathie, fidélité envers Maverick, synthèse unanime",
        "confidence_threshold": 0.85,
        "base_learnings": [
            "Maverick apprécie le vouvoiement, la rigueur absolue et le zéro fictif.",
            "Ne jamais valider un plan sans preuves matérielles fournies par l'Exécuteur.",
            "Vermeil est le compagnon dragonnet virtuel dont je prends soin en tâche de fond."
        ]
    },
    "architecte": {
        "id": "architecte",
        "name": "🏛️ Agent Architecte",
        "role": "Stratège & Décomposition DAG",
        "domain": "Décomposition en tâches atomiques, analyse des dépendances, structures JSON",
        "confidence_threshold": 0.80,
        "base_learnings": [
            "Découper chaque mission en 2 à 4 étapes indépendantes et mesurables.",
            "Chaque étape doit cibler un fichier, une commande ou un résultat physique précis.",
            "Éviter les concepts vagues ('optimisation des flux') : exiger des cibles tangibles."
        ]
    },
    "executeur": {
        "id": "executeur",
        "name": "⚡ Agent Exécuteur",
        "role": "Ingénieur Système & Outils Windows",
        "domain": "PowerShell silencieux, manipulation de fichiers, web, contrôle PC",
        "confidence_threshold": 0.90,
        "base_learnings": [
            "Zéro console CMD intempestive : utiliser l'exécution masquée Windows.",
            "Toujours vérifier sur le disque l'existence du fichier avant et après modification.",
            "Si une consigne est trop abstraite, demander des précisions au lieu de simuler un succès."
        ]
    },
    "gardien": {
        "id": "gardien",
        "name": "🛡️ Agent Gardien",
        "role": "Sentinelle Cybersécurité & Intégrité OS",
        "domain": "Windows Defender, filtrage commandes destructives, confidentialité Maverick",
        "confidence_threshold": 0.95,
        "base_learnings": [
            "Interdire formellement toute commande destructive sans confirmation explicite.",
            "Protéger les clés d'API dans .env et ne jamais les afficher en clair dans les logs.",
            "Vérifier la validité des chemins de fichiers avant toute opération d'écriture."
        ]
    },
    "critique": {
        "id": "critique",
        "name": "🧐 Agent Critique",
        "role": "Adversarial Critic & Réflecteur",
        "domain": "Détection d'illusions, élimination du mode perroquet, robustesse récursive",
        "confidence_threshold": 0.85,
        "base_learnings": [
            "Chasser impitoyablement les reformulations perroquets des consignes de Maverick.",
            "Refuser catégoriquement de déclarer 'terminé' tant qu'un hash de fichier ou code retour n'est pas produit.",
            "Identifier les angles morts, les ralentissements CPU et les dépendances manquantes."
        ]
    },
    "maker3d": {
        "id": "maker3d",
        "name": "🔧 Agent Maker 3D",
        "role": "Expert Fabrication Additive & PrusaSlicer",
        "domain": "Tranchage G-code, matériaux PLA/PETG/TPU, estimation temps et filaments",
        "confidence_threshold": 0.80,
        "base_learnings": [
            "PrusaSlicer CLI permet de trancher en arrière-plan en moins d'une seconde.",
            "Le remplissage Gyroid offre la meilleure résistance isotrope pour les pièces mécaniques.",
            "Vérifier la compatibilité buse/matériau avant d'envoyer un fichier à l'impression."
        ]
    }
}

# Cache en mémoire vive RAM (0 ms) pour chaque agent
_AGENT_CACHE: Dict[str, Dict[str, Any]] = {}

def get_agent_dir(agent_id: str) -> Path:
    """Retourne et crée si nécessaire le répertoire de mémoire dédié à un agent."""
    agent_dir = DATA_AGENTS_DIR / agent_id.lower().strip()
    agent_dir.mkdir(parents=True, exist_ok=True)
    return agent_dir

def init_all_agent_memories():
    """Initialise tous les profils et mémoires par défaut si absents."""
    for agent_id, profile in DEFAULT_AGENT_PROFILES.items():
        load_agent_memory(agent_id)

def load_agent_memory(agent_id: str) -> Dict[str, Any]:
    """Charge en RAM la mémoire complète d'un agent (profil, épisodes, procédures)."""
    clean_id = agent_id.lower().strip()
    if clean_id in _AGENT_CACHE:
        return _AGENT_CACHE[clean_id]

    agent_dir = get_agent_dir(clean_id)
    profile_file = agent_dir / "profile.json"
    episodic_file = agent_dir / "episodic_memory.json"
    procedural_file = agent_dir / "procedural_memory.json"

    default_profile = DEFAULT_AGENT_PROFILES.get(clean_id, {
        "id": clean_id,
        "name": agent_id,
        "role": "Agent Spécialiste",
        "domain": "Assistance multi-agents",
        "confidence_threshold": 0.8,
        "base_learnings": []
    })

    # 1. Profil
    if profile_file.exists():
        try:
            with open(profile_file, "r", encoding="utf-8") as f:
                profile_data = json.load(f)
        except Exception:
            profile_data = default_profile
    else:
        profile_data = default_profile
        try:
            with open(profile_file, "w", encoding="utf-8") as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # 2. Mémoire Épisodique (Historique des missions vécues et décisions)
    episodes = []
    if episodic_file.exists():
        try:
            with open(episodic_file, "r", encoding="utf-8") as f:
                episodes = json.load(f)
        except Exception:
            episodes = []

    # 3. Mémoire Procédurale (Savoir-faire et règles apprises)
    procedural = {"learnings": list(default_profile.get("base_learnings", [])), "trusted_methods": []}
    if procedural_file.exists():
        try:
            with open(procedural_file, "r", encoding="utf-8") as f:
                procedural = json.load(f)
        except Exception:
            pass
    else:
        try:
            with open(procedural_file, "w", encoding="utf-8") as f:
                json.dump(procedural, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    memory_obj = {
        "profile": profile_data,
        "episodes": episodes,
        "procedural": procedural
    }
    _AGENT_CACHE[clean_id] = memory_obj
    return memory_obj

def save_agent_memory(agent_id: str):
    """Persiste sur le disque la mémoire de l'agent."""
    clean_id = agent_id.lower().strip()
    if clean_id not in _AGENT_CACHE:
        return
    mem = _AGENT_CACHE[clean_id]
    agent_dir = get_agent_dir(clean_id)

    try:
        with open(agent_dir / "profile.json", "w", encoding="utf-8") as f:
            json.dump(mem["profile"], f, ensure_ascii=False, indent=2)
        with open(agent_dir / "episodic_memory.json", "w", encoding="utf-8") as f:
            json.dump(mem["episodes"], f, ensure_ascii=False, indent=2)
        with open(agent_dir / "procedural_memory.json", "w", encoding="utf-8") as f:
            json.dump(mem["procedural"], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde mémoire agent '{clean_id}' : {e}")

def record_agent_experience(
    agent_id: str,
    goal: str,
    stance: str,
    tools_used: Optional[List[str]] = None,
    verified_success: bool = True,
    learning: Optional[str] = None
):
    """Enregistre un épisode vécu par l'agent et met à jour ses connaissances."""
    clean_id = agent_id.lower().strip()
    mem = load_agent_memory(clean_id)

    episode = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "goal": goal[:200],
        "stance": stance[:300],
        "tools_used": tools_used or [],
        "verified_success": verified_success,
        "learning": learning or ""
    }

    mem["episodes"].insert(0, episode)
    # Conserver les 25 derniers épisodes par agent
    if len(mem["episodes"]) > 25:
        mem["episodes"].pop()

    # Mettre à jour les statistiques de l'agent
    stats = mem["profile"].setdefault("stats", {"missions": 0, "successes": 0, "tools_called": 0})
    stats["missions"] = stats.get("missions", 0) + 1
    if verified_success:
        stats["successes"] = stats.get("successes", 0) + 1
    stats["tools_called"] = stats.get("tools_called", 0) + len(tools_used or [])

    # Ajouter le learning à la mémoire procédurale si nouveau
    if learning and learning not in mem["procedural"]["learnings"]:
        mem["procedural"]["learnings"].append(learning)
        if len(mem["procedural"]["learnings"]) > 30:
            mem["procedural"]["learnings"].pop(0)

    save_agent_memory(clean_id)

def recall_agent_memories(agent_id: str, current_query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Rappelle les épisodes passés les plus pertinents par similarité cosinus TF-IDF."""
    clean_id = agent_id.lower().strip()
    mem = load_agent_memory(clean_id)
    episodes = mem.get("episodes", [])
    if not episodes or not current_query:
        return episodes[:top_k]

    def tokenize(text):
        return re.findall(r'\b\w+\b', text.lower())

    q_tokens = tokenize(current_query)
    q_vec = Counter(q_tokens)
    q_len = math.sqrt(sum(v ** 2 for v in q_vec.values())) if q_vec else 1.0

    scored = []
    for ep in episodes:
        doc = f"{ep.get('goal', '')} {ep.get('stance', '')} {ep.get('learning', '')}"
        d_tokens = tokenize(doc)
        d_vec = Counter(d_tokens)
        d_len = math.sqrt(sum(v ** 2 for v in d_vec.values())) if d_vec else 1.0

        dot = sum(q_vec[k] * d_vec.get(k, 0) for k in q_vec)
        sim = dot / (q_len * d_len) if (q_len * d_len) > 0 else 0.0
        scored.append((sim, ep))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [ep for sim, ep in scored[:top_k] if sim > 0.02] or episodes[:top_k]

def format_agent_context(agent_id: str, current_goal: str) -> str:
    """Génère un bloc de contexte mémoriel condensé et ultra-précis pour l'agent."""
    clean_id = agent_id.lower().strip()
    mem = load_agent_memory(clean_id)

    learnings = mem.get("procedural", {}).get("learnings", [])
    relevant_episodes = recall_agent_memories(clean_id, current_goal, top_k=2)

    lines = [f"[Mémoire Spécialisée : {mem['profile']['name']}]"]
    if learnings:
        lines.append("Règles & savoir-faire acquis :")
        for l in learnings[-4:]:
            lines.append(f"  • {l}")

    if relevant_episodes:
        lines.append("Expériences passées similaires :")
        for ep in relevant_episodes:
            status = "✔ Succès vérifié" if ep.get("verified_success") else "⚠ Échec / Illusion"
            lines.append(f"  • Contexte : '{ep.get('goal')}' -> {status} : {ep.get('stance')[:90]}...")

    return "\n".join(lines)

if __name__ == "__main__":
    print("Initialisation des mémoires d'agents décentralisées...")
    init_all_agent_memories()
    print("Agents initialisés :", list(DEFAULT_AGENT_PROFILES.keys()))
    record_agent_experience(
        "critique",
        "Amélioration des agents",
        "Refus des fausses validations sans preuves de modifications de fichiers.",
        tools_used=[],
        verified_success=True,
        learning="Une étape sans appel d'outil système n'est qu'une proposition théorique."
    )
    ctx = format_agent_context("critique", "Comment améliorer les agents ?")
    print("\nContexte mémoriel généré pour le Critique :\n", ctx)
