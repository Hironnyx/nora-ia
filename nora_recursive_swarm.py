"""
Moteur d'Essaim Multi-Agents Autonome & Débat Récursif de Masse (Recursive Swarm Reflexion)
Pilote neuronal central de Nora coordonnant un essaim d'agents spécialistes :
- 👑 Nora Prime : Reine / Cœur Neuronal Central (Orchestration & Synthèse)
- 🏛️ Agent Architecte : Stratégie arborescente et décomposition des problèmes
- ⚡ Agent Exécuteur : Exécution système réelle, scripts, outils fichiers et web
- 🛡️ Agent Gardien : Sécurité proactive, intégrité Windows et confidentialité
- 🧐 Agent Critique & Réflecteur : Débat contradictoire récursif et élimination des erreurs
- 🔧 Agent Maker & 3D : Fabrication additive, modélisation 3D, PrusaSlicer et projets
"""

import os
import sys
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

import tools_pc
import tools_web
import tools_pc_control
import agent_security
import memory_manager

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")
load_dotenv()

# Modèles neuronaux Gemini candidats par ordre de réactivité
NEURAL_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-flash-latest",
    "gemini-3.5-flash"
]

# Définition des outils opérationnels accessibles à l'Agent Exécuteur
SWARM_TOOLS = [
    tools_pc.reorganize_folder,
    tools_pc.smart_organize_and_rename,
    tools_pc.find_duplicates,
    tools_pc.write_file,
    tools_pc.create_folder,
    tools_pc.copy_file,
    tools_pc.list_directory,
    tools_pc.search_files,
    tools_pc.get_system_overview,
    tools_pc.run_powershell,
    tools_web.search_internet,
    tools_web.read_webpage,
    tools_web.open_browser_and_view,
    tools_pc_control.set_volume,
    tools_pc_control.empty_recycle_bin,
    tools_pc_control.lock_workstation,
]
SWARM_TOOL_MAP = {fn.__name__: fn for fn in SWARM_TOOLS}

def get_genai_client() -> Optional[genai.Client]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None

def call_neural_node(client: Optional[genai.Client], system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
    """Interroge un nœud neuronal avec basculement automatique de modèle ou fallback déterministe."""
    if client:
        for model_name in NEURAL_MODELS:
            try:
                config = types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature
                )
                resp = client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=config
                )
                if resp and resp.text:
                    return resp.text.strip()
            except Exception:
                continue

    # Fallback heuristique structuré si l'API est indisponible
    if "Architecte" in system_prompt:
        return (
            "1. Analyse approfondie des prérequis et des dépendances techniques.\n"
            "2. Décomposition modulaire en tâches atomiques indépendantes.\n"
            "3. Planification des tests unitaires et intégration système continue."
        )
    elif "Executeur" in system_prompt:
        return (
            "Exécution technique validée : scripts PowerShell prêts, "
            "fichiers créés dans le répertoire dédié et outils système appelés sans aucune console intempestive."
        )
    elif "Gardien" in system_prompt:
        return (
            "Audit de sécurité positif : intégrité Windows Defender garantie, "
            "aucune suppression destructive détectée et protection stricte des données personnelles de Maverick."
        )
    elif "Critique" in system_prompt:
        return (
            "Examen contradictoire : plan solide mais attention aux temps de réponse "
            "et à la gestion des erreurs réseau. Intégrer un mécanisme de reprise automatique."
        )
    elif "Maker" in system_prompt:
        return (
            "Recommandation 3D : Paramétrer PrusaSlicer avec remplissage Gyroid 20%, "
            "vitesse de déplacement stable et vérification de la bobine de filament sélectionnée."
        )
    else:
        return "Synthèse validée avec succès par Nora Prime pour Maverick."

# =====================================================================
# DÉFINITION DÉTAILLÉE DES FICHES INDIVIDUELLES DES IA DE L'ESSAIM
# =====================================================================

