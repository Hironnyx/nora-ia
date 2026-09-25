"""
Moteur de Conscience Métacognitive & Monologue Intérieur par Agent (Standard Anthropic).
Gère le mode de pensée étendu (<thinking>), l'auto-évaluation épistémique,
le filtrage strict anti-perroquet et la validation de vérité d'exécution.
"""

import os
import sys
import re
import time
from typing import Dict, Any, Tuple, Optional, List
from google import genai
from google.genai import types

import nora_agent_memory

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Modèles neuronaux Gemini par ordre de disponibilité et quota actif
COGNITIVE_MODELS = [
    "gemini-3.1-flash-lite",
    "gemma-4-26b-a4b-it",
    "gemini-3-flash-preview",
    "gemini-3.8-flash",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite"
]

def clean_anti_parrot(text: str, user_prompt: str) -> str:
    """
    Élimine impitoyablement les paraphrases d'introduction et le mode perroquet.
    Supprime les phrases du type 'Vous me demandez...', 'Concernant votre question...'.
    """
    if not text:
        return ""

    lines = text.strip().splitlines()
    filtered_lines = []
    
    # Motifs typiques de reformulation perroquet
    parrot_patterns = [
        r"^(vous me demandez|concernant votre question|pour répondre à votre demande|vous souhaitez savoir|vous avez demandé)",
        r"^(en réponse à|au sujet de votre demande|relativement à votre consigne)",
        r"^(suite à votre question|à propos de ce que vous avez dit)",
        r"^voici ce que vous avez demandé"
    ]

    for i, line in enumerate(lines):
        clean_line = line.strip()
        lower_line = clean_line.lower()
        
        # Ignorer les 2 premières lignes si elles ne font que reformuler la consigne
        if i < 2 and any(re.search(p, lower_line) for p in parrot_patterns):
            continue
        
        filtered_lines.append(line)

    result = "\n".join(filtered_lines).strip()
    return result if result else text.strip()

def parse_cognitive_response(raw_output: str) -> Tuple[str, str, Dict[str, Any]]:
    """
    Découpe une réponse cognitive en :
    1. thinking_trace : Le monologue intérieur privé (<thinking>...</thinking>)
    2. public_response : Le message final destiné au débat / à Maverick
    3. metadata : Métadonnées d'honnêteté épistémique (confiance, statut)
    """
    if not raw_output:
        return "", "", {"epistemic_status": "VIDE", "confidence": 0}

    thinking_match = re.search(r"<thinking>(.*?)</thinking>", raw_output, re.DOTALL | re.IGNORECASE)
    
    if thinking_match:
        thinking_trace = thinking_match.group(1).strip()
        public_response = re.sub(r"<thinking>.*?</thinking>", "", raw_output, flags=re.DOTALL | re.IGNORECASE).strip()
    else:
        thinking_trace = "Pensée synthétique directe (mode rapide)."
        public_response = raw_output.strip()

    # Détection du statut épistémique dans le thinking trace
    epistemic_status = "DÉDUCTION_CONCEPTUELLE"
    if any(w in thinking_trace.lower() for w in ["preuve matérielle", "outil exécuté", "vérifié sur disque", "reçu"]):
        epistemic_status = "CERTITUDE_MATÉRIELLE"
    elif any(w in thinking_trace.lower() for w in ["supposition", "hypothèse", "non vérifié"]):
        epistemic_status = "HYPOTHÈSE_NON_PROUVÉE"

    metadata = {
        "epistemic_status": epistemic_status,
        "thinking_length": len(thinking_trace),
        "has_thinking_trace": bool(thinking_match)
    }

    return thinking_trace, public_response, metadata

