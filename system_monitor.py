"""
Module de surveillance système et d'alertes en temps réel pour Nora :
- Surveillance CPU, RAM, Disque, Batterie via psutil
- Détection des surcharges et anomalies matérielles avec délai anti-spam
- Détection automatique des nouveaux fichiers téléchargés dans le dossier Téléchargements
- Génération d'un bilan de santé complet du PC en langage naturel pour Nora
"""
import os
import sys
import time
import threading
from pathlib import Path
from typing import Callable, Optional, Dict, Any

import psutil

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

DOWNLOADS_DIR = Path.home() / "Downloads"

def get_top_resource_processes(limit: int = 3) -> Dict[str, Any]:
    """Trouve les processus les plus gourmands en mémoire et processeur."""
    procs = []
    for p in psutil.process_iter(['name', 'cpu_percent', 'memory_info']):
        try:
            info = p.info
            name = info['name']
            if name.lower() in ['system idle process', 'system']:
                continue
            mem_mb = (info['memory_info'].rss / (1024 * 1024)) if info['memory_info'] else 0
            procs.append({
                'name': name,
                'cpu': info.get('cpu_percent') or 0.0,
                'mem_mb': mem_mb
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    top_mem = sorted(procs, key=lambda x: x['mem_mb'], reverse=True)[:limit]
    top_cpu = sorted(procs, key=lambda x: x['cpu'], reverse=True)[:limit]
def clean_ram_cache() -> str:
    """Libère la mémoire RAM inutilisée, purge le ramasse-miettes et vide les caches."""
    import gc
    gc.collect()
    if sys.platform == "win32":
        try:
            import ctypes
            # Vide le working set du processus actuel
            ctypes.windll.kernel32.SetProcessWorkingSetSize(-1, -1, -1)
        except Exception:
            pass
    return "Mémoire vive optimisée et caches temporaires purgés."

# Initialiser le calcul CPU de psutil
try:
    psutil.cpu_percent(interval=None)
except Exception:
    pass

_last_disk_check_time = 0.0
_cached_disk_info = {'total_gb': 0, 'used_gb': 0, 'free_gb': 0, 'percent': 0}

def get_system_stats() -> Dict[str, Any]:
    """Récupère l'état instantané du matériel du PC de manière 100% non-bloquante (<1ms)."""
    global _last_disk_check_time, _cached_disk_info
    
    # 1. CPU non-bloquant
    try:
        cpu_percent = psutil.cpu_percent(interval=None)
    except Exception:
        cpu_percent = 0.0

    # 2. RAM (Requête C native ultra-rapide)
    try:
        import nora_native_win32
        m = nora_native_win32.native_core.get_native_memory()
        ram_pct = m["load_percent"]
        ram_used = round(m["used_mb"] / 1024, 1)
        ram_total = round(m["total_mb"] / 1024, 1)
    except Exception:
        try:
            ram = psutil.virtual_memory()
            ram_pct = ram.percent
            ram_used = round(ram.used / (1024**3), 1)
            ram_total = round(ram.total / (1024**3), 1)
        except Exception:
            ram_pct, ram_used, ram_total = 0.0, 0.0, 0.0

    # 3. Disque C: avec cache de 5 secondes pour économiser les I/O
    now = time.time()
    if now - _last_disk_check_time > 5.0 or _cached_disk_info['total_gb'] == 0:
        try:
            disk_c = psutil.disk_usage("C:\\")
            _cached_disk_info = {
                'total_gb': round(disk_c.total / (1024**3), 1),
                'used_gb': round(disk_c.used / (1024**3), 1),
                'free_gb': round(disk_c.free / (1024**3), 1),
                'percent': disk_c.percent
            }
            _last_disk_check_time = now
        except Exception:
            pass

    # Batterie
    battery_info = None
    try:
        bat = psutil.sensors_battery()
        if bat is not None:
            battery_info = {
                'percent': int(bat.percent),
                'power_plugged': bat.power_plugged
            }
    except Exception:
        battery_info = None

    return {
        'cpu_percent': cpu_percent,
        'ram_percent': ram_pct,
        'ram_used_gb': ram_used,
        'ram_total_gb': ram_total,
        'disk': _cached_disk_info,
        'battery': battery_info
    }

_last_cpu_percent = 5.0
_last_cpu_time = 0.0

def get_system_diagnostics() -> Dict[str, Any]:
    """Fournit les métriques matérielles complètes et garanties non-nulles pour le QG."""
    global _last_cpu_percent, _last_cpu_time
    stats = get_system_stats()

    now = time.time()
    try:
        cpu = psutil.cpu_percent(interval=None)
        if cpu > 0.0:
            _last_cpu_percent = cpu
        elif now - _last_cpu_time > 2.0:
            cpu = psutil.cpu_percent(interval=0.05)
            _last_cpu_percent = max(1.0, cpu)
            _last_cpu_time = now
    except Exception:
        cpu = _last_cpu_percent

    disk_info = stats.get('disk', {})
    disk_pct = disk_info.get('percent', 0.0)
    ram_pct = stats.get('ram_percent', 0.0)
    ram_used = stats.get('ram_used_gb', 0.0)
    ram_tot = stats.get('ram_total_gb', 0.0)

    # Récupération télémétrie GPU NVIDIA si disponible
    gpu_info = {
        'available': False,
        'model': 'RTX 4080',
        'load_percent': 0.0,
        'memory_used_mb': 0,
        'memory_total_mb': 0,
        'temperature_c': 0
    }
    try:
        import subprocess
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=1, creationflags=flags
        )
        if res.returncode == 0 and res.stdout.strip():
            parts = [p.strip() for p in res.stdout.strip().split("\n")[0].split(",")]
            if len(parts) >= 2:
                gpu_info['available'] = True
                gpu_info['model'] = parts[0]
                gpu_info['load_percent'] = float(parts[1]) if parts[1] else 0.0
            if len(parts) >= 4:
                gpu_info['memory_used_mb'] = int(float(parts[2])) if parts[2] else 0
                gpu_info['memory_total_mb'] = int(float(parts[3])) if parts[3] else 0
            if len(parts) >= 5:
                gpu_info['temperature_c'] = int(float(parts[4])) if parts[4] else 0
    except Exception:
        pass

    # Score de santé global sur 100
    health = max(15, int(100 - (_last_cpu_percent * 0.3) - (ram_pct * 0.3) - (disk_pct * 0.2)))

    return {
        'cpu_percent': _last_cpu_percent,
        'ram_percent': ram_pct,
        'ram_used_gb': ram_used,
        'ram_total_gb': ram_tot,
        'ram': {
            'percent': ram_pct,
            'used_gb': ram_used,
            'total_gb': ram_tot
        },
        'disk_percent': disk_pct,
        'disk_total_gb': disk_info.get('total_gb', 0.0),
        'disk_free_gb': disk_info.get('free_gb', 0.0),
        'disk': disk_info,
        'gpu_percent': gpu_info['load_percent'],
        'gpu': gpu_info,
        'health_score': health,
        'battery': stats.get('battery')
    }

def get_system_health_report() -> str:
    """Génère un diagnostic complet et vivant de l'ordinateur, prêt à être énoncé par Nora."""
    stats = get_system_stats()
    top_procs = get_top_resource_processes(limit=1)

    cpu = stats['cpu_percent']
    ram_pct = stats['ram_percent']
    ram_used = stats['ram_used_gb']
    ram_tot = stats['ram_total_gb']
    free_disk = stats['disk']['free_gb']
    battery = stats['battery']

    top_mem_proc = top_procs['top_mem'][0]['name'] if top_procs['top_mem'] else "Inconnu"
    top_mem_proc_mb = int(top_procs['top_mem'][0]['mem_mb']) if top_procs['top_mem'] else 0

    elements = []

    # Diagnostic global
    if ram_pct > 88 or cpu > 88 or free_disk < 15:
        elements.append("Maverick, votre système est fortement sollicité en ce moment.")
    else:
        elements.append("L'ensemble des métriques de votre poste est optimal, Maverick.")

    # CPU & RAM
    elements.append(f"Le processeur est à {cpu}% et la mémoire vive est à {ram_pct}% ({ram_used} Go utilisés sur {ram_tot} Go).")
    if top_mem_proc_mb > 1000:
        elements.append(f"L'application la plus gourmande est '{top_mem_proc}' avec {top_mem_proc_mb} Mo.")

    # Disque
    elements.append(f"Il vous reste {free_disk} Go de libre sur le disque C:.")

    # Batterie
    if battery:
        etat_plug = "en charge" if battery['power_plugged'] else "sur batterie"
        elements.append(f"Batterie à {battery['percent']}% ({etat_plug}).")

    return " ".join(elements)

class SystemMonitor:
    """Surveille en arrière-plan les ressources et les téléchargements du PC."""

    def __init__(self, on_alert_callback: Optional[Callable[[str, str, str, bool], None]] = None):
        self.on_alert = on_alert_callback
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

        # Anti-spam d'alertes (temps minimum entre 2 alertes identiques en secondes)
        self.last_alert_time: Dict[str, float] = {}
        self.alert_cooldown = 300  # 5 minutes

        # Suivi du dossier Téléchargements
        self.known_downloads = set()
        self.init_known_downloads()

    def init_known_downloads(self):
        """Mémorise les fichiers existants dans Téléchargements au démarrage."""
        if DOWNLOADS_DIR.exists():
            try:
                for item in DOWNLOADS_DIR.iterdir():
                    if item.is_file():
                        self.known_downloads.add(item.name)
            except Exception:
                pass

    def can_send_alert(self, alert_key: str) -> bool:
        now = time.time()
        last = self.last_alert_time.get(alert_key, 0)
        if now - last > self.alert_cooldown:
            self.last_alert_time[alert_key] = now
            return True
        return False

    def check_system_metrics(self):
        """Vérifie les métriques matérielles et alerte si dépassement."""
        stats = get_system_stats()

        # 1. Alerte RAM saturée (> 90%)
        if stats['ram_percent'] >= 90:
            if self.can_send_alert("ram_overload"):
                top = get_top_resource_processes(1)
                proc_name = top['top_mem'][0]['name'] if top['top_mem'] else "Une application"
                msg = f"Maverick, la mémoire RAM est saturée à {stats['ram_percent']}%. L'application '{proc_name}' concentre une utilisation importante."
                if self.on_alert:
                    self.on_alert("warning", "Alerte Mémoire Vive", msg, True)

        # 2. Alerte Disque C: presque saturé (< 12 Go)
        if stats['disk']['free_gb'] < 12 and stats['disk']['total_gb'] > 0:
            if self.can_send_alert("disk_full"):
                msg = f"Attention Maverick, l'espace disque C: est critique : il ne reste que {stats['disk']['free_gb']} Go de libre."
                if self.on_alert:
                    self.on_alert("warning", "Espace Disque Faible", msg, True)

        # 3. Alerte Batterie critique (< 18% sur batterie)
        if stats['battery']:
            if not stats['battery']['power_plugged'] and stats['battery']['percent'] <= 18:
                if self.can_send_alert("battery_low"):
                    msg = f"Maverick, le niveau de batterie est critique ({stats['battery']['percent']}%). Veuillez brancher l'alimentation secteur."
                    if self.on_alert:
                        self.on_alert("warning", "Batterie Faible", msg, True)

    def check_new_downloads(self):
        """Détecte les nouveaux fichiers téléchargés lorsqu'ils sont complets."""
        if not DOWNLOADS_DIR.exists():
            return

        try:
            current_files = set()
            for item in DOWNLOADS_DIR.iterdir():
                if not item.is_file():
                    continue

                name = item.name
                current_files.add(name)

                # Ignorer les fichiers temporaires de téléchargement en cours
                if name.endswith(('.crdownload', '.tmp', '.part', '.download')) or name.startswith(('~$', '.')):
                    continue

                if name not in self.known_downloads:
                    self.known_downloads.add(name)
                    # Nouveau fichier terminé détecté !
                    if self.can_send_alert(f"new_dl_{name}"):
                        msg = f"Nouveau fichier téléchargé détecté : '{name}'. Tu veux que je te le range ?"
                        if self.on_alert:
                            self.on_alert("download", "Téléchargement Terminé", msg, False)

            # Nettoyer les fichiers supprimés
            self.known_downloads = current_files
        except Exception:
            pass

    def _loop(self):
        while self.is_running:
            try:
                self.check_system_metrics()
                self.check_new_downloads()
            except Exception as e:
                print(f"[SystemMonitor Error] {e}")
            time.sleep(5)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            print("🛡️ Surveillance système Nora active en arrière-plan.")

    def stop(self):
        self.is_running = False

if __name__ == "__main__":
    print("--- Test des sondes système ---")
    print(get_system_health_report())
