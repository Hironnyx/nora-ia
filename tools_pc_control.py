"""
Module de contrôle direct du PC et d'automatisation Windows pour Nora :
- Gestion du volume audio (lecture, réglage précis en %, mute/unmute) via pycaw
- Lancement instantané d'applications populaires et protocoles Windows
- Actions système : Verrouillage de session, vidage de corbeille
"""
import os
import sys
import ctypes
import subprocess
import webbrowser
from typing import Optional, Tuple

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# =====================================================================
# 1. GESTION DU VOLUME AUDIO
# =====================================================================
def _get_audio_endpoint():
    try:
        try:
            import comtypes
            comtypes.CoInitialize()
        except Exception:
            pass
        from pycaw.pycaw import AudioUtilities
        spk = AudioUtilities.GetSpeakers()
        if spk and hasattr(spk, 'EndpointVolume'):
            return spk.EndpointVolume
    except Exception as e:
        print(f"[Audio Error] {e}")
    return None

def get_volume() -> int:
    """Retourne le volume actuel en pourcentage (0 à 100)."""
    endpoint = _get_audio_endpoint()
    if endpoint:
        try:
            return int(round(endpoint.GetMasterVolumeLevelScalar() * 100))
        except Exception:
            pass
    return 50

def set_volume(level: int) -> Tuple[bool, str]:
    """Règle le volume principal à un pourcentage précis (0 à 100)."""
    level = max(0, min(100, int(level)))
    endpoint = _get_audio_endpoint()
    if endpoint:
        try:
            endpoint.SetMute(0, None)  # Dé-mute automatiquement si le son était coupé
            endpoint.SetMasterVolumeLevelScalar(level / 100.0, None)
            return True, f"Volume réglé à {level}%."
        except Exception as e:
            return False, f"Erreur de réglage : {e}"
    return False, "Périphérique audio introuvable."

def change_volume_relative(delta: int) -> Tuple[bool, str]:
    """Augmente ou diminue le volume relativement (+10, -10, etc.)."""
    current = get_volume()
    target = max(0, min(100, current + delta))
    return set_volume(target)

def toggle_mute() -> Tuple[bool, str]:
    """Bascule entre Muet et Son rétabli."""
    endpoint = _get_audio_endpoint()
    if endpoint:
        try:
            current_mute = endpoint.GetMute()
            new_mute = 0 if current_mute else 1
            endpoint.SetMute(new_mute, None)
            stat = "Son coupé." if new_mute else f"Son rétabli à {get_volume()}%."
            return True, stat
        except Exception as e:
            return False, f"Erreur mute : {e}"
    return False, "Périphérique audio introuvable."

# =====================================================================
# 2. LANCEMENT D'APPLICATIONS ET SITES
# =====================================================================
APP_MAPPINGS = {
    "spotify": ("spotify:", "Spotify"),
    "discord": ("discord:", "Discord"),
    "steam": ("steam:", "Steam"),
    "calc": ("calc", "Calculatrice"),
    "calculatrice": ("calc", "Calculatrice"),
    "notepad": ("notepad", "Bloc-notes"),
    "bloc-notes": ("notepad", "Bloc-notes"),
    "bloc notes": ("notepad", "Bloc-notes"),
    "explorer": ("explorer", "Explorateur de fichiers"),
    "explorateur": ("explorer", "Explorateur de fichiers"),
    "terminal": ("wt", "Windows Terminal"),
    "invite de commande": ("cmd", "Invite de commande"),
    "cmd": ("cmd", "Invite de commande"),
    "youtube": ("https://www.youtube.com", "YouTube"),
    "google": ("https://www.google.com", "Google"),
    "navigateur": ("https://www.google.com", "Navigateur Internet"),
    "vscode": ("code", "Visual Studio Code"),
    "vs code": ("code", "Visual Studio Code"),
    "code": ("code", "Visual Studio Code"),
}

def launch_application(app_name_query: str) -> Tuple[bool, str]:
    """Ouvre une application ou un service Windows selon le mot-clé."""
    query = app_name_query.strip().lower()

    # Recherche directe dans le dictionnaire
    for key, (target, pretty_name) in APP_MAPPINGS.items():
        if key in query:
            try:
                if target.startswith("http"):
                    webbrowser.open(target)
                elif target.endswith(":"):
                    os.system(f"start {target}")
                else:
                    os.system(f"start {target}")
                return True, f"{pretty_name} est lancé !"
            except Exception as e:
                return False, f"Impossible de lancer {pretty_name} : {e}"

    # Essai générique Windows (start <nom>)
    try:
        subprocess.Popen(
            f"start {app_name_query}",
            shell=True,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
        )
        return True, f"Tentative d'ouverture de '{app_name_query}' en cours."
    except Exception as e:
        return False, f"Impossible d'ouvrir '{app_name_query}' : {e}"

# =====================================================================
# 3. ACTIONS SYSTÈME WINDOWS
# =====================================================================
def lock_workstation() -> Tuple[bool, str]:
    """Verrouille immédiatement l'ordinateur Windows."""
    try:
        user32 = ctypes.windll.user32
        res = user32.LockWorkStation()
        if res:
            return True, "Ordinateur verrouillé."
        else:
            return False, "Échec du verrouillage."
    except Exception as e:
        return False, f"Erreur de verrouillage : {e}"

def empty_recycle_bin() -> Tuple[bool, str]:
    """Vide la corbeille de Windows silencieusement."""
    try:
        cmd = ["powershell", "-NoProfile", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"]
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
        )
        return True, "La corbeille a été vidée avec succès."
    except Exception as e:
        return False, f"Erreur lors du vidage de la corbeille : {e}"

if __name__ == "__main__":
    print(f"Volume actuel : {get_volume()}%")
    print("Test contrôle PC prêt.")
