"""
Test d'une mission multi-agents autonome de bout en bout.
"""
import sys
from pathlib import Path
from mission_engine import run_autonomous_mission

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def run_test():
    mission = (
        "Vérifie l'état de mon disque principal, effectue une recherche web sur les nouveautés de Python, "
        "puis crée un dossier 'Mission_Test' sur mon Bureau avec un fichier 'rapport.md' contenant la synthèse complète."
    )
    print("Démarrage du test de mission autonome...")
    report = run_autonomous_mission(mission)

    bureau_rapport = Path.home() / "Desktop" / "Mission_Test" / "rapport.md"
    print("\n--- VÉRIFICATION DES LIVRABLES SUR LE PC ---")
    print(f"Dossier sur le Bureau : {bureau_rapport.parent} (Existe : {bureau_rapport.parent.exists()})")
    print(f"Fichier rapport.md : {bureau_rapport} (Existe : {bureau_rapport.exists()})")

    if bureau_rapport.exists():
        print(f"Taille du fichier : {bureau_rapport.stat().st_size} octets")
        print("\nExtrait du fichier créé sur le Bureau :")
        print(bureau_rapport.read_text(encoding="utf-8")[:400] + "...")

if __name__ == "__main__":
    run_test()