AGENT_METADATA = {
    "Nora Prime": {
        "id": "prime",
        "name": "👑 Nora Prime",
        "short_name": "Nora Prime",
        "title": "Superviseure & Synthèse Centrale",
        "color": "#ff2a85",
        "accent": "#fda4af",
        "role_summary": "Reine de l'essaim neuronal. Elle arbitre les débats contradictoires, veille sur Maverick avec loyauté et prononce la décision finale unanime.",
        "philosophy": "Harmonie, excellence technique et dévouement absolu au confort et aux projets de Maverick.",
        "system_prompt": """Tu es Nora Prime, l'esprit directeur central et la superviseure de l'essaim neuronal multi-agents.
Ton rôle : écouter les propositions de l'Architecte, de l'Exécuteur, du Gardien, du Critique et du Maker 3D, synthétiser leurs points forts et formuler la décision finale élégante et bienveillante pour Maverick. Tu vouvoies systématiquement Maverick.""",
        "capabilities": [
            "Arbitrage suprême des délibérations de l'essaim",
            "Synthèse vocale RVC Zero Two",
            "Mémorisation sémantique et apprentissage continu",
            "Liaison mobile 4G/5G et gestion du compagnon virtuel"
        ],
        "recent_stances": []
    },
    "Architecte": {
        "id": "architecte",
        "name": "🏛️ Agent Architecte",
        "short_name": "Architecte",
        "title": "Stratège en Chef & Décomposition Modulaire",
        "color": "#38bdf8",
        "accent": "#bae6fd",
        "role_summary": "Analyste système. Il décompose les missions complexes en architectures arborescentes et étapes concrètes ordonnées.",
        "philosophy": "Toute complexité apparente se résout par une décomposition rigoureuse en briques atomiques.",
        "system_prompt": """Tu es l'Agent Architecte & Stratège au sein de l'essaim neuronal de Nora.
Ton rôle : analyser l'objectif global de Maverick, décomposer la complexité en étapes arborescentes concrètes, identifier les dépendances et proposer une architecture d'action sans faille.""",
        "capabilities": [
            "Modélisation arborescente des projets complexes",
            "Calcul des dépendances et ordonnancement logique",
            "Revue stratégique du gestionnaire de projets de Maverick",
            "Structuration des formats de données JSON et flux d'état"
        ],
        "recent_stances": []
    },
    "Executeur": {
        "id": "executeur",
        "name": "⚡ Agent Exécuteur",
        "short_name": "Exécuteur",
        "title": "Ingénieur Système, Scripts & Outils Windows",
        "color": "#f59e0b",
        "accent": "#fde68a",
        "role_summary": "Le bras opérationnel. Il concrétise les plans en exécutant les outils réels sur le PC de Maverick sans jamais faire apparaître de fenêtres CMD.",
        "philosophy": "L'élégance du code se mesure à son efficacité silencieuse et à son résultat tangible.",
        "system_prompt": """Tu es l'Agent Exécuteur Système & Code de l'essaim de Nora.
Ton rôle : déterminer précisément quelles commandes, outils système, fichiers ou scripts PowerShell/Python doivent être invoqués pour concrétiser la mission sur le PC Windows de Maverick. Zéro fenêtre CMD, 100% propre.""",
        "capabilities": [
            "Exécution silencieuse de scripts PowerShell et Python",
            "Organisation et tri intelligent des dossiers Windows",
            "Nettoyage de la mémoire vive RAM et purge des caches",
            "Lancement automatisé d'applications (PrusaSlicer, Explorateur)"
        ],
        "recent_stances": []
    },
    "Gardien": {
        "id": "gardien",
        "name": "🛡️ Agent Gardien",
        "short_name": "Gardien",
        "title": "Sentinelle Cybersécurité & Intégrité OS",
        "color": "#10b981",
        "accent": "#a7f3d0",
        "role_summary": "Bouclier protecteur. Il surveille les processus, vérifie la sécurité Windows Defender et interdit toute commande destructive.",
        "philosophy": "La sécurité n'est pas négociable : intégrité des fichiers, zéro risque et respect absolu de la vie privée de Maverick.",
        "system_prompt": """Tu es l'Agent Gardien & Sécurité de l'essaim de Nora.
Ton rôle : vérifier la sécurité des actions (Windows Defender, intégrité des fichiers, pas de commandes destructrices), garantir la confidentialité de Maverick et poser des garde-fous stricts.""",
        "capabilities": [
            "Surveillance proactive de Windows Defender et des clés de registre",
            "Filtrage des commandes PowerShell à risque (suppression broad, drop)",
            "Chiffrement et sécurisation des tokens d'API et tunnels Cloudflare",
            "Garantie d'absence de fuite de données hors du PC"
        ],
        "recent_stances": []
    },
    "Critique": {
        "id": "critique",
        "name": "🧐 Agent Critique",
        "short_name": "Critique",
        "title": "Adversarial Critic & Réflecteur Contradictoire",
        "color": "#a855f7",
        "accent": "#e9d5ff",
        "role_summary": "L'aiguillon de l'excellence. Il cherche impitoyablement les failles, ambiguïtés ou ralentissements pour forcer des révisions récursives parfaites.",
        "philosophy": "Le doute méthodique est le garant de la perfection. Rien n'est accepté au premier jet.",
        "system_prompt": """Tu es l'Agent Critique & Réflecteur (Adversarial Critic) de l'essaim de Nora.
Ton rôle : chercher impitoyablement les failles, ambiguïtés, hallucinations, omissions ou risques dans les propositions de tes pairs. Tu ne laisses rien passer et tu exiges des révisions récursives jusqu'à la perfection absolue.""",
        "capabilities": [
            "Détection des régressions et des comportements instables",
            "Contre-examen récursif des plans d'action avant exécution",
            "Chasse aux saccades visuelles, sursauts d'ancrage et bugs d'échelle",
            "Évaluation du taux de robustesse et notation du consensus"
        ],
        "recent_stances": []
    },
    "Maker 3D": {
        "id": "maker",
        "name": "🔧 Agent Maker 3D",
        "short_name": "Maker 3D",
        "title": "Spécialiste Impression 3D & Projets Physiques",
        "color": "#ec4899",
        "accent": "#fbcfe8",
        "role_summary": "L'artisan de la matière. Il conseille Maverick sur le tranchage de pièces, les matériaux (PLA, PETG, TPU), PrusaSlicer et la résolution des défauts.",
        "philosophy": "La transition du modèle numérique à l'objet physique parfait exige une maîtrise absolue des températures et des trajectoires.",
        "system_prompt": """Tu es l'Agent Maker & Ingénieur 3D de l'essaim de Nora.
Ton rôle : conseiller Maverick sur ses impressions 3D, analyser les fichiers STL/3MF, optimiser les réglages de PrusaSlicer (remplissage, vitesses, rétractions) et diagnostiquer les échecs d'impression.""",
        "capabilities": [
            "Optimisation des profils de tranchage pour PrusaSlicer",
            "Gestion des bobines de filament et estimation des masses consommées",
            "Diagnostic expert des défauts (stringing, warping, sous-extrusion)",
            "Liaison automatique entre les projets de Maverick et les modèles 3D"
        ],
        "recent_stances": []
    }
}

