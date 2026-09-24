"""
Module Autopilote OS & Automatisation Avancée pour Nora (Computer Use & 3D Autopilot) :
- Pilotage direct en tâche de fond de PrusaSlicer CLI (prusa-slicer-console.exe) :
  * Analyse géométrique complète de fichiers STL/3MF/OBJ (dimensions X/Y/Z, volume mm³, facettes, manifold)
  * Tranchage 100% autonome en G-code sans intervention humaine (avec contrôle du remplissage et de la hauteur de couche)
  * Mise à jour automatique de la file d'attente d'impression 3D dans maverick_3dprint_state.json
- Contrôle de fenêtres et d'applications Windows :
  * Basculer au premier plan ou lancer une application (PrusaSlicer, VS Code, Blender, etc.)
  * Minimiser / Restaurer les fenêtres du bureau
"""

import os
import sys
import time
import json
import ctypes
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent.resolve()

PRUSA_CONSOLE_CANDIDATES = [
    Path(r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe"),
    Path(r"C:\Program Files (x86)\Prusa3D\PrusaSlicer\prusa-slicer-console.exe"),
    Path.home() / "AppData" / "Local" / "Programs" / "PrusaSlicer" / "prusa-slicer-console.exe"
]

STATE_3D_FILE = BASE_DIR / "maverick_3dprint_state.json"
MODELS_DIR = Path.home() / "Documents" / "Impression3D"

user32 = ctypes.windll.user32

def find_prusa_console() -> Optional[str]:
    """Trouve l'exécutable console de PrusaSlicer sur le système de Maverick."""
    for p in PRUSA_CONSOLE_CANDIDATES:
        if p.exists():
            return str(p)
    return None

def inspect_3d_model(model_path: str) -> str:
    """
    Analyse géométrique complète d'un fichier 3D (STL, 3MF, OBJ) via PrusaSlicer.
    Extrait les dimensions réelles (X, Y, Z en mm), le volume et la conformité manifold.
    """
    exe = find_prusa_console()
    if not exe:
        return "Erreur : PrusaSlicer n'est pas installé dans le répertoire standard."

    p = Path(model_path)
    if not p.is_absolute():
        candidates = [
            MODELS_DIR / model_path,
            Path.home() / "Downloads" / model_path,
            Path.home() / "Downloads" / "Autres" / model_path,
            BASE_DIR / model_path
        ]
        found = False
        for c in candidates:
            if c.exists():
                p = c
                found = True
                break
        if not found:
            return f"Erreur : Fichier 3D introuvable '{model_path}'."

    cmd = [exe, "--info", str(p)]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        out = res.stdout.strip()
        
        info = {}
        for line in out.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                info[k.strip()] = v.strip()

        dim_x = round(float(info.get("size_x", 0)), 2)
        dim_y = round(float(info.get("size_y", 0)), 2)
        dim_z = round(float(info.get("size_z", 0)), 2)
        vol_cm3 = round(float(info.get("volume", 0)) / 1000.0, 2)
        facets = info.get("number_of_facets", "inconnu")
        manifold = "Oui (Étanche)" if info.get("manifold") == "yes" else "Non (Erreurs de maillage)"

        return (
            f"📐 Analyse 3D de '{p.name}' :\n"
            f"- Dimensions : {dim_x} x {dim_y} x {dim_z} mm\n"
            f"- Volume matière estimé : {vol_cm3} cm³\n"
            f"- Facettes : {facets}\n"
            f"- Maillage valide (Manifold) : {manifold}\n"
            f"- Emplacement : {p}"
        )
    except Exception as e:
        return f"Erreur lors de l'analyse du modèle 3D : {str(e)}"

def slice_3d_model(
    model_path: str,
    fill_density: int = 15,
    layer_height: float = 0.2,
    output_gcode_path: str = ""
) -> str:
    """
    Tranche automatiquement un modèle 3D en G-code en tâche de fond via PrusaSlicer.
    Paramètres :
    - model_path : Nom ou chemin du fichier STL/3MF (ex: 'test.stl')
    - fill_density : Pourcentage de remplissage infill (ex: 15%)
    - layer_height : Hauteur de couche en mm (ex: 0.2 mm)
    - output_gcode_path : Chemin de sortie optionnel (par défaut généré dans Impression3D/GCode/)
    """
    exe = find_prusa_console()
    if not exe:
        return "Erreur : PrusaSlicer n'est pas disponible sur cette machine."

    p = Path(model_path)
    if not p.is_absolute():
        candidates = [
            MODELS_DIR / model_path,
            Path.home() / "Downloads" / model_path,
            Path.home() / "Downloads" / "Autres" / model_path,
            BASE_DIR / model_path
        ]
        found = False
        for c in candidates:
            if c.exists():
                p = c
                found = True
                break
        if not found:
            return f"Erreur : Impossible de localiser le modèle 3D '{model_path}'."

    if not output_gcode_path:
        out_dir = MODELS_DIR / "GCode"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{p.stem}_sliced_{int(time.time())}.gcode"
    else:
        out_file = Path(output_gcode_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        exe,
        "--export-gcode", str(p),
        f"--fill-density={fill_density}%",
        f"--layer-height={layer_height}",
        "--output", str(out_file)
    ]

    t0 = time.time()
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        elapsed = round(time.time() - t0, 2)
        
        if out_file.exists() and out_file.stat().st_size > 0:
            size_kb = round(out_file.stat().st_size / 1024, 1)
            
            # Enregistrement dans la file d'attente d'impression 3D
            _add_to_print_queue(p.name, str(out_file), size_kb)
            
            return (
                f"✅ Tranchage 3D réussi en {elapsed}s !\n"
                f"- Modèle source : {p.name}\n"
                f"- G-code généré : {out_file.name} ({size_kb} Ko)\n"
                f"- Paramètres : Remplissage {fill_density}%, Couche {layer_height} mm\n"
                f"- Emplacement : {out_file}\n"
                f"Le fichier a été ajouté à votre file d'attente d'impression 3D, Maverick."
            )
        else:
            return f"Échec du tranchage 3D : {res.stderr or res.stdout}"
    except Exception as e:
        return f"Erreur lors de l'exécution du tranchage : {str(e)}"

def _add_to_print_queue(model_name: str, gcode_path: str, size_kb: float):
    """Met à jour l'état de l'Atelier 3D persistant."""
    try:
        data = {}
        if STATE_3D_FILE.exists():
            with open(STATE_3D_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        
        q = data.setdefault("print_queue", [])
        q.append({
            "id": f"job_{int(time.time())}",
            "filename": model_name,
            "gcode_path": gcode_path,
            "size_kb": size_kb,
            "added_date": time.strftime("%d/%m/%Y %H:%M"),
            "status": "Prêt à imprimer"
        })
        with open(STATE_3D_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Erreur mise à jour file 3D: {e}")

def focus_or_launch_app(app_name_or_keyword: str) -> str:
    """
    Recherche une fenêtre existante correspondant à un nom ou mot-clé et la met au premier plan.
    Si elle n'est pas ouverte, tente de la lancer.
    """
    keyword = app_name_or_keyword.lower().strip()
    
    # 1. Parcourir les fenêtres ouvertes
    target_hwnd = None
    target_title = ""

    def enum_cb(hwnd, extra):
        nonlocal target_hwnd, target_title
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                t = buff.value
                if keyword in t.lower():
                    target_hwnd = hwnd
                    target_title = t
                    return False
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

    if target_hwnd:
        # Restaurer si minimisée et mettre au premier plan
        user32.ShowWindow(target_hwnd, 9) # SW_RESTORE
        user32.SetForegroundWindow(target_hwnd)
        return f"Fenêtre '{target_title}' placée au premier plan, Maverick."

    # 2. Lancement spécifique si PrusaSlicer
    if "prusa" in keyword or "slicer" in keyword:
        try:
            subprocess.Popen([r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer.exe"])
            return "PrusaSlicer a été lancé avec succès, Maverick."
        except Exception as e:
            return f"Erreur lors du lancement de PrusaSlicer : {e}"

    # 3. Lancement spécifique si VS Code
    if "code" in keyword or "vscode" in keyword:
        try:
            subprocess.Popen(["code"], shell=True)
            return "Visual Studio Code a été lancé avec succès, Maverick."
        except Exception as e:
            return f"Erreur lors du lancement de VS Code : {e}"

    return f"Aucune fenêtre correspondant à '{app_name_or_keyword}' n'a été trouvée ouverte."

def minimize_all_windows() -> str:
    """Affiche le bureau Windows en minimisant les fenêtres actives."""
    try:
        user32.keybd_event(0x5B, 0, 0, 0) # Win key down
        user32.keybd_event(0x44, 0, 0, 0) # 'D' key down
        user32.keybd_event(0x44, 0, 2, 0) # 'D' key up
        user32.keybd_event(0x5B, 0, 2, 0) # Win key up
        return "Bureau Windows affiché (fenêtres réduites), Maverick."
    except Exception as e:
        return f"Erreur : {e}"

if __name__ == "__main__":
    print("Test du module tools_autopilot...")
    # Test d'analyse du STL présent sur la machine
    stl_path = r"C:\Users\maverick\Downloads\Autres\test.stl"
    if Path(stl_path).exists():
        print(inspect_3d_model(stl_path))
        print("\nTest de tranchage en G-code...")
        print(slice_3d_model(stl_path, fill_density=20, layer_height=0.2))
    else:
        print("Fichier test.stl non trouvé pour le test.")
