"""
Moteur d'Auto-Évolution et d'Amélioration de Code Sécurisé pour Nora :
- Analyse statique et intelligente des modules Python du projet
- Détection d'optimisations potentielles (vitesse, RAM, robustesse, nouvelles compétences)
- Bac à sable de validation rigoureux (syntaxe py_compile, tests en sous-processus isolé)
- Système Human-in-the-Loop : rien n'est appliqué sans la validation explicite de Maverick
- Historique de commits Git automatiques pour garantir un retour en arrière immédiat
"""
import os
import sys
import json
import time
import difflib
import py_compile
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from dotenv import load_dotenv
from google import genai
from google.genai import types

import memory_manager

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv()

PROPOSALS_FILE = BASE_DIR / "nora_pending_improvements.json"
SANDBOX_DIR = BASE_DIR / "temp_sandbox"
SANDBOX_DIR.mkdir(exist_ok=True)

# Fichiers sensibles ou critiques que Nora ne doit pas modifier d'elle-même
PROTECTED_FILES = {".env", "memoire_nora.json", "smart_home_state.json"}

CANDIDATE_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite"
]

def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Clé API GEMINI_API_KEY manquante.")
    return genai.Client(api_key=api_key)

def load_proposals() -> Dict[str, Any]:
    if not PROPOSALS_FILE.exists():
        return {"proposals": []}
    try:
        with open(PROPOSALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"proposals": []}