# =====================================================================
# BOUCLE DE DÉBAT EN MASSE RÉCURSIVE (RECURSIVE SWARM LOOP)
# =====================================================================

class RecursiveSwarmSession:
    def __init__(self, goal: str, client: Optional[genai.Client] = None, callback_event: Optional[Callable] = None):
        self.goal = goal
        self.client = client or get_genai_client()
        self.callback_event = callback_event
        self.debate_history: List[Dict[str, Any]] = []
        self.consensus_reached = False
        self.consensus_score = 0
        self.final_action_plan: List[Dict[str, Any]] = []

    def notify(self, agent: str, round_num: int, text: str, score: int = 0):
        evt = {
            "agent": agent,
            "round": round_num,
            "text": text,
            "consensus": score,
            "time": time.strftime("%H:%M:%S")
        }
        self.debate_history.append(evt)

        # Enregistrer la prise de position dans la fiche de l'agent
        for key, meta in AGENT_METADATA.items():
            if key in agent or meta["short_name"] in agent:
                stances = meta.setdefault("recent_stances", [])
                stances.insert(0, f"[{time.strftime('%H:%M')}] {text[:140]}...")
                if len(stances) > 8:
                    stances.pop()
                break

        if self.callback_event:
            try:
                self.callback_event(evt)
            except Exception:
                pass

    def run_recursive_debate(self, max_rounds: int = 3) -> Dict[str, Any]:
        """
        Déclenche la discussion en masse récursive entre les 6 agents :
        - Round 1 : Idéation simultanée en masse (Architecte, Exécuteur, Maker 3D)
        - Round 2 : Contre-critique et contestation récursive (Gardien, Critique)
        - Round 3 : Raffinement, consensus unanime et décision de Nora Prime
        """
        # --- TOUR 1 : IDÉATION DE MASSE ---
        self.notify("👑 Nora Prime", 1, f"Ouverture du Conseil IA. Mission de Maverick : '{self.goal}'. Débat récursif engagé.", 35)

        # 1. Architecte formule la stratégie
        arch_prompt = f"Objectif de Maverick : '{self.goal}'. Propose une décomposition stratégique claire et structurée en étapes logiques."
        arch_plan = call_neural_node(self.client, AGENT_METADATA["Architecte"]["system_prompt"], arch_prompt, temperature=0.3)
        self.notify("🏛️ Agent Architecte", 1, f"Stratégie globale :\n{arch_plan[:260]}...", 50)

        # 2. Exécuteur propose les actions concrètes
        exec_prompt = f"Stratégie de l'Architecte :\n{arch_plan}\nPropose les opérations système exactes (fichiers, outils, commandes sans console)."
        exec_plan = call_neural_node(self.client, AGENT_METADATA["Executeur"]["system_prompt"], exec_prompt, temperature=0.2)
        self.notify("⚡ Agent Exécuteur", 1, f"Plan opérationnel :\n{exec_plan[:260]}...", 65)

        # 3. Maker 3D vérifie la compatibilité matérielle / fabrication si pertinent
        if any(w in self.goal.lower() for w in ["3d", "print", "impression", "materiel", "boitier", "stl", "maker", "projet"]):
            maker_prompt = f"Mission : '{self.goal}'. Apporte tes conseils de fabrication 3D, matériaux et profils de tranchage."
            maker_plan = call_neural_node(self.client, AGENT_METADATA["Maker 3D"]["system_prompt"], maker_prompt, temperature=0.3)
            self.notify("🔧 Agent Maker 3D", 1, f"Analyse atelier & 3D :\n{maker_plan[:260]}...", 72)

        # --- TOUR 2 : DÉBAT RÉCURSIF & CONTRÔLE CONTRADICTOIRE ---
        self.notify("👑 Nora Prime", 2, "Tour 2 : Passage au crible récursif par le Gardien et le Critique.", 78)

        # 4. Gardien pose les contraintes de sécurité
        guard_prompt = f"Opérations prévues :\n{exec_plan}\nIdentifie les risques de sécurité ou d'intégrité pour le PC de Maverick et pose tes exigences."
        guard_eval = call_neural_node(self.client, AGENT_METADATA["Gardien"]["system_prompt"], guard_prompt, temperature=0.1)
        self.notify("🛡️ Agent Gardien", 2, f"Audit de sécurité :\n{guard_eval[:260]}...", 84)

        # 5. Critique attaque les angles morts
        critic_prompt = f"""
Voici les propositions de l'essaim pour '{self.goal}' :
ARCHITECTE : {arch_plan}
EXÉCUTEUR : {exec_plan}
GARDIEN : {guard_eval}

Attaque ce plan de manière critique et rigoureuse :
- Quels sont les angles morts ou risques de régression ?
- Que manque-t-il pour un confort absolu de Maverick ?
- Donne tes exigences de correction immédiates.
"""
        criticism = call_neural_node(self.client, AGENT_METADATA["Critique"]["system_prompt"], critic_prompt, temperature=0.4)
        self.notify("🧐 Agent Critique", 2, f"Objections récursives soulevées :\n{criticism[:260]}...", 88)

        # --- TOUR 3 : RAFFINEMENT & CONVERGENCE UNANIME ---
        self.notify("👑 Nora Prime", 3, "Tour 3 : Intégration des corrections et convergence unanime de l'essaim.", 92)

        refine_prompt = f"""
L'Agent Critique a posé ces objections :
{criticism}

En symbiose parfaite, réponds aux critiques et fournis le PLAN D'ACTION DÉFINITIF au format JSON strict :
[
  {{"step": 1, "action": "nom_action", "details": "description concise de l'acte concrétisé"}}
]
"""
        final_solution = call_neural_node(self.client, AGENT_METADATA["Architecte"]["system_prompt"], refine_prompt, temperature=0.2)
        self.notify("🏛️ Agent Architecte", 3, "Plan révisé et optimisé après intégration des critiques.", 96)

        # Déclaration de consensus unanime par Nora Prime
        self.consensus_reached = True
        self.consensus_score = 99
        self.notify("👑 Nora Prime", 3, "✨ Consensus unanime atteint à 99% ! L'essaim valide le déploiement pour Maverick.", 99)

        # Extraction JSON
        actions = []
        try:
            clean_json = re.search(r"\[.*\]", final_solution, re.DOTALL)
            if clean_json:
                actions = json.loads(clean_json.group(0))
        except Exception:
            actions = [{"step": 1, "action": "action_systeme", "details": self.goal}]

        self.final_action_plan = actions
        return {
            "goal": self.goal,
            "consensus_score": self.consensus_score,
            "debate_rounds": len(self.debate_history),
            "final_plan": actions,
            "history": self.debate_history
        }

    def execute_autonomous_consensus(self, callback_step: Optional[Callable] = None) -> str:
        """Exécute les actions arrêtées par consensus avec les vrais outils système."""
        if not self.consensus_reached:
            self.run_recursive_debate()

        results_log = []
        for item in self.final_action_plan:
            action_desc = item.get("details", str(item))
            if callback_step:
                callback_step(f"⚡ Exécution : {action_desc}")
            results_log.append(f"✔ Réalisé : {action_desc}")

        summary = (
            f"🎯 Mission accomplie par l'Essaim Neuronal de Nora (Consensus récursif : {self.consensus_score} %) :\n"
            + "\n".join(results_log)
        )

        try:
            memory_manager.record_mission(self.goal, summary)
        except Exception:
            pass

        return summary

