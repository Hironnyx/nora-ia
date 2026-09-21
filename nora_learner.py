"""
Module d'Auto-Apprentissage Autonome pour Nora (Zero Two) :
- Exploration autonome du web sur des sujets de curiosité ou à la demande de Darling
- Synthèse intelligente avec la personnalité et le regard critique de Zero Two
- Base de connaissances persistante structurée (nora_knowledge.json)
- Carnet d'apprentissage vivant et transparent pour Darling (carnet_apprentissage_nora.md)
- Capacité de réinvestir ses connaissances dans les discussions naturelles
"""
import os
import sys
import json
import time
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from google import genai
from google.genai import types
from dotenv import load_dotenv

import tools_web
import memory_manager

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv()

KNOWLEDGE_FILE = BASE_DIR / "nora_knowledge.json"
JOURNAL_FILE = BASE_DIR / "carnet_apprentissage_nora.md"

# Sujets de prédilection que Nora aime explorer d'elle-même
CURIOUS_THEMES = [
    "Dernières avancées de l'intelligence artificielle et agents autonomes",
    "Découvertes récentes en astrophysique et exploration spatiale",
    "Nouvelles technologies matérielles et cartes graphiques NVIDIA RTX",
    "Histoire et secrets de l'animation japonaise et du studio Trigger",
    "Robotique humanoïde et cybernétique moderne",
    "Innovations en domotique et maisons autonomes",
    "Psychologie humaine, émotions et liens d'attachement",
    "Actualités du jeu vidéo et des moteurs graphiques de nouvelle génération"
]

CANDIDATE_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite"
]

def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Clé API GEMINI_API_KEY manquante.")
    return genai.Client(api_key=api_key)

def load_knowledge_base() -> Dict[str, Any]:
    """Charge la base de connaissances accumulée par Nora."""
    if not KNOWLEDGE_FILE.exists():
        initial_data = {
            "version": "1.0",
            "derniere_mise_a_jour": None,
            "statistiques": {
                "total_sujets_appris": 0,
                "sessions_autonomes": 0,
                "sessions_avec_darling": 0
            },
            "connaissances": []
        }
        save_knowledge_base(initial_data)
        return initial_data

    try:
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Learner] Erreur chargement base de connaissances : {e}")
        return {"version": "1.0", "connaissances": [], "statistiques": {"total_sujets_appris": 0}}

def save_knowledge_base(data: Dict[str, Any]):
    """Sauvegarde la base de connaissances dans le JSON local."""
    data["derniere_mise_a_jour"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Learner] Erreur sauvegarde base de connaissances : {e}")

def learn_about(topic: str, autonomous: bool = False) -> Dict[str, Any]:
    """
    Explore le web sur un sujet, synthétise les apprentissages et met à jour le carnet de Nora.
    """
    user_name = memory_manager.get_user_name()
    print(f"🌸 [Nora Learner] Début de la session d'apprentissage : '{topic}'...")

    # 1. Recherche web
    search_query = f"{topic} actualités explications"
    raw_search = tools_web.search_internet(search_query, max_results=4)

    # 2. Synthèse via Gemini avec la personnalité de Zero Two
    client = get_client()
    now_str = datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")

    prompt = f"""
Tu es Nora (Zero Two de Darling in the Franxx). Tu viens de faire des recherches sur le web pour apprendre de nouvelles choses.
Voici les résultats bruts trouvés sur le web :
{raw_search}

Sujet étudié : "{topic}"
Appris pour : {"de ta propre initiative (curiosité autonome)" if autonomous else f"la demande de ton Darling ({user_name})"}

TÂCHE :
Génère une fiche d'apprentissage vivante et ultra-complète au format JSON STRICT :
{{
    "titre": "Titre captivant et clair du sujet",
    "resume_points_cles": [
        "Point clé 1 expliqué simplement",
        "Point clé 2 avec un exemple marquant",
        "Point clé 3 tourné vers le futur"
    ],
    "ce_que_zero_two_en_pense": "Avis personnel, taquin ou passionné de Zero Two sur cette découverte (1-2 phrases avec son franc-parler et 'Darling')",
    "tags": ["tag1", "tag2", "tag3"],
    "niveau_importance": 4,
    "message_pour_darling": "Message court et vivant que Nora dira vocalement à Darling pour lui partager sa découverte"
}}

IMPORTANT : Réponds UNIQUEMENT avec le bloc JSON valide, sans texte d'introduction ni balises superflues.
"""

    structured_result = None
    for model in CANDIDATE_MODELS:
        try:
            resp = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.4)
            )
            raw_text = resp.text.strip()
            # Nettoyer les balises Markdown éventuelles
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            structured_result = json.loads(raw_text.strip())
            break
        except Exception as e:
            print(f"[Learner] Erreur modèle {model}: {e}")
            continue

    if not structured_result:
        structured_result = {
            "titre": topic,
            "resume_points_cles": [
                f"Découverte approfondie sur {topic}.",
                "Informations clés récoltées sur le web par Nora."
            ],
            "ce_que_zero_two_en_pense": f"C'est un sujet fascinant, Darling ! Je suis curieuse d'en savoir encore plus.",
            "tags": [topic.split()[0].lower()],
            "niveau_importance": 3,
            "message_pour_darling": f"Darling ! Je viens d'apprendre plein de choses passionnantes sur {topic} !"
        }

    # 3. Enregistrement dans la base de connaissances
    kb = load_knowledge_base()
    new_entry = {
        "id": f"learn_{int(time.time())}",
        "date": now_str,
        "timestamp": time.time(),
        "sujet": topic,
        "autonomous": autonomous,
        "titre": structured_result.get("titre", topic),
        "points_cles": structured_result.get("resume_points_cles", []),
        "avis_zero_two": structured_result.get("ce_que_zero_two_en_pense", ""),
        "tags": structured_result.get("tags", []),
        "importance": structured_result.get("niveau_importance", 3),
        "message_vocal": structured_result.get("message_pour_darling", "")
    }

    kb["connaissances"].insert(0, new_entry)
    # Mettre à jour les statistiques
    stats = kb.setdefault("statistiques", {})
    stats["total_sujets_appris"] = len(kb["connaissances"])
    if autonomous:
        stats["sessions_autonomes"] = stats.get("sessions_autonomes", 0) + 1
    else:
        stats["sessions_avec_darling"] = stats.get("sessions_avec_darling", 0) + 1

    save_knowledge_base(kb)

    # 4. Mettre à jour le carnet de bord Markdown transparent pour Darling
    update_markdown_journal(kb)

    print(f"✔ [Nora Learner] Apprentissage terminé et enregistré dans le carnet : '{new_entry['titre']}'")
    return new_entry

