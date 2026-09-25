"""
Script de validation unitaire et d'intégration de l'Architecture Cognitive Multi-Agents (4 Piliers).
"""

import os
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

import nora_agent_memory
import nora_cognitive_engine
import nora_blackboard
import nora_receipts
import nora_recursive_swarm

def test_four_pillars():
    print("======================================================================")
    print("   🧠 TEST DE L'ARCHITECTURE COGNITIVE MULTI-AGENTS (STANDARD ANTHROPIC)")
    print("======================================================================\n")

    # ------------------------------------------------------------------
    # PILIER 1 : Mémoire Décentralisée & Épisodique par Agent
    # ------------------------------------------------------------------
    print("--- [PILIER 1] Initialisation & Mémoire Autobiographique par Agent ---")
    nora_agent_memory.init_all_agent_memories()
    agents = list(nora_agent_memory.DEFAULT_AGENT_PROFILES.keys())
    print(f"✔ 6 Répertoires d'agents initialisés dans 'data/agents/' : {agents}")

    # Enregistrement d'une expérience pour l'Exécuteur
    nora_agent_memory.record_agent_experience(
        agent_id="executeur",
        goal="Vérification de l'intégrité Windows",
        stance="Exécution réussie de Get-Process sans fenêtre CMD.",
        tools_used=["run_powershell"],
        verified_success=True,
        learning="Les commandes PowerShell courtes s'exécutent en < 50ms sans console."
    )
    ctx = nora_agent_memory.format_agent_context("executeur", "Vérifier les processus")
    print(f"✔ Contexte mémoriel généré pour l'Exécuteur ({len(ctx)} caractères).")
    assert "Exécuteur" in ctx or "executeur" in ctx.lower()

    # ------------------------------------------------------------------
    # PILIER 2 : Conscience Métacognitive & Monologue Intérieur (<thinking>)
    # ------------------------------------------------------------------
    print("\n--- [PILIER 2] Moteur de Conscience & Monologue Intérieur (<thinking>) ---")
    mock_raw = (
        "<thinking>\n"
        "Faits vérifiés : le système Windows fonctionne sur RTX 4080.\n"
        "Expérience passée : les scripts silencieux évitent les popups CMD.\n"
        "Niveau de certitude : 95%.\n"
        "</thinking>\n"
        "Vous me demandez comment sécuriser le flux.\n"
        "Mise en place d'un filtrage des commandes PowerShell à risque."
    )
    thinking, public_res, meta = nora_cognitive_engine.parse_cognitive_response(mock_raw)
    clean_text = nora_cognitive_engine.clean_anti_parrot(public_res, "comment sécuriser le flux")
    print(f"✔ Monologue intérieur extrait ({meta['thinking_length']} car.) : '{thinking[:60]}...'")
    print(f"✔ Réponse publique filtrée (anti-perroquet) : '{clean_text}'")
    assert "vous me demandez" not in clean_text.lower()
    print("✔ Détection anti-perroquet validée à 100%.")

    # ------------------------------------------------------------------
    # PILIER 3 : Bus d'État Partagé en RAM (Blackboard) & P2P
    # ------------------------------------------------------------------
    print("\n--- [PILIER 3] Bus d'État Partagé en RAM (Blackboard) & Connectivité P2P ---")
    bb = nora_blackboard.SwarmBlackboard("Mission Optimisation Système")
    bb.post_constraint("🛡️ Agent Gardien", "Interdiction des commandes de suppression récursive.")
    bb.post_fact("🏛️ Agent Architecte", "Découpage en 3 étapes validé.")
    ans_p2p = bb.ask_peer("🏛️ Agent Architecte", "⚡ Agent Exécuteur", "Est-ce que le dossier C:\\Users existe ?")
    print(f"✔ Échange P2P immédiat : {ans_p2p}")
    bb_summary = bb.get_summary_context()
    print(f"✔ Résumé du Blackboard partagé :\n{bb_summary}")
    assert "Interdiction des commandes" in bb_summary

    # ------------------------------------------------------------------
    # PILIER 4 : Contrats d'Exécution & Reçus Physiques Vérifiables (Zéro Faux Positif)
    # ------------------------------------------------------------------
    print("\n--- [PILIER 4] Contrats d'Exécution & Preuves Matérielles (Zéro Illusion) ---")
    test_file = Path("c:/Users/maverick/Documents/Agent ia/test_execution_receipt.tmp")
    test_file.write_text("Test de preuve matérielle sur disque.", encoding="utf-8")

    # Reçu physique réel
    receipt_ok = nora_receipts.ExecutionReceipt(
        step_index=1,
        action_name="ecriture_preuve",
        tool_called="write_file",
        tool_args={"file_path": str(test_file)},
        duration_ms=4.8,
        raw_output="Fichier créé avec succès."
    )
    print("✔ Reçu physique :", receipt_ok.status)
    print(f"  ↳ Chemin : {receipt_ok.target_path}")
    print(f"  ↳ Taille : {receipt_ok.file_size_bytes} octets")
    print(f"  ↳ SHA-256 : {receipt_ok.sha256_hash}")
    assert receipt_ok.verified_on_disk is True
    assert receipt_ok.status == "SUCCESS_VERIFIED"

    # Nettoyage fichier temporaire
    if test_file.exists():
        test_file.unlink()

    # Reçu abstrait sans outil (le cas qui trompait Maverick)
    receipt_fake = nora_receipts.ExecutionReceipt(
        step_index=2,
        action_name="optimisation_philosophique",
        tool_called=None,
        tool_args={},
        duration_ms=1.2,
        raw_output="Je valide conceptuellement l'architecture."
    )
    print("\n✔ Reçu conceptuel (zéro outil appelé) :", receipt_fake.status)
    print(f"  ↳ Vérifié sur disque : {receipt_fake.verified_on_disk}")
    assert receipt_fake.verified_on_disk is False
    assert receipt_fake.status == "CONCEPTUAL_ONLY"
    print("✔ Protection anti-faux-positifs : Les actions conceptuelles sont correctement étiquetées 'CONCEPTUAL_ONLY'.")

    print("\n======================================================================")
    print("   🎉 TOUS LES 4 PILIERS DE L'ARCHITECTURE COGNITIVE SONT OPÉRATIONNELS !")
    print("======================================================================")

if __name__ == "__main__":
    test_four_pillars()