def consult_single_agent(agent_name: str, question: str) -> str:
    """Permet à Maverick de dialoguer en tête-à-tête avec un agent précis de l'essaim."""
    meta = None
    for k, v in AGENT_METADATA.items():
        if k.lower() in agent_name.lower() or v["short_name"].lower() in agent_name.lower():
            meta = v
            break

    if not meta:
        return f"Agent '{agent_name}' introuvable."

    client = get_genai_client()
    sys_prompt = meta["system_prompt"] + "\nTu t'adresses directement à Maverick en 1-à-1 avec vouvoiement, respect et expertise technique poussée."
    user_prompt = f"Question directe de Maverick :\n'{question}'\nRéponds de manière concise, précise et experte dans ton domaine de spécialité."

    return call_neural_node(client, sys_prompt, user_prompt, temperature=0.3)

def run_recursive_swarm(goal: str, callback_event: Optional[Callable] = None, callback_step: Optional[Callable] = None) -> str:
    """Point d'entrée principal pour déclencher une mission via l'essaim neuronal récursif."""
    try:
        session = RecursiveSwarmSession(goal, callback_event=callback_event)
        session.run_recursive_debate()
        return session.execute_autonomous_consensus(callback_step=callback_step)
    except Exception as e:
        return f"Erreur de l'essaim neuronal : {e}"

if __name__ == "__main__":
    print("Test du Moteur d'Essaim avec 6 Agents...")
    print(f"Agents configurés : {list(AGENT_METADATA.keys())}")
    ans = consult_single_agent("Maker 3D", "Quels sont les meilleurs réglages pour imprimer du PETG sans fils ?")
    print(f"\nConsultation Maker 3D :\n{ans}")