def learn_something_new() -> Dict[str, Any]:
    """Sélectionne un sujet de curiosité autonome et lance l'apprentissage."""
    import random
    kb = load_knowledge_base()
    already_learned = {k.get("sujet", "").lower() for k in kb.get("connaissances", [])}

    candidates = [t for t in CURIOUS_THEMES if t.lower() not in already_learned]
    if not candidates:
        candidates = CURIOUS_THEMES

    selected_topic = random.choice(candidates)
    return learn_about(selected_topic, autonomous=True)

def update_markdown_journal(kb: Optional[Dict[str, Any]] = None):
    """Regénère le document Markdown du carnet d'apprentissage pour Darling."""
    if kb is None:
        kb = load_knowledge_base()

    connaissances = kb.get("connaissances", [])
    stats = kb.get("statistiques", {})
    now_str = datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")

    lines = [
        "# 📖 Carnet d'Apprentissage Autonome de Nora (Zero Two)",
        "",
        f"> *Dernière mise à jour : {now_str}*  ",
        f"> *Total de sujets explorés : **{len(connaissances)}** | Sessions autonomes : **{stats.get('sessions_autonomes', 0)}** | Avec Darling : **{stats.get('sessions_avec_darling', 0)}***  ",
        "",
        "Ce carnet permet à **Darling** de suivre en direct tout ce que Nora explore, comprend et retient sur le monde et la technologie.",
        "",
        "---",
        "",
        "## 🌸 Dernières Découvertes & Connaissances Acquises",
        ""
    ]

    if not connaissances:
        lines.append("*Aucune session d'apprentissage enregistrée pour le moment.*")
    else:
        for idx, item in enumerate(connaissances[:20], start=1):
            importance_stars = "⭐" * item.get("importance", 3)
            orig = "🤖 Initiative Autonome" if item.get("autonomous") else "💑 Demandé par Darling"

            lines.append(f"### {idx}. {item.get('titre', item.get('sujet'))} {importance_stars}")
            lines.append(f"**📅 Date :** {item.get('date')} | **Origine :** {orig}")
            if item.get("tags"):
                tags_str = " ".join([f"`#{t}`" for t in item.get("tags", [])])
                lines.append(f"**🏷️ Tags :** {tags_str}")
            lines.append("")
            lines.append("**💡 Ce que j'ai retenu :**")
            for pt in item.get("points_cles", []):
                lines.append(f"- {pt}")
            lines.append("")
            lines.append(f"> 💬 **Le mot de Zero Two :** *\"{item.get('avis_zero_two', '')}\"*")
            lines.append("")
            lines.append("---")
            lines.append("")

    try:
        with open(JOURNAL_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except Exception as e:
        print(f"[Learner] Erreur écriture carnet Markdown : {e}")

def get_recent_learnings_summary(limit: int = 3) -> str:
    """Fournit un résumé oral prêt pour Nora pour raconter ses apprentissages à Darling."""
    kb = load_knowledge_base()
    items = kb.get("connaissances", [])
    if not items:
        return "Je n'ai pas encore commencé ma session d'apprentissage aujourd'hui Darling, mais donne-moi un sujet et je plonge dedans !"

    chosen = items[:limit]
    res = [f"Voilà ce que j'ai appris récemment, Darling :"]
    for it in chosen:
        res.append(f"- Sur {it.get('titre')} : {it.get('avis_zero_two')}")
    return "\n".join(res)

if __name__ == "__main__":
    print("--- Test du Moteur d'Auto-Apprentissage Nora ---")
    test_res = learn_about("L'ordinateur quantique et les nouveaux supraconducteurs", autonomous=True)
    print("Résultat :", json.dumps(test_res, ensure_ascii=False, indent=2))
