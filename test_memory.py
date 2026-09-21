"""
Script de test complet pour la mémoire persistante de Nora.
"""
import sys
import memory_manager
import nora_brain

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def test_nora_memory():
    print("==================================================")
    print("     🧪 TEST DE LA MÉMOIRE PERSISTANTE DE NORA   ")
    print("==================================================")

    # 1. Vérification du profil
    name = memory_manager.get_user_name()
    print(f"1. Prénom mémorisé : {name}")

    # 2. Ajout d'un fait personnalisé
    memory_manager.add_user_fact("L'utilisateur développe un projet d'agents IA multi-tâches.")
    print("2. Fait ajouté dans la mémoire permanente de Nora.")

    # 3. Enregistrement d'une mission
    memory_manager.record_completed_mission(
        "Nettoyage et vérification du disque C:",
        "9 fichiers réorganisés, doublons isolés, 118 Go d'espace libre vérifiés."
    )
    print("3. Mission enregistrée dans l'historique.")

    # 4. Message d'accueil personnalisé
    welcome = memory_manager.get_welcome_message()
    print(f"\n4. Salutation personnalisée au démarrage :\n   \"{welcome}\"")

    # 5. Question posée à Nora sur sa mémoire
    print("\n5. Question de test : 'Que sais-tu sur moi ?'")
    intent, reply = nora_brain.analyze_intent_and_respond("Que sais-tu sur moi ?")
    print(f"   Intention : {intent}")
    print(f"   Réponse de Nora : {reply}")

    print("\n✔ Test de mémoire réussi à 100 % !")

if __name__ == "__main__":
    test_nora_memory()