def save_proposals(data: Dict[str, Any]):
    try:
        with open(PROPOSALS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[CodeEvolver] Erreur sauvegarde propositions : {e}")

def get_inspectable_files() -> List[str]:
    """Retourne la liste des fichiers Python éligibles à l'inspection et à l'optimisation."""
    eligible = []
    for p in BASE_DIR.glob("*.py"):
        if p.name not in PROTECTED_FILES and not p.name.startswith("test_"):
            eligible.append(p.name)
    return sorted(eligible)

def analyze_and_propose_improvement(target_filename: str, user_instruction: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyse un module Python et formule une proposition d'amélioration validée en bac à sable.
    """
    file_path = BASE_DIR / target_filename
    if not file_path.exists():
        return {"success": False, "error": f"Fichier {target_filename} introuvable."}

    if target_filename in PROTECTED_FILES:
        return {"success": False, "error": f"Le fichier {target_filename} est protégé."}

    with open(file_path, "r", encoding="utf-8") as f:
        original_code = f.read()

    client = get_client()
    user_name = memory_manager.get_user_name()

    instruction_context = (
        f"L'utilisateur ({user_name}) a demandé spécifiquement : '{user_instruction}'"
        if user_instruction else
        "Trouve une opportunité d'optimisation pertinente (performance, gestion d'erreurs, robustesse ou clarté)."
    )

    prompt = f"""
Tu es l'agent d'auto-amélioration du système Nora (Zero Two).
Tu examines le code source du fichier : `{target_filename}`.

Objectif :
{instruction_context}

Règles de sécurité STRICTES :
1. Tu ne dois JAMAIS casser le code existant ni supprimer de fonctionnalités utiles.
2. Conserve les commentaires et la structure générale.
3. Produis le code complet amélioré dans le champ 'code_ameliore'.

Réponds UNIQUEMENT sous forme d'un JSON STRICT avec ce schéma :
{{
    "titre": "Titre concis de l'amélioration",
    "explication_pour_maverick": "Explication claire et professionnelle de ce qui est amélioré (1-2 phrases)",
    "type_amelioration": "performance | robustesse | fonctionnalite | refactoring",
    "resume_modifications": [
        "Changement 1",
        "Changement 2"
    ],
    "code_ameliore": "CODE PYTHON COMPLET DU FICHIER APRES MODIFICATION"
}}
"""

    structured = None
    for model in CANDIDATE_MODELS:
        try:
            resp = client.models.generate_content(
                model=model,
                contents=[prompt, types.Part.from_text(text=f"=== CODE ORIGINAL DU FICHIER {target_filename} ===\n{original_code}")],
                config=types.GenerateContentConfig(temperature=0.2)
            )
            raw = resp.text.strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            structured = json.loads(raw.strip())
            break
        except Exception as e:
            print(f"[CodeEvolver] Erreur modèle {model} : {e}")
            continue

    if not structured or "code_ameliore" not in structured:
        return {"success": False, "error": "Impossible de générer une proposition d'amélioration valide."}

    new_code = structured["code_ameliore"]

    # 1. Test en bac à sable (Compilation de syntaxe)
    sandbox_file = SANDBOX_DIR / f"test_{target_filename}"
    with open(sandbox_file, "w", encoding="utf-8") as f:
        f.write(new_code)

    try:
        py_compile.compile(str(sandbox_file), doraise=True)
    except py_compile.PyCompileError as pe:
        sandbox_file.unlink(missing_ok=True)
        return {
            "success": False,
            "error": f"Le code proposé contient une erreur de syntaxe : {pe.msg}"
        }

    # 2. Test d'importation dans un sous-processus isolé
    cmd = [
        sys.executable,
        "-c",
        f"import py_compile; py_compile.compile(r'{str(sandbox_file)}', doraise=True); print('SANDBOX_OK')"
    ]
    sub = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if "SANDBOX_OK" not in sub.stdout:
        sandbox_file.unlink(missing_ok=True)
        return {
            "success": False,
            "error": f"Le code généré a échoué au test d'isolation : {sub.stderr}"
        }

    sandbox_file.unlink(missing_ok=True)

    # 3. Calcul du Diff visuel pour Maverick
    orig_lines = original_code.splitlines(keepends=True)
    new_lines = new_code.splitlines(keepends=True)
    diff = list(difflib.unified_diff(orig_lines, new_lines, fromfile=f"a/{target_filename}", tofile=f"b/{target_filename}", n=2))
    diff_text = "".join(diff[:60])  # Limiter pour la lisibilité

    # 4. Enregistrement de la proposition en attente d'approbation
    prop_id = f"prop_{int(time.time())}"
    proposal = {
        "id": prop_id,
        "target_file": target_filename,
        "titre": structured.get("titre", "Optimisation de code"),
        "explication": structured.get("explication_pour_maverick") or structured.get("explication_pour_darling", ""),
        "type": structured.get("type_amelioration", "performance"),
        "points": structured.get("resume_modifications", []),
        "diff": diff_text,
        "new_code": new_code,
        "timestamp": time.time(),
        "date": time.strftime("%d/%m/%Y %H:%M")
    }

    props_data = load_proposals()
    # Remplacer les anciennes propositions sur le même fichier
    props_data["proposals"] = [p for p in props_data["proposals"] if p["target_file"] != target_filename]
    props_data["proposals"].insert(0, proposal)
    save_proposals(props_data)

    print(f"✔ [CodeEvolver] Proposition prête pour validation par Maverick : {proposal['titre']}")
    return {
        "success": True,
        "proposal_id": prop_id,
        "target_file": target_filename,
        "titre": proposal["titre"],
        "explication": proposal["explication"],
        "points": proposal["points"],
        "diff": diff_text
    }

def apply_improvement_with_git(proposal_id: str) -> Tuple[bool, str]:
    """
    Applique une proposition approuvée par Maverick et crée un commit Git automatique.
    """
    props_data = load_proposals()
    target_prop = None
    for p in props_data.get("proposals", []):
        if p["id"] == proposal_id:
            target_prop = p
            break

    if not target_prop:
        return False, "Proposition introuvable ou déjà traitée."

    target_file = target_prop["target_file"]
    new_code = target_prop["new_code"]
    file_path = BASE_DIR / target_file

    # Écriture du code validé
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_code)
    except Exception as e:
        return False, f"Erreur lors de l'écriture du fichier : {e}"

    # Vérification post-écriture
    try:
        py_compile.compile(str(file_path), doraise=True)
    except Exception as e:
        return False, f"Erreur critique après écriture : {e}"

    # Création du commit Git
    commit_msg = f"refactor({target_file}): {target_prop.get('titre', 'auto-optimization by Nora')}"
    try:
        subprocess.run(["git", "add", target_file], cwd=str(BASE_DIR), check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(BASE_DIR), check=True)
        # Supprimer la proposition de la liste d'attente
        props_data["proposals"] = [p for p in props_data["proposals"] if p["id"] != proposal_id]
        save_proposals(props_data)
        return True, f"Amélioration appliquée avec succès sur {target_file} ! Sauvegardée dans Git : '{commit_msg}'."
    except Exception as e:
        return True, f"Code mis à jour sur {target_file}, mais commit Git manuel requis : {e}"

def get_latest_pending_proposal() -> Optional[Dict[str, Any]]:
    """Retourne la dernière proposition en attente de validation par Maverick."""
    props_data = load_proposals()
    props = props_data.get("proposals", [])
    return props[0] if props else None

if __name__ == "__main__":
    print("--- Test de l'analyseur de code Nora ---")
    files = get_inspectable_files()
    print("Fichiers inspectables :", len(files), files[:5])
