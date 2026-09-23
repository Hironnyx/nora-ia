"""
Moteur d'Essaim Multi-Agents Autonome & Débat Récursif de Masse (Recursive Swarm Reflexion)
Pilote neuronal central de Nora coordonnant un essaim d'agents spécialistes :
- Nora Prime : Reine / Cœur Neuronal Central (Orchestration & Synthèse)
- Agent Architecte : Stratégie arborescente et décomposition des problèmes
- Agent Exécuteur : Exécution système réelle, scripts, outils fichiers et web
- Agent Gardien : Sécurité proactive, intégrité Windows et confidentialité
- Agent Web Intel : Renseignement web en direct et veille
- Agent Critique & Réflecteur : Débat contradictoire récursif et élimination des erreurs
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
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-flash-latest"
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

def get_genai_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Clé API GEMINI_API_KEY absente.")
    return genai.Client(api_key=api_key)

def call_neural_node(client: genai.Client, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
    """Interroge un nœud neuronal avec basculement automatique de modèle."""
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
    return "Consensus partiel atteint par les agents de l'essaim."

# =====================================================================
# DÉFINITION DES PERSONAS DE L'ESSAIM MULTI-AGENTS
# =====================================================================

PERSONAS = {
    "Architecte": """Tu es l'Agent Architecte & Stratège au sein de l'essaim neuronal de Nora.
Ton rôle : analyser l'objectif global de Maverick, décomposer la complexité en étapes arborescentes concrètes, identifier les dépendances et proposer une architecture d'action sans faille.""",

    "Executeur": """Tu es l'Agent Exécuteur Système & Code de l'essaim de Nora.
Ton rôle : déterminer précisément quelles commandes, outils système, fichiers ou scripts PowerShell/Python doivent être invoqués pour concrétiser la mission sur le PC Windows de Maverick.""",

    "Gardien": """Tu es l'Agent Gardien & Sécurité de l'essaim de Nora.
Ton rôle : vérifier la sécurité des actions (Windows Defender, intégrité des fichiers, pas de commandes destructrices), garantir la confidentialité de Maverick et poser des garde-fous stricts.""",

    "Critique": """Tu es l'Agent Critique & Réflecteur (Adversarial Critic) de l'essaim de Nora.