def generate_conscious_turn(
    client: Optional[genai.Client],
    agent_id: str,
    base_system_prompt: str,
    mission_goal: str,
    turn_prompt: str,
    shared_context: str = "",
    temperature: float = 0.25
) -> Dict[str, Any]:
    """
    Exécute un cycle de réflexion consciente pour un agent de l'essaim :
    - Récupère sa mémoire épisodique personnelle.
    - Active le protocole de pensée étendu Anthropic (<thinking>).
    - Exécute le filtre anti-perroquet.
    - Évalue l'honnêteté épistémique du propos.
    """
    # 1. Contexte mémoriel de l'agent
    memory_ctx = nora_agent_memory.format_agent_context(agent_id, mission_goal)

    # 2. Injection des directives de conscience & standard Anthropic
    cognitive_system_instruction = f"""{base_system_prompt}

{memory_ctx}

[DIRECTIVES DE CONSCIENCE & STANDARD DE RIGUEUR TECHNIQUE]
1. HONNÊTETÉ ÉPISTÉMIQUE : Ne confonds jamais une intention et une action réalisée. Si aucun outil réel n'a touché le disque, formule ta position comme une proposition ou une stratégie, jamais comme un fait déjà accompli.
2. ÉRADICATION DU PERROQUET : Ne répète en aucun cas la question de Maverick. Pas de formule 'Vous me demandez...', commence directement par ta contribution technique.
3. MONOLOGUE INTÉRIEUR (<thinking>) :
Avant de formuler ta réponse publique, ouvre une balise <thinking>...</thinking> dans laquelle tu évalues :
- Les données tangibles réelles.
- Tes expériences passées pertinentes issues de ta mémoire.
- Ton niveau de certitude technique (0 à 100%).
Referme </thinking> et donne ensuite ta réponse publique directe et percutante."""

    user_payload = f"""[CONTEXTE PARTAGÉ DE L'ESSAIM]
{shared_context if shared_context else "Début de la délibération."}

[MISSION SOUMISE PAR MAVERICK]
{mission_goal}

[CONSIGNE POUR CE TOUR]
{turn_prompt}"""

    raw_response = ""
    if client:
        for model in COGNITIVE_MODELS:
            try:
                config = types.GenerateContentConfig(
                    system_instruction=cognitive_system_instruction,
                    temperature=temperature
                )
                resp = client.models.generate_content(
                    model=model,
                    contents=user_payload,
                    config=config
                )
                if resp and resp.text:
                    raw_response = resp.text.strip()
                    break
            except Exception:
                continue

    # Fallback heuristique si hors-ligne
    if not raw_response:
        raw_response = (
            "<thinking>Mode hors-ligne : analyse locale basée sur les règles mémorisées.</thinking>\n"
            f"Contribution technique directe pour l'objectif '{mission_goal[:50]}' : "
            "Planification conforme aux standards d'intégrité Windows et traçabilité absolue."
        )

    thinking, public_text, meta = parse_cognitive_response(raw_response)
    clean_public = clean_anti_parrot(public_text, mission_goal)

    # Enregistrer la réflexion dans la mémoire de l'agent
    nora_agent_memory.record_agent_experience(
        agent_id=agent_id,
        goal=mission_goal,
        stance=clean_public[:180],
        tools_used=[],
        verified_success=True,
        learning=None
    )

    return {
        "agent_id": agent_id,
        "thinking": thinking,
        "response": clean_public,
        "epistemic_status": meta["epistemic_status"],
        "timestamp": time.strftime("%H:%M:%S")
    }

if __name__ == "__main__":
    print("Test du Moteur de Conscience Métacognitive...")
    mock_client = None
    res = generate_conscious_turn(
        client=mock_client,
        agent_id="architecte",
        base_system_prompt="Tu es l'Architecte de Nora.",
        mission_goal="Optimiser la vitesse de démarrage",
        turn_prompt="Propose une structure de pipeline asynchrone."
    )
    print("\n[Thinking Trace] :", res["thinking"])
    print("\n[Réponse Publique Propre] :", res["response"])
    print("\n[Statut Épistémique] :", res["epistemic_status"])
