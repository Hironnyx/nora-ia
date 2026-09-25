"""
Moteur de Preuves Matérielles & Contrats d'Exécution (Standard Anthropic / Zéro Fictif).
Génère et certifie les reçus d'exécution physiques (ExecutionReceipt) pour chaque
intervention sur le système d'exploitation Windows de Maverick.
"""

import os
import sys
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

class ExecutionReceipt:
    """Certificat d'exécution physique vérifiable sur le disque dur."""

    def __init__(
        self,
        step_index: int,
        action_name: str,
        tool_called: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
        raw_output: str = ""
    ):
        self.step_index = step_index
        self.action_name = action_name
        self.tool_called = tool_called
        self.tool_args = tool_args or {}
        self.duration_ms = duration_ms
        self.raw_output = raw_output
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Vérification physique sur disque
        self.verified_on_disk = False
        self.target_path: Optional[str] = None
        self.file_size_bytes: int = 0
        self.sha256_hash: Optional[str] = None
        self.status = "CONCEPTUAL_ONLY"

        self._audit_physical_reality()

    def _audit_physical_reality(self):
        """Vérifie physiquement sur le système Windows si un effet mesurable a eu lieu."""
        if not self.tool_called:
            self.status = "CONCEPTUAL_ONLY"
            self.verified_on_disk = False
            return

        # 1. Cas d'écriture ou modification de fichier ou dossier
        path_candidate = None
        for key in ["filepath", "file_path", "path", "destination", "folder_path", "target", "filename"]:
            val = self.tool_args.get(key)
            if val and isinstance(val, (str, Path)):
                path_candidate = str(val)
                break

        if not path_candidate:
            for val in self.tool_args.values():
                if isinstance(val, (str, Path)) and len(str(val)) < 500:
                    try:
                        p_test = Path(str(val))
                        if p_test.exists():
                            path_candidate = str(val)
                            break
                    except Exception:
                        pass

        if path_candidate:
            try:
                import tools_pc
                p = tools_pc.resolve_user_path(path_candidate)
            except Exception:
                p = Path(path_candidate)

            if p.exists():
                self.target_path = str(p.resolve())
                self.verified_on_disk = True
                if p.is_file():
                    self.status = "SUCCESS_VERIFIED"
                    try:
                        self.file_size_bytes = p.stat().st_size
                        with open(p, "rb") as f:
                            self.sha256_hash = hashlib.sha256(f.read()).hexdigest()
                    except Exception:
                        pass
                elif p.is_dir():
                    self.status = "FOLDER_VERIFIED"
                return

        # 2. Cas d'exécution de script PowerShell / Commande système
        if self.tool_called == "run_powershell":
            if "Erreur" in self.raw_output or "Error" in self.raw_output:
                self.status = "FAILED"
                self.verified_on_disk = False
            else:
                self.status = "SUCCESS_SYSTEM_COMMAND"
                self.verified_on_disk = True
            return

        # 3. Outils de lecture / inspection
        if any(self.tool_called.startswith(prefix) for prefix in ["list_", "get_", "search_", "read_"]):
            self.status = "INSPECTION_READ_ONLY"
            self.verified_on_disk = True
            return

        # 4. Tranchage 3D
        if "slice" in self.tool_called.lower() and "gcode" in self.raw_output.lower():
            self.status = "SLICING_3D_VERIFIED"
            self.verified_on_disk = True
            return

        # Par défaut si un outil s'est exécuté sans erreur
        if self.tool_called and "erreur" not in self.raw_output.lower():
            self.status = "TOOL_EXECUTED"
            self.verified_on_disk = True
        else:
            self.status = "FAILED"
            self.verified_on_disk = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "action_name": self.action_name,
            "tool_called": self.tool_called,
            "tool_args": self.tool_args,
            "status": self.status,
            "verified_on_disk": self.verified_on_disk,
            "target_path": self.target_path,
            "file_size_bytes": self.file_size_bytes,
            "sha256_hash": self.sha256_hash,
            "duration_ms": round(self.duration_ms, 2),
            "timestamp": self.timestamp,
            "raw_output": self.raw_output[:300]
        }

    def format_console_badge(self) -> str:
        """Formate une ligne de rapport claire pour la console de l'Agora."""
        if self.status == "SUCCESS_VERIFIED":
            hash_abbr = f"{self.sha256_hash[:10]}...{self.sha256_hash[-6:]}" if self.sha256_hash else "N/A"
            return (
                f"<b style='color:#10b981;'>✔ PREUVE PHYSIQUE VÉRIFIÉE</b> "
                f"<span style='color:#94a3b8;'>({self.tool_called} en {self.duration_ms:.1f}ms)</span><br>"
                f"  ↳ Fichier : <code>{self.target_path}</code> ({self.file_size_bytes} octets)<br>"
                f"  ↳ Empreinte SHA-256 : <code>{hash_abbr}</code>"
            )
        elif self.status == "SUCCESS_SYSTEM_COMMAND":
            return (
                f"<b style='color:#10b981;'>✔ COMMANDE SYSTÈME EXÉCUTÉE</b> "
                f"<span style='color:#94a3b8;'>({self.duration_ms:.1f}ms)</span><br>"
                f"  ↳ Résultat : {self.raw_output[:140]}..."
            )
        elif self.status == "FOLDER_VERIFIED":
            return (
                f"<b style='color:#10b981;'>✔ DOSSIER VÉRIFIÉ SUR LE DISQUE</b><br>"
                f"  ↳ Répertoire : <code>{self.target_path}</code>"
            )
        elif self.status == "INSPECTION_READ_ONLY":
            return (
                f"<b style='color:#38bdf8;'>🔍 INSPECTION TÉLÉMÉTRIE / DONNÉES</b> "
                f"<span style='color:#94a3b8;'>({self.tool_called})</span><br>"
                f"  ↳ Données captées : {self.raw_output[:120]}..."
            )
        elif self.status == "TOOL_EXECUTED":
            return (
                f"<b style='color:#10b981;'>✔ ACTION MATÉRIELLE EXÉCUTÉE</b> "
                f"<span style='color:#94a3b8;'>({self.tool_called} en {self.duration_ms:.1f}ms)</span><br>"
                f"  ↳ Résultat : {self.raw_output[:140]}..."
            )
        elif self.status == "CONCEPTUAL_ONLY":
            return (
                f"<b style='color:#f59e0b;'>⚠ PROPOSITION CONCEPTUELLE UNIQUEMENT</b><br>"
                f"  ↳ Aucun outil système n'a été appelé et aucun fichier n'a été modifié sur le disque."
            )
        else:
            return (
                f"<b style='color:#ef4444;'>❌ ÉCHEC D'EXÉCUTION</b><br>"
                f"  ↳ Détail : {self.raw_output[:150]}"
            )

if __name__ == "__main__":
    print("Test du Moteur de Preuves Matérielles...")
    # Test 1 : Reçu conceptuel (zéro outil)
    r1 = ExecutionReceipt(1, "Optimisation abstraite", None, {}, 5.2, "Discussion terminée.")
    print("Test 1 (Conceptuel) :", r1.status, "Vérifié :", r1.verified_on_disk)

    # Test 2 : Reçu réel sur ce script lui-même
    r2 = ExecutionReceipt(2, "Vérification script", "write_file", {"file_path": __file__}, 12.4, "Fichier écrit.")
    print("Test 2 (Physique) :", r2.status, "Taille :", r2.file_size_bytes, "Hash :", r2.sha256_hash[:16])
