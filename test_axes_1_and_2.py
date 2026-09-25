"""
Validation unitaire des Axes 1 & 2 :
- Axe 1 : Rendu stylisé du monologue intérieur (<thinking>) et filtrage toggle.
- Axe 2 : Capture de la vision de contexte actif et injection dans le Blackboard de l'Agora.
"""

import sys
import re

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

import nora_context_vision
import nora_recursive_swarm

def test_axes():
    print("==========================================================")
    print("       🧪 TEST DES AXES 1 ET 2 (VISION & THINKING UI)     ")
    print("==========================================================")

    # 1. Test Axe 2 : Vision Contexte
    print("\n--- [AXE 2] Capture de Vision Contexte Actif ---")
    ctx = nora_context_vision.context_vision.get_current_context()
    print("✔ Contexte de la fenêtre active détecté :")
    print(f"  • Application : {ctx.get('app')}")
    print(f"  • Titre : {ctx.get('title')}")
    print(f"  • Catégorie : {ctx.get('category')}")
    print(f"  • Description : {ctx.get('description')}")
    assert ctx.get("app") is not None

    # Test d'initialisation d'une session Swarm avec injection automatique
    print("\n--- [AXE 2] Injection automatique dans le Blackboard ---")
    session = nora_recursive_swarm.RecursiveSwarmSession("Comment optimiser ce projet ?")
    summary = session.blackboard.get_summary_context()
    print(f"✔ Résumé du Blackboard généré :\n{summary}")
    assert "Vision Contexte" in summary
    assert ctx.get('app') in summary or "Bureau Windows" in summary

    # 2. Test Axe 1 : Formatage du Monologue Intérieur
    print("\n--- [AXE 1] Formatage du Monologue Intérieur (<thinking>) ---")
    session.notify(
        agent="🏛️ Agent Architecte",
        round_num=1,
        text="Proposition d'architecture modulaire.",
        score=50,
        thinking="Analyse des fichiers sources actifs. Certitude 90%.",
        epistemic_status="DÉDUCTION_TECHNIQUE"
    )
    last_event = session.debate_history[-1]
    formatted_html = last_event["text"]
    print("✔ HTML généré avec conteneur stylisé de pensée :")
    print(formatted_html[:280] + "...")
    assert "MONOLOGUE INTÉRIEUR" in formatted_html
    assert "DÉDUCTION_TECHNIQUE" in formatted_html

    # Test du toggle (masquage si case décochée)
    unfolded = re.sub(r"<div style=.*?MONOLOGUE INTÉRIEUR.*?</div>", "", formatted_html, flags=re.DOTALL | re.IGNORECASE).strip()
    print("\n✔ Test du filtre toggle (quand la case est décochée) :")
    print(f"  ↳ Texte épuré : '{unfolded}'")
    assert "MONOLOGUE INTÉRIEUR" not in unfolded
    assert "Proposition d'architecture modulaire." in unfolded

    print("\n==========================================================")
    print("   🎉 LES AXES 1 ET 2 SONT VALIDÉS ET 100% OPÉRATIONNELS !")
    print("==========================================================")

if __name__ == "__main__":
    test_axes()
