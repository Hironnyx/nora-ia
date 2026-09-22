"""
Module Mode Gaming pour Nora :
- Boost RAM : Purge de la mémoire de travail (Working Set) des applications d'arrière-plan via l'API Windows (psapi.dll).
- Mode Silence / Ne Pas Déranger : Maintient Nora silencieuse pendant les sessions de jeu pour ne pas perturber l'audio.
- Détection des jeux en cours d'exécution.
"""
import os
import sys
import ctypes
import psutil
from typing import Optional, Tuple

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

_GAMING_MODE_ACTIVE = False

# Liste des exécutables de jeux populaires pour détection automatique
KNOWN_GAMES = {
    "cs2.exe": "Counter-Strike 2",
    "valorant-win64-shipping.exe": "Valorant",
    "league of legends.exe": "League of Legends",
    "leagueclient.exe": "League of Legends",
    "r5apex.exe": "Apex Legends",
    "fortniteclient-win64-shipping.exe": "Fortnite",
    "minecraft.exe": "Minecraft",
    "javaw.exe": "Minecraft / Java Game",
    "gta5.exe": "Grand Theft Auto V",
    "cyberpunk2077.exe": "Cyberpunk 2077",
    "genshinimpact.exe": "Genshin Impact",
    "robloxplayerbeta.exe": "Roblox",
    "overwatch.exe": "Overwatch 2",
    "rocketleague.exe": "Rocket League",
    "dota2.exe": "Dota 2",
    "rainbowsix.exe": "Rainbow Six Siege",
    "eldenring.exe": "Elden Ring",
    "destiny2.exe": "Destiny 2",
    "starfield.exe": "Starfield",
    "helldivers2.exe": "Helldivers 2",
    "baldursgate3.exe": "Baldur's Gate 3",
}

# Processus système critiques à ne jamais toucher
SYSTEM_WHITELIST = {
    "system", "registry", "smss.exe", "csrss.exe", "wininit.exe", "services.exe",
    "lsass.exe", "svchost.exe", "dwm.exe", "explorer.exe", "antigravity.exe"
}

def optimize_ram_boost() -> Tuple[int, float]:
    """
    Purge le working set des processus inactifs via EmptyWorkingSet de psapi.dll.
    Retourne (nombre_processus_optimisés, mo_libérés).
    """
    if sys.platform != "win32":
        return 0, 0.0

    mem_before = psutil.virtual_memory().available
    current_pid = os.getpid()
    count_cleaned = 0

    # Droits Windows nécessaires : PROCESS_QUERY_INFORMATION (0x0400) | PROCESS_SET_QUOTA (0x0100)
    PROCESS_ALL_QUERY_QUOTA = 0x0400 | 0x0100
    kernel32 = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            pid = proc.info['pid']
            name = (proc.info['name'] or "").lower()

            if pid == current_pid or pid <= 4 or name in SYSTEM_WHITELIST:
                continue

            # Ne pas purger les jeux actifs
            if name in KNOWN_GAMES:
                continue

            h_proc = kernel32.OpenProcess(PROCESS_ALL_QUERY_QUOTA, False, pid)
            if h_proc:
                success = psapi.EmptyWorkingSet(h_proc)
                kernel32.CloseHandle(h_proc)
                if success:
                    count_cleaned += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception:
            continue

    mem_after = psutil.virtual_memory().available
    freed_bytes = max(0, mem_after - mem_before)
    freed_mb = round(freed_bytes / (1024 * 1024), 1)

    return count_cleaned, freed_mb

def is_gaming_mode() -> bool:
    """Indique si le mode gaming est actuellement actif."""
    global _GAMING_MODE_ACTIVE
    return _GAMING_MODE_ACTIVE

def set_gaming_mode(enabled: bool) -> str:
    """Active ou désactive le mode gaming."""
    global _GAMING_MODE_ACTIVE
    _GAMING_MODE_ACTIVE = enabled

    if enabled:
        count, freed = optimize_ram_boost()
        game = detect_running_game()
        game_str = f" Jeu détecté : {game}." if game else ""
        return (
            f"🎮 Mode Performance Jeu ACTIVÉ, Maverick. {count} processus en arrière-plan vidés de leur cache "
            f"({freed} Mo de RAM libérés).{game_str} Priorité absolue accordée à vos performances."
        )
    else:
        return "✨ Mode Performance DÉSACTIVÉ. Les alertes audio reprennent leur cours normal, Maverick."

def toggle_gaming_mode() -> Tuple[bool, str]:
    """Bascule l'état du mode gaming."""
    new_state = not is_gaming_mode()
    msg = set_gaming_mode(new_state)
    return new_state, msg

def detect_running_game() -> Optional[str]:
    """Détecte si un jeu répertorié est actuellement en cours d'exécution."""
    for proc in psutil.process_iter(['name']):
        try:
            name = (proc.info['name'] or "").lower()
            if name in KNOWN_GAMES:
                return KNOWN_GAMES[name]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

if __name__ == "__main__":
    print("Test Gaming Mode...")
    print(f"Jeu en cours: {detect_running_game()}")
    count, mb = optimize_ram_boost()
    print(f"RAM Boost: {count} processus optimisés, {mb} Mo libérés.")
    print(set_gaming_mode(True))
    print(f"Mode Gaming actif ? {is_gaming_mode()}")
    print(set_gaming_mode(False))
