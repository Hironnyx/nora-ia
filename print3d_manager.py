"""
Atelier d'Impression 3D & Fabrication Additive pour Maverick (3D Printing Hub) :
- Intégration directe 1-clic avec PrusaSlicer (C:\\Program Files\\Prusa3D\\PrusaSlicer\\prusa-slicer.exe)
- File d'attente d'impression & Catalogue de modèles 3D (STL, 3MF, OBJ, GCODE)
- Télémétrie en temps réel (Buse °C, Plateau chauffant °C, Vitesse ventilateur, Progression, Couches)
- Gestionnaire d'inventaire de bobines de filament (PLA, PETG, TPU, ABS, jauges de poids et couleurs)
- Conseiller IA en tranchage, orientation et diagnostic de pannes (Stringing, Warping, Adhérence)
- Persistance dans maverick_3dprint_state.json
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent

STATE_FILE = BASE_DIR / "maverick_3dprint_state.json"
MODELS_DIR = Path.home() / "Documents" / "Impression3D"

# Détection de l'exécutable PrusaSlicer
PRUSA_SLICER_CANDIDATES = [
    Path(r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer.exe"),
    Path(r"C:\Program Files (x86)\Prusa3D\PrusaSlicer\prusa-slicer.exe"),
    Path.home() / "AppData" / "Local" / "Programs" / "PrusaSlicer" / "prusa-slicer.exe"
]

def find_prusaslicer_exe() -> Optional[str]:
    for p in PRUSA_SLICER_CANDIDATES:
        if p.exists():
            return str(p)
    return None

DEFAULT_3D_STATE = {
    "printer_telemetry": {
        "status": "Non connectée",
        "nozzle_temp": 0,
        "nozzle_target": 0,
        "bed_temp": 0,
        "bed_target": 0,
        "fan_speed": 0,
        "progress_percent": 0,
        "current_layer": 0,
        "total_layers": 0,
        "print_duration": "--",
        "time_remaining": "--",
        "active_file": "Aucun",
        "endpoint": ""
    },
    "filament_spools": [],
    "print_queue": []
}

class Print3DManager:
    """Gestionnaire de l'atelier d'impression 3D pour Maverick."""

    def __init__(self):
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        self.state: Dict[str, Any] = self._load_state()
        self.prusaslicer_path = find_prusaslicer_exe()

    def _load_state(self) -> Dict[str, Any]:
        if not STATE_FILE.exists():
            self._save_state(DEFAULT_3D_STATE)
            return dict(DEFAULT_3D_STATE)
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else dict(DEFAULT_3D_STATE)
        except Exception as e:
            print(f"Erreur chargement atelier 3D : {e}")
            return dict(DEFAULT_3D_STATE)

    def _save_state(self, data: Optional[Dict[str, Any]] = None):
        if data is not None:
            self.state = data
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde atelier 3D : {e}")

    # =========================================================================
    # INTÉGRATION PRUSASLICER
    # =========================================================================
    def launch_prusaslicer(self, file_path: Optional[str] = None) -> bool:
        """Lance PrusaSlicer en 1 clic avec le fichier 3D spécifié si présent."""
        exe = self.prusaslicer_path or find_prusaslicer_exe()
        if not exe or not Path(exe).exists():
            return False

        try:
            cmd = [exe]
            if file_path and Path(file_path).exists():
                cmd.append(str(Path(file_path).resolve()))
            subprocess.Popen(cmd)
            return True
        except Exception as e:
            print(f"Erreur lancement PrusaSlicer : {e}")
            return False

    # =========================================================================
    # CATALOGUE & FILE D'ATTENTE D'IMPRESSION
    # =========================================================================
    def get_print_queue(self) -> List[Dict[str, Any]]:
        return self.state.get("print_queue", [])

    def add_print_job(self, title: str, file_format: str = "STL", material: str = "PLA+",
                      estimated_time: str = "1h 30m", estimated_grams: int = 40,
                      layer_height: str = "0.20mm", file_path: str = "") -> Dict[str, Any]:
        new_job = {
            "id": f"print_{int(time.time())}_{len(self.state.get('print_queue', [])) + 1}",
            "title": title.strip(),
            "format": file_format.upper(),
            "material": material,
            "estimated_time": estimated_time,
            "estimated_grams": estimated_grams,
            "layer_height": layer_height,
            "infill": "20% Gyroid",
            "status": "En attente",
            "path": file_path.strip()
        }
        self.state.setdefault("print_queue", []).insert(0, new_job)
        self._save_state()
        return new_job

    def set_job_status(self, job_id: str, new_status: str) -> bool:
        for job in self.state.get("print_queue", []):
            if job.get("id") == job_id:
                job["status"] = new_status
                # Si terminé, déduire le filament si applicable
                if new_status == "Terminé":
                    mat = job.get("material", "PLA+")
                    grams = job.get("estimated_grams", 0)
                    self.consume_filament_auto(mat, grams)
                self._save_state()
                return True
        return False

    def remove_job(self, job_id: str) -> bool:
        q = self.state.get("print_queue", [])
        init_len = len(q)
        self.state["print_queue"] = [j for j in q if j.get("id") != job_id]
        if len(self.state["print_queue"]) != init_len:
            self._save_state()
            return True
        return False

    # =========================================================================
    # FICHIERS RÉELS DU DOSSIER IMPRESSION 3D
    # =========================================================================
    def scan_models_dir(self) -> List[Dict[str, Any]]:
        """Scanne le dossier réel Documents/Impression3D pour trouver les fichiers 3D."""
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        found = []
        exts = {".stl", ".3mf", ".obj", ".step", ".gcode"}
        try:
            for f in MODELS_DIR.iterdir():
                if f.is_file() and f.suffix.lower() in exts:
                    size_mb = f.stat().st_size / (1024 * 1024)
                    found.append({
                        "name": f.name,
                        "stem": f.stem,
                        "format": f.suffix[1:].upper(),
                        "path": str(f.resolve()),
                        "size_mb": round(size_mb, 2),
                        "modified": time.strftime("%d/%m/%Y %H:%M", time.localtime(f.stat().st_mtime))
                    })
        except Exception as e:
            print(f"Erreur scan dossier Impression3D : {e}")
        return found

    def import_model_file(self, src_path: str) -> Optional[Dict[str, Any]]:
        """Copie un fichier 3D réel dans Documents/Impression3D."""
        p = Path(src_path)
        if not p.exists() or not p.is_file():
            return None
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        dest = MODELS_DIR / p.name
        import shutil
        shutil.copy2(p, dest)
        return {
            "name": dest.name,
            "stem": dest.stem,
            "format": dest.suffix[1:].upper(),
            "path": str(dest.resolve()),
            "size_mb": round(dest.stat().st_size / (1024 * 1024), 2)
        }

    def open_models_folder(self):
        """Ouvre l'explorateur Windows dans Documents/Impression3D."""
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(str(MODELS_DIR))

    # =========================================================================
    # GESTIONNAIRE DE BOBINES DE FILAMENT
    # =========================================================================
    def get_spools(self) -> List[Dict[str, Any]]:
        return self.state.get("filament_spools", [])

    def add_spool(self, material: str, brand: str, color_name: str, color_hex: str,
                  total_weight_g: int = 1000, temp_nozzle: int = 210, temp_bed: int = 60) -> Dict[str, Any]:
        new_spool = {
            "id": f"spool_{int(time.time())}_{len(self.state.get('filament_spools', [])) + 1}",
            "material": material.strip(),
            "brand": brand.strip(),
            "color_name": color_name.strip(),
            "color_hex": color_hex.strip(),
            "total_weight_g": total_weight_g,
            "remaining_weight_g": total_weight_g,
            "temp_nozzle": temp_nozzle,
            "temp_bed": temp_bed
        }
        self.state.setdefault("filament_spools", []).append(new_spool)
        self._save_state()
        return new_spool

    def delete_spool(self, spool_id: str) -> bool:
        spools = self.state.get("filament_spools", [])
        init_len = len(spools)
        self.state["filament_spools"] = [s for s in spools if s.get("id") != spool_id]
        if len(self.state["filament_spools"]) != init_len:
            self._save_state()
            return True
        return False

    def consume_filament_auto(self, material_pref: str, grams: int):
        """Déduit automatiquement les grammes de filament de la bobine correspondante."""
        spools = self.get_spools()
        for s in spools:
            if material_pref.lower() in s.get("material", "").lower():
                s["remaining_weight_g"] = max(0, s.get("remaining_weight_g", 0) - grams)
                self._save_state()
                break

    # =========================================================================
    # TÉLÉMÉTRIE IMPRIMANTE
    # =========================================================================
    def get_telemetry(self) -> Dict[str, Any]:
        return self.state.get("printer_telemetry", DEFAULT_3D_STATE["printer_telemetry"])

    def update_telemetry(self, updates: Dict[str, Any]):
        t = self.state.setdefault("printer_telemetry", {})
        for k, v in updates.items():
            t[k] = v
        self._save_state()

    # =========================================================================
    # CONSEILLER IA EN TRANCHAGE & RÉSOUDRE LES DÉFAUTS
    # =========================================================================
    def get_slicing_advice(self, part_type: str, material: str) -> str:
        """Conseils du Maker 3D et de Nora pour réussir l'impression."""
        mat_lower = material.lower()
        if "petg" in mat_lower:
            return (
                "Conseil Maker 3D pour PETG : Buse à 240°C, Plateau à 85°C. "
                "Ventilation modérée (40-50%) pour éviter le délaminage. Vitesse de rétraction 35 mm/s "
                "pour supprimer le stringing."
            )
        elif "tpu" in mat_lower:
            return (
                "Conseil Maker 3D pour TPU flexible : Buse à 225°C, vitesse d'extrusion très lente (20-25 mm/s), "
                "désactivez complètement la rétraction pour éviter que le filament ne s'enroule autour de l'extrudeur."
            )
        elif "abs" in mat_lower or "asa" in mat_lower:
            return (
                "Conseil Maker 3D pour ABS/ASA : Buse à 250°C, Plateau à 100°C. "
                "Caisson fermé indispensable sans courant d'air pour contrer le warping violent. Activez une bordure (Brim) de 5 mm."
            )
        else: # PLA standard
            return (
                "Conseil Maker 3D pour PLA : Buse à 210°C, Plateau à 60°C. "
                "Privilégiez un remplissage Gyroid à 15-20% pour une solidité isotrope et une vitesse de 80-120 mm/s sans vibration."
            )

    def diagnose_issue(self, issue_keyword: str) -> str:
        """Diagnostic de défauts d'impression courants."""
        kw = issue_keyword.lower()
        if "stringing" in kw or "fils" in kw:
            return (
                "Résolution du Stringing (cheveux d'ange) :\n"
                "1. Augmentez la distance de rétraction de +0.5 mm.\n"
                "2. Baissez la température de buse de 5°C.\n"
                "3. Activez le mode 'Éviter de traverser les périmètres' (Combing) dans PrusaSlicer."
            )
        elif "warping" in kw or "décollement" in kw or "coin" in kw:
            return (
                "Résolution du Warping (coins décollés) :\n"
                "1. Nettoyez le plateau à l'alcool isopropylique (IPA) 99%.\n"
                "2. Augmentez la température du plateau de +5°C sur les premières couches.\n"
                "3. Ajoutez une bordure (Brim) de 5 mm autour de la pièce."
            )
        elif "shift" in kw or "décalage" in kw:
            return (
                "Résolution du Décalage de couches (Layer Shift) :\n"
                "1. Vérifiez la tension des courroies X et Y (ne doivent pas flotter ni être trop tendues).\n"
                "2. Réduisez les accélérations et vitesses de déplacement dans PrusaSlicer.\n"
                "3. Contrôlez que la buse ne heurte pas un surplomb déformé."
            )
        else:
            return (
                "Diagnostic d'impression général :\n"
                "Vérifiez l'écrasement de la première couche (Z-Offset) et la planéité du plateau. "
                "Un plateau propre garantit 90% du succès d'une impression 3D."
            )

# Singleton
print3d_manager = Print3DManager()

if __name__ == "__main__":
    print("Test du Print3D Manager...")
    ps = print3d_manager.prusaslicer_path
    print(f"PrusaSlicer détecté : {ps}")
    print(f"Nombre de bobines en stock : {len(print3d_manager.get_spools())}")
    for s in print3d_manager.get_spools():
        print(f"- {s['brand']} {s['material']} ({s['color_name']}) : {s['remaining_weight_g']}g restants")
    print("\nConseil PLA :")
    print(print3d_manager.get_slicing_advice("boitier", "PLA"))
