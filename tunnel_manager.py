"""
Gestionnaire d'Accès Distant Sécurisé (4G / 5G) pour Nora :
- Permet à l'application smartphone d'accéder au PC depuis n'importe où dans le monde
- Utilise Cloudflare Quick Tunnel (chiffrement SSL HTTPS de bout en bout, gratuit, sans ouverture de port box)
- Télécharge automatiquement l'exécutable cloudflared officiel si absent
- Enregistre l'adresse distante dans remote_url.txt pour configuration facile
"""
import os
import sys
import re
import time
import urllib.request
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CLOUDFLARED_EXE = BASE_DIR / "cloudflared.exe"
REMOTE_URL_FILE = BASE_DIR / "remote_url.txt"
PORT = 8000

CLOUDFLARED_URL = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"

def ensure_cloudflared() -> bool:
    """Télécharge cloudflared.exe s'il n'est pas déjà présent."""
    if CLOUDFLARED_EXE.exists() and CLOUDFLARED_EXE.stat().st_size > 1000000:
        return True

    print("🌐 Téléchargement du module de tunnel sécurisé Cloudflare (gratuit & chiffré)...")
    try:
        urllib.request.urlretrieve(CLOUDFLARED_URL, str(CLOUDFLARED_EXE))
        print("✔ Module de tunnel prêt !")
        return True
    except Exception as e:
        print(f"⚠️ Impossible de télécharger cloudflared automatiquement : {e}")
        return False

def start_remote_tunnel():
    """Lance le tunnel Cloudflare et extrait l'URL HTTPS publique sécurisée."""
    if not ensure_cloudflared():
        print("Veuillez vérifier votre connexion Internet.")
        return

    print(f"🚀 Lancement du tunnel sécurisé vers http://localhost:{PORT}...")
    cmd = [str(CLOUDFLARED_EXE), "tunnel", "--url", f"http://localhost:{PORT}"]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    tunnel_url = None
    regex_url = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    for line in proc.stdout:
        match = regex_url.search(line)
        if match:
            tunnel_url = match.group(0)
            break

    if tunnel_url:
        print("\n" + "="*65)
        print("🎉 NORA EST MAINTENANT ACCESSIBLE PARTOUT EN 4G / 5G !")
        print("="*65)
        print(f"\n👉 VOTRE ADRESSE DISTANTE : {tunnel_url}\n")
        print("Dans l'application mobile, appuyez sur l'engrenage ⚙️ et")
        print("collez cette adresse pour l'utiliser hors de chez vous !")
        print("="*65 + "\n")

        with open(REMOTE_URL_FILE, "w", encoding="utf-8") as f:
            f.write(tunnel_url)

        # Maintenir le processus en vie
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            print("Tunnel fermé.")
    else:
        print("Impossible d'obtenir l'URL du tunnel. Sortie :")
        try:
            proc.terminate()
        except Exception:
            pass

if __name__ == "__main__":
    start_remote_tunnel()
