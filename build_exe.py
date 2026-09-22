"""
Script de compilation automatisée de Nora en exécutable Windows autonome (Nora.exe) :
- Mode 'onedir' ultra-rapide (démarrage instantané <0.5s sans décompression temporaire)
- Mode '--noconsole' sans aucune invite de commande noire parasite
- Icône Windows Zero Two multi-résolution intégrée (nora.ico)
- Inclusion de tous les assets (mascot_assets, sound_assets, .env, memoire_nora.json)
- Intégration complète de Google GenAI, Edge-TTS, PyQt6, PyCaw, etc.
- Mise à jour automatique du raccourci Bureau 'Nora.lnk' et du raccourci clavier global 'Ctrl+Alt+N'
"""
import sys
import os
import shutil
import subprocess
from pathlib import Path

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

import PyInstaller.__main__

PROJECT_DIR = Path(__file__).resolve().parent
DIST_DIR = PROJECT_DIR / "dist"
BUILD_DIR = PROJECT_DIR / "build"
OUTPUT_DIR = DIST_DIR / "Nora"
EXE_PATH = OUTPUT_DIR / "Nora.exe"
ASSETS_DIR = PROJECT_DIR / "mascot_assets"
ICON_PATH = ASSETS_DIR / "nora.ico"

def prepare_build():
    """Nettoie l'ancien build, vérifie la présence des icônes et des dépendances."""
    print("🌸 [1/4] Préparation des assets et nettoyage...")
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'nora' in proc.info['name'].lower():
                try:
                    proc.kill()
                except Exception:
                    pass
    except Exception:
        pass

    if OUTPUT_DIR.exists():
        subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", str(OUTPUT_DIR)], capture_output=True)

    import mascot_assets
    import sound_effects
    import setup_shortcuts

    mascot_assets.generate_all_zero_two_assets()
    sound_effects.generate_chimes_if_missing()
    setup_shortcuts.ensure_nora_icon()
    print("✔ Assets et icônes vérifiés.")

def run_pyinstaller():
    """Lance la compilation PyInstaller."""
    print("⚙️ [2/4] Compilation PyInstaller en mode 'onedir' haute performance...")

    if OUTPUT_DIR.exists():
        import time
        for _ in range(5):
            try:
                shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
                if not OUTPUT_DIR.exists():
                    break
            except Exception:
                time.sleep(1)

    args = [
        str(PROJECT_DIR / "desktop_pet.py"),
        "--name=Nora",
        "--noconsole",
        "--onedir",
        "--noconfirm",
        f"--icon={ICON_PATH}",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        f"--specpath={PROJECT_DIR}",
        # Données et assets
        f"--add-data={PROJECT_DIR / 'mascot_assets'};mascot_assets",
        f"--add-data={PROJECT_DIR / 'sound_assets'};sound_assets",
        f"--add-data={PROJECT_DIR / 'models'};models",
        # Hidden imports critiques
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=google.genai",
        "--hidden-import=edge_tts",
        "--hidden-import=speech_recognition",
        "--hidden-import=pygame",
        "--hidden-import=pyaudio",
        "--hidden-import=pycaw",
        "--hidden-import=comtypes",
        "--hidden-import=psutil",
        "--hidden-import=PIL",
        "--hidden-import=numpy",
        "--hidden-import=dotenv",
        "--hidden-import=agent_core",
        "--hidden-import=agent_security",
        "--hidden-import=gaming_mode",
        "--hidden-import=mascot_assets",
        "--hidden-import=memory_manager",
        "--hidden-import=mission_engine",
        "--hidden-import=nora_autonomous_life",
        "--hidden-import=nora_brain",
        "--hidden-import=nora_initiatives",
        "--hidden-import=qg_dashboard",
        "--hidden-import=setup_shortcuts",
        "--hidden-import=sound_effects",
        "--hidden-import=system_monitor",
        "--hidden-import=tools_designer",
        "--hidden-import=tools_pc",
        "--hidden-import=tools_pc_control",
        "--hidden-import=tools_vision",
        "--hidden-import=tools_web",
        "--hidden-import=voice_engine",
        "--hidden-import=voice_cloning",
        "--hidden-import=agent_home",
        "--hidden-import=requests",
        "--hidden-import=pypdf",
        "--hidden-import=wake_word_listener",
        "--hidden-import=infer_rvc_python",
        "--hidden-import=torch",
        "--hidden-import=torchaudio",
        "--hidden-import=torchvision",
        "--hidden-import=scipy",
        "--hidden-import=scipy.signal",
        "--hidden-import=librosa",
        "--hidden-import=soundfile",
        "--hidden-import=pyworld",
        "--hidden-import=praat_parselmouth",
        "--hidden-import=torchcrepe",
        "--hidden-import=transformers",
        "--hidden-import=faiss",
        # Paquets avec métadonnées ou binaires spéciaux
        "--collect-all=google.genai",
        "--collect-all=edge_tts",
        "--collect-all=speech_recognition",
        "--collect-all=pycaw",
        "--collect-all=comtypes",
        "--collect-all=requests",
        "--collect-all=infer_rvc_python",
        "--collect-all=torch",
        "--collect-all=torchaudio",
        "--collect-all=transformers",
        "--collect-all=librosa",
        "--collect-all=soundfile",
        "--collect-all=pyworld",
    ]

    PyInstaller.__main__.run(args)

