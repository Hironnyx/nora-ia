"""
Module de Cache Audio LRU Instantané pour la Voix Zero Two de Nora (0 ms de latence).
Permet de restituer immédiatement les répliques fréquentes sans solliciter Edge-TTS ni RVC.
"""

import os
import sys
import time
import shutil
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent

CACHE_DIR = BASE_DIR / "data" / "audio_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

MAX_CACHE_FILES = 400
MAX_CACHE_SIZE_BYTES = 150 * 1024 * 1024  # 150 Mo

def _compute_key(text: str) -> str:
    """Génère une clé de hachage unique normalisée à partir du texte."""
    clean = " ".join(text.strip().lower().split())
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()[:24]

def get_cached_audio(text: str) -> Optional[Path]:
    """
    Retourne le chemin du fichier WAV Zero Two en cache si présent et valide (>1000 octets).
    Met à jour la date d'accès pour l'éviction LRU.
    """
    if not text or len(text.strip()) == 0:
        return None
    key = _compute_key(text)
    candidate = CACHE_DIR / f"{key}.wav"
    if candidate.exists() and candidate.stat().st_size > 1000:
        try:
            # Toucher le fichier pour maintenir l'ordonnancement LRU
            candidate.touch(exist_ok=True)
        except Exception:
            pass
        return candidate
    return None

def save_cached_audio(text: str, audio_path: Path) -> Optional[Path]:
    """
    Sauvegarde un fichier audio produit par RVC dans le cache persistant sous forme WAV.
    Gère la purge LRU automatique si le cache dépasse les plafonds.
    """
    if not text or not audio_path.exists() or audio_path.stat().st_size < 1000:
        return None

    key = _compute_key(text)
    target = CACHE_DIR / f"{key}.wav"

    try:
        if audio_path.suffix.lower() == ".wav":
            shutil.copy2(str(audio_path), str(target))
        else:
            # Si le fichier source n'est pas WAV, convertir proprement
            import subprocess
            ffmpeg_exe = BASE_DIR / "ffmpeg.exe"
            if not ffmpeg_exe.exists():
                ffmpeg_exe = Path(sys.executable).parent / "ffmpeg.exe"
            if not ffmpeg_exe.exists():
                try:
                    import imageio_ffmpeg
                    ffmpeg_exe = Path(imageio_ffmpeg.get_ffmpeg_exe())
                except Exception:
                    pass

            if ffmpeg_exe.exists():
                flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
                subprocess.run(
                    [str(ffmpeg_exe), "-y", "-i", str(audio_path), "-acodec", "pcm_s16le", "-ar", "44100", str(target)],
                    capture_output=True, creationflags=flags
                )
            else:
                shutil.copy2(str(audio_path), str(target))

        _prune_cache_if_needed()
        return target
    except Exception as e:
        print(f"⚠️ [AudioCache] Erreur lors de la mise en cache : {e}")
        return None

def is_cached(text: str) -> bool:
    """Vérifie rapidement si une phrase est déjà mémorisée dans le cache."""
    return get_cached_audio(text) is not None

def _prune_cache_if_needed():
    """Élimine les fichiers audio les plus anciens si la taille ou le nombre dépasse la limite."""
    try:
        files = list(CACHE_DIR.glob("*.wav"))
        if len(files) <= MAX_CACHE_FILES:
            total_size = sum(f.stat().st_size for f in files)
            if total_size <= MAX_CACHE_SIZE_BYTES:
                return

        # Trier du plus ancien au plus récent accès
        files.sort(key=lambda f: f.stat().st_mtime)
        while len(files) > MAX_CACHE_FILES or sum(f.stat().st_size for f in files) > MAX_CACHE_SIZE_BYTES:
            oldest = files.pop(0)
            try:
                oldest.unlink(missing_ok=True)
            except Exception:
                pass
    except Exception:
        pass

def get_cache_stats() -> Dict[str, Any]:
    """Retourne les métriques d'occupation du cache audio Zero Two."""
    files = list(CACHE_DIR.glob("*.wav"))
    total_bytes = sum(f.stat().st_size for f in files)
    return {
        "file_count": len(files),
        "total_mb": round(total_bytes / (1024 * 1024), 2),
        "directory": str(CACHE_DIR)
    }

if __name__ == "__main__":
    print("Test du Cache Audio Zero Two Instantané...")
    stats = get_cache_stats()
    print(f"Statistiques : {stats}")
    test_key = _compute_key("À vos ordres Maverick.")
    print(f"Clé générée pour 'À vos ordres Maverick.' : {test_key}")
