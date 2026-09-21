"""
Script de téléchargement automatique des modèles RVC v2 pour Zero Two :
- zeroTwo-v2.pth (55 Mo) : Poids du réseau de neurones Zero Two v2
- zeroTwo.index (79 Mo) : Index d'incorporation de similarité
- hubert_base.pt (180 Mo) : Extracteur de représentations vocales HuBERT
- rmvpe.pt (40 Mo) : Extracteur de pitch haute fidélité RMVPE
"""
import os
import sys
import urllib.request
import time
from pathlib import Path

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

MODELS_DIR = Path(__file__).resolve().parent / "models" / "rvc_zero_two"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "zeroTwo-v2.pth": "https://huggingface.co/Nekochu/RVC2-zero-two_darling-in-the-franxx/resolve/main/weights/zeroTwo-v2.pth",
    "zeroTwo.index": "https://huggingface.co/Nekochu/RVC2-zero-two_darling-in-the-franxx/resolve/main/weights/added_IVF643_Flat_nprobe_1_RVC2-Voice_zero-two_darling-in-the-franxx-_v2.index",
    "hubert_base.pt": "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt",
    "rmvpe.pt": "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt",
}

def download_file(filename: str, url: str):
    dest = MODELS_DIR / filename
    if dest.exists() and dest.stat().st_size > 1000000:
        print(f"✔ {filename} déjà présent ({dest.stat().st_size / (1024*1024):.1f} Mo).")
        return

    print(f"⬇️ Téléchargement de {filename} depuis Hugging Face...")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )

    t0 = time.time()
    with urllib.request.urlopen(req) as resp, open(dest, "wb") as out_f:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            out_f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                percent = (downloaded / total) * 100
                sys.stdout.write(f"\r   [{percent:.1f}%] {downloaded/(1024*1024):.1f}/{total/(1024*1024):.1f} Mo")
                sys.stdout.flush()

    duration = time.time() - t0
    print(f"\n✔ {filename} téléchargé avec succès en {duration:.1f}s !")

if __name__ == "__main__":
    print("🌸 Démarrage du téléchargement des modèles vocaux Zero Two...")
    for fname, furl in FILES.items():
        try:
            download_file(fname, furl)
        except Exception as e:
            print(f"❌ Erreur sur {fname}: {e}")
    print("✨ Tous les modèles sont prêts dans:", MODELS_DIR)