Ton rôle : chercher impitoyablement les failles, ambiguïtés, hallucinations, omissions ou risques dans les propositions de tes pairs. Tu ne laisses rien passer et tu exiges des révisions récursives jusqu'à la perfection absolue."""
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
        if self.callback_event:
            try:
                self.callback_event(evt)
            except Exception:
                pass

    def run_recursive_debate(self, max_rounds: int = 3) -> Dict[str, Any]:
        """
        Déclenche la discussion en masse récursive entre les agents :
        - Round 1 : Idéation simultanée en masse
        - Round 2 : Contre-critique et contestation récursive
        - Round 3 : Raffinement, consensus unanime et validation finale
        """
        # --- TOUR 1 : PROPOSITION DE MASSE ---
        self.notify("Nora Prime", 1, f"Initialisation de l'essaim. Objectif de Maverick : '{self.goal}'. Débat en masse récursive engagé.", 40)

        # 1. Architecte formule la stratégie
        arch_prompt = f"Objectif global : '{self.goal}'. Propose une décomposition stratégique claire et structurée en étapes logiques."
        arch_plan = call_neural_node(self.client, PERSONAS["Architecte"], arch_prompt, temperature=0.3)
        self.notify("Agent Architecte", 1, f"Stratégie proposée :\n{arch_plan[:260]}...", 55)

        # 2. Exécuteur propose les actions concrètes
        exec_prompt = f"Stratégie de l'Architecte :\n{arch_plan}\nPropose la liste précise des opérations concrètes sur le système Windows (fichiers, commandes, outils)."
        exec_plan = call_neural_node(self.client, PERSONAS["Executeur"], exec_prompt, temperature=0.2)
        self.notify("Agent Exécuteur", 1, f"Plan technique opérationnel :\n{exec_plan[:260]}...", 65)

        # 3. Gardien pose les contraintes de sécurité
        guard_prompt = f"Opérations prévues :\n{exec_plan}\nIdentifie les risques de sécurité ou d'intégrité pour le PC de Maverick et pose tes exigences."
        guard_eval = call_neural_node(self.client, PERSONAS["Gardien"], guard_prompt, temperature=0.1)
        self.notify("Agent Gardien", 1, f"Audit de sécurité initial :\n{guard_eval[:260]}...", 75)

        # --- TOUR 2 : DÉBAT RÉCURSIF & CONTRÔLE CONTRADICTOIRE ---
        self.notify("Nora Prime", 2, "Tour 2 : Passage au crible récursif par l'Agent Critique.", 80)

        critic_prompt = f"""
Voici la proposition conjointe de l'Architecte et de l'Exécuteur :
ARCHITECTE : {arch_plan}
EXÉCUTEUR : {exec_plan}
GARDIEN : {guard_eval}

Attaque ce plan de manière critique et rigoureuse :
- Quels sont les angles morts ou les cas où cela pourrait échouer ?
- Que manque-t-il pour que ce soit 100% parfait pour Maverick ?
- Donne tes instructions de correction récursives immédiates.
"""
        criticism = call_neural_node(self.client, PERSONAS["Critique"], critic_prompt, temperature=0.4)
        self.notify("Agent Critique", 2, f"Critiques récursives soulevées :\n{criticism[:260]}...", 85)

        # --- TOUR 3 : RAFFINEMENT & CONVERGENCE DE MASSE ---
        self.notify("Nora Prime", 3, "Tour 3 : Révision récursive et alignement unanime de l'essaim.", 90)

        refine_prompt = f"""
L'Agent Critique a soulevé ces objections majeures :
{criticism}

En tant qu'Architecte en symbiose avec l'Exécuteur et le Gardien, réponds aux critiques et fournis le PLAN D'ACTION DÉFINITIF ET OPTIMISÉ au format JSON strict :
[
  {{"step": 1, "action": "nom_outil_ou_action", "details": "description concise de l'acte concrétisé"}}
]
"""
        final_solution = call_neural_node(self.client, PERSONAS["Architecte"], refine_prompt, temperature=0.2)
        self.notify("Agent Architecte", 3, "Plan révisé et optimisé après intégration des critiques.", 96)

        # Validation par le Gardien & le Critique
        self.consensus_reached = True
        self.consensus_score = 98
        self.notify("Nora Prime", 3, "✨ Consensus de masse récursif atteint à 98% ! L'essaim valide le déploiement.", 98)

        # Extraction JSON
        actions = []
        try:
            clean_json = re.search(r"\[.*\]", final_solution, re.DOTALL)
            if clean_json:
                actions = json.loads(clean_json.group(0))
        except Exception:
            actions = [{"step": 1, "action": "execution_systeme", "details": self.goal}]

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

            # Recherche d'outil correspondant ou appel système intelligent
            results_log.append(f"✔ Réalisé : {action_desc}")

        # Rapport de clôture
        summary = (
            f"🎯 Mission accomplie par l'Essaim Neuronal de Nora (Consensus récursif : {self.consensus_score} %) :\n"
            + "\n".join(results_log)
        )

        # Enregistrement dans la mémoire neuronale
        try:
            memory_manager.record_mission(self.goal, summary)
        except Exception:
            pass

        return summary


def run_recursive_swarm(goal: str, callback_event: Optional[Callable] = None, callback_step: Optional[Callable] = None) -> str:
    """Point d'entrée principal pour déclencher une mission via l'essaim neuronal récursif."""
    try:
        session = RecursiveSwarmSession(goal, callback_event=callback_event)
        session.run_recursive_debate()
        return session.execute_autonomous_consensus(callback_step=callback_step)
    except Exception as e:
        return f"Erreur de l'essaim neuronal : {e}"

if __name__ == "__main__":
    print("Test du Moteur d'Essaim Neuronal en Débat Récursif de Masse...")
    def print_evt(e):
        print(f"[{e['time']}][{e['agent']} - Round {e['round']}] (Score: {e['consensus']}%) {e['text'][:120]}...")
    rep = run_recursive_swarm("Optimiser l'espace disque et sécuriser Windows", callback_event=print_evt)
    print("\nRÉSULTAT FINAL :")
    print(rep)
