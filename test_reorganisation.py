"""
Script de démonstration pour tester immédiatement la réorganisation de fichiers sur votre PC.
"""
import sys
import shutil
from pathlib import Path
import tools_pc

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def demo_test():
    print("==================================================")
    print("  🧪 TEST DE RÉORGANISATION AUTOMATIQUE SUR PC    ")
    print("==================================================")
    
    # Création d'un dossier temporaire avec plusieurs types de fichiers
    demo_dir = Path("dossier_demonstration")
    demo_dir.mkdir(exist_ok=True)
    
    sample_files = [
        "rapport_mensuel.pdf",
        "facture_electricite.docx",
        "photo_vacances.png",
        "avatar.jpg",
        "setup_vlc.exe",
        "sauvegarde.zip",
        "script_analyse.py",
        "chanson_preferee.mp3",
        "video_demo.mp4"
    ]
    
    print(f"\n1. Création de {len(sample_files)} fichiers exemples dans '{demo_dir}'...")
    for filename in sample_files:
        (demo_dir / filename).write_text("Exemple de contenu pour le test.", encoding="utf-8")
        print(f"   + {filename}")
        
    print("\n2. Lancement du tri automatique...")
    result = tools_pc.reorganize_folder(str(demo_dir))
    print(result)
    
    print("\n3. Contenu après réorganisation :")
    for category_folder in demo_dir.iterdir():
        if category_folder.is_dir():
            files = [f.name for f in category_folder.iterdir()]
            print(f"   📁 {category_folder.name}/ : {', '.join(files)}")
            
    print("\n✔ Démonstration terminée avec succès !")
    print("Vous pouvez inspecter le dossier 'dossier_demonstration' créé dans votre projet.")

if __name__ == "__main__":
    demo_test()