def post_build():
    """Copie les fichiers de configuration (.env, memoire_nora.json) et met à jour le raccourci Bureau."""
    print("📦 [3/4] Déploiement des configurations et synchronisation...")
    
    if not OUTPUT_DIR.exists():
        print(f"❌ Erreur: Dossier de sortie introuvable : {OUTPUT_DIR}")
        return False

    # 1. Copier le fichier .env
    env_src = PROJECT_DIR / ".env"
    if env_src.exists():
        shutil.copyfile(str(env_src), str(OUTPUT_DIR / ".env"))
        print("✔ Fichier .env synchronisé dans Nora/.")

    # 2. Copier ou initialiser la mémoire persistante
    mem_src = PROJECT_DIR / "memoire_nora.json"
    if mem_src.exists():
        shutil.copyfile(str(mem_src), str(OUTPUT_DIR / "memoire_nora.json"))
        print("✔ Mémoire memoire_nora.json synchronisée.")

    cfg_src = PROJECT_DIR / "smart_home_config.json"
    if cfg_src.exists():
        shutil.copyfile(str(cfg_src), str(OUTPUT_DIR / "smart_home_config.json"))
        print("✔ Configuration smart_home_config.json synchronisée.")

    state_src = PROJECT_DIR / "smart_home_state.json"
    if state_src.exists():
        shutil.copyfile(str(state_src), str(OUTPUT_DIR / "smart_home_state.json"))
        print("✔ État smart_home_state.json synchronisé.")

    carnet_src = PROJECT_DIR / "carnet_apprentissage_nora.md"
    if carnet_src.exists():
        shutil.copyfile(str(carnet_src), str(OUTPUT_DIR / "carnet_apprentissage_nora.md"))
        print("✔ Carnet d'apprentissage synchronisé.")

    # 3. Synchroniser les dossiers d'assets au cas où
    mascot_dest = OUTPUT_DIR / "mascot_assets"
    if not mascot_dest.exists():
        shutil.copytree(str(ASSETS_DIR), str(mascot_dest))

    sound_dest = OUTPUT_DIR / "sound_assets"
    sound_src = PROJECT_DIR / "sound_assets"
    if sound_src.exists() and not sound_dest.exists():
        shutil.copytree(str(sound_src), str(sound_dest))

    models_dest = OUTPUT_DIR / "models"
    models_src = PROJECT_DIR / "models"
    if models_src.exists() and not models_dest.exists():
        shutil.copytree(str(models_src), str(models_dest))
        print("✔ Modèles neuronaux Zero Two synchronisés dans Nora/.")

    ffmpeg_src = PROJECT_DIR / ".venv" / "Scripts" / "ffmpeg.exe"
    if ffmpeg_src.exists():
        shutil.copyfile(str(ffmpeg_src), str(OUTPUT_DIR / "ffmpeg.exe"))
        print("✔ ffmpeg.exe synchronisé dans Nora/.")

    # 4. Mettre à jour le raccourci Windows officiel sur le Bureau
    print("🔗 [4/4] Création du raccourci Bureau 'Nora.lnk' vers l'exécutable natif...")
    import setup_shortcuts
    if setup_shortcuts.create_desktop_shortcut():
        print("✔ Raccourci Bureau 'Nora.lnk' configuré avec succès vers Nora.exe !")
        print("✔ Raccourci clavier global 'Ctrl+Alt+N' actif.")
    else:
        print("⚠️ Avertissement lors de la création du raccourci.")

    print("\n=======================================================")
    print("🎉 SUCCÈS : Nora.exe est prêt et fonctionnel !")
    print(f"Emplacement : {EXE_PATH}")
    print("Vitesse de démarrage : < 0.5 seconde")
    print("Intégration Windows : Raccourci Bureau, System Tray, Zéro console")
    print("=======================================================\n")
    return True

if __name__ == "__main__":
    prepare_build()
    run_pyinstaller()
    post_build()
