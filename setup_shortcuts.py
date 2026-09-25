"""
Gestion des raccourcis Windows et du démarrage automatique pour Nora :
- Génère une icône Windows .ico de Zero Two à partir des assets
- Crée le raccourci Bureau 'Nora.lnk' avec la combinaison de touches 'Ctrl+Alt+N'
- Permet d'activer/désactiver le lancement automatique au démarrage de Windows (shell:startup)
- Utilise pythonw.exe pour un lancement 100% silencieux sans fenêtre de console noire
"""
import os
import sys
import subprocess
from pathlib import Path
from PIL import Image

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

PROJECT_DIR = Path(r"C:\Users\maverick\Documents\Agent ia").resolve()
NORA_EXE = PROJECT_DIR / "dist" / "Nora" / "Nora.exe"
PYTHONW_EXE = PROJECT_DIR / ".venv" / "Scripts" / "pythonw.exe"
PYTHON_EXE = PROJECT_DIR / ".venv" / "Scripts" / "python.exe"
DESKTOP_PET = PROJECT_DIR / "desktop_pet.py"
ASSETS_DIR = PROJECT_DIR / "mascot_assets"
ICON_PATH = ASSETS_DIR / "nora.ico"

DESKTOP_DIR = Path.home() / "Desktop"
STARTUP_DIR = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

def ensure_nora_icon() -> Path:
    """Convertit nora_idle.png en icône Windows multi-résolution .ico."""
    png_path = ASSETS_DIR / "nora_idle.png"
    if not png_path.exists():
        from mascot_assets import generate_all_zero_two_assets
        generate_all_zero_two_assets()

    img = Image.open(str(png_path)).convert("RGBA")
    # Génère les résolutions standards Windows (16, 32, 48, 64, 128, 256)
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(str(ICON_PATH), format='ICO', sizes=icon_sizes)
    return ICON_PATH

def create_windows_shortcut(
    shortcut_path: Path,
    target_path: Path,
    arguments: str = "",
    working_dir: Path = PROJECT_DIR,
    icon_path: Path = ICON_PATH,
    hotkey: str = "",
    description: str = "Nora Mascotte IA"
) -> bool:
    """Crée un raccourci Windows (.lnk) avec WScript.Shell via PowerShell."""
    ensure_nora_icon()
    
    target_str = str(target_path)
    work_str = str(working_dir)
    ico_str = str(icon_path) if icon_path.exists() else target_str
    lnk_str = str(shortcut_path)

    ps1_script = PROJECT_DIR / "make_shortcut.ps1"
    try:
        res = subprocess.run(
            [
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(ps1_script),
                lnk_str, target_str, arguments, work_str, f"{ico_str},0", description, hotkey
            ],
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
        )
        return res.returncode == 0
    except Exception as e:
        print(f"Erreur création raccourci : {e}")
        return False

def create_desktop_shortcut() -> bool:
    """Crée le raccourci officiel sur le Bureau avec le raccourci clavier Ctrl+Alt+N."""
    desktop_lnk = DESKTOP_DIR / "Nora.lnk"
    if PYTHONW_EXE.exists():
        target = PYTHONW_EXE
        args = "desktop_pet.py"
        work_dir = PROJECT_DIR
        icon = ICON_PATH
    elif NORA_EXE.exists():
        target = NORA_EXE
        args = ""
        work_dir = NORA_EXE.parent
        icon = NORA_EXE.parent / "mascot_assets" / "nora.ico"
        if not icon.exists():
            icon = ICON_PATH
    else:
        target = PYTHON_EXE
        args = "desktop_pet.py"
        work_dir = PROJECT_DIR
        icon = ICON_PATH

    return create_windows_shortcut(
        shortcut_path=desktop_lnk,
        target_path=target,
        arguments=args,
        working_dir=work_dir,
        icon_path=icon,
        hotkey="Ctrl+Alt+N",
        description="NORA WORKSTATION | Copilote & Ingénierie (Ctrl+Alt+N)"
    )

def is_startup_enabled() -> bool:
    """Vérifie si Nora est configurée pour démarrer avec Windows."""
    startup_lnk = STARTUP_DIR / "Nora.lnk"
    return startup_lnk.exists()

def set_startup_enabled(enabled: bool) -> bool:
    """Active ou désactive le lancement de Nora au démarrage de Windows."""
    startup_lnk = STARTUP_DIR / "Nora.lnk"
    if enabled:
        if PYTHONW_EXE.exists():
            target = PYTHONW_EXE
            args = "desktop_pet.py"
            work_dir = PROJECT_DIR
            icon = ICON_PATH
        elif NORA_EXE.exists():
            target = NORA_EXE
            args = ""
            work_dir = NORA_EXE.parent
            icon = NORA_EXE.parent / "mascot_assets" / "nora.ico"
            if not icon.exists():
                icon = ICON_PATH
        else:
            target = PYTHON_EXE
            args = "desktop_pet.py"
            work_dir = PROJECT_DIR
            icon = ICON_PATH

        return create_windows_shortcut(
            shortcut_path=startup_lnk,
            target_path=target,
            arguments=args,
            working_dir=work_dir,
            icon_path=icon,
            description="Lancement automatique de Nora au démarrage de Windows"
        )
    else:
        if startup_lnk.exists():
            try:
                startup_lnk.unlink()
                return True
            except Exception:
                return False
        return True

if __name__ == "__main__":
    print("Création de l'icône et des raccourcis...")
    ico = ensure_nora_icon()
    print(f"✔ Icône générée : {ico}")
    if create_desktop_shortcut():
        print("✔ Raccourci Bureau 'Nora.lnk' créé avec la combinaison Ctrl+Alt+N !")
    print(f"Statut démarrage automatique actuel : {'Actif' if is_startup_enabled() else 'Inactif'}")
