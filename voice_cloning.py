"""
Module de Clonage Vocal IA Studio de Zero Two (Darling in the Franxx) :
- Moteur RVC v2 haute performance accéléré par NVIDIA GeForce RTX 4080 (CUDA)
- Modèle entraîné Zero Two v2 (55 Mo) + Index d'incorporation acoustique (79 Mo)
- Extracteur de pitch RMVPE haute précision
- Chargement différé et pré-chauffage en arrière-plan (zéro latence au démarrage de Nora)
- Bascule de secours automatique vers la voix standard en cas de besoin
"""
import os
import sys
import time
import threading
from pathlib import Path

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent.resolve()

# Assurer que ffmpeg est accessible dans le PATH
scripts_dir = str(Path(sys.executable).parent)
if scripts_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = scripts_dir + os.pathsep + os.environ.get("PATH", "")

MODELS_DIR = BASE_DIR / "models" / "rvc_zero_two"
MODEL_PATH = MODELS_DIR / "zeroTwo-v2.pth"
INDEX_PATH = MODELS_DIR / "zeroTwo.index"
RMVPE_PATH = MODELS_DIR / "rmvpe.pt"
HUBERT_HF_DIR = MODELS_DIR / "hubert_base_hf"

_converter_lock = threading.Lock()
_converter_instance = None
_is_initialized = False
_init_in_progress = False

def is_rvc_models_present() -> bool:
    """Vérifie si les poids du modèle Zero Two et l'extracteur RMVPE sont présents."""
    return (
        MODEL_PATH.exists()
        and RMVPE_PATH.exists()
        and MODEL_PATH.stat().st_size > 1000000
    )

def _get_or_init_converter():
    """Initialise de façon thread-safe le convertisseur RVC sur la RTX 4080."""
    global _converter_instance, _is_initialized, _init_in_progress
    if _converter_instance is not None:
        return _converter_instance

    with _converter_lock:
        if _converter_instance is not None:
            return _converter_instance

        if not is_rvc_models_present():
            print("[VoiceCloning] Modèles Zero Two absents dans models/rvc_zero_two.")
            return None

        try:
            import torch
            from infer_rvc_python import BaseLoader

            use_gpu = torch.cuda.is_available()
            if use_gpu:
                dev_name = torch.cuda.get_device_name(0)
                print(f"🌸 [VoiceCloning] Initialisation RVC Zero Two sur {dev_name} (CUDA)...")
            else:
                print("⚠️ [VoiceCloning] CUDA non disponible, fallback CPU...")

            hubert_arg = str(HUBERT_HF_DIR) if HUBERT_HF_DIR.exists() else None
            converter = BaseLoader(
                only_cpu=not use_gpu,
                hubert_path=hubert_arg,
                rmvpe_path=str(RMVPE_PATH)
            )

            idx_str = str(INDEX_PATH) if INDEX_PATH.exists() else ""
            converter.apply_conf(
                tag="zero_two",
                file_model=str(MODEL_PATH),
                pitch_algo="rmvpe+",
                pitch_lvl=0,  # 0 = conserve la hauteur naturelle féminine de Vivienne
                file_index=idx_str,
                index_influence=0.75,
                respiration_median_filtering=3,
                envelope_ratio=0.25,
                consonant_breath_protection=0.33
            )

            _converter_instance = converter
            _is_initialized = True
            print("✔ [VoiceCloning] Modèle Zero Two chargé et prêt !")
            return _converter_instance

        except Exception as e:
            print(f"❌ [VoiceCloning] Erreur initialisation RVC : {e}")
            return None

def warmup_in_background():
    """Pré-charge le modèle en arrière-plan pour que la première phrase soit instantanée."""
    global _init_in_progress
    if _is_initialized or _init_in_progress:
        return

    def _worker():
        global _init_in_progress
        _init_in_progress = True
        try:
            _get_or_init_converter()
        finally:
            _init_in_progress = False

    t = threading.Thread(target=_worker, daemon=True)
    t.start()

def convert_to_zero_two(audio_path: Path) -> Path:
    """
    Convertit un fichier audio avec le timbre et les formants de Zero Two.
    En cas de problème, renvoie le fichier d'origine de manière transparente.
    """
    import memory_manager
    if not memory_manager.is_voice_cloning_enabled():
        return audio_path

    if not is_rvc_models_present():
        return audio_path

    converter = _get_or_init_converter()
    if converter is None:
        return audio_path

    with _converter_lock:
        try:
            t0 = time.time()
            res = converter(
                audio_files=[str(audio_path)],
                tag_list=["zero_two"],
                type_output="wav",
                show_progress=False
            )
            dur = time.time() - t0

            if res and len(res) > 0:
                out_path = Path(res[0])
                if out_path.exists() and out_path.stat().st_size > 1000:
                    # print(f"✨ [Zero Two Voice] Voix convertie en {dur:.2f}s !")
                    return out_path

        except Exception as e:
            print(f"[VoiceCloning] Échec conversion : {e}")

    return audio_path
