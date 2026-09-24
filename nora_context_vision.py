"""
Module de Vision Contextuelle Active & Détection d'Application pour Nora (Context Vision Engine) :
- Surveille en tâche de fond la fenêtre active au premier plan sur Windows (0% CPU).
- Identifie l'exécutable, le titre de la fenêtre et la catégorie d'activité de Maverick :
  * 3D_PRINTING : PrusaSlicer, Cura, Bambu Studio, OrcaSlicer, etc.
  * 3D_MODELING : Blender, Fusion 360, FreeCAD, SolidWorks, etc.
  * DEVELOPMENT : VS Code, Visual Studio, Cursor, PyCharm, Terminal, etc.
  * GAMING : Steam, jeux plein écran, launchers.
  * WEB_RESEARCH : Chrome, Firefox, Edge, Brave.
  * PRODUCTIVITY : Documents, tableurs, éditeurs de texte.
- Détecte les transitions d'activité pour permettre à Nora d'adapter spontanément
  sa posture, son dialogue, ses suggestions d'assistance et le mode de son dragonnet Vermeil.
- Fournit une fonction de capture d'écran ciblée sur la fenêtre active pour analyse IA.
"""

import os
import sys
import time
import ctypes
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import psutil

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent.resolve()

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

class NoraContextVision:
    """Moteur de détection de contexte passif et d'activité active de Maverick."""

    def __init__(self):
        self.last_context: Dict[str, Any] = {}
        self.last_switch_time = time.time()
        self.active_category = "GENERAL"
        self.active_app_name = "explorer.exe"
        self.active_window_title = "Bureau Windows"

    def get_current_context(self) -> Dict[str, Any]:
        """
        Interroge instantanément la fenêtre au premier plan de Windows via Win32 (<0.5 ms).
        Retourne un dictionnaire complet décrivant l'activité courante de Maverick.
        """
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return {
                "category": "DESKTOP",
                "app": "explorer.exe",
                "title": "Bureau Windows",
                "is_fullscreen": False,
                "description": "Maverick est sur son bureau Windows ou en transition."
            }

        # 1. Titre de la fenêtre
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        title = buff.value.strip() or "Fenêtre sans titre"

        # 2. Processus associé
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        exe_name = "unknown.exe"
        try:
            proc = psutil.Process(pid.value)
            exe_name = proc.name()
        except Exception:
            pass

        # 3. Détection plein écran (ex: pour les jeux ou présentations)
        is_fullscreen = self._check_fullscreen(hwnd)

        # 4. Classification catégorielle intelligente
        cat, desc = self._classify_activity(exe_name, title)

        now = time.time()
        if exe_name != self.active_app_name or cat != self.active_category:
            self.last_switch_time = now
            self.active_app_name = exe_name
            self.active_category = cat
            self.active_window_title = title

        context = {
            "category": cat,
            "app": exe_name,
            "title": title,
            "pid": pid.value,
            "hwnd": hwnd,
            "is_fullscreen": is_fullscreen,
            "time_in_app_seconds": int(now - self.last_switch_time),
            "description": desc
        }
        self.last_context = context
        return context

    def _check_fullscreen(self, hwnd) -> bool:
        """Détecte si la fenêtre active occupe l'intégralité de l'écran principal."""
        try:
            rect = ctypes.wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            screen_w = user32.GetSystemMetrics(0) # SM_CXSCREEN
            screen_h = user32.GetSystemMetrics(1) # SM_CYSCREEN
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            return w >= screen_w and h >= screen_h
        except Exception:
            return False

    def _classify_activity(self, exe: str, title: str) -> Tuple[str, str]:
        """Catégorise l'activité de Maverick en fonction de l'exécutable et du titre."""
        lower_exe = exe.lower()
        lower_title = title.lower()

        # Impression 3D
        if any(k in lower_exe for k in ["prusa-slicer", "cura", "bambu", "orca", "creality"]) or "slicer" in lower_title:
            return "3D_PRINTING", "Maverick prépare ou tranche un modèle 3D sur PrusaSlicer."

        # Modélisation 3D / CAD
        if any(k in lower_exe for k in ["blender", "fusion360", "freecad", "solidworks", "inventor", "3dsmax", "maya"]):
            return "3D_MODELING", "Maverick conçoit ou modélise une pièce en 3D."

        # Développement & Code
        if any(k in lower_exe for k in ["code", "devenv", "pycharm", "cursor", "sublime", "notepad++", "windowsterminal", "powershell"]):
            return "DEVELOPMENT", "Maverick travaille sur du code ou une console de développement."

        # Jeux Vidéo & Immersion
        if any(k in lower_exe for k in ["steam", "epicgames", "riotclient", "genshin", "valorant", "cyberpunk"]):
            return "GAMING", "Maverick est en session de jeu vidéo."

        # Recherche & Web
        if any(k in lower_exe for k in ["chrome", "firefox", "msedge", "brave", "opera"]):
            return "WEB_RESEARCH", "Maverick effectue des recherches ou consulte le web."

        # Bureautique & Documents
        if any(k in lower_exe for k in ["winword", "excel", "powerpnt", "acrobat", "foxit"]):
            return "PRODUCTIVITY", "Maverick consulte ou rédige des documents."

        return "GENERAL", f"Maverick utilise {exe}."

    def capture_active_window(self, output_path: Optional[Path] = None) -> Optional[Path]:
        """Capture uniquement la fenêtre active pour une analyse visuelle instantanée."""
        try:
            from PIL import ImageGrab
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None
            
            rect = ctypes.wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            bbox = (rect.left, rect.top, rect.right, rect.bottom)
            
            if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
                return None

            img = ImageGrab.grab(bbox=bbox)
            if not output_path:
                target_dir = BASE_DIR / "temp_captures"
                target_dir.mkdir(parents=True, exist_ok=True)
                output_path = target_dir / f"active_win_{int(time.time())}.png"

            img.save(output_path, "PNG")
            return output_path
        except Exception as e:
            print(f"⚠️ [ContextVision] Erreur capture fenêtre active: {e}")
            return None

# Singleton mondial
context_vision = NoraContextVision()

if __name__ == "__main__":
    print("Test du Moteur de Vision Contextuelle Active de Nora...")
    ctx = context_vision.get_current_context()
    print("Contexte actif détecté :")
    for k, v in ctx.items():
        print(f"  - {k}: {v}")
