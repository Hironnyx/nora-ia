"""
Bus d'État Partagé & Connectivité Inter-Agents P2P (Standard Anthropic / Dynamic Blackboard).
Permet aux agents de l'essaim d'échanger des faits en 0 ms en RAM, de s'interpeller
directement ('ask_peer') et d'invoquer des outils d'inspection en direct.
"""

import os
import sys
import threading
import time
from typing import Dict, List, Any, Optional, Callable

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

import tools_pc
import tools_web

# Outils de consultation et d'inspection accessibles à TOUS les agents
READ_ONLY_INSPECTION_TOOLS = {
    "list_directory": tools_pc.list_directory,
    "search_files": tools_pc.search_files,
    "get_system_overview": tools_pc.get_system_overview,
    "search_internet": tools_web.search_internet,
    "read_webpage": tools_web.read_webpage,
}

class SwarmBlackboard:
    """Tableau blanc partagé en RAM (State Bus) pour l'essaim neuronal."""

    def __init__(self, mission_goal: str):
        self.lock = threading.Lock()
        self.mission_goal = mission_goal
        self.created_at = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Données partagées par les agents
        self.shared_facts: List[Dict[str, Any]] = []
        self.active_constraints: List[str] = []
        self.inter_agent_messages: List[Dict[str, Any]] = []
        self.live_telemetry: Dict[str, Any] = {}
        self.inspections_performed: List[Dict[str, Any]] = []

    def post_fact(self, author_agent: str, fact_description: str, confidence: float = 1.0):
        """Publie un fait établi accessible immédiatement par tous les autres agents."""
        with self.lock:
            self.shared_facts.append({
                "author": author_agent,
                "fact": fact_description,
                "confidence": confidence,
                "time": time.strftime("%H:%M:%S")
            })

    def post_constraint(self, author_agent: str, constraint: str):
        """Enregistre une contrainte stricte (ex: imposée par le Gardien)."""
        with self.lock:
            self.active_constraints.append(f"[{author_agent}] {constraint}")

    def ask_peer(self, sender: str, recipient: str, question: str) -> str:
        """
        Communication directe P2P entre deux agents :
        L'agent demandeur pose une question technique ciblée au spécialiste.
        Si la question concerne un état du PC, l'Exécuteur peut lancer une sonde immédiate.
        """
        record = {
            "sender": sender,
            "recipient": recipient,
            "question": question,
            "time": time.strftime("%H:%M:%S")
        }

        # Traitement spécifique si on interroge l'Exécuteur sur un chemin ou un fichier
        clean_q = question.lower()
        if "executeur" in recipient.lower():
            if any(w in clean_q for w in ["existe", "présent", "dossier", "fichier", "chemin"]):
                import re
                paths = re.findall(r'[a-zA-Z]:\\[^"\'\s]+', question)
                if paths:
                    target = paths[0]
                    exists = os.path.exists(target)
                    ans = f"Vérification disque : '{target}' existe = {exists}."
                    record["answer"] = ans
                    with self.lock:
                        self.inter_agent_messages.append(record)
                    return ans

        # Réponse générique instantanée
        ans = f"Réception par {recipient} : prise en compte dans la délibération."
        record["answer"] = ans
        with self.lock:
            self.inter_agent_messages.append(record)
        return ans

    def perform_inspection(self, agent_name: str, tool_name: str, args: Dict[str, Any]) -> str:
        """Permet à un agent d'inspecter la réalité matérielle avant d'affirmer quoi que ce soit."""
        fn = READ_ONLY_INSPECTION_TOOLS.get(tool_name)
        if not fn:
            return f"Outil d'inspection '{tool_name}' inconnu."

        try:
            res = fn(**args)
            record = {
                "agent": agent_name,
                "tool": tool_name,
                "args": args,
                "result_snippet": str(res)[:120],
                "time": time.strftime("%H:%M:%S")
            }
            with self.lock:
                self.inspections_performed.append(record)
            return str(res)
        except Exception as e:
            return f"Erreur inspection : {e}"

    def get_summary_context(self) -> str:
        """Formate le tableau blanc sous forme de résumé textuel dense pour les prompts d'agents."""
        with self.lock:
            lines = [f"Objectif commun : {self.mission_goal}"]
            if self.active_constraints:
                lines.append("Contraintes de sécurité actives :")
                for c in self.active_constraints[-3:]:
                    lines.append(f"  • {c}")
            if self.shared_facts:
                lines.append("Faits établis sur le tableau partagé :")
                for f in self.shared_facts[-4:]:
                    lines.append(f"  • [{f['author']}] {f['fact']}")
            if self.inspections_performed:
                lines.append("Inspections matérielles récentes :")
                for ins in self.inspections_performed[-2:]:
                    lines.append(f"  • {ins['agent']} via {ins['tool']} -> {ins['result_snippet']}")
            return "\n".join(lines)

if __name__ == "__main__":
    print("Test du Bus d'État Partagé (Dynamic Blackboard)...")
    bb = SwarmBlackboard("Vérification de l'intégrité du système")
    bb.post_constraint("🛡️ Agent Gardien", "Ne supprimer aucun fichier sans accord explicite.")
    bb.post_fact("🏛️ Agent Architecte", "Découpage en 3 étapes validé.")
    ans = bb.ask_peer("🏛️ Agent Architecte", "⚡ Agent Exécuteur", "Est-ce que C:\\Users\\maverick existe ?")
    print("Réponse P2P :", ans)
    print("\nRésumé du Blackboard :\n", bb.get_summary_context())
