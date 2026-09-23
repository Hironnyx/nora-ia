"""
Gestionnaire de Projets Haute Fidélité pour Maverick (Project Manager Hub) :
- Suivi structuré des projets (Code/IA, Impression 3D, Électronique, Domotique, etc.)
- Checklist de tâches interactives avec calcul automatique de la progression en %
- Liens directs vers les dossiers Windows et dépôts GitHub
- Analyse stratégique et conseils automatisés de Nora & l'Agent Architecte
- Persistance dans maverick_projects.json
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

PROJECTS_FILE = BASE_DIR / "maverick_projects.json"

DEFAULT_PROJECTS = [
    {
        "id": "proj_nora_core",
        "title": "Nora Copilote IA & Mascotte Zero Two",
        "category": "Code / IA",
        "status": "En cours",
        "priority": "Haute",
        "folder_path": str(BASE_DIR),
        "github_repo": "https://github.com/Hironnyx/nora-ia",
        "deadline": "2026-10-15",
        "tasks": [
            {"id": 1, "text": "Moteur cinématique de marche plein corps sans coupure", "done": True},
            {"id": 2, "text": "Animal de compagnie autonome de Nora", "done": True},
            {"id": 3, "text": "Agora multi-agents avec pages individuelles", "done": True},
            {"id": 4, "text": "Intégration de l'atelier d'impression 3D PrusaSlicer", "done": False},
            {"id": 5, "text": "Compilation finale de Nora.exe pour Maverick", "done": False}
        ],
        "notes": "Agent autonome complet avec délibération récursive de masse, synthèse vocale RVC Zero Two et contrôle du PC.",
        "ai_review": "Projet prioritaire majeur. Finaliser l'atelier d'impression 3D et le gestionnaire de filament pour une suite d'outils parfaite."
    },
    {
        "id": "proj_3d_cases",
        "title": "Atelier Impression 3D & Boîtiers Électroniques",
        "category": "Impression 3D",
        "status": "En cours",
        "priority": "Haute",
        "folder_path": str(Path.home() / "Documents" / "Impression3D"),
        "github_repo": "",
        "deadline": "2026-10-30",
        "tasks": [
            {"id": 1, "text": "Configurer les profils de tranchage PrusaSlicer pour PLA et PETG", "done": True},
            {"id": 2, "text": "Modéliser un support de bureau avec lueur LED", "done": False},
            {"id": 3, "text": "Calibrer les rétractions pour éliminer le stringing", "done": False},
            {"id": 4, "text": "Imprimer un prototype d'essai à 0.20mm", "done": False}
        ],
        "notes": "Pièces mécaniques et boîtiers imprimés avec PrusaSlicer. Bobines PLA et PETG prêtes.",
        "ai_review": "Conseil de Nora : privilégiez un remplissage gyroid à 20% pour une résistance mécanique uniforme dans les 3 axes."
    },
    {
        "id": "proj_smart_workspace",
        "title": "Ambiance Lumineuse & Domotique Bureau",
        "category": "Domotique",
        "status": "En cours",
        "priority": "Moyenne",
        "folder_path": "",
        "github_repo": "",
        "deadline": "2026-11-10",
        "tasks": [
            {"id": 1, "text": "Synchroniser les lumières Philips Hue avec le statut de Nora", "done": True},
            {"id": 2, "text": "Programmer la scène d'ambiance Nuit et la scène Zero Two", "done": True},
            {"id": 3, "text": "Activer la bascule automatique en Mode Gaming Ultra", "done": False}
        ],
        "notes": "Espace de travail ergonomique et immersif avec retour visuel d'état.",
        "ai_review": "L'automatisation des scènes d'ambiance selon l'heure renforce le confort visuel de Maverick lors des sessions tardives."
    }
]

class ProjectManager:
    """Gestionnaire de projets pour Maverick."""

    def __init__(self):
        self.projects: List[Dict[str, Any]] = self._load_projects()

    def _load_projects(self) -> List[Dict[str, Any]]:
        if not PROJECTS_FILE.exists():
            self._save_projects(DEFAULT_PROJECTS)
            return list(DEFAULT_PROJECTS)
        try:
            with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else list(DEFAULT_PROJECTS)
        except Exception as e:
            print(f"Erreur chargement projets : {e}")
            return list(DEFAULT_PROJECTS)

    def _save_projects(self, data: Optional[List[Dict[str, Any]]] = None):
        if data is not None:
            self.projects = data
        try:
            with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.projects, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde projets : {e}")

    def get_all(self) -> List[Dict[str, Any]]:
        # Mettre à jour la progression de chaque projet
        for p in self.projects:
            tasks = p.get("tasks", [])
            if tasks:
                done = sum(1 for t in tasks if t.get("done"))
                p["progress"] = int((done / len(tasks)) * 100)
            else:
                p["progress"] = 0
        return self.projects

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        for p in self.projects:
            if p.get("id") == project_id:
                return p
        return None

    def create_project(self, title: str, category: str = "Autre", priority: str = "Moyenne",
                       folder_path: str = "", github_repo: str = "", notes: str = "", deadline: str = "") -> Dict[str, Any]:
        new_id = f"proj_{int(time.time())}_{len(self.projects) + 1}"
        new_proj = {
            "id": new_id,
            "title": title.strip(),
            "category": category,
            "status": "En cours",
            "priority": priority,
            "folder_path": folder_path.strip(),
            "github_repo": github_repo.strip(),
            "deadline": deadline.strip(),
            "tasks": [],
            "notes": notes.strip(),
            "progress": 0,
            "created_at": time.strftime("%d/%m/%Y"),
            "ai_review": "Projet initialisé. Définissez les premières étapes pour que Nora puisse vous orienter."
        }
        self.projects.append(new_proj)
        self._save_projects()
        return new_proj

    def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        p = self.get_project(project_id)
        if not p:
            return False
        for k, v in updates.items():
            p[k] = v
        self._save_projects()
        return True

    def delete_project(self, project_id: str) -> bool:
        initial_len = len(self.projects)
        self.projects = [p for p in self.projects if p.get("id") != project_id]
        if len(self.projects) != initial_len:
            self._save_projects()
            return True
        return False

    def add_task(self, project_id: str, task_text: str) -> bool:
        p = self.get_project(project_id)
        if not p or not task_text.strip():
            return False
        tasks = p.setdefault("tasks", [])
        next_id = max([t.get("id", 0) for t in tasks], default=0) + 1
        tasks.append({"id": next_id, "text": task_text.strip(), "done": False})
        self._save_projects()
        return True

    def toggle_task(self, project_id: str, task_id: int) -> bool:
        p = self.get_project(project_id)
        if not p:
            return False
        for t in p.get("tasks", []):
            if t.get("id") == task_id:
                t["done"] = not t.get("done", False)
                self._save_projects()
                return True
        return False

    def delete_task(self, project_id: str, task_id: int) -> bool:
        p = self.get_project(project_id)
        if not p:
            return False
        p["tasks"] = [t for t in p.get("tasks", []) if t.get("id") != task_id]
        self._save_projects()
        return True

    def open_folder(self, project_id: str) -> bool:
        p = self.get_project(project_id)
        if not p or not p.get("folder_path"):
            return False
        path_str = p["folder_path"]
        if Path(path_str).exists():
            try:
                os.startfile(path_str)
                return True
            except Exception:
                pass
        return False

    def ask_nora_advice(self, project_id: str) -> str:
        """Génère une recommandation stratégique par Nora et l'Agent Architecte."""
        p = self.get_project(project_id)
        if not p:
            return "Projet introuvable."

        title = p.get("title", "")
        cat = p.get("category", "")
        tasks = p.get("tasks", [])
        pending = [t["text"] for t in tasks if not t.get("done")]
        done = [t["text"] for t in tasks if t.get("done")]

        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=api_key)
                prompt = (
                    f"Tu es Nora, l'assistante IA de Maverick au style Zero Two, conseillée par l'Agent Architecte. "
                    f"Voici l'état du projet de Maverick '{title}' (Catégorie: {cat}) :\n"
                    f"- Tâches accomplies : {', '.join(done) if done else 'Aucune'}\n"
                    f"- Tâches en attente : {', '.join(pending) if pending else 'Toutes terminées'}\n"
                    f"- Notes : {p.get('notes', '')}\n\n"
                    f"Donne une recommandation concise, motivante et concrète (2-3 phrases) à Maverick "
                    f"en vous adressant à lui avec vouvoiement et respect."
                )
                resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.4)
                )
                if resp and resp.text:
                    advice = resp.text.strip()
                    p["ai_review"] = advice
                    self._save_projects()
                    return advice
            except Exception as e:
                print(f"Erreur conseil IA projet : {e}")

        # Fallback intelligent
        if pending:
            advice = f"Maverick, concentrez vos efforts sur la prochaine étape : '{pending[0]}'. L'essaim et moi restons à vos côtés pour concrétiser ce jalon."
        elif done:
            advice = "Toutes les tâches actuelles sont finalisées avec brio, Maverick ! Nous pouvons valider ce projet ou ajouter de nouveaux objectifs."
        else:
            advice = "Maverick, définissons les 3 premières tâches concrètes pour lancer la dynamique de ce projet."

        p["ai_review"] = advice
        self._save_projects()
        return advice

# Singleton
project_manager = ProjectManager()

if __name__ == "__main__":
    print("Test du Project Manager...")
    projs = project_manager.get_all()
    print(f"Nombre de projets chargés : {len(projs)}")
    for p in projs:
        print(f"- {p['title']} [{p['category']}] ({p['progress']}%)")
    adv = project_manager.ask_nora_advice(projs[0]["id"])
    print(f"Conseil de Nora : {adv}")
