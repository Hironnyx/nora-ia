"""
Gestionnaire d'Accès Distant Automatisé (4G / 5G) pour Nora :
- Permet à l'application smartphone d'accéder au PC depuis n'importe où sans manipulation manuelle
- Utilise Cloudflare Quick Tunnel (chiffrement SSL HTTPS de bout en bout, gratuit, sans ouverture de port)
- Publie automatiquement l'endpoint dans remote_endpoint.json et le pousse sur GitHub
- Découverte automatique instantanée par l'application Android sans copier/coller d'adresse
"""
import os
import sys
import re
import time
import json
import urllib.request
import subprocess
import threading
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CLOUDFLARED_EXE = BASE_DIR / "cloudflared.exe"
REMOTE_URL_FILE = BASE_DIR / "remote_url.txt"
REMOTE_ENDPOINT_FILE = BASE_DIR / "remote_endpoint.json"
PORT = 8000
LOCAL_IP = "192.168.1.183"

CLOUDFLARED_URL = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"

_current_tunnel_proc = None
_current_tunnel_url = None

def ensure_cloudflared() -> bool:
    """Télécharge cloudflared.exe s'il n'est pas déjà présent."""
    if CLOUDFLARED_EXE.exists() and CLOUDFLARED_EXE.stat().st_size > 1000000:
        return True

    print("[INFO] Telechargement du module de tunnel securise Cloudflare (gratuit & chiffre)...")
    try:
        urllib.request.urlretrieve(CLOUDFLARED_URL, str(CLOUDFLARED_EXE))
        print("[OK] Module de tunnel pret !")
        return True
    except Exception as e:
        print(f"[WARN] Impossible de telecharger cloudflared automatiquement : {e}")
        return False

def publish_endpoint(tunnel_url: str):
    """Enregistre le point d'accès distant et le synchronise sur GitHub pour auto-découverte."""
    data = {
        "tunnel_url": tunnel_url,
        "local_ip": LOCAL_IP,
        "port": PORT,
        "status": "online",
        "updated_at": datetime.now().isoformat()
    }
    with open(REMOTE_ENDPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    with open(REMOTE_URL_FILE, "w", encoding="utf-8") as f:
        f.write(tunnel_url)

    # Push Git silencieux en arrière-plan sans aucune fenêtre console
    def _git_push():
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
        try:
            subprocess.run(["git", "add", "remote_endpoint.json"], cwd=str(BASE_DIR), capture_output=True, creationflags=flags)
            subprocess.run(["git", "commit", "-m", "chore: auto-update remote 4g/5g tunnel endpoint [skip ci]"], cwd=str(BASE_DIR), capture_output=True, creationflags=flags)
            subprocess.run(["git", "push", "origin", "main"], cwd=str(BASE_DIR), capture_output=True, creationflags=flags)
            print("[OK] Point d'acces 4G/5G synchronise sur le Cloud pour l'application mobile !")
        except Exception as e:
            print(f"[WARN] Erreur publication GitHub : {e}")

    threading.Thread(target=_git_push, daemon=True).start()

def start_remote_tunnel(background: bool = False):
    """Lance le tunnel Cloudflare et extrait l'URL HTTPS publique sécurisée."""
    global _current_tunnel_proc, _current_tunnel_url

    if not ensure_cloudflared():
        print("Veuillez verifier votre connexion Internet.")
        return None

    print(f"[INFO] Lancement du tunnel securise vers http://localhost:{PORT}...")
    cmd = [str(CLOUDFLARED_EXE), "tunnel", "--url", f"http://localhost:{PORT}"]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
    )
    _current_tunnel_proc = proc

    regex_url = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    def _monitor():
        global _current_tunnel_url
        for line in proc.stdout:
            match = regex_url.search(line)
            if match:
                _current_tunnel_url = match.group(0)
                print("\n" + "="*65)
                print("[SUCCESS] NORA EST CONNECTEE AU RESEAU MONDIAL 4G / 5G !")
                print(f"URL DISTANTE : {_current_tunnel_url}")
                print("L'application mobile passera dessus automatiquement sans rien toucher.")
                print("="*65 + "\n")
                publish_endpoint(_current_tunnel_url)
                break

    monitor_thread = threading.Thread(target=_monitor, daemon=True)
    monitor_thread.start()

    if not background:
        monitor_thread.join()
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            print("Tunnel fermé.")

    return proc

def get_current_tunnel_url():
    global _current_tunnel_url
    if _current_tunnel_url:
        return _current_tunnel_url
    if REMOTE_URL_FILE.exists():
        try:
            return REMOTE_URL_FILE.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    return None

if __name__ == "__main__":
    start_remote_tunnel(background=False)
